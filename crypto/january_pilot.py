"""Explicit January-only historical pilot. Never a general historical release."""
from datetime import timedelta
from decimal import Decimal as D
from .readiness import dt
from .streaming import StreamingStore,StreamingFixtureRunner
from .joint_portfolio import JointPolicy
from .sim_execution import SpotFilters,digest
COINS=('BTCEUR','ETHEUR','SOLEUR')
START=dt('2024-01-01');ENTRY=dt('2024-01-08');END=dt('2024-02-01')
LAST_ENTRY=END-timedelta(hours=4,minutes=15)
SOURCE='assumption:january-pilot-v1'
SOURCES={f'https://data.binance.vision/data/spot/monthly/klines/{s}/{tf}/{s}-{tf}-2024-01.zip' for s in COINS for tf in ('15m','1h','4h')}

def filters():
 return {s:SpotFilters(symbol=s,source='assumption:phase6b-three-coin-v1',status='assumed',note='Hypothetical; historical Binance filters unproven',tick='.01',min_qty='.00001',step='.00001',max_qty='1000000',market_min_qty='.00001',market_step='.00001',market_max_qty='1000000',min_notional=10,notional_min=10) for s in COINS}

class JanuaryStore(StreamingStore):
 def _accept_source(self,source):return source in SOURCES
 def add_candles(self,kind,rows):
  def checked():
   for c in rows:
    if c.symbol not in COINS or not START<=c.opened<c.closed<=END:raise ValueError('Outside January pilot')
    yield c
  return super().add_candles(kind,checked())
 async def prepare_research(self,engine,at,coins):
  if tuple(coins)!=COINS or not ENTRY<=at<=LAST_ENTRY:raise ValueError('Outside pilot analysis window')
  return await super().prepare_research(engine,at,coins)
 def add_reports(self,reports):
  def checked():
   for r in reports:
    if r.coin not in COINS or not ENTRY<=r.timestamp<=LAST_ENTRY:raise ValueError('Outside pilot reports')
    yield r
  return super().add_reports(checked())

class JanuaryRunner(StreamingFixtureRunner):
 def _accept_plan(self):
  return (type(self.store) is JanuaryStore and self.plan.source==SOURCE and self.plan.coins==COINS
          and self.plan.development.start==START and self.plan.development.end==END
          and self.policy==JointPolicy() and self.rules==filters() and self.benchmark=='aligned_trend')
 def _manifest(self):
  return super()._manifest()|{'technical_fixture_only':False,'historical_pilot':'january-pilot-v1','entries_from':ENTRY.isoformat(),'hypothetical_filters':True}
 async def evaluate(self,at):
  if not ENTRY<=at<=END:raise ValueError('Outside pilot execution window')
  return await super().evaluate(at)
