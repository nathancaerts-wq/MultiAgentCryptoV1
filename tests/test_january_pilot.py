import asyncio
import pytest
from crypto.january_pilot import *
from crypto.data import Candle,DataEngine
from crypto.streaming import StreamingStore
from scripts.january_pilot import JanuaryData
from scripts.january_quality import audit


def test_pilot_bounds_before_fetch(tmp_path):
 s=JanuaryStore(tmp_path/'pilot.sqlite3');e=DataEngine(s,JanuaryData(s))
 for at in (START,END,dt('2026-01-01')):
  with pytest.raises(ValueError):asyncio.run(s.prepare_research(e,at,COINS))
 with pytest.raises(ValueError):JanuaryData(s).fetch('BTCEUR','1h',START-timedelta(hours=1),START)
 s.close()


def test_source_policy_is_separate(tmp_path):
 a=StreamingStore(tmp_path/'old.sqlite3');b=JanuaryStore(tmp_path/'new.sqlite3')
 for source in SOURCES:assert not a._accept_source(source) and b._accept_source(source)
 assert a._accept_source('fixture:test') and not b._accept_source('fixture:test')
 assert not b._accept_source(next(iter(SOURCES)).replace('2024-01','2026-01'))
 a.close();b.close()


def test_import_cannot_cross_month(tmp_path):
 s=JanuaryStore(tmp_path/'pilot.sqlite3')
 c=Candle(symbol='BTCEUR',interval='15m',opened=END,closed=END+timedelta(minutes=15),open=1,high=1,low=1,close=1,volume=1,quote_volume=1,source=next(iter(SOURCES)))
 with pytest.raises(ValueError):s.add_candles('bars',[c])
 assert s.db.execute('SELECT count(*) FROM stream_input').fetchone()[0]==0;s.close()


def test_frozen_assumptions():
 f=filters()
 assert tuple(f)==COINS and all(x.status=='assumed' and x.min_notional==10 and x.step==D('.00001') and x.tick==D('.01') for x in f.values())
 assert JointPolicy().decision.hypothesis=='aligned_trend'
