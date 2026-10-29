"""Exactly one separately approved continuation; no restart or policy changes."""
import asyncio,json,resource,signal,time
from pathlib import Path
from collections import Counter
from scripts.phase6h_b_replay import OUT,DB,STEP,checked_manifest,make_plan,sha
from crypto.historical_recovery import RecoveryStore,HistoricalRecoveryRunner
from crypto.development_2024 import policy,filters,END
import scripts.development_2024 as old
R=OUT/'resume_300'

def write(name,value):
    p=R/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(value,indent=2,default=str)+'\n');t.replace(p)

def boundaries(last,end):
    first=last+STEP
    count=int((end-first)/STEP)+1
    if count!=1937:raise ValueError('Not exactly the approved remainder')
    return first,count

def main():
    began=time.monotonic();store=runner=None;at=None
    # Exclusive attempt marker persists even when the process crashes.
    reg=json.loads((R/'registration.json').read_text());m=json.loads(Path(reg['manifest']).read_text())
    if sha(reg['manifest'])!=reg['sha256']:raise ValueError('Resume manifest changed')
    for p,h in m['files'].items():
        if sha(p)!=h:raise ValueError('Registered resume input changed: '+p)
    with (R/'attempt.json').open('x') as f:json.dump(dict(started=True,manifest=reg['sha256'],maximum_seconds=300),f)
    resource.setrlimit(resource.RLIMIT_AS,(1610612736,)*2)
    def stop(*_):raise TimeoutError('Explicit single 300-second continuation limit')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,300-(time.monotonic()-began)))
    try:
        from shutil import disk_usage
        original=checked_manifest()
        store=RecoveryStore(DB)
        runner=HistoricalRecoveryRunner(store=store,plan=make_plan(original),policy=policy('baseline'),filters=filters())
        initial,l=runner._read()
        if initial['hash']!=m['checkpoint_hash'] or initial['at']!=m['last_committed'] or initial['pending']:
            raise ValueError('Approved checkpoint mismatch')
        at,count=boundaries(old.dt(initial['at']),END)
        processed=0
        async def run():
            nonlocal at,processed
            while at<=END:
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>1288490188:raise MemoryError('RSS limit')
                if disk_usage('/workspace').free<2147483648:raise OSError('Disk reserve')
                await runner.run((at,));processed+=1
                if processed%250==0:print(json.dumps(dict(processed=processed,at=str(at),seconds=time.monotonic()-began)),flush=True)
                at+=STEP
        asyncio.run(run())
        if processed!=1937:raise ValueError('Remainder count differs')
        old.OUT=OUT
        result=old.metrics(runner,'recovery24h')
        state,ledger=runner._read();starts=[];expires=[];actions=Counter()
        for e in ledger.events:
            actions[e['action']]+=1
            if e['action']=='cooldown_started':starts.append(e)
            if e['action']=='cooldown_expired':expires.append(e)
        intervals=[dict(start=e['at'],until=e['details']['until'],epoch=e['details']['epoch']) for e in starts]
        result.update(recovery=state['recovery'],cooldown_intervals=intervals,cooldown_count=len(starts),cooldown_expiries=len(expires),
          cooldown_seconds=sum((min(END,old.dt(e['until']))-old.dt(e['start'])).total_seconds() for e in intervals),
          risk_events={k:actions[k] for k in ('daily_loss_pause','drawdown_pause','joint_emergency_stop')},loss_streak_pause_from=None,pause_until=None,
          elapsed_seconds=time.monotonic()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,hypothetical_filters_unproven=True)
        restored=HistoricalRecoveryRunner(store=store,plan=make_plan(original),policy=policy('baseline'),filters=filters())
        if restored.snapshot()!=runner.snapshot():raise ValueError('Reconstruction differs')
        if len(ledger.trades)!=initial['recovery']['processed'] or not ledger.drawdown_paused:
            raise ValueError('Latched drawdown protection changed')
        result['checkpoint_reconstruction_equal']=True
        result['elapsed_seconds']=time.monotonic()-began
        result['resume_processed_boundaries']=processed
        if (OUT/'result.json').exists():raise ValueError('Existing result preserved')
        with (OUT/'result.json').open('x') as f:json.dump(result,f,indent=2,default=str);f.write('\n')
        write('completion.json',dict(status='complete',processed=processed,seconds=time.monotonic()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,final_state_hash=state['hash']))
    except BaseException as exc:
        v=dict(status='incomplete_diagnostic',reason=str(exc),seconds=time.monotonic()-began,next_boundary=at)
        if runner:
            try:
                s,l=runner._read();v.update(last_committed=s['at'],hash=s['hash'],pending=s['pending'],recovery=s['recovery'])
            except Exception as e:v['checkpoint_error']=str(e)
        write('interruption.json',v);raise
    finally:
        if store:store.close()
if __name__=='__main__':main()
