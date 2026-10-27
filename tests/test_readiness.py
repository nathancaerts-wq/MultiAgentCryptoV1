import asyncio
from datetime import timedelta
from decimal import Decimal as D
import pytest
from crypto.readiness import *
from crypto.readiness_runner import FixtureJointRunner
from crypto.research_benchmarks import BuyHoldIndex,cash_benchmark
from crypto.storage import SQLiteStore
from crypto.protocol import Period
from test_joint_portfolio import inputs,reports_at,COINS
from test_trade_agents import bar,AT,FixtureData,rules

@pytest.mark.parametrize('a,b',[('2025-01-15','2025-01-16'),('2026-01-01','2026-01-02'),('2025-01-14','2025-01-17'),('2025-01-01','2025-02-01')])
def test_locked(a,b):
 with pytest.raises(ValueError): permitted(dt(a),dt(b))

@pytest.mark.parametrize('name',list(PERIODS))
def test_allowed(name): permitted(*PERIODS[name])

def history(at=AT):
 f=FixtureData()
 return {tf:[c.model_copy(update={'quote_volume':D(20000)}) for c in f.fetch('BTCEUR',tf,at-timedelta(days=7),at)] for tf in ('15m','1h')}

def test_liquidity_future_and_gap():
 h=history(); assert admission(h,'BTCEUR',AT) is None
 h['15m'][-1]=h['15m'][-1].model_copy(update={'quote_volume':D(0)})
 assert admission(h,'BTCEUR',AT)=='liquiditeit_15m'
 h['15m'].append(bar(0,quote_volume=D('1e20')))
 assert admission(h,'BTCEUR',AT)=='liquiditeit_15m'
 h['1h'].pop(0)
 with pytest.raises(ValueError): admission(h,'BTCEUR',AT)

def test_low_hourly():
 h=history();h['1h']=[c.model_copy(update={'quote_volume':D(0)}) for c in h['1h']]
 assert admission(h,'BTCEUR',AT)=='liquiditeit_24h'

def test_manifest_mutation(tmp_path):
 p=tmp_path/'data';p.write_text('abc')
 m=manifest([p],{'risk':'.005'},[]);verify_manifest(m)
 p.write_text('def')
 with pytest.raises(ValueError):verify_manifest(m)

def test_manifest_config_mutation():
 m=manifest([],{'risk':'.005'},[]);m['configuration']['risk']='.01'
 with pytest.raises(ValueError):verify_manifest(m)

def test_metadata_unknown(): assert metadata_evidence(rules(),AT)=='historische_filters_onbewezen'

def test_cash(): assert cash_benchmark()['equity']==200

def test_index_hand_calculation_and_once():
 costs=__import__('crypto.sim_execution',fromlist=['FillCosts']).FillCosts(fee=0,spread=0,slippage=0)
 coins=WATCHLIST;b=BuyHoldIndex(coins,costs)
 b.enter(dict.fromkeys(coins,D(10)),dict.fromkeys(coins,True))
 assert abs(b.value(dict.fromkeys(coins,D(20)))-400)<D('.000000001')
 with pytest.raises(ValueError): b.enter(dict.fromkeys(coins,D(10)),dict.fromkeys(coins,True))
 with pytest.raises(ValueError): b.value({})

def test_index_cash_exclusions_and_costs():
 b=BuyHoldIndex(WATCHLIST);b.enter(dict.fromkeys(WATCHLIST,D(100)),dict.fromkeys(WATCHLIST,False))
 assert b.value({})==200
 b=BuyHoldIndex(WATCHLIST);b.enter(dict.fromkeys(WATCHLIST,D(100)),dict.fromkeys(WATCHLIST,True))
 assert b.cash>=0 and b.value(dict.fromkeys(WATCHLIST,D(100)))<200

@pytest.mark.parametrize('benchmark',['aligned_trend','ema_trend'])
def test_long_shared_fixture_reproducible(benchmark):
 args=inputs()
 args['bars']={s:[bar(i,symbol=s) for i in range(-1,401)] for s in COINS}
 args['plan']=args['plan'].model_copy(update={
  'development':Period(start=AT-timedelta(hours=1),end=AT+timedelta(days=5)),
  'validation':Period(start=AT+timedelta(days=6),end=AT+timedelta(days=7)),
  'independent_test':Period(start=AT+timedelta(days=8),end=AT+timedelta(days=9))})
 # synthetic period crosses old lock: choose earlier fixture dates instead
 shift=timedelta(days=20)
 args['bars']={s:[c.model_copy(update={'opened':c.opened-shift,'closed':c.closed-shift}) for c in rows] for s,rows in args['bars'].items()}
 args['reports']=[]
 from crypto.protocol import report_digest
 args['plan']=args['plan'].model_copy(update={k:Period(start=getattr(args['plan'],k).start-shift,end=getattr(args['plan'],k).end-shift) for k in ('development','validation','independent_test')}|{'report_hashes':(report_digest([]),report_digest([]),report_digest([]))})
 snapshots=[]
 for _ in range(2):
  store=SQLiteStore()
  r=FixtureJointRunner(store=store,benchmark=benchmark,**args)
  a=AT-shift
  asyncio.run(r.run([a,a+timedelta(minutes=15)]))
  reopened=FixtureJointRunner(store=store,benchmark=benchmark,**args)
  asyncio.run(reopened.run([a+timedelta(minutes=30)]))
  with pytest.raises(ValueError):asyncio.run(reopened.run([a+timedelta(hours=2)]))
  snapshots.append(reopened.snapshot());store.close()
 assert snapshots[0]==snapshots[1] and D(snapshots[0]['cash'])==200

def test_runner_blocks_real_before_storage():
 args=inputs();args['plan']=args['plan'].model_copy(update={'source':'https://data.binance.vision'})
 s=SQLiteStore()
 with pytest.raises(ValueError):FixtureJointRunner(store=s,**args)
 assert not s.list('joint_protocols');s.close()

def test_crossframe_mismatch():
 from crypto.data import Candle
 t=dt('2024-01-01')
 low=[Candle(symbol='BTCEUR',interval='15m',opened=t+timedelta(minutes=15*i),closed=t+timedelta(minutes=15*(i+1)),open=10,high=10,low=10,close=10,volume=1,quote_volume=10,source='fixture:test') for i in range(4)]
 h=Candle(symbol='BTCEUR',interval='1h',opened=t,closed=t+timedelta(hours=1),open=10,high=10,low=10,close=10,volume=4,quote_volume=40,source='fixture:test')
 consistent(low,[h])
 with pytest.raises(ValueError):consistent(low,[h.model_copy(update={'volume':D(3)})])
 with pytest.raises(ValueError):consistent(low[:-1],[h])

@pytest.mark.parametrize('benchmark',['aligned_trend','ema_trend'])
def test_runner_real_fixture_fill_dedup_and_restart(benchmark):
 args=inputs();h={s:{tf:[c.model_copy(update={'symbol':s}) for c in rows] for tf,rows in history().items()} for s in COINS}
 store=SQLiteStore();r=FixtureJointRunner(store=store,history=h,benchmark=benchmark,**args)
 first=asyncio.run(r.run([AT]))[-1]
 assert first['holdings'] and D(first['cash'])<200
 assert asyncio.run(r.run([AT]))[-1]==first
 reopened=FixtureJointRunner(store=store,history=h,benchmark=benchmark,**args)
 assert reopened.snapshot()==first
 assert len(store.list('joint_settlements'))==1
 store.close()

def test_quality_failure_per_coin_day(monkeypatch):
 import crypto.readiness as module
 monkeypatch.setitem(module.PERIODS,'test_fixture',(dt('2024-01-01'),dt('2024-01-03')))
 class Missing:
  def fetch(self,*args):raise ValueError('checksum mismatch')
 report=quality_report(Missing(),'BTCEUR','test_fixture')
 assert report['status']=='incomplete' and len(report['days'])==2
 assert all('checksum' in row['reason'] for row in report['days'])
 assert not report['performance_computed']
