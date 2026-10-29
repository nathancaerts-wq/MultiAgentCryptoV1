"""Synthetic only: no historical database or network access."""
import asyncio
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
import inspect
import pytest
from crypto.recovery_research import RecoveryResearchPortfolio,advance,initial,_RecoveryReview
from crypto.research_execution import ResearchExecutionEngine,ledger_state
from crypto.joint_portfolio import JointPortfolio,JointPolicy
from crypto.protocol import Period
from crypto.storage import SQLiteStore
from test_joint_portfolio import reports_at,selected
from test_trade_agents import plan,bar,rules

AT=datetime(2024,1,31,12,tzinfo=timezone.utc)
COINS=('BTCEUR','ETHEUR','SOLEUR')

def args():
    reports=reports_at(AT)
    # Fixture reports for SOL use the same causal synthetic adapter.
    from crypto.analysis import run_research
    from crypto.data import DataEngine
    from test_trade_agents import FixtureData
    tmp=SQLiteStore()
    try: reports=asyncio.run(run_research(DataEngine(tmp,FixtureData()),AT,COINS))
    finally: tmp.close()
    p=plan(reports,coins=COINS,development=Period(start=AT-timedelta(hours=1),end=AT+timedelta(days=4)),
           validation=Period(start=AT+timedelta(days=5),end=AT+timedelta(days=6)),
           independent_test=Period(start=AT+timedelta(days=7),end=AT+timedelta(days=8)))
    rows={s:[bar(symbol=s,opened=AT+timedelta(minutes=15*i),closed=AT+timedelta(minutes=15*(i+1))) for i in range(-1,180)] for s in COINS}
    return dict(plan=p,policy=JointPolicy(),filters={s:rules(s) for s in COINS},reports=reports,bars=rows)

@pytest.fixture
def setup(tmp_path):
    a=args();path=tmp_path/'fixture.db';store=SQLiteStore(path)
    s=RecoveryResearchPortfolio(store,enabled=True,**a)
    yield s,a,path
    store.close()

def close(s,i,at=None,price='99',symbol=None):
    at=at or AT+timedelta(minutes=15*(i+1));symbol=symbol or COINS[i%3]
    with s.store.transaction():
        before,l=s._read();state=dict(before)
        l.rules=s.rules[symbol];state['active_rules']=symbol
        assert l.buy('buy'+str(i),at-timedelta(minutes=15),D(100),D('.1'),D(95),at+timedelta(hours=4))
        assert l.sell('exit'+str(i),at,D(price),'synthetic close')
        l.trades[-1]['symbol']=symbol
        state.update(at=at.isoformat(),mark=None,pending=None,checked_at=None)
        s._save(before,state,l,'fixture_settlement')
    return s._read()

def trigger(s):
    for i in range(3): close(s,i)
    return datetime.fromisoformat(s._read()[0]['recovery']['pause_until'])

def tick(s,at):return asyncio.run(s.evaluate(at))

def test_exact_three_and_shared_coins(setup):
    s,_,_=setup
    for i in range(3):
        st,l=close(s,i);assert st['recovery']['loss_count']==i+1
        assert bool(st['recovery']['pause_until'])==(i==2)
    assert len(l.trades)==3 and l.cash<D(200)
    assert len({t['symbol'] for t in l.trades})==3
    assert datetime.fromisoformat(st['recovery']['pause_until'])==AT+timedelta(minutes=45,hours=24)

@pytest.mark.parametrize('offset',[-15,0,15])
def test_expiry_boundary(setup,offset):
    s,_,_=setup;end=trigger(s);before,l=s._read();financial=ledger_state(l)
    tick(s,end+timedelta(minutes=offset));st,l=s._read()
    assert st['recovery']['epoch']==(0 if offset<0 else 1)
    assert st['recovery']['loss_count']==(3 if offset<0 else 0)
    for key in ('cash','trades','fees','realized','peak','day_start','day_paused','drawdown_paused'):
        assert ledger_state(l)[key]==financial[key]
    assert sum(e['action']=='cooldown_expired' for e in l.events)==(0 if offset<0 else 1)

@pytest.mark.parametrize('price',['102','101'])
def test_profit_breaks_streak(setup,price):
    s,_,_=setup;close(s,0);st,l=close(s,1,price=price)
    assert D(l.trades[-1]['net'])>0 and st['recovery']['loss_count']==0
    assert close(s,2)[0]['recovery']['loss_count']==1

def test_zero_breaks_streak_pure():
    rows=[dict(exit_id=str(i),exited_at=(AT+timedelta(minutes=i)).isoformat(),net=n) for i,n in enumerate(['-1','0','-1'])]
    r=advance(initial(),rows);assert r['loss_count']==1
    assert advance(r,rows)==r

def test_second_cycle_and_no_history_erased(setup):
    s,_,_=setup;end=trigger(s);old=s._read()[1].trades.copy();tick(s,end)
    for i in range(3,6): close(s,i,at=end+timedelta(minutes=15*(i-2)))
    st,l=s._read();assert st['recovery']['epoch']==1 and st['recovery']['loss_count']==3
    assert l.trades[:3]==old and len(l.trades)==6
    assert D(l.realized)==sum(D(t['net']) for t in l.trades)
    assert datetime.fromisoformat(st['recovery']['pause_until'])==end+timedelta(hours=24,minutes=45)

@pytest.mark.parametrize('at_end',[False,True])
def test_restart_and_duplicate_expiry(setup,at_end):
    s,a,path=setup;end=trigger(s)
    restarted=RecoveryResearchPortfolio(s.store,enabled=True,**a)
    assert restarted._read()[0]==s._read()[0]
    when=end if at_end else end-timedelta(minutes=15)
    tick(restarted,when);before=restarted._read()[0]
    again=RecoveryResearchPortfolio(s.store,enabled=True,**a);tick(again,when)
    assert again._read()[0]==before
    # Real connection close/reopen after checkpoint.
    s.store.close();s.store=SQLiteStore(path)
    final=RecoveryResearchPortfolio(s.store,enabled=True,**a)
    assert final._read()[0]==before

@pytest.mark.parametrize('flag',['drawdown_paused','day_paused'])
def test_expiry_preserves_other_pause(setup,flag):
    s,_,_=setup;end=trigger(s)
    with s.store.transaction():
        st,l=s._read();setattr(l,flag,True);s._save(st,st,l,'synthetic_pause')
    tick(s,end)
    assert getattr(s._read()[1],flag)

def test_emergency_stop_preserved(setup):
    s,_,_=setup;end=trigger(s);s.stop();tick(s,end)
    assert s.risk.stopped and s._read()[0]['stopped']
    assert s._risk_reason(entry(s,end),s._read()[1])=='noodstop'

@pytest.mark.parametrize('where',['close','expiry'])
def test_crash_rolls_back_complete_transaction(setup,monkeypatch,where):
    s,_,_=setup
    if where=='expiry':end=trigger(s)
    before,l=s._read();events=deepcopy(l.events);original=s.store.put
    def fail(table,key,value):
        original(table,key,value)
        if table=='joint_states':raise RuntimeError('crash after checkpoint insertion')
    with monkeypatch.context() as m:
        m.setattr(s.store,'put',fail)
        with pytest.raises(RuntimeError):
            if where=='close':close(s,0)
            else:tick(s,end)
    assert s._read()[0]==before and s._read()[1].events==events
    if where=='close':assert len(close(s,0)[1].trades)==1
    else:tick(s,end);assert s._read()[0]['recovery']['epoch']==1

def test_duplicate_and_changed_prefix_rejected():
    t=dict(exit_id='x',exited_at=AT.isoformat(),net='-1')
    r=advance(initial(),[t]);assert advance(r,[t])==r
    with pytest.raises(ValueError):advance(r,[t,t])
    with pytest.raises(ValueError):advance(r,[t|{'net':'1'}])
    with pytest.raises(ValueError):advance(r,[t,dict(exit_id='z',exited_at=(AT-timedelta(minutes=1)).isoformat(),net='-1')])

def test_pending_at_expiry_fails_closed(setup):
    s,_,_=setup;end=trigger(s)
    # A valid reservation normally cannot coexist with a triggered flat pause.
    with s.store.transaction():
        st,l=s._read();state=dict(st);state['pending']=dict(side='buy',cash='1',risk='.01',exposure='1',quantity='.01')
        s._save(st,state,l,'synthetic_pending')
    with pytest.raises(ValueError,match='reservering'):tick(s,end)
    assert s._read()[0]['recovery']['loss_count']==3

def test_disabled_exact_decisions_fills_finances_and_audit():
    a=args();stores=[SQLiteStore(),SQLiteStore()]
    try:
        b=JointPortfolio(stores[0],**a);r=RecoveryResearchPortfolio(stores[1],enabled=False,**a)
        rb=tick(b,AT);rr=tick(r,AT);assert rb==rr and selected(rr)
        assert b.execute(rb['id'])==r.execute(rr['id'])
        assert b.execute(rb['id'])==r.execute(rr['id'])
        assert b.snapshot()==r.snapshot() and b._read()[0]==r._read()[0]
        assert b._read()[1].events==r._read()[1].events
    finally:
        for st in stores:st.close()

def test_baseline_review_copy_only_changes_loss_gate():
    base=inspect.getsource(ResearchExecutionEngine._reason);new=inspect.getsource(_RecoveryReview._reason)
    left=base.index('        losses = 0');right=base.index('        stop =',left)
    nl=new.index("        if s.recovery[");nr=new.index('        stop =',nl)
    assert base[:left]==new[:nl] and base[right:]==new[nr:]

def test_sources_and_dates_guard(setup):
    s,a,_=setup
    bad=deepcopy(a);bad['plan']=bad['plan'].model_copy(update={'source':'https://data.binance.vision'})
    with pytest.raises(ValueError,match='synthetisch'):RecoveryResearchPortfolio(SQLiteStore(),enabled=True,**bad)
    with pytest.raises(ValueError):tick(s,datetime(2025,1,1,tzinfo=timezone.utc))

def entry(s,at):
    from crypto.trade_agents import message
    return message('entry',s._read()[0]['active_rules'],at,s.policy.decision,dict(action='ENTRY_CANDIDATE',reference='100',quantity='.1',stop='95'))

def test_gate_at_review_and_execution_reference(setup):
    s,_,_=setup;end=trigger(s)
    assert s._risk_reason(entry(s,end-timedelta(minutes=15)),s._read()[1])=='verliesreekspauze'
    # Time passing alone does not reset a checkpoint; decision transition required.
    assert s._risk_reason(entry(s,end),s._read()[1],D(100))=='verliesreekspauze'
    tick(s,end)
    assert s._risk_reason(entry(s,end),s._read()[1]) is None
    assert s._risk_reason(entry(s,end),s._read()[1],D(100)) is None
    assert s._risk_reason(entry(s,end-timedelta(minutes=15)),s._read()[1])=='voorstel van vóór hervatting'
    assert s._risk_reason(entry(s,end),s._read()[1],D(94))=='ongeldige stop na koersgap'

@pytest.mark.parametrize('flag,reason',[('day_paused','dagverliespauze'),('drawdown_paused','drawdownpauze')])
def test_other_risk_veto_wins_after_expiry(setup,flag,reason):
    s,_,_=setup;end=trigger(s);tick(s,end)
    l=s._read()[1]
    # Same-day observation must retain the flag in the review's isolated view.
    l.observe(end,D(100));setattr(l,flag,True)
    assert s._risk_reason(entry(s,end),l)==reason
    assert getattr(l,flag)

def test_actual_enabled_fill_dedup_and_rollback(setup,monkeypatch):
    s,_,_=setup;b=tick(s,AT);assert selected(b)
    before=s._read()[0];put=s.store.put
    with monkeypatch.context() as m:
        def fail(table,key,value):
            put(table,key,value)
            if table=='joint_states':raise RuntimeError('execution crash')
        m.setattr(s.store,'put',fail)
        with pytest.raises(RuntimeError):s.execute(b['id'])
    assert s._read()[0]==before
    out=s.execute(b['id']);assert out['success']
    state=s._read()[0];assert s.execute(b['id'])['replay']
    assert s._read()[0]==state and s._read()[1].position

def test_nonquarter_settlement_rounds_expiry_up(setup):
    s,_,_=setup
    for i in range(3):close(s,i,at=AT+timedelta(minutes=15*i+1))
    end=datetime.fromisoformat(s._read()[0]['recovery']['pause_until'])
    tick(s,end.replace(minute=30));assert s._read()[0]['recovery']['epoch']==0
    tick(s,end.replace(minute=45));assert s._read()[0]['recovery']['epoch']==1

def test_disabled_after_three_losses_keeps_baseline_pause(setup):
    _,a,_=setup;store=SQLiteStore()
    try:
        s=RecoveryResearchPortfolio(store,enabled=False,**a)
        for i in range(3):close(s,i)
        assert s._risk_reason(entry(s,AT+timedelta(hours=1)),s._read()[1])=='verliesreekspauze'
        assert 'recovery' not in s._read()[0]
    finally:store.close()

def test_enabled_real_agent_stop_fill_and_close_counter():
    a=args()
    for symbol,rows in a['bars'].items():
        a['bars'][symbol]=[c.model_copy(update={'low':D(90)}) if c.opened==AT else c for c in rows]
    store=SQLiteStore()
    try:
        s=RecoveryResearchPortfolio(store,enabled=True,**a)
        b=tick(s,AT);assert s.execute(b['id'])['success']
        b=tick(s,AT+timedelta(minutes=15));assert b['reservation']['side']=='sell'
        assert s.execute(b['id'])['success']
        st,l=s._read();assert len(l.trades)==1 and D(l.trades[0]['net'])<0
        assert st['recovery']['loss_count']==1 and l.position is None
        assert s.execute(b['id'])['replay'] and len(s._read()[1].trades)==1
    finally:store.close()

@pytest.mark.parametrize('change',['coins','year','policy'])
def test_constructor_scope_cannot_expand(setup,change):
    _,a,_=setup;a=deepcopy(a)
    if change=='coins':a['plan']=a['plan'].model_copy(update={'coins':('BTCEUR',)})
    if change=='year':a['plan']=a['plan'].model_copy(update={'development':Period(start='2025-01-01T00:00:00Z',end='2025-01-02T00:00:00Z')})
    if change=='policy':a['policy']=JointPolicy(decision=a['policy'].decision.model_copy(update={'max_consecutive_losses':2}))
    st=SQLiteStore()
    try:
        with pytest.raises(ValueError):RecoveryResearchPortfolio(st,enabled=True,**a)
    finally:st.close()
