"""Bounded synthetic-only measurement, no year or historical execution."""
import asyncio
import cProfile
import gc
import json
import os
from pathlib import Path
import pstats
import resource
import signal
import sys
import tempfile
import time
from collections import Counter
from datetime import timedelta
from decimal import Decimal as D
from scripts.measure_scalability import AT, COINS, Synthetic, candle
from crypto.analysis import run_research
from crypto.data import DataEngine
from crypto.joint_portfolio import JointPolicy
from crypto.protocol import ResearchPlan, Period, report_digest
from crypto.readiness import dt
from crypto.readiness_runner import FixtureJointRunner
from crypto.sim_execution import SpotFilters
from crypto.storage import SQLiteStore
from crypto.streaming import StreamingStore, StreamingFixtureRunner


def main(n,variant):
    assert n in (100,500,1000) and variant in ('before','after')
    # Hard 1.5 GiB address-space ceiling; early stop at 1.2 GiB RSS.
    resource.setrlimit(resource.RLIMIT_AS,(1536*1024**2,1536*1024**2))
    out=Path('experiments/audit_hash')/f'{variant}_{n}.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    source_hashes={p:__import__('hashlib').sha256(Path(p).read_bytes()).hexdigest() for p in ('crypto/streaming.py','scripts/measure_audit.py')}
    import crypto.storage as st,crypto.data as dat
    from datetime import datetime,timezone
    st.now=lambda:datetime(2026,10,27,tzinfo=timezone.utc)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return datetime(2026,10,27,tzinfo=timezone.utc)
    dat.datetime=Clock
    started=time.perf_counter();samples=[];phases={};step_times=[];phase='setup'
    prof=cProfile.Profile();prof.enable()
    def snapshot(label,engine=None):
        gc.collect()
        counts=Counter(type(o).__module__+'.'+type(o).__name__ for o in gc.get_objects())
        sample=dict(label=label,elapsed=time.perf_counter()-started,rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    tracked_objects=sum(counts.values()),objects=dict(counts.most_common(15)),
                    candles=counts['crypto.data.Candle'],messages=counts['crypto.models.Message'])
        if engine:sample['caches']={k:len(getattr(engine,k,{})) for k in ('_technical_cache','_candle_cache')}
        samples.append(sample)
        if sample['rss_kib']>int(1.2*1024**2):raise MemoryError('Early RSS stop at 1.2 GiB')
    def partial(*_):
        out.write_text(json.dumps(dict(status='timeout',n=n,variant=variant,phase=phase,samples=samples,phases=phases,elapsed=time.perf_counter()-started),indent=2)+'\n')
        os._exit(124)
    signal.signal(signal.SIGTERM,partial)
    with tempfile.TemporaryDirectory(prefix='stream-measure-',dir='/workspace') as directory:
        os.environ['SQLITE_TMPDIR']=directory
        dbpath=Path(directory)/'replay.sqlite3'
        if variant=='before':
            import subprocess,types
            baseline=types.ModuleType('crypto._audit_baseline');baseline.__package__='crypto'
            exec(subprocess.check_output(['git','show','00271e19a459491d3a68c58c53f49a37defd00b8:crypto/streaming.py']),baseline.__dict__)
            store=baseline.StreamingStore(dbpath);runner_class=baseline.StreamingFixtureRunner
        else:store=StreamingStore(dbpath);runner_class=StreamingFixtureRunner
        sys.path.insert(0,str(Path('tests').resolve()))
        from test_trade_agents import FixtureData
        engine=DataEngine(store,FixtureData());reports=[]
        rules={s:SpotFilters(symbol=s,source='fixture:bottleneck-v1',status='assumed',note='synthetic',tick='.01',min_qty='.001',max_qty='1000',step='.001') for s in COINS}
        for sym in COINS:
            for start in range(-1,n+18,100):
                rows=[]
                for i in range(start,min(start+100,n+18)):
                    c=candle(sym,'15m',AT+timedelta(minutes=15*i))
                    rows.append(c.model_copy(update=dict(open=D('106.4'),high=D(107),low=D(99) if i in (0,2,4) else D(106),close=D(100) if i in (0,2,4) else D('106.4'))))
                store.add_candles('bars',rows)
            for tf in ('15m','1h'):
                end=(AT+timedelta(minutes=15*(n+20))).replace(minute=0)
                store.add_candles('history',(c.model_copy(update={'quote_volume':D(20000)}) for c in FixtureData().fetch(sym,tf,AT-timedelta(days=7),end)))
        phases['setup']=time.perf_counter()-started;snapshot('setup',engine)
        phase='analysis';t=time.perf_counter()
        async def analysis():
            for i in range(n):
                at=AT+timedelta(minutes=15*i)
                await store.prepare_research(engine,at,COINS)
                if (i+1)%500==0:snapshot('analysis_'+str(i+1),engine)
        asyncio.run(analysis());phases[phase]=time.perf_counter()-t
        phase='initialize';t=time.perf_counter()
        report_hash=store.seal()['reports']
        plan=ResearchPlan(coins=COINS,source='fixture:bottleneck-v1',dataset_sha256='1'*64,
                report_hashes=(report_hash,report_digest([]),report_digest([])),
                development=Period(start=AT-timedelta(minutes=15),end=max(AT+timedelta(days=4),AT+timedelta(minutes=15*(n+18),hours=4))),
                validation=Period(start=dt('2025-02-01'),end=dt('2025-03-01')),
                independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')))
        args=dict(store=store,plan=plan,policy=JointPolicy(),filters=rules)
        runner=runner_class(**args)
        phases[phase]=time.perf_counter()-t;snapshot('initialized',engine)
        phase='replay';t=time.perf_counter()
        async def replay():
            for start in range(0,n,100):
                for i in range(start,min(start+100,n)):
                    begun=time.perf_counter()
                    await runner.run((AT+timedelta(minutes=15*i),))
                    step_times.append(time.perf_counter()-begun)
                if (start+100)%500==0:snapshot('replay_'+str(start+100),engine)
        asyncio.run(replay());phases[phase]=time.perf_counter()-t
        runner._read()[1].reconcile();snapshot('finished',engine)
        prof.disable()
        assert len(runner._read()[1].trades)>=3, 'Active trades missing'
        rows=[]
        for (file,line,fn),v in pstats.Stats(prof).stats.items():
            rows.append(dict(file=file,line=line,function=fn,calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]))
        rows.sort(key=lambda r:-r['cumulative_seconds'])
        tables=('results','datasets','analyses','stream_input','stream_states','stream_history')
        result=dict(status='complete',variant=variant,n=n,elapsed=sum(phases.values()),phases=phases,
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,samples=samples,profile=rows[:40],hash_profile=[r for r in rows if r['function'] in ('streamed_hash','pieces','raws','event_pieces')],
                    first_100_replay_seconds=sum(step_times[:100]),last_100_replay_seconds=sum(step_times[-100:]),
                    trades=len(runner._read()[1].trades),snapshot=runner.snapshot(),reconciled=True,
                    sql_payload_bytes={table:store.db.execute(f'SELECT coalesce(sum(length(payload)),0) FROM {table}').fetchone()[0] for table in tables},
                    address_space_limit_bytes=1536*1024**2,rss_stop_bytes=int(1.2*1024**3),timeout_seconds=360 if n==5000 else 180,
                    historical_data_used=False,independent_test_opened=False,storage_parent='/workspace',sqlite_temp_parent=directory,
                    source_sha256=source_hashes)
        result['content_hashes']={}
        import hashlib
        for table in ('results','analyses','regimes','scan_runs','stream_states','stream_history','joint_batches','joint_settlements','audit'):
            h=hashlib.sha256()
            query=f'SELECT * FROM {table} ORDER BY '+('id' if table in ('results','analyses','regimes','scan_runs','joint_batches','joint_settlements','audit') else 'portfolio,revision' if table=='stream_states' else 'portfolio,kind,seq')
            for row in store.db.execute(query):h.update(json.dumps(row,sort_keys=True).encode());h.update(b'\n')
            result['content_hashes'][table]=h.hexdigest()
        out.write_text(json.dumps(result,indent=2)+'\n');store.close()
        print(variant,n,round(result['elapsed'],3),result['peak_rss_kib'],flush=True)

if __name__=='__main__':main(int(sys.argv[1]),sys.argv[2])
