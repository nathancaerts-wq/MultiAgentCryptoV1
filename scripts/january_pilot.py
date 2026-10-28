"""One authorized pilot. Persistent checkpoints; existing run is never overwritten."""
import asyncio,json,os,resource,signal,time,hashlib
from pathlib import Path
from datetime import timedelta
from collections import Counter
from decimal import Decimal as D
from crypto.january_pilot import *
from crypto.protocol import ResearchPlan,Period,report_digest
from crypto.data import DataEngine,SECONDS,validate_series
from crypto.sim_execution import canonical
from scripts.january_quality import audit
from scripts.phase6b_full_audit import CachedDownloads,MonthlyAuditAdapter

OUT=Path('experiments/january_pilot');DB=Path('/workspace/january_pilot.sqlite3')
class JanuaryData:
 def __init__(self,store):self.store=store
 def fetch(self,s,tf,a,b):
  if s not in COINS or not START<=a<b<=END:raise ValueError('Outside January data')
  rows=list(self.store.candles('history',s,tf,a,b));return validate_series(rows,s,tf,a,b,b)

def main():
 if DB.exists() or (OUT/'result.json').exists():raise ValueError('Existing run preserved; explicit resume required')
 resource.setrlimit(resource.RLIMIT_AS,(1536*1024**2,1536*1024**2))
 os.environ['SQLITE_TMPDIR']='/workspace'
 begun=time.perf_counter();phase='quality';steps=0;prepared=0;runner=None;store=None
 def diagnostic(reason):
  result=dict(status='incomplete_diagnostic',reason=reason,phase=phase,processed_steps=steps,prepared_steps=prepared,processed_execution_candles=steps*3,elapsed=time.perf_counter()-begun,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint=str(DB),independent_test_opened=False)
  OUT.joinpath('result.json').write_text(json.dumps(result,indent=2)+'\n')
 def interrupt(*_):diagnostic('timeout_or_termination');os._exit(124)
 signal.signal(signal.SIGTERM,interrupt)
 try:
  quality=audit()
  if quality!=json.loads((OUT/'quality.json').read_text()):raise ValueError('Quality changed before run')
  store=JanuaryStore(DB);cache=CachedDownloads('/workspace/phase6b_archive_cache',max_requests=0)
  phase='import'
  for s in COINS:
   for tf in ('15m','1h','4h'):
    a=MonthlyAuditAdapter(cache)
    for day in range(31):
     rows=a.fetch(s,tf,START+timedelta(days=day),START+timedelta(days=day+1))
     store.add_candles('history',rows)
     if tf=='15m':store.add_candles('bars',rows)
  phase='analysis';engine=DataEngine(store,JanuaryData(store))
  async def prepare():
   nonlocal prepared
   at=ENTRY
   while at<=LAST_ENTRY:
    reports=await store.prepare_research(engine,at,COINS)
    if len(reports)!=3 or any(any(f['status']!='complete' for f in r.data['frames'].values()) for r in reports):raise ValueError('Incomplete analysis')
    prepared+=1;at+=timedelta(minutes=15)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>1.2*1024**2:raise MemoryError('RSS budget')
  asyncio.run(prepare());seal=store.seal()
  plan=ResearchPlan(coins=COINS,source=SOURCE,dataset_sha256=digest(quality),report_hashes=(seal['reports'],report_digest([]),report_digest([])),development=Period(start=START,end=END),validation=Period(start=dt('2025-02-01'),end=dt('2025-12-31T20:00')),independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')),hypotheses=('aligned_trend',))
  manifest=dict(protocol=json.loads((OUT/'protocol.json').read_text()),quality=quality,input_seal=seal,plan=plan.model_dump(mode='json'),policy=JointPolicy().model_dump(mode='json'),filters={s:f.model_dump(mode='json') for s,f in filters().items()},files={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('crypto/january_pilot.py','scripts/january_pilot.py','crypto/streaming.py','experiments/january_pilot/protocol.json')})
  (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
  phase='replay';runner=JanuaryRunner(store=store,plan=plan,policy=JointPolicy(),filters=filters())
  async def replay():
   nonlocal steps
   for i in range(2305):
    await runner.run((ENTRY+timedelta(minutes=15*i),));steps+=1
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>1.2*1024**2:raise MemoryError('RSS budget')
  asyncio.run(replay());phase='verification';runner.verify_history();state,l=runner._read();l.reconcile()
  if l.position or state['pending'] or state['at']!=END.isoformat():raise ValueError('Incomplete terminal portfolio')
  restored=JanuaryRunner(store=store,plan=plan,policy=JointPolicy(),filters=filters())
  if restored.snapshot()!=runner.snapshot():raise ValueError('Checkpoint reconstruction mismatch')
  reasons=Counter();candidates=approved=rejected=rejected_buy=approved_exits=0
  for (raw,) in store.db.execute('SELECT payload FROM joint_batches'):
   b=json.loads(raw)
   approved_exits+=int(bool(b['exit'] and b['exit']['approved'] and b['exit']['candidate']['result']['action']=='EXIT_CANDIDATE'))
   for c in b['candidates']:
    candidates+=int(c['decision']['result']['action']=='BUY_CANDIDATE')
    rejected_buy+=int(c['decision']['result']['action']=='BUY_CANDIDATE' and not c['selected'])
    approved+=int(c['selected']);rejected+=int(not c['selected']);reasons[c['reason']]+=int(not c['selected'])
  trades=list(l.trades);wins=[D(t['net']) for t in trades if D(t['net'])>0];losses=[D(t['net']) for t in trades if D(t['net'])<0]
  result=dict(status='complete',processed_steps=steps,prepared_steps=prepared,processed_execution_candles=2304*3,candidate_signals=candidates,approved_reservations=approved,rejected_buy_proposals=rejected_buy,approved_exit_proposals=approved_exits,total_fees=l.fees,rejected_coin_assessments=rejected,rejections=dict(reasons),trades=len(trades),winrate=D(len(wins))/len(trades) if trades else None,net=l.realized,average_win=sum(wins)/len(wins) if wins else None,average_loss=sum(losses)/len(losses) if losses else None,expectancy=l.realized/len(trades) if trades else None,max_drawdown=l.max_drawdown,per_coin={s:{'trades':sum(t['symbol']==s for t in trades),'net':sum((D(t['net']) for t in trades if t['symbol']==s),D(0))} for s in COINS},portfolio=runner.snapshot(),elapsed=time.perf_counter()-begun,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint=str(DB),independent_test_opened=False)
  (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
 except Exception as exc:diagnostic(type(exc).__name__+': '+str(exc));raise
 finally:
  if store:store.close()
if __name__=='__main__':main()
