"""Synthetic boundary/financial tests only; no archive or return study is started."""
import asyncio
import json
from decimal import Decimal as D
from datetime import timedelta
import pytest
from crypto.development_2024 import *
from crypto.data import Candle
from crypto.protocol import Period
from scripts.development_2024 import make_plan


def candle(at=START, source_value=None):
    return Candle(symbol='BTCEUR', interval='15m', opened=at, closed=at+timedelta(minutes=15),
                  open=10, high=10, low=10, close=10, volume=1, quote_volume=10,
                  source=source_value or 'https://data.binance.vision/data/spot/monthly/klines/BTCEUR/15m/BTCEUR-15m-2024-01.zip')


@pytest.mark.parametrize('at', [START-timedelta(minutes=15), END, dt('2025-02-01'), dt('2026-01-01')])
def test_import_rejects_non_development_atomically(tmp_path, at):
    s=DevelopmentStore(tmp_path/'x')
    with pytest.raises(ValueError): s.add_candles('history',[candle(),candle(at)])
    assert s.db.execute('SELECT count(*) FROM stream_input').fetchone()[0]==0
    s.close()


def test_provenance_month_and_coin_are_bound(tmp_path):
    s=DevelopmentStore(tmp_path/'x')
    with pytest.raises(ValueError,match='provenance'): s.add_candles('bars',[candle(dt('2024-02-01'))])
    with pytest.raises(ValueError): s.add_candles('bars',[candle(source_value='fixture:synthetic')])
    s.add_candles('bars',[candle()]);s.close()


@pytest.mark.parametrize('at',[START,LAST_ENTRY+timedelta(minutes=15),END,dt('2026-01-01')])
def test_analysis_gate_before_engine_access(tmp_path,at):
    s=DevelopmentStore(tmp_path/'x')
    with pytest.raises(ValueError):asyncio.run(s.prepare_research(None,at,COINS))
    s.close()


def test_data_gate_before_store_access():
    d=DevelopmentData(None)
    for a,b in [(END,END+timedelta(minutes=15)),(START-timedelta(days=1),START)]:
        with pytest.raises(ValueError):d.fetch('BTCEUR','15m',a,b)


def test_fixed_study_scenarios_and_plan_identity(tmp_path):
    m={'quality':{'fixture':True},'input_seal':{'reports':'a'*64}}
    ids=set();r=object.__new__(DevelopmentRunner);r.store=DevelopmentStore(tmp_path/'x');r.rules=filters()
    for b in ('aligned_trend','ema_trend'):
        for s in COSTS:
            r.plan=make_plan(m,s,b);r.policy=policy(s);r.benchmark=b
            assert r._accept_plan();ids.add(r.plan.fingerprint)
            assert r.policy.decision.planned_risk==D('.005') and r.policy.max_open_positions==1
    assert len(ids)==6
    r.plan=r.plan.model_copy(update={'development':Period(start=START,end=dt('2026-01-01'))})
    assert not r._accept_plan();r.store.close()


def test_january_gate_detects_mismatch_without_continuation(monkeypatch):
    from types import SimpleNamespace
    from scripts.development_2024 import january_gate
    class Bad:
        def _read(self):return {'at':dt('2024-02-01').isoformat(),'pending':None},SimpleNamespace(cash=D(200),position=None,trades=[])
    with pytest.raises(ValueError,match='January comparison failed'):january_gate(Bad())


def test_metrics_exact_active_synthetic_ledger(tmp_path,monkeypatch):
    import scripts.development_2024 as m
    from test_streaming import args_active,prepare,open_runner
    from crypto.streaming import StreamingStore
    from test_trade_agents import AT
    args=args_active();s=StreamingStore(tmp_path/'x');prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT,AT+timedelta(minutes=15)]))
    monkeypatch.setattr(m,'OUT',tmp_path);monkeypatch.setattr(m,'END',AT+timedelta(minutes=15))
    monkeypatch.setattr(m,'START',AT-timedelta(hours=1));monkeypatch.setattr(m,'ENTRY',AT)
    result=m.metrics(r,'synthetic')
    assert result['trades']==1 and result['unique_fills']==2
    assert result['net']==r._read()[1].realized
    assert result['approved_entries']==1
    assert D(result['equity'])==200+result['net']
    s.close()
