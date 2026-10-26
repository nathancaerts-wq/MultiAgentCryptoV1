"""Gezamenlijke boekhouding: synthetische kleine ontwikkeltests, geen netwerk."""
import asyncio
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal as D
import json
import pytest
from fastapi.testclient import TestClient
from crypto.api import create_app
from crypto.analysis import run_research
from crypto.data import DataEngine
from crypto.models import Limits
from crypto.joint_portfolio import JointPortfolio, JointPolicy
from crypto.sim_execution import digest
from crypto.storage import SQLiteStore
from crypto.trade_agents import DecisionPolicy
from test_trade_agents import AT, FixtureData, bar, rules, plan

COINS=('BTCEUR','ETHEUR')


def reports_at(at=AT):
    with_store=SQLiteStore()
    try: return asyncio.run(run_research(DataEngine(with_store,FixtureData()),at,COINS))
    finally: with_store.close()


def inputs(at=AT, reports=None, bars=None, **kw):
    reports=reports if reports is not None else reports_at(at)
    rows=bars if bars is not None else {s:[bar(i,symbol=s) for i in range(-1,21)] for s in COINS}
    return dict(plan=plan(reports),policy=JointPolicy(),filters={s:rules(s) for s in COINS},reports=reports,bars=rows)|kw

@pytest.fixture
def store():
    s=SQLiteStore();yield s;s.close()

def portfolio(store,**kw):return JointPortfolio(store,**inputs(**kw))
def evaluate(s,at=AT):return asyncio.run(s.evaluate(at))
def selected(batch):return next((c for c in batch['candidates'] if c['selected']),None)


def test_single_cash_and_simultaneous_reservation(store):
    s=portfolio(store)
    assert s.snapshot()['cash']=='200'
    result=evaluate(s)
    assert len(result['candidates'])==2 and sum(c['selected'] for c in result['candidates'])==1
    assert all(c['eligible'] and c['risk_approved'] for c in result['candidates'])
    assert selected(result)['symbol']=='BTCEUR'
    snap=s.snapshot()
    assert D(snap['cash'])==200 and D(snap['reserved_cash'])>0
    assert D(snap['available_cash'])+D(snap['reserved_cash'])==200
    assert D(snap['reserved_risk'])<=1 and D(snap['reserved_exposure'])<=100
    assert not snap['holdings'] and not store.list('joint_settlements')
    assert 'gereserveerd' in result['candidates'][1]['reason']


def test_rotation_and_input_order_neutrality(store):
    for offset,expected in [(0,'BTCEUR'),(15,'ETHEUR')]:
        at=AT+timedelta(minutes=offset)
        args=inputs(at=at)
        first=JointPortfolio(store,**args)
        result=evaluate(first,at)
        assert selected(result)['symbol']==expected
        other=SQLiteStore()
        try:
            args['reports']=list(reversed(args['reports']))
            args['bars']=dict(reversed(list(args['bars'].items())))
            args['filters']=dict(reversed(list(args['filters'].items())))
            second=JointPortfolio(other,**args)
            assert evaluate(second,at)==result
        finally:other.close()


def test_score_has_priority_over_tie_rotation(store):
    reports=reports_at()
    reports[1].result['components']['scanner']['ranking'][0]['score']='75'
    s=portfolio(store,reports=reports)
    result=evaluate(s)
    assert selected(result)['symbol']=='ETHEUR'
    assert '75' in result['candidates'][0]['ranking_reason']


def test_costs_unrealized_and_duplicate_fill(store):
    s=portfolio(store);b=evaluate(s);c=selected(b)['entry']['result']
    settled=s.execute(b['id']);assert settled['success']
    snap=s.snapshot();q=D(c['quantity']);price=D(c['price']);fee=D(c['fee'])
    assert D(snap['cash'])==D(200)-q*price-fee
    assert D(snap['fees'])==fee and D(snap['cost_basis'])==q*price+fee
    assert D(snap['unrealized'])==q*D('106.4')-D(snap['cost_basis'])
    assert D(snap['equity'])==D(snap['cash'])+q*D('106.4')
    assert D(snap['reserved_cash'])==0
    before=deepcopy(snap)
    assert s.execute(b['id'])['replay'] and s.snapshot()==before
    assert len(store.list('joint_settlements'))==1


def test_default_one_position_blocks_other_coin(store):
    r=reports_at()+reports_at(AT+timedelta(minutes=15))
    s=portfolio(store,reports=r);b=evaluate(s);s.execute(b['id'])
    next_batch=evaluate(s,AT+timedelta(minutes=15))
    assert selected(next_batch) is None
    assert all('positielimiet' in c['reason'] for c in next_batch['candidates'])
    assert len(s.snapshot()['holdings'])==1
    with pytest.raises(ValueError):s.execute(next_batch['id'])


def switched_inputs():
    r=reports_at()+reports_at(AT+timedelta(minutes=30))
    # BTC krijgt een expliciet synthetisch conflict; ETH blijft kandidaat.
    r[2].result['conflicts']=['synthetisch conflict']
    rows={s:[bar(i,symbol=s) for i in range(-1,21)] for s in COINS}
    rows['BTCEUR'][1]=bar(0,open='106.4',high=107,low=99,close=100)
    return inputs(reports=r,bars=rows)


def run_switch(s):
    b=evaluate(s);assert s.execute(b['id'])['success']
    e=evaluate(s,AT+timedelta(minutes=15));assert e['reservation']['side']=='sell'
    assert s.execute(e['id'])['success']
    after_exit=s.snapshot()
    b=evaluate(s,AT+timedelta(minutes=30));assert selected(b)['symbol']=='ETHEUR'
    assert s.execute(b['id'])['success']
    return after_exit,s.snapshot()


def test_cash_pnl_fees_shared_when_switching_coin(store):
    s=JointPortfolio(store,**switched_inputs())
    flat,end=run_switch(s)
    assert D(flat['cash'])<200 and D(flat['realized'])<0
    assert not flat['holdings'] and list(end['holdings'])==['ETHEUR']
    assert D(end['cash'])+D(end['cost_basis'])==200+D(end['realized'])
    assert end['realized']==flat['realized']==end['realized_by_coin']['BTCEUR']
    assert end['realized_by_coin']['ETHEUR']=='0'
    assert D(end['fees'])>D(flat['fees'])>0
    assert len(store.list('joint_protocols'))==1
    assert len([r for r in store.list('joint_states') if r['kind']=='initial'])==1


def test_full_portfolio_reproducible_with_reopen(store,tmp_path):
    args=switched_inputs()
    first=JointPortfolio(store,**args);result=run_switch(first)
    path=tmp_path/'joint.db';other=SQLiteStore(path)
    second=JointPortfolio(other,**args);b=evaluate(second);second.execute(b['id']);other.close()
    other=SQLiteStore(path);second=JointPortfolio(other,**args)
    e=evaluate(second,AT+timedelta(minutes=15));second.execute(e['id']);flat=second.snapshot()
    b=evaluate(second,AT+timedelta(minutes=30));second.execute(b['id'])
    assert (flat,second.snapshot())==result
    assert store.list('joint_states')==other.list('joint_states')
    assert store.list('joint_batches')==other.list('joint_batches')
    other.close()


def test_concurrent_agents_and_connections_reserve_once(store,tmp_path):
    path=tmp_path/'shared.db';one=SQLiteStore(path);two=SQLiteStore(path)
    args=inputs();a=JointPortfolio(one,**args);b=JointPortfolio(two,**args)
    async def concurrent():return await asyncio.gather(a.evaluate(AT),b.evaluate(AT))
    results=asyncio.run(concurrent())
    assert results[0]==results[1]
    assert len(one.list('joint_batches'))==1
    assert a.snapshot()==b.snapshot()
    assert a.execute(results[0]['id'])['success']
    assert b.execute(results[1]['id'])['replay']
    assert len(two.list('joint_settlements'))==1
    one.close();two.close()


def test_reservation_expiry_releases_cash_and_cannot_fill_old_signal(store):
    r=reports_at()+reports_at(AT+timedelta(minutes=15));s=portfolio(store,reports=r)
    first=evaluate(s);second=evaluate(s,AT+timedelta(minutes=15))
    assert selected(second)['symbol']=='ETHEUR'
    old=s.execute(first['id'])
    assert not old['success'] and old['kind']=='expiry'
    assert s.snapshot()['cash']=='200'
    assert s.execute(second['id'])['success']
    assert list(s.snapshot()['holdings'])==['ETHEUR']


def test_gap_does_not_spend_unreserved_cash(store):
    args=inputs();args['bars']['BTCEUR'][1]=bar(0,open=108,high=109,low=107,close=108)
    s=JointPortfolio(store,**args);b=evaluate(s);out=s.execute(b['id'])
    assert not out['success'] and 'gereserveerde cash' in out['reason']
    assert s.snapshot()['cash']=='200' and s.snapshot()['reserved_cash']=='0'
    assert not s.snapshot()['holdings']
    assert s.execute(b['id'])['replay']


def test_future_extremes_do_not_affect_selection_or_entry(store):
    args=inputs();a=JointPortfolio(store,**args);first=evaluate(a);out=a.execute(first['id'])
    other=SQLiteStore()
    try:
        args['bars']['BTCEUR'][1]=bar(0,high=1000000,low=1)
        b=JointPortfolio(other,**args);second=evaluate(b)
        assert first==second and out==b.execute(second['id'])
        assert a.snapshot()==b.snapshot()
    finally:other.close()


def test_risk_engine_veto_and_recheck_before_execution(store,monkeypatch):
    s=portfolio(store)
    monkeypatch.setattr(s.risk,'check',lambda *a,**k:'centrale veto')
    b=evaluate(s)
    assert selected(b) is None and all(c['reason']=='centrale veto' for c in b['candidates'])
    with pytest.raises(ValueError):s.execute(b['id'])
    assert s.snapshot()['cash']=='200'


def test_stop_after_reservation_prevents_entry_and_persists(store):
    args=inputs();s=JointPortfolio(store,**args);b=evaluate(s)
    s.risk.stopped=True
    out=s.execute(b['id']);assert not out['success'] and out['reason']=='noodstop'
    restored=JointPortfolio(store,**args)
    assert restored.risk.stopped and restored.snapshot()['cash']=='200'


def test_no_agent_can_execute_unselected_or_fabricated_proposal(store):
    s=portfolio(store);b=evaluate(s)
    for bad in (str(b['candidates'][1]['entry']['event_id']),'fake',selected(b)['entry']['event_id']):
        with pytest.raises(ValueError):s.execute(bad)
    assert s.snapshot()['cash']=='200' and not store.list('joint_settlements')
    # Zelfs een gewijzigde opgeslagen kandidaat doorstaat de exacte herkomstcheck niet.
    key=selected(b)['entry']['event_id']
    row=json.loads(store.db.execute('SELECT payload FROM results WHERE id=?',(key,)).fetchone()[0])
    row['result']['quantity']='999'
    store.db.execute('UPDATE results SET payload=? WHERE id=?',(json.dumps(row),key))
    with pytest.raises(ValueError,match='agentherkomst'):s.execute(b['id'])
    assert s.snapshot()['cash']=='200'


def test_transaction_failure_rolls_back_fill_and_reservation(store,monkeypatch):
    s=portfolio(store);b=evaluate(s);before=s.snapshot();put=store.put
    def broken(table,*args):
        if table=='joint_states': raise RuntimeError('disk simulation')
        return put(table,*args)
    monkeypatch.setattr(store,'put',broken)
    with pytest.raises(RuntimeError):s.execute(b['id'])
    assert not store.list('joint_settlements') and s.snapshot()==before
    monkeypatch.setattr(store,'put',put)
    assert s.execute(b['id'])['success']

@pytest.mark.parametrize('problem',['missing_report','stale','conflict','missing_bars','time_gap','timezone','test_period'])
def test_missing_or_invalid_data_fail_closed(store,problem):
    args=inputs()
    if problem=='missing_report':args['reports']=args['reports'][:1];args['plan']=plan(args['reports'])
    elif problem=='stale':
        args['reports'][0]=args['reports'][0].model_copy(update={'timestamp':AT-timedelta(hours=1)})
        args['plan']=plan(args['reports'])
    elif problem=='conflict':
        for r in args['reports']:r.result['conflicts']=['synthetisch conflict']
        args['plan']=plan(args['reports'])
    elif problem=='missing_bars':del args['bars']['ETHEUR']
    elif problem=='time_gap':args['bars']['ETHEUR'].pop(3)
    if problem in ('missing_bars','time_gap'):
        with pytest.raises(ValueError):JointPortfolio(store,**args)
        return
    s=JointPortfolio(store,**args)
    if problem in ('timezone','test_period'):
        at=AT.replace(tzinfo=None) if problem=='timezone' else args['plan'].independent_test.start
        with pytest.raises(ValueError):evaluate(s,at)
    else:assert selected(evaluate(s)) is None
    assert s.snapshot()['cash']=='200' and not store.list('joint_settlements')
    assert all(r['stage']=='development' for r in store.list('research_exposures'))


def test_corrupted_state_fails_closed(store):
    s=portfolio(store);b=evaluate(s)
    row=store.db.execute('SELECT id,payload FROM joint_states ORDER BY rowid DESC LIMIT 1').fetchone()
    value=json.loads(row[1]);value['ledger']['cash']='201'
    store.db.execute('UPDATE joint_states SET payload=? WHERE id=?',(json.dumps(value),row[0]))
    with pytest.raises(ValueError,match='hashketen'):s.execute(b['id'])
    assert not store.list('joint_settlements')


def test_policy_and_limits_immutable_and_no_production_mutations(store):
    args=inputs();s=JointPortfolio(store,**args)
    old={t:store.list(t) for t in ('orders','positions','portfolio_history','proposals','risk_decisions','research_fills','backtest_runs')}
    b=evaluate(s);s.execute(b['id'])
    assert old=={t:store.list(t) for t in old}
    with pytest.raises(ValueError):JointPolicy(max_open_positions=2)
    with pytest.raises(ValueError):JointPolicy(starting_cash='400')
    s.risk.limits=Limits(trade_risk='.01')
    with pytest.raises(ValueError,match='risicolimieten'):s.snapshot()


def test_position_cannot_skip_exit_candle(store):
    s=JointPortfolio(store,**switched_inputs());b=evaluate(s);s.execute(b['id'])
    with pytest.raises(ValueError,match='Iedere volgende'):evaluate(s,AT+timedelta(minutes=30))
    e=evaluate(s,AT+timedelta(minutes=15));assert e['reservation']['side']=='sell'
    with pytest.raises(ValueError,match='exit eerst'):evaluate(s,AT+timedelta(minutes=30))
    s.risk.stopped=True
    assert s.execute(e['id'])['success']  # Noodstop verhindert geen risicoverlagende exit.


def test_readonly_joint_api(store):
    s=portfolio(store);evaluate(s)
    with TestClient(create_app(store)) as c:
        for route in ('joint-protocols','joint-states','joint-candidates','joint-settlements'):
            assert c.get('/'+route).status_code==200
            assert c.post('/'+route,json={}).status_code==405
        assert len(c.get('/joint-candidates').json())==1


def test_loss_streak_survives_switch_to_another_coin(store):
    args=switched_inputs();args['policy']=JointPolicy(decision=DecisionPolicy(max_consecutive_losses=1))
    s=JointPortfolio(store,**args);s.execute(evaluate(s)['id'])
    s.execute(evaluate(s,AT+timedelta(minutes=15))['id'])
    batch=evaluate(s,AT+timedelta(minutes=30))
    eth=next(c for c in batch['candidates'] if c['symbol']=='ETHEUR')
    assert not eth['selected'] and eth['reason']=='verliesreekspauze'
    assert not s.snapshot()['holdings']

@pytest.mark.parametrize('gap,expected',[('70','dagverliespauze'),('.02','drawdownpauze')])
def test_global_loss_protections_persist_after_exit(store,gap,expected):
    r=reports_at()+reports_at(AT+timedelta(minutes=45));args=inputs(reports=r)
    v=D(gap);args['bars']['BTCEUR'][2]=bar(1,open=v,high=v+D('.01'),low=v-D('.01'),close=v)
    args['filters']={s:rules(s,min_notional=0) for s in COINS}
    s=JointPortfolio(store,**args);s.execute(evaluate(s)['id'])
    evaluate(s,AT+timedelta(minutes=15))
    s.execute(evaluate(s,AT+timedelta(minutes=30))['id'])
    assert not s.snapshot()['holdings'] and D(s.snapshot()['cash'])<194
    restored=JointPortfolio(store,**args)
    batch=evaluate(restored,AT+timedelta(minutes=45))
    assert selected(batch) is None
    reasons=[c['reason'] for c in batch['candidates']]
    # De dagverliesveto kan vóór de eveneens geactiveerde drawdownveto komen.
    assert all(r in ('dagverliespauze','drawdownpauze') for r in reasons)
    _,l=restored._read()
    if expected=='drawdownpauze':assert l.drawdown_paused
    else:assert l.day_paused


def test_stop_is_central_across_connections(store,tmp_path):
    args=inputs();path=tmp_path/'stop.db';one=SQLiteStore(path);two=SQLiteStore(path)
    a=JointPortfolio(one,**args);b=JointPortfolio(two,**args)
    batch=evaluate(a);b.stop()
    out=a.execute(batch['id'])
    assert not out['success'] and out['reason']=='noodstop'
    assert a.snapshot()['cash']==b.snapshot()['cash']=='200'
    one.close();two.close()


def test_inconsistent_balance_rejected_even_with_recomputed_state_hash(store):
    s=portfolio(store);b=evaluate(s)
    row=store.db.execute('SELECT id,payload FROM joint_states ORDER BY rowid DESC LIMIT 1').fetchone()
    value=json.loads(row[1]);value['ledger']['cash']='201'
    value['hash']=digest({k:v for k,v in value.items() if k!='hash'})
    store.db.execute('UPDATE joint_states SET payload=? WHERE id=?',(json.dumps(value),row[0]))
    with pytest.raises(ArithmeticError,match='reconciliatie'):s.execute(b['id'])
    assert not store.list('joint_settlements')


def test_separate_scanner_universes_cannot_be_ranked_together(store):
    r=reports_at()
    r[1].data['dependencies'][-1]='different-scanner'
    s=portfolio(store,reports=r)
    batch=evaluate(s)
    assert selected(batch) is None
    assert all('vergelijkingsuniversum' in c['reason'] for c in batch['candidates'])


def test_central_snapshot_api_exposes_only_one_cash_balance(store):
    s=portfolio(store);evaluate(s)
    with TestClient(create_app(store)) as c:
        snap=c.get('/joint-portfolios').json()
        assert snap==[s.snapshot()]
        assert snap[0]['cash']=='200' and D(snap[0]['available_cash'])<200
        assert c.post('/joint-portfolios',json={}).status_code==405


def test_risk_budget_and_cash_used_are_central_after_loss(store,monkeypatch):
    s=JointPortfolio(store,**switched_inputs());first=evaluate(s)
    s.execute(first['id']);s.execute(evaluate(s,AT+timedelta(minutes=15))['id'])
    cash=D(s.snapshot()['cash']);check=s.risk.check;calls=[]
    def inspect(*args,**kwargs):
        calls.append(kwargs.copy())
        return check(*args,**kwargs)
    monkeypatch.setattr(s.risk,'check',inspect)
    batch=evaluate(s,AT+timedelta(minutes=30));c=selected(batch)
    assert c['symbol']=='ETHEUR' and calls
    assert all(k['cash']==k['equity']==cash and k['exposure']==0 for k in calls)
    assert D(c['entry']['result']['planned_risk'])<=cash*D('.005')<1


def test_batch_ranking_and_approval_cannot_change_after_reservation(store):
    s=portfolio(store);batch=evaluate(s)
    raw=json.loads(store.db.execute('SELECT payload FROM joint_batches WHERE id=?',(batch['id'],)).fetchone()[0])
    raw['candidates'][0]['score']='99'
    store.db.execute('UPDATE joint_batches SET payload=? WHERE id=?',(json.dumps(raw),batch['id']))
    with pytest.raises(ValueError,match='goedgekeurde batch'):s.execute(batch['id'])
    assert s.snapshot()['cash']=='200' and not store.list('joint_settlements')


def test_invalid_candidate_is_retained_and_next_valid_coin_can_reserve(store):
    args=inputs();args['filters']['BTCEUR']=rules('BTCEUR',min_notional='1000')
    s=JointPortfolio(store,**args);b=evaluate(s)
    assert selected(b)['symbol']=='ETHEUR'
    btc=next(c for c in b['candidates'] if c['symbol']=='BTCEUR')
    assert not btc['eligible'] and btc['reason']==btc['agent_reason']=='MIN_NOTIONAL'
    assert len(store.list('joint_batches')[0]['candidates'])==2
