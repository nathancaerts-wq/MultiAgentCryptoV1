import asyncio,json
from datetime import timedelta
from decimal import Decimal as D
import pytest
from crypto.analysis import AnalysisContext,run_research
from crypto.data import DataEngine
from crypto.indicators import IndicatorConfig
from crypto.joint_portfolio import JointPortfolio
from crypto.sim_execution import digest
from crypto.storage import SQLiteStore
from test_trade_agents import AT,FixtureData
from test_joint_portfolio import inputs


def test_exact_feature_cache_hits_and_isolation():
 s=SQLiteStore();e=DataEngine(s,FixtureData())
 a=AnalysisContext(e,'BTCEUR',AT);original=json.loads(json.dumps(a.frames))
 a.frames['1h']['missing'].append('mutated caller')
 b=AnalysisContext(e,'BTCEUR',AT)
 assert b.frames==original and e._technical_cache_counts=={'hits':3,'misses':3}
 c=AnalysisContext(e,'BTCEUR',AT+timedelta(minutes=15))
 assert c.frames['1h']==b.frames['1h'] and c.frames['4h']==b.frames['4h']
 assert e._technical_cache_counts=={'hits':5,'misses':4}
 s.close()


def test_parameter_and_source_change_invalidate_features():
 s=SQLiteStore();e=DataEngine(s,FixtureData());AnalysisContext(e,'BTCEUR',AT)
 AnalysisContext(e,'BTCEUR',AT,config=IndicatorConfig(fast=8))
 assert e._technical_cache_counts['misses']==6
 key,payload=s.db.execute("SELECT id,payload FROM datasets WHERE json_extract(payload,'$.rows[0].interval')='1h'").fetchone()
 value=json.loads(payload);value['rows'][-1]['volume']='12345'
 s.db.execute('UPDATE datasets SET payload=? WHERE id=?',(json.dumps(value),key))
 c=AnalysisContext(e,'BTCEUR',AT)
 assert c.frames['1h']['status']=='complete'
 assert e._technical_cache_counts['misses']==7
 s.close()


def test_future_cache_cannot_pass_series_validation():
 s=SQLiteStore();e=DataEngine(s,FixtureData());AnalysisContext(e,'BTCEUR',AT)
 with pytest.raises(ValueError):e.load('BTCEUR','1h',AT-timedelta(hours=32),AT,AT-timedelta(hours=1))
 s.close()


def test_compute_implementation_identity_part_of_cache_key():
 s=SQLiteStore();e=DataEngine(s,FixtureData());rows=e.load('BTCEUR','1h',AT-timedelta(hours=32),AT,AT)
 assert e.technical_features(rows,IndicatorConfig(),lambda *_:{'result':1},'same')=={'result':1}
 assert e.technical_features(rows,IndicatorConfig(),lambda *_:{'result':2},'same')=={'result':2}
 assert e._technical_cache_counts['misses']==2;s.close()


def test_feature_cache_is_bounded():
 s=SQLiteStore();e=DataEngine(s,FixtureData())
 compute=lambda *_:{'data':[]}
 for i in range(200):e.technical_features([],IndicatorConfig(),compute,str(i))
 assert len(e._technical_cache)==128;s.close()


def test_full_state_hash_proof_does_not_accept_invalid_event_chain():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());r.snapshot()
 key,raw=s.db.execute('SELECT id,payload FROM joint_states').fetchone()
 state=json.loads(raw);state['ledger']['events'][0]['action']='tampered'
 state['hash']=digest({k:v for k,v in state.items() if k!='hash'})
 s.db.execute('UPDATE joint_states SET payload=? WHERE id=?',(json.dumps(state),key))
 with pytest.raises(ValueError,match='auditketen'):r.snapshot()
 s.close()


def test_new_save_always_validates_events():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());before,ledger=r._read()
 ledger.events[0]['action']='tamper'
 with pytest.raises(ValueError,match='auditketen'):
  with s.transaction():r._save(before,dict(before),ledger,'invalid')
 assert r.snapshot()['cash']=='200';s.close()


def test_report_time_index_tracks_replacement_and_mutation():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());assert len(r._reports_at(AT))==2
 r.reports[0].data['as_of']=(AT+timedelta(minutes=15)).isoformat()
 assert len(r._reports_at(AT))==1 and len(r._reports_at(AT+timedelta(minutes=15)))==1
 with pytest.raises(ValueError):r.snapshot()
 s.close()


def test_cached_and_uncached_analysis_messages_exact():
 class UncachedEngine(DataEngine):
  def technical_features(self,rows,config,compute,window_hash):return compute(rows,config)
 stores=[SQLiteStore(),SQLiteStore()]
 engines=[DataEngine(stores[0],FixtureData()),UncachedEngine(stores[1],FixtureData())]
 for i in range(20):
  at=AT+timedelta(minutes=15*i)
  outputs=[asyncio.run(run_research(e,at,['BTCEUR','ETHEUR','SOLEUR'])) for e in engines]
  assert [m.model_dump(mode='json') for m in outputs[0]]==[m.model_dump(mode='json') for m in outputs[1]]
 assert engines[0]._technical_cache_counts['hits']>0
 for s in stores:s.close()


def test_long_analysis_and_replay_match_prechange_reference(monkeypatch):
 import gzip
 from datetime import datetime,timezone
 from pathlib import Path
 import crypto.storage as storage
 from scripts.scalability_reference import capture
 monkeypatch.setattr(storage,'now',lambda:datetime(2026,10,27,tzinfo=timezone.utc))
 expected=json.loads(gzip.decompress(Path('experiments/scalability/reference_before.json.gz').read_bytes()))
 assert capture()==expected


def test_future_extremes_do_not_change_past_analysis():
 class FutureExtreme(FixtureData):
  def fetch(self,symbol,interval,start,end):
   rows=super().fetch(symbol,interval,start,end)
   return [c.model_copy(update={k:D('1000000000') for k in ('open','high','low','close')}) if c.opened>=AT else c for c in rows]
 s=SQLiteStore();e=DataEngine(s,FutureExtreme())
 before=asyncio.run(run_research(e,AT,['BTCEUR']))
 asyncio.run(run_research(e,AT+timedelta(days=1),['BTCEUR']))
 after=asyncio.run(run_research(e,AT,['BTCEUR']))
 assert [m.model_dump(mode='json') for m in before]==[m.model_dump(mode='json') for m in after]
 s.close()


def test_parsed_candle_cache_uses_actual_payload_and_independent_lists():
 s=SQLiteStore();e=DataEngine(s,FixtureData());start=AT-timedelta(hours=32)
 original=e.load('BTCEUR','1h',start,AT,AT)
 e.load('BTCEUR','1h',start,AT,AT)
 returned=e.load('BTCEUR','1h',start,AT,AT);assert e._candle_cache_counts['hits']==1
 returned.clear();assert e.load('BTCEUR','1h',start,AT,AT)==original
 key,raw=s.db.execute('SELECT id,payload FROM datasets').fetchone();payload=json.loads(raw)
 payload['rows'][-1]['source']='fixture:new-source-version'
 s.db.execute('UPDATE datasets SET payload=? WHERE id=?',(json.dumps(payload),key))
 updated=e.load('BTCEUR','1h',start,AT,AT)
 assert updated[-1].source=='fixture:new-source-version'
 with pytest.raises(ValueError):e.load('BTCEUR','1h',start,AT,AT-timedelta(seconds=1))
 s.close()


def test_parsed_candle_cache_is_bounded():
 s=SQLiteStore();e=DataEngine(s,FixtureData())
 for i in range(130):
  end=AT+timedelta(minutes=15*i);start=end-timedelta(minutes=30)
  e.load('BTCEUR','15m',start,end,end);e.load('BTCEUR','15m',start,end,end)
 assert len(e._candle_cache)==128;s.close()
