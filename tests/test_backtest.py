from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
import asyncio
import json
import pytest
from crypto.sim_execution import FillCosts,SpotFilters,OfflineLedger,digest
from crypto.backtest import SimulationProtocol,BacktestRunner,simulate,candle_digest
from crypto.protocol import ResearchPlan,Period,report_digest
from crypto.data import Candle,DataEngine,SECONDS
from crypto.analysis import run_research
from crypto.storage import SQLiteStore

AT=datetime(2025,1,10,tzinfo=timezone.utc)

def rules(**kw):
    return SpotFilters(**(dict(symbol='BTCEUR',source='fixture:assumed',status='assumed',note='Expliciete testfilters, geen historische beursclaim',tick='.01',min_qty='.001',max_qty='100',step='.001',min_notional='1')|kw))

def costs(**kw):return FillCosts(**(dict(fee=0,spread=0,slippage=0)|kw))

def bar(i=0,**kw):
    t=AT+timedelta(hours=i)
    return Candle(**(dict(symbol='BTCEUR',interval='1h',opened=t,closed=t+timedelta(hours=1),open='100',high='101',low='99',close='100',volume='10',quote_volume='1000',source='fixture:backtest')|kw))

def plan(**kw):
    return ResearchPlan(**(dict(coins=('BTCEUR',),source='fixture:backtest',dataset_sha256='a'*64,report_hashes=(report_digest([]),)*3,
        development=Period(start=AT,end=AT+timedelta(hours=8)),validation=Period(start=AT+timedelta(days=1),end=AT+timedelta(days=2)),independent_test=Period(start=AT+timedelta(days=3),end=AT+timedelta(days=4)),fee=0,slippage=0)|kw))


def ledger(**kw):return OfflineLedger(costs(),rules(),**kw)

def test_hand_calculated_round_trip():
    l=ledger()
    assert l.buy('one',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert l.cash==190 and l.snapshot(D(101))['unrealized']==D('.1')
    assert l.sell('two',AT+timedelta(hours=1),D(110),'manual')
    assert l.cash==201 and l.realized==1 and l.position is None
    l.reconcile()
    for i,event in enumerate(l.events):
        assert event['hash']==digest({k:v for k,v in event.items() if k!='hash'})
        if i:assert event['previous']==l.events[i-1]['hash']


def test_costs_and_adverse_rounding():
    c=costs(fee='.001',spread='.002',slippage='.001')
    l=OfflineLedger(c,rules())
    assert l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert l.position.average_price==D('100.20') and l.cash==D('189.96998000')
    assert l.sell('s',AT+timedelta(hours=1),D(100),'test')
    assert l.cash==D('199.94000000') and l.fees==D('.02000000')
    trade=l.trades[0]
    assert trade['entry_impact']['spread']==D('.01')
    assert trade['exit_impact']['slippage']==D('.01')
    assert trade['entry_impact']['adverse_tick_rounding']==0
    assert c.price(D('100.003'),'buy',D('.01'))==D('100.21')
    assert c.price(D('100.003'),'sell',D('.01'))==D('99.80')

@pytest.mark.parametrize('kw,reason',[({'min_qty':'1'},'LOT_SIZE'),({'market_min_qty':'1'},'MARKET_LOT_SIZE'),({'min_notional':'50'},'MIN_NOTIONAL'),({'notional_min':'50'},'NOTIONAL_MIN'),({'notional_max':'1'},'NOTIONAL_MAX'),({'max_price':'99'},'PRICE_FILTER'),({'avg_price_mins':5},'historische_gemiddelde_notionalprijs_ontbreekt')])
def test_filters(kw,reason):
    l=OfflineLedger(costs(),rules(**kw))
    assert not l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert l.events[-1]['details']['reason']==reason and l.cash==200


def test_market_steps_and_disable_notional():
    r=rules(step='.002',market_step='.003',min_notional='50',min_notional_market=False)
    assert r.quantity_step==D('.006')
    assert r.check(D('.102'),D(100),AT) is None
    assert r.check(D('.1'),D(100),AT)=='MARKET_LOT_SIZE'


def test_historical_metadata_known_time():
    r=rules(status='validated',source='https://api.binance.com/api/v3/exchangeInfo',known_at=AT+timedelta(days=1),valid_from=AT,valid_until=AT+timedelta(days=2))
    assert r.check(D('.1'),D(100),AT)=='historische_metadata_niet_geldig'
    with pytest.raises(ValueError):rules(status='validated')

@pytest.mark.parametrize('quantity,stop,reason',[('3','95','onvoldoende_saldo_inclusief_kosten'),('1.1','99.9','exposure_limit'),('.3','95','planned_risk_limit'),('.1001','95','LOT_SIZE'),('.1','100','ongeldige_stop_target_of_horizon')])
def test_rejections(quantity,stop,reason):
    l=ledger();assert not l.buy('b',AT,D(100),D(quantity),D(stop),AT+timedelta(hours=4))
    assert l.events[-1]['details']['reason']==reason
    assert l.cash==200 and l.position is None


def test_duplicate_and_no_sell_before_buy():
    l=ledger();assert l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert not l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert not l.sell('early',AT-timedelta(hours=1),D(110),'test')
    assert l.sell('s',AT+timedelta(hours=1),D(110),'test')
    assert not l.sell('s',AT+timedelta(hours=1),D(110),'test')
    assert l.cash==201

@pytest.mark.parametrize('op,hi,lo,target,expected,ambiguous',[(100,110,90,105,95,True),(90,110,89,105,90,True),(100,110,99,105,105,False)])
def test_stops_gaps_ambiguity(op,hi,lo,target,expected,ambiguous):
    l=ledger();l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4),D(target))
    l.process_bar(bar(open=str(op),high=str(hi),low=str(lo),close=str(op)),1)
    assert l.trades[0]['exit']==expected and l.trades[0]['ambiguous']==ambiguous


def test_daily_pause_and_reset_and_drawdown():
    l=ledger()
    l.buy('b',AT,D(100),D('.9'),D(99),AT+timedelta(hours=4))
    l.process_bar(bar(1,open='90',high='91',low='89',close='90'),1)
    assert l.day_paused
    assert not l.buy('blocked',AT+timedelta(hours=2),D(90),D('.01'),D(89),AT+timedelta(hours=6))
    assert l.events[-1]['details']['reason']=='daily_loss_pause'
    l.observe(AT+timedelta(days=1),D(90));assert not l.day_paused
    m=ledger();m.buy('b',AT,D(100),D('.9'),D(99),AT+timedelta(hours=4))
    m.process_bar(bar(1,open='70',high='71',low='69',close='70'),1)
    assert m.drawdown_paused
    m.observe(AT+timedelta(days=1),D(70));assert m.drawdown_paused


def test_size_and_gap_recheck():
    l=ledger();q,stop=l.size(D(100),D(2))
    assert q*D(2)<=1
    assert not l.buy('gap',AT,D(110),q,stop,AT+timedelta(hours=4))
    assert l.events[-1]['details']['reason']=='planned_risk_limit'


def selection(i=1):
    return {'decision_at':(AT+timedelta(hours=i)).isoformat(),'event_id':f'fixture-{i}', 'features':{'1h':{'atr':'1'}},'hypotheses':{'aligned_trend':{'eligible':True}},'benchmarks':{'ema_trend':True}}


def test_next_candle_future_extremes_do_not_change_entry():
    bars=[bar(i) for i in range(8)]
    first=simulate(plan(),rules(),costs(),bars,[selection()],'aligned_trend')
    changed=list(bars);changed[1]=bar(1,high='1000',low='99',close='100')
    second=simulate(plan(),rules(),costs(),changed,[selection()],'aligned_trend')
    a=[e for e in first['events'] if e['action']=='buy'];b=[e for e in second['events'] if e['action']=='buy']
    assert a==b and a[0]['at']==(AT+timedelta(hours=1)).isoformat()
    assert first['trades'][0]['exited_at']==(AT+timedelta(hours=5)).isoformat()
    assert first['metrics']['net_result']==0

@pytest.mark.parametrize('mutation',[lambda b:b[:-1]+[b[-2]],lambda b:b[1:],lambda b:b[::-1]])
def test_bad_bars(mutation):
    with pytest.raises(ValueError):
        # validation requires the externally specified original period as well
        from crypto.data import validate_series
        validate_series(mutation([bar(i) for i in range(8)]),'BTCEUR','1h',AT,AT+timedelta(hours=8),AT+timedelta(days=1))


def test_failed_exit_keeps_position_and_reconciles():
    l=OfflineLedger(costs(),rules(min_notional='9.5'))
    assert l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert not l.sell('s',AT+timedelta(hours=1),D(90),'gap')
    assert l.position.quantity==D('.1') and l.cash==190
    l.reconcile()

class Synthetic:
    def fetch(self,symbol,interval,start,end):
        result=[]
        for i in range(int((end-start).total_seconds())//SECONDS[interval]):
            t=start+timedelta(seconds=i*SECONDS[interval]);p=D(100+i)
            result.append(Candle(symbol=symbol,interval=interval,opened=t,closed=t+timedelta(seconds=SECONDS[interval]),open=p,high=p+1,low=p-1,close=p,volume=10,quote_volume=1000,source='fixture:backtest'))
        return result


def setup_run(store,authorize=None):
    reports=asyncio.run(run_research(DataEngine(store,Synthetic()),AT+timedelta(hours=1),['BTCEUR']))
    # Stable historical execution prefix; selection does not read these future bars.
    bars={'BTCEUR':[bar(i,open='131',high='132',low='130',close='131') for i in range(8)]}
    p=plan(report_hashes=(report_digest(reports),report_digest([]),report_digest([])))
    spec=SimulationProtocol(costs=costs(),filters=(rules(),),candle_hashes=(candle_digest(bars),)*3,data_kind='synthetic_fixture',independent_test_authorization=authorize)
    runner=BacktestRunner(store);key=runner.register(p,spec)
    return runner,key,p,spec,reports,bars


def test_runner_integration_isolated_and_reproducible(tmp_path):
    path=tmp_path/'backtest.sqlite3';store=SQLiteStore(path)
    runner,key,p,spec,reports,bars=setup_run(store)
    before={t:store.list(t) for t in ('orders','positions','portfolio_history','agents','strategies','risk_decisions')}
    first=runner.run(key,'development',reports,bars)
    assert first['results']['BTCEUR']['aligned_trend']['metrics']['trades']==1
    assert first['results']['BTCEUR']['aligned_trend']['metrics']['evidence']=='insufficient_evidence'
    assert before=={t:store.list(t) for t in before}
    store.close();store=SQLiteStore(path)
    replay=BacktestRunner(store).run(key,'development',reports,bars)
    assert replay['replay'] is True
    assert {k:v for k,v in replay.items() if k!='replay'}=={k:v for k,v in first.items() if k!='replay'}
    assert len(store.list('backtest_runs'))==1
    store.close()


def test_holdout_locked_and_protocol_immutable():
    s=SQLiteStore();runner,key,p,spec,reports,bars=setup_run(s)
    with pytest.raises(PermissionError):runner.run(key,'independent_test',[],bars)
    assert not s.list('research_exposures')
    with pytest.raises(ValueError): runner.register(p,spec.model_copy(update={'costs':FillCosts(fee=0,slippage=0,spread='.002')}))
    altered={'BTCEUR':list(bars['BTCEUR'])};altered['BTCEUR'][0]=bar()
    with pytest.raises(ValueError,match='Candles'):runner.run(key,'development',reports,altered)
    s.close()


def test_explicit_holdout_authorization_and_consumption():
    s=SQLiteStore();p=plan()
    bars={'BTCEUR':[bar(i,opened=p.independent_test.start+timedelta(hours=i),closed=p.independent_test.start+timedelta(hours=i+1)) for i in range(24)]}
    spec=SimulationProtocol(costs=costs(),filters=(rules(),),candle_hashes=(candle_digest(bars),)*3,data_kind='synthetic_fixture',independent_test_authorization='Expliciet toegestaan door fixtureprotocol vóór evaluatie')
    runner=BacktestRunner(s);key=runner.register(p,spec)
    first=runner.run(key,'independent_test',[],bars)
    assert first['inspection']['independent_test_untouched'] is False
    assert first['inspection']['independent_first_view'] is True
    again=runner.run(key,'independent_test',[],bars)
    assert again['replay'] is True
    assert len(s.list('backtest_runs'))==1
    assert all(x['metrics']['trades']==0 for name,x in first['results']['BTCEUR'].items() if name!='buy_and_hold')
    s.close()


def test_daily_gap_loss_counts_on_new_day():
    l=ledger();late=AT+timedelta(hours=23)
    assert l.buy('b',late,D(100),D('.9'),D(99),late+timedelta(hours=4))
    l.observe(late+timedelta(minutes=59),D(100))
    l.observe(AT+timedelta(days=1),D(90))
    assert l.day_paused and l.day_start==200


def test_no_ledger_mutation_on_invalid_financial_inputs():
    l=ledger()
    assert not l.buy('nan',AT,D('NaN'),D('.1'),D(95),AT+timedelta(hours=4))
    assert l.cash==200 and not l.position
    l.cash-=D(1)
    with pytest.raises(ArithmeticError):l.reconcile()


def test_runner_rejects_missing_bar_even_if_hash_registered():
    s=SQLiteStore();runner,key,p,spec,reports,bars=setup_run(s)
    s.close()
    s=SQLiteStore();runner=BacktestRunner(s)
    bars['BTCEUR'].pop(3)
    spec=spec.model_copy(update={'candle_hashes':(candle_digest(bars),)*3})
    key=runner.register(p,spec)
    with pytest.raises(ValueError):runner.run(key,'development',reports,bars)
    assert not s.list('backtest_runs')
    assert s.audits()[-1]['action']=='backtest_failed'
    s.close()


def test_runner_rejects_fixture_as_official_source():
    s=SQLiteStore();r,key,p,spec,reports,bars=setup_run(s);s.close()
    s=SQLiteStore();r=BacktestRunner(s)
    spec=spec.model_copy(update={'data_kind':'binance_spot'})
    key=r.register(p,spec)
    with pytest.raises(ValueError,match='Bron'):r.run(key,'development',reports,bars)
    assert not s.list('backtest_runs');s.close()


def test_read_only_backtest_api():
    from fastapi.testclient import TestClient
    from crypto.api import create_app
    s=SQLiteStore();runner,key,p,spec,reports,bars=setup_run(s)
    runner.run(key,'development',reports,bars)
    with TestClient(create_app(s)) as client:
        assert len(client.get('/backtests').json())==1
        assert len(client.get('/simulation-protocols').json())==1
        assert client.post('/backtests',json={}).status_code==405
    s.close()


def test_fee_rounding_and_stop_filter():
    c=costs(fee='.001')
    assert c.charge(D('.00001'),D('.01'))==D('.00000001')
    l=OfflineLedger(costs(),rules(min_price='96'))
    assert not l.buy('b',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4))
    assert l.events[-1]['details']['reason']=='ongeldige_stop_target_of_horizon'


def test_incomplete_exit_does_not_claim_full_net():
    bars=[bar(i,open='90' if i>1 else '100',high='101',low='89' if i>1 else '99',close='90' if i>1 else '100') for i in range(8)]
    outcome=simulate(plan(),rules(min_notional='48'),costs(),bars,[selection()],'aligned_trend')
    assert outcome['ending_ledger']['holdings']
    assert outcome['metrics']['complete'] is False
    assert outcome['metrics']['net_result'] is None
    assert outcome['metrics']['net_without_top_3_winners'] is None
