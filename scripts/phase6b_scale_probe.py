"""Meet de echte fixture-runner met zes munten/366 dagen; begrensde subprocess."""
import json, os, resource, subprocess, sys, time
from pathlib import Path
OUTPUT=Path('experiments/phase6b_scale_probe.json')

def child():
 resource.setrlimit(resource.RLIMIT_AS,(1_500_000_000,1_500_000_000))
 import asyncio
 from datetime import timedelta
 from crypto.data import Candle,WATCHLIST
 from crypto.readiness import dt
 from crypto.protocol import ResearchPlan,Period,report_digest
 from crypto.joint_portfolio import JointPolicy
 from crypto.readiness_runner import FixtureJointRunner
 from crypto.sim_execution import SpotFilters
 from crypto.storage import SQLiteStore
 start=dt('2024-01-01');end=dt('2025-01-01');n=366*96
 begun=time.monotonic();state=dict(candles_per_coin=n,coins=6,completed_steps=0,completed=False)
 def checkpoint(phase):
  state.update(phase=phase,elapsed_seconds=time.monotonic()-begun,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  OUTPUT.write_text(json.dumps(state,indent=2)+'\n')
 checkpoint('building_candles')
 bars={}
 for s in WATCHLIST:
  bars[s]=[Candle(symbol=s,interval='15m',opened=start+timedelta(minutes=15*i),closed=start+timedelta(minutes=15*(i+1)),open=100,high=100,low=100,close=100,volume=1000,quote_volume=100000,source='fixture:scale') for i in range(n)]
 checkpoint('initializing_real_joint_runner')
 plan=ResearchPlan(coins=tuple(sorted(WATCHLIST)),source='fixture:scale',dataset_sha256='1'*64,report_hashes=(report_digest([]),)*3,development=Period(start=start,end=end),validation=Period(start=dt('2025-02-01'),end=dt('2025-03-01')),independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')))
 filters={s:SpotFilters(symbol=s,source='fixture:scale',status='assumed',note='synthetic',tick='.01',min_qty='.001',max_qty='1000',step='.001') for s in WATCHLIST}
 store=SQLiteStore();runner=FixtureJointRunner(store=store,plan=plan,policy=JointPolicy(),filters=filters,reports=[],bars=bars)
 checkpoint('replaying_real_joint_runner_no_reports')
 async def replay():
  for i in range(n):
   await runner.run([start+timedelta(minutes=15*i)])
   state['completed_steps']=i+1
   if i%100==0: checkpoint('replaying_real_joint_runner_no_reports')
 asyncio.run(replay());state['completed']=True;checkpoint('complete');store.close()

def main():
 if '--child' in sys.argv: child();return
 env=dict(os.environ,PYTHONPATH='.')
 try:
  p=subprocess.run([sys.executable,__file__,'--child'],env=env,timeout=45,capture_output=True,text=True)
  status=dict(exit_code=p.returncode,error=p.stderr[-1500:])
 except subprocess.TimeoutExpired: status=dict(timeout_seconds=45)
 state=json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {}
 state.update(status);state['historical_performance_computed']=False
 OUTPUT.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))
if __name__=='__main__':main()
