"""Exacte analyse-/replayreferentie, 100 synthetische stappen; geen jaar of marktdata."""
import asyncio,gzip,json,sys
from datetime import timedelta,datetime,timezone
from pathlib import Path
from scripts.measure_scalability import AT,COINS,Synthetic,candle
from crypto.analysis import run_research
from crypto.data import DataEngine
from crypto.protocol import ResearchPlan,Period,report_digest
from crypto.readiness import dt
from crypto.readiness_runner import FixtureJointRunner
from crypto.joint_portfolio import JointPolicy
from crypto.sim_execution import SpotFilters
from crypto.storage import SQLiteStore
import crypto.storage as storage


def capture():
 s=SQLiteStore();engine=DataEngine(s,Synthetic());reports=[]
 async def analysis():
  for i in range(100):reports.extend(await run_research(engine,AT+timedelta(minutes=15*i),COINS))
 asyncio.run(analysis())
 p=ResearchPlan(coins=COINS,source='fixture:scalability-reference',dataset_sha256='2'*64,report_hashes=(report_digest(reports),report_digest([]),report_digest([])),development=Period(start=AT-timedelta(minutes=15),end=AT+timedelta(days=4)),validation=Period(start=dt('2025-02-01'),end=dt('2025-03-01')),independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')))
 rules={sym:SpotFilters(symbol=sym,source='fixture:reference',status='assumed',note='synthetic',tick='.01',min_qty='.001',max_qty='1000',step='.001') for sym in COINS}
 bars={sym:[candle(sym,'15m',AT+timedelta(minutes=15*i)) for i in range(-1,118)] for sym in COINS}
 r=FixtureJointRunner(store=s,plan=p,policy=JointPolicy(),filters=rules,reports=reports,bars=bars)
 async def replay():
  for i in range(100):await r.run([AT+timedelta(minutes=15*i)])
 asyncio.run(replay());r._read()[1].reconcile()
 result={t:s.list(t) for t in ('results','analyses','regimes','scan_runs','joint_states','joint_batches','joint_settlements')}
 result['audit']=s.audits();s.close();return result

if __name__=='__main__':
 storage.now=lambda:datetime(2026,10,27,tzinfo=timezone.utc)
 raw=json.dumps(capture(),sort_keys=True).encode()
 Path(sys.argv[1]).write_bytes(gzip.compress(raw,mtime=0))
