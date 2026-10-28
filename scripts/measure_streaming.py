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
    assert n in (500,1000,2000,5000) and variant in ('legacy','stream')
    # Hard 1.5 GiB address-space ceiling; early stop at 1.2 GiB RSS.
    resource.setrlimit(resource.RLIMIT_AS,(1536*1024**2,1536*1024**2))
    out=Path('experiments/streaming')/f'{variant}_{n}.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    source_hashes={p:__import__('hashlib').sha256(Path(p).read_bytes()).hexdigest() for p in ('crypto/streaming.py','scripts/measure_streaming.py')}
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
        store=SQLiteStore() if variant=='legacy' else StreamingStore(dbpath)
        engine=DataEngine(store,Synthetic());reports=[]
        rules={s:SpotFilters(symbol=s,source='fixture:bottleneck-v1',status='assumed',note='synthetic',tick='.01',min_qty='.001',max_qty='1000',step='.001') for s in COINS}
        if variant=='legacy':bars={s:[candle(s,'15m',AT+timedelta(minutes=15*i)) for i in range(-1,n+18)] for s in COINS}
        else:
            for s in COINS:
                for start in range(-1,n+18,100):
                    store.add_candles('bars',(candle(s,'15m',AT+timedelta(minutes=15*i)) for i in range(start,min(start+100,n+18))))
        phases['setup']=time.perf_counter()-started;snapshot('setup',engine)
        phase='analysis';t=time.perf_counter()
        async def analysis():
            for i in range(n):
                at=AT+timedelta(minutes=15*i)
                if variant=='legacy':reports.extend(await run_research(engine,at,COINS))
                else:await store.prepare_research(engine,at,COINS)
                if (i+1)%500==0:snapshot('analysis_'+str(i+1),engine)
        asyncio.run(analysis());phases[phase]=time.perf_counter()-t
        phase='initialize';t=time.perf_counter()
        report_hash=report_digest(reports) if variant=='legacy' else store.seal()['reports']
        plan=ResearchPlan(coins=COINS,source='fixture:bottleneck-v1',dataset_sha256='1'*64,
                report_hashes=(report_hash,report_digest([]),report_digest([])),
                development=Period(start=AT-timedelta(minutes=15),end=max(AT+timedelta(days=4),AT+timedelta(minutes=15*(n+18),hours=4))),
                validation=Period(start=dt('2025-02-01'),end=dt('2025-03-01')),
                independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')))
        args=dict(store=store,plan=plan,policy=JointPolicy(),filters=rules)
        runner=FixtureJointRunner(**args,reports=reports,bars=bars) if variant=='legacy' else StreamingFixtureRunner(**args)
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
        rows=[]
        for (file,line,fn),v in pstats.Stats(prof).stats.items():
            rows.append(dict(file=file,line=line,function=fn,calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]))
        rows.sort(key=lambda r:-r['cumulative_seconds'])
        tables=('results','datasets','analyses','joint_states') if variant=='legacy' else ('results','datasets','analyses','stream_input','stream_states','stream_history')
        result=dict(status='complete',variant=variant,n=n,elapsed=sum(phases.values()),phases=phases,
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,samples=samples,profile=rows[:40],
                    first_100_replay_seconds=sum(step_times[:100]),last_100_replay_seconds=sum(step_times[-100:]),
                    trades=len(runner._read()[1].trades),snapshot=runner.snapshot(),reconciled=True,
                    sql_payload_bytes={table:store.db.execute(f'SELECT coalesce(sum(length(payload)),0) FROM {table}').fetchone()[0] for table in tables},
                    address_space_limit_bytes=1536*1024**2,rss_stop_bytes=int(1.2*1024**3),timeout_seconds=360 if n==5000 else 180,
                    historical_data_used=False,independent_test_opened=False,storage_parent='/workspace',sqlite_temp_parent=directory,
                    source_sha256=source_hashes)
        out.write_text(json.dumps(result,indent=2)+'\n');store.close()
        print(variant,n,round(result['elapsed'],3),result['peak_rss_kib'],flush=True)

if __name__=='__main__':main(int(sys.argv[1]),sys.argv[2])
