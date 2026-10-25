import asyncio
import sqlite3
from datetime import timedelta, date
from decimal import Decimal
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from crypto.models import Message, Proposal, MarketRules, Limits, now
from crypto.storage import SQLiteStore, TABLES
from crypto.orchestrator import Orchestrator, Task
from crypto.risk import RiskEngine, ExecutionEngine, PortfolioManager
from crypto.research import ResearchOptimizer
from crypto.market import BinancePublic, select_universe
from crypto.api import create_app
from crypto.agents import COMPONENTS


def message(**kw):
    return Message(**(dict(agent_id='a', coin='BTC', timeframe='1h', data={'close': 100}, result={'score': .5}, rationale='testdata', ttl_seconds=60) | kw))


class Fake:
    def __init__(self, msg=None, delay=0, error=False):
        self.msg, self.delay, self.error = msg or message(), delay, error
        self.inputs = None

    async def run(self, inputs):
        self.inputs = inputs
        await asyncio.sleep(self.delay)
        if self.error:
            raise RuntimeError('test')
        return self.msg


@pytest.fixture
def store():
    db = SQLiteStore()
    yield db
    db.close()


@pytest.mark.parametrize('changes', [dict(agent_id=''), dict(data={}), dict(result={}), dict(rationale=''), dict(ttl_seconds=0), dict(timestamp='2026-01-01T00:00:00'), dict(status='error'), dict(errors=('bad',)), dict(unexpected=1)])
def test_schema(changes):
    with pytest.raises(ValidationError):
        message(**changes)


def test_registration_pause_resume(store):
    o = Orchestrator(store)
    o.register('a', Fake())
    with pytest.raises(ValueError):
        o.register('a', Fake())
    o.pause('a')
    assert asyncio.run(o.execute([Task('one','a')])) == {}
    o.resume('a')
    assert 'one' in asyncio.run(o.execute([Task('one','a')]))
    assert len(store.audits()) >= 5


def test_dependencies(store):
    o = Orchestrator(store)
    a, b = Fake(), Fake(message(agent_id='b'))
    o.register('a', a)
    o.register('b', b)
    assert list(asyncio.run(o.execute([Task('two','b',('one',)), Task('one','a')]))) == ['one','two']
    assert b.inputs == (a.msg,)


@pytest.mark.parametrize('tasks', [[Task('a','a',('b',)), Task('b','a',('a',))], [Task('a','a',('missing',))], [Task('a','missing')], [Task('a','a'), Task('a','a')]])
def test_bad_plan(store, tasks):
    o = Orchestrator(store)
    o.register('a', Fake())
    with pytest.raises(ValueError):
        asyncio.run(o.execute(tasks))
    assert store.list('results') == []


@pytest.mark.parametrize('agent', [Fake(delay=.05), Fake(error=True), Fake(message(timestamp=now()-timedelta(days=1))), Fake(message(timestamp=now()+timedelta(days=1))), Fake(message(agent_id='imposter')), Fake(message(status='error',errors=('bad',)))])
def test_fail_closed(store, agent):
    o = Orchestrator(store, timeout=.01)
    o.register('a',agent)
    o.register('b',Fake(message(agent_id='b')))
    assert asyncio.run(o.execute([Task('a','a'),Task('b','b',('a',))])) == {}
    assert len(store.list('errors')) == 2


def test_duplicate_event_persistent(tmp_path):
    path = tmp_path/'test.sqlite3'
    m = message()
    for _ in range(2):
        s = SQLiteStore(path)
        o = Orchestrator(s)
        o.register('a',Fake(m))
        asyncio.run(o.execute([Task('one','a')]))
        assert len(s.list('results')) == 1
        s.close()


def test_database_rollback(store):
    with pytest.raises(RuntimeError):
        with store.transaction():
            store.put('coins','BTC',{'name':'Bitcoin'})
            raise RuntimeError()
    assert not store.list('coins')
    assert set(TABLES) <= {r[0] for r in store.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def inputs():
    return dict(proposal=Proposal(symbol='BTCEUR',quantity='0.1',price='100',stop='95'),rules=MarketRules(symbol='BTCEUR',enabled=True,min_qty='.01',max_qty='10',step='.01',tick='.01',min_notional='5'),cash=200,equity=200,exposure=0,daily_loss=0,peak=200,correlation=0)


def test_risk_success_and_duplicates(store):
    risk = RiskEngine(Limits(),Limits())
    args = inputs()
    engine = ExecutionEngine(store,risk)
    assert engine.propose(**args)
    with pytest.raises(sqlite3.IntegrityError):
        engine.propose(**args)
    assert len(store.list('orders')) == 1
    assert store.list('orders')[0]['status'] == 'proposed'


@pytest.mark.parametrize('patch', [dict(cash=1),dict(exposure=100),dict(daily_loss=10),dict(peak=300),dict(exposure=1,correlation=.9),dict(rules=None),dict(correlation=None),dict(equity=0),dict(cash=float('nan')),dict(exposure=-1),dict(proposal=Proposal(symbol='BTCEUR',quantity='1',price='100',stop='90')),dict(proposal=Proposal(symbol='OTHER',quantity='.1',price='100',stop='95')),dict(proposal=Proposal(symbol='BTCEUR',quantity='.001',price='100',stop='95')),dict(proposal=Proposal(symbol='BTCEUR',quantity='.1',price='100',stop='95',timestamp=now()-timedelta(days=1)))])
def test_risk_rejections(patch):
    assert RiskEngine(Limits(),Limits()).check(**(inputs() | patch)) is not None


def test_emergency_and_hard_limits():
    risk = RiskEngine(Limits(),Limits())
    risk.stopped = True
    assert risk.check(**inputs()) == 'noodstop'
    with pytest.raises(ValueError):
        RiskEngine(Limits(),Limits(exposure='.9'))


def test_rejected_order_absent(store):
    assert not ExecutionEngine(store,RiskEngine(Limits(),Limits())).propose(**(inputs() | {'cash':0}))
    assert not store.list('orders')
    assert store.list('risk_decisions')[0]['approved'] is False


def test_research_isolation(store):
    r = ResearchOptimizer(store, {'window':(5,50)})
    r.hypothesis('Momentum hypothese')
    key = r.candidate({'window':10},date(2020,1,1),date(2021,1,1),'BTC')
    with pytest.raises(ValueError):
        r.candidate({'window':10},date(2020,6,1),date(2022,1,1),'BTC')
    with pytest.raises(ValueError):
        r.candidate({'trade_risk':.5},date(2022,1,1),date(2023,1,1),'BTC')
    r.approve(key,'onderzoeker','handmatig beoordeeld voorbeeld; geen strategieactivatie')
    assert store.list('strategies')[0]['active'] is False
    assert not store.list('orders')


def test_binance_and_universe():
    document = {'symbols':[{'symbol':'BTCEUR','quoteAsset':'EUR','status':'TRADING','isSpotTradingAllowed':True,'filters':[{'filterType':'LOT_SIZE','minQty':'.01','maxQty':'10','stepSize':'.01'},{'filterType':'PRICE_FILTER','tickSize':'.01'},{'filterType':'MIN_NOTIONAL','minNotional':'5'}]}]}
    rules = BinancePublic.rules(document)
    assert rules[0].min_notional == Decimal('5')
    assert select_universe(rules,{}) == []
    assert select_universe(rules,{'BTCEUR':dict(quality=True,volume=200000,depth=2000,spread=.001,history=2000)}) == ['BTCEUR']


def test_api(store):
    with TestClient(create_app(store)) as client:
        for path in ('health','agents','coins','market','signals','research','portfolio','risk-limits','audit','errors'):
            assert client.get('/'+path).status_code == 200
        assert client.get('/portfolio').json()['cash'] == '200'
        assert client.get('/health').json()['live_execution'] is False
        assert client.post('/orders',json={}).status_code == 404
        assert len(client.get('/agents').json()['interfaces']) == 13


def test_catalog():
    assert len({c.id for c in COMPONENTS}) == 13
    assert {'risk','execution','portfolio'} <= {c.id for c in COMPONENTS if c.kind == 'deterministic'}
