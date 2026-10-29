"""One approved 2024-only recovery comparison. No network or baseline replay."""
import argparse,asyncio,hashlib,json,os,resource,shutil,signal,sqlite3,time
from collections import Counter
from datetime import timedelta
from pathlib import Path
from decimal import Decimal as D
from crypto.historical_recovery import HistoricalRecoveryRunner,RecoveryStore,SOURCE,copy_inputs
from crypto.development_2024 import START,ENTRY,END,COINS,policy,filters
from crypto.protocol import ResearchPlan
from crypto.sim_execution import canonical,digest
import scripts.development_2024 as old
OUT=Path('experiments/phase6h_b');DB=Path('/workspace/phase6h_b_recovery.sqlite3')
ORIGINAL=Path('/workspace/development_2024.sqlite3');STEP=timedelta(minutes=15)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def write(name,value):
    p=OUT/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(value,indent=2,default=str)+'\n');t.replace(p)

def checked_manifest():
    r=json.loads((OUT/'execution_registration.json').read_text());p=Path(r['manifest'])
    if sha(p)!=r['sha256']:raise ValueError('Execution manifest changed')
    m=json.loads(p.read_text())
    for f,h in m['files'].items():
        if sha(f)!=h:raise ValueError('Registered file changed: '+f)
    return m

def make_plan(m):
    p=ResearchPlan.model_validate(m['baseline_plan'])
    return p.model_copy(update={'source':SOURCE})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','replay']);ap.add_argument('--resume',action='store_true');a=ap.parse_args()
    began=time.monotonic();store=runner=None;at=None
    resource.setrlimit(resource.RLIMIT_AS,(1610612736,)*2)
    def interrupt(*args):raise TimeoutError('Registered 1800-second limit/interruption')
    signal.signal(signal.SIGALRM,interrupt);signal.signal(signal.SIGTERM,interrupt);signal.alarm(1800)
    def check():
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>1288490188:raise MemoryError('Registered RSS limit')
        if shutil.disk_usage('/workspace').free<2147483648:raise OSError('Free disk reserve')
    try:
        m=checked_manifest();check()
        if a.phase=='prepare':
            if DB.exists():raise ValueError('Existing preparation preserved; no automatic restart')
            if sha(ORIGINAL)!=m['original_database_sha256']:raise ValueError('Original database changed')
            store=RecoveryStore(DB)
            source_db=sqlite3.connect('file:'+str(ORIGINAL)+'?mode=ro&immutable=1',uri=True)
            source_db.execute('PRAGMA query_only=ON')
            try:copy_inputs(source_db,store)
            finally:source_db.close()
            check();seal=store.verify_inputs()
            if seal!=m['input_seal']:raise ValueError('Copied input seal differs')
            write('preparation_approved.json',dict(status='complete',input_seal=seal,seconds=time.monotonic()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        else:
            if not (OUT/'preparation_approved.json').exists():raise ValueError('Preparation absent')
            if (OUT/'result.json').exists():raise ValueError('Completed result preserved')
            store=RecoveryStore(DB)
            runner=HistoricalRecoveryRunner(store=store,plan=make_plan(m),policy=policy('baseline'),filters=filters())
            state,ledger=runner._read();last=old.dt(state['at'])
            if last!=START and not a.resume:raise ValueError('Checkpoint exists; explicit --resume required')
            at=ENTRY if last==START else last if state['pending'] else last+STEP
            async def run():
                nonlocal at
                while at<=END:
                    await runner.run((at,))
                    if at==old.dt('2024-01-11T16:00'):
                        s,l=runner._read();baseline=json.loads(Path('experiments/development_2024/aligned_trend_baseline.json').read_text())
                        def financial(t):return {k:str(v) if isinstance(v,D) else v for k,v in t.items() if k not in ('entry_id','exit_id')}
                        actual=json.loads(canonical(list(l.trades)))
                        if l.cash!=D('197.03206319') or [financial(t) for t in actual]!=[financial(t) for t in baseline['trade_records']]:
                            raise ValueError('Financial prefix differs from baseline before recovery')
                        write('baseline_prefix_check.json',dict(passed=True,at=at,cash=l.cash,trades=3,financial_records_equal=True))
                    if int((at-ENTRY)/STEP)%1000==0:
                        check();s,l=runner._read()
                        print(canonical(dict(at=at,seconds=round(time.monotonic()-began,3),trades=len(l.trades),cash=l.cash,epoch=s['recovery']['epoch'])),flush=True)
                        write('progress.json',dict(at=at,revision=s['revision'],state_hash=s['hash'],recovery=s['recovery'],cash=l.cash,fees=l.fees,seconds=time.monotonic()-began))
                    at+=STEP
            asyncio.run(run());check()
            old.OUT=OUT
            result=old.metrics(runner,'recovery24h')
            state,ledger=runner._read();events=list(ledger.events)
            starts=[e for e in events if e['action']=='cooldown_started'];ends=[e for e in events if e['action']=='cooldown_expired']
            intervals=[dict(start=e['at'],until=e['details']['until'],epoch=e['details']['epoch']) for e in starts]
            cooldown_seconds=sum((min(END,old.dt(e['until']))-old.dt(e['start'])).total_seconds() for e in intervals)
            actions=Counter(e['action'] for e in events)
            result.update(recovery=state['recovery'],cooldown_intervals=intervals,cooldown_count=len(starts),cooldown_expiries=len(ends),cooldown_seconds=cooldown_seconds,
                          risk_events={k:actions[k] for k in ('daily_loss_pause','drawdown_pause','joint_emergency_stop')},loss_streak_pause_from=None,pause_until=None,
                          elapsed_seconds=time.monotonic()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,hypothetical_filters_unproven=True)
            restored=HistoricalRecoveryRunner(store=store,plan=make_plan(m),policy=policy('baseline'),filters=filters())
            if restored.snapshot()!=runner.snapshot() or restored._read()[0]['recovery']!=state['recovery']:raise ValueError('Checkpoint reconstruction mismatch')
            result['checkpoint_reconstruction_equal']=True
            write('result.json',result)
    except BaseException as exc:
        v=dict(status='incomplete_diagnostic',phase=a.phase,error=type(exc).__name__,reason=str(exc),next_boundary=at,seconds=time.monotonic()-began)
        if runner:
            try:
                s,l=runner._read();v.update(last_committed=s['at'],revision=s['revision'],state_hash=s['hash'],recovery=s['recovery'],pending=s['pending'])
            except Exception as e:v['checkpoint_error']=str(e)
        write('interruption_approved.json',v);raise
    finally:
        if store:store.close()
if __name__=='__main__':main()
