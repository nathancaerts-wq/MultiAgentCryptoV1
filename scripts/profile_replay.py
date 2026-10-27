"""Begrensd cProfile-onderzoek van uitsluitend synthetische data."""
import argparse,asyncio,cProfile,json,pstats,resource,signal,time
from pathlib import Path
from datetime import timedelta
from crypto.data import Candle
from crypto.readiness import dt
from crypto.protocol import ResearchPlan,Period,report_digest
from crypto.joint_portfolio import JointPolicy
from crypto.readiness_runner import FixtureJointRunner
from crypto.sim_execution import SpotFilters
from crypto.storage import SQLiteStore

class BudgetExceeded(Exception):pass

def main():
 p=argparse.ArgumentParser();p.add_argument('--size',type=int,required=True);p.add_argument('--label',required=True);p.add_argument('--seconds',type=int,default=30);a=p.parse_args()
 out=Path('experiments/performance')/f'{a.label}_{a.size}'
 started=time.perf_counter();prof=cProfile.Profile();steps=0;stage='data_input';times={};runner=None
 def timeout(*_):raise BudgetExceeded()
 signal.signal(signal.SIGALRM,timeout);signal.alarm(a.seconds);prof.enable()
 try:
  start=dt('2024-01-01');end=start+timedelta(minutes=15*a.size);coins=('BTCEUR','ETHEUR','SOLEUR')
  bars={s:[Candle(symbol=s,interval='15m',opened=start+timedelta(minutes=15*i),closed=start+timedelta(minutes=15*(i+1)),open=100,high=100,low=100,close=100,volume=1000,quote_volume=100000,source='fixture:profile') for i in range(a.size)] for s in coins}
  times[stage]=time.perf_counter()-started;stage='initialization';t=time.perf_counter()
  plan=ResearchPlan(coins=coins,source='fixture:profile',dataset_sha256='1'*64,report_hashes=(report_digest([]),)*3,development=Period(start=start,end=end),validation=Period(start=dt('2025-02-01'),end=dt('2025-03-01')),independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')))
  filters={s:SpotFilters(symbol=s,source='fixture:profile',status='assumed',note='synthetic',tick='.01',min_qty='.001',max_qty='1000',step='.001') for s in coins}
  store=SQLiteStore();runner=FixtureJointRunner(store=store,plan=plan,policy=JointPolicy(),filters=filters,reports=[],bars=bars)
  times[stage]=time.perf_counter()-t;stage='replay';t=time.perf_counter()
  async def run():
   nonlocal steps
   for i in range(a.size):
    await runner.run([start+timedelta(minutes=15*i)]);steps=i+1
  asyncio.run(run());times[stage]=time.perf_counter()-t;status='completed'
 except BudgetExceeded:status='timeout'
 finally:
  signal.alarm(0);prof.disable();prof.dump_stats(str(out)+'.prof')
 stats=pstats.Stats(prof)
 rows=[dict(file=k[0],line=k[1],function=k[2],calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]) for k,v in stats.stats.items()]
 rows.sort(key=lambda r:r['cumulative_seconds'],reverse=True)
 result=dict(status=status,size_per_coin=a.size,coins=3,steps=steps,candles_processed=steps*3,elapsed=time.perf_counter()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,stage=stage,stage_seconds=times,budget_seconds=a.seconds,profiled=True,synthetic_only=True,complete_agent_reports=False,top=rows[:45],components=[r for r in rows if '/crypto/' in r['file']])
 if status=='completed':
  _,ledger=runner._read();ledger.reconcile();result.update(transactions=len(ledger.trades),ledger_consistent=True)
 Path(str(out)+'.json').write_text(json.dumps(result,indent=2)+'\n');print(a.label,a.size,status,steps,flush=True)
if __name__=='__main__':main()
