"""Kleine deterministische fase-5-workflows; geen netwerk of onafhankelijke testinzage."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import json
import pytest
from fastapi.testclient import TestClient
from crypto.analysis import run_research
from crypto.data import Candle, DataEngine, SECONDS
from crypto.models import Limits, Message
from crypto.protocol import ResearchPlan, Period, report_digest
from crypto.sim_execution import OfflineLedger, SpotFilters, FillCosts
from crypto.storage import SQLiteStore
from crypto.trade_agents import DecisionPolicy, DecisionAgent, EntryAgent, ExitAgent
from crypto.research_execution import ResearchTradingSession, ledger_state, restore_ledger
from crypto.api import create_app

AT = datetime(2025,1,10,12,tzinfo=timezone.utc)

class FixtureData:
    def fetch(self,symbol,interval,start,end):
        rows=[]
        for i in range(int((end-start).total_seconds())//SECONDS[interval]):
            v=D(100)+D(i)*D('.2')+[D(0),D(1),D(-1),D('.2')][i%4]
            t=start+timedelta(seconds=SECONDS[interval]*i)
            rows.append(Candle(symbol=symbol,interval=interval,opened=t,closed=t+timedelta(seconds=SECONDS[interval]),
                               open=v,high=v+1,low=v-1,close=v,volume=10,quote_volume=1000,source='fixture:phase5'))
        return rows

@pytest.fixture
def store():
    s=SQLiteStore(); yield s; s.close()

def report(store,symbol='BTCEUR'):
    return asyncio.run(run_research(DataEngine(store,FixtureData()),AT,[symbol]))[0]

def plan(reports=(),**changes):
    base=dict(coins=('BTCEUR','ETHEUR'),source='fixture:phase5',dataset_sha256='5'*64,
              report_hashes=(report_digest(reports),report_digest([]),report_digest([])),
              development=Period(start=AT-timedelta(hours=1),end=AT+timedelta(hours=8)),
              validation=Period(start=AT+timedelta(days=1),end=AT+timedelta(days=2)),
              independent_test=Period(start=AT+timedelta(days=3),end=AT+timedelta(days=4)))
    return ResearchPlan(**(base|changes))

def rules(symbol='BTCEUR',**changes):
    return SpotFilters(**(dict(symbol=symbol,source='fixture:phase5',status='assumed',note='Synthetische filters',
                              tick='.01',min_qty='.001',max_qty='100',step='.001',min_notional='1')|changes))

def bar(offset=-1,**changes):
    opened=AT+timedelta(minutes=15*offset)
    return Candle(**(dict(symbol='BTCEUR',interval='15m',opened=opened,closed=opened+timedelta(minutes=15),
                         open='106.4',high='107',low='106',close='106.4',volume=10,quote_volume=1000,source='fixture:phase5')|changes))

def session(store,**changes):
    r=report(store); p=plan([r]); bars=[bar(i) for i in range(-1,18)]
    kwargs=dict(store=store,plan=p,policy=DecisionPolicy(),symbol='BTCEUR',filters=rules(),reports=[r],bars=bars)
    kwargs.update(changes)
    return ResearchTradingSession(**kwargs)

def evaluate(s,at=AT): return asyncio.run(s.evaluate(at))
def decision(r,p=None,at=AT,position=None):
    return asyncio.run(DecisionAgent(p or plan([r]),DecisionPolicy(),r.coin,at,r,position).run(()))

def candidate(result,action='ENTRY_CANDIDATE'):
    return next(r for r in result['reviews'] if r['candidate']['result']['action']==action)


def test_eligible_unknown_sentiment_is_not_positive(store):
    r=report(store); m=decision(r)
    assert m.result['action']=='BUY_CANDIDATE'
    assert m.result['sentiment']=='unknown' and m.result['uncertainties']
    assert set(m.result['contributions'])=={'scanner','regime','technical','multi_timeframe','sentiment'}
    assert m==decision(r)
    assert m.result['research_only'] and 'approved' not in m.result

@pytest.mark.parametrize('component',['scanner','regime','technical','multi_timeframe','sentiment'])
def test_missing_component_holds(store,component):
    r=report(store).model_copy(deep=True); del r.result['components'][component]
    m=decision(r); assert m.result['action']=='HOLD' and m.result['missing']

@pytest.mark.parametrize('kind',['conflict','future','stale','wrong_end','incomplete','wrong_coin','nan','unknown_regime','sentiment','news_future','scanner_old'])
def test_bad_data_holds(store,kind):
    r=report(store).model_copy(deep=True)
    if kind=='conflict':r.result['conflicts'].append('Tegenstrijdige analyse')
    elif kind=='future':r=r.model_copy(update={'timestamp':AT+timedelta(seconds=1)})
    elif kind=='stale':r=r.model_copy(update={'timestamp':AT-timedelta(hours=1)})
    elif kind=='wrong_end':r.data['frames']['4h']['end']=(AT+timedelta(hours=4)).isoformat()
    elif kind=='incomplete':r.data['frames']['4h']['status']='incomplete'
    elif kind=='wrong_coin':r=r.model_copy(update={'coin':'SOLEUR'})
    elif kind=='nan':r.data['frames']['1h']['atr']='NaN'
    elif kind=='unknown_regime':r.result['components']['regime']['classification']='uncertain'
    elif kind=='sentiment':r.result['components']['sentiment']['sentiment']='positive'
    elif kind=='news_future':r.result['components']['sentiment']['items']=[dict(id='future',symbol='BTCEUR',source='https://example.org/fixture',title='Synthetisch',published=AT.isoformat(),available=(AT+timedelta(seconds=1)).isoformat(),expires=(AT+timedelta(hours=1)).isoformat())]
    elif kind=='scanner_old':r.result['components']['scanner']['ranking'][0]['data_end']=(AT-timedelta(hours=1)).isoformat()
    m=decision(r); assert m.result['action']=='HOLD'
    assert m.result['missing'] or m.result['conflicts']


def test_unclosed_and_timezone(store):
    r=report(store)
    assert decision(r,at=AT+timedelta(seconds=1)).result['action']=='HOLD'
    with pytest.raises(ValueError):decision(r,at=AT.replace(tzinfo=None))


def test_multi_coin_watchlist(store):
    for symbol in ('BTCEUR','ETHEUR'):
        r=report(store,symbol)
        assert decision(r).result['action']=='BUY_CANDIDATE'
        s=ResearchTradingSession(store,plan([r]),DecisionPolicy(),symbol,rules(symbol),[r],
                                 [bar(i,symbol=symbol) for i in range(-1,18)])
        assert candidate(evaluate(s))['approved']


def test_entry_cost_risk_and_no_automatic_order(store):
    s=session(store); before=ledger_state(s.ledger)
    result=evaluate(s); review=candidate(result); r=review['candidate']['result']
    assert review['approved'] and D(r['planned_risk'])<=1 and D(r['fee'])>0
    assert D(r['quantity'])*D(r['price'])<=100
    assert r['earliest_execution']==AT.isoformat()
    assert s.ledger.cash==200 and ledger_state(s.ledger)==before
    assert not store.list('orders') and not store.list('proposals') and not store.list('research_fills')

@pytest.mark.parametrize('change,reason',[(dict(min_notional='1000'),'MIN_NOTIONAL'),(dict(min_qty='10'),'LOT_SIZE'),(dict(avg_price_mins=5),'historische_gemiddelde')])
def test_order_filter_rejections(store,change,reason):
    s=session(store,filters=rules(**change)); res=evaluate(s)
    entry=res['messages']['entry:BTCEUR']
    assert entry.result['action']=='REJECTED' and reason in entry.result['reason']
    assert not any(r['approved'] for r in res['reviews'])


def test_cash_and_duplicate_position_rejected(store):
    s=session(store)
    r=candidate(evaluate(s)); assert s.execution.simulate(r['id'])['success']
    res=evaluate(s,AT+timedelta(minutes=15))
    assert res['messages']['decision:BTCEUR'].result['action']=='HOLD'
    assert not any(r['approved'] for r in res['reviews'])
    s.ledger.cash=D('.01')
    m=asyncio.run(EntryAgent(s.policy,s.symbol,AT,s.ledger,bar()).run((decision(report(store)),)))
    assert m.result['action']=='REJECTED'


def test_risk_engine_cannot_be_bypassed_and_emergency_rechecked(store):
    s=session(store); r=candidate(evaluate(s)); assert r['approved']
    s.risk.stopped=True
    filled=s.execution.simulate(r['id'])
    assert not filled['success'] and filled['reason']=='noodstop'
    assert s.ledger.cash==200 and s.ledger.position is None
    with pytest.raises(ValueError):s.execution.propose(None)
    with pytest.raises(ValueError):s.execution.simulate('fabricated')


def test_forged_decision_not_executable(store):
    s=session(store); r=candidate(evaluate(s))
    original=Message.model_validate(r['candidate'])
    from uuid import uuid4
    forged=original.model_copy(update={'event_id':uuid4()})
    review=s.execution.review(forged)
    assert review['approved']  # Risicorekenen geeft geen bevoegdheid zonder agentherkomst.
    with pytest.raises(ValueError,match='orchestrator'):s.execution.simulate(review['id'])
    assert s.ledger.cash==200


def test_gap_rechecks_price_and_planned_risk(store):
    bars=[bar(i) for i in range(-1,18)];bars[1]=bar(0,open=115,high=116,low=114,close=115)
    s=session(store,bars=bars); r=candidate(evaluate(s))
    assert r['approved']
    result=s.execution.simulate(r['id'])
    assert not result['success'] and 'risico' in result['reason']


def test_next_candle_and_future_extremes_do_not_select_entry(store):
    r=report(store); p=plan([r]); outcomes=[]
    for extreme in (D(107),D(1000000)):
        sstore=SQLiteStore()
        bars=[bar(i) for i in range(-1,18)];bars[1]=bar(0,high=extreme)
        s=ResearchTradingSession(sstore,p,DecisionPolicy(),'BTCEUR',rules(),[r],bars)
        out=evaluate(s); review=candidate(out)
        fill=s.execution.simulate(review['id'])
        assert fill['success'] and s.ledger.position.entered_at==AT
        outcomes.append((out['messages']['decision:BTCEUR'],review['candidate'],s.ledger.position.average_price))
        sstore.close()
    assert outcomes[0]==outcomes[1]


def test_dedup_persistent_restore_and_ledger_consistency(store,tmp_path):
    r=report(store);p=plan([r]);bars=[bar(i) for i in range(-1,18)]
    path=tmp_path/'decision.db'
    sstore=SQLiteStore(path);s=ResearchTradingSession(sstore,p,DecisionPolicy(),'BTCEUR',rules(),[r],bars)
    first=evaluate(s);again=evaluate(s)
    assert first['messages']==again['messages'] and first['reviews']==again['reviews']
    rev=candidate(first);fill=s.execution.simulate(rev['id']);assert fill['success']
    before=ledger_state(s.ledger)
    assert s.execution.simulate(rev['id'])['replay'] and ledger_state(s.ledger)==before
    sstore.close();sstore=SQLiteStore(path)
    reopened=ResearchTradingSession(sstore,p,DecisionPolicy(),'BTCEUR',rules(),[r],bars)
    assert ledger_state(reopened.ledger)==before
    reopened.ledger.reconcile()
    assert reopened.execution.simulate(rev['id'])['replay']
    assert len(sstore.list('research_fills'))==1
    sstore.close()


def positioned(**kw):
    l=OfflineLedger(FillCosts(),rules())
    assert l.buy('position',AT,D(100),D('.1'),D(95),AT+timedelta(hours=4),target=D(110))
    return l

@pytest.mark.parametrize('changes,reason,raw',[
    (dict(open=100,high=111,low=94,close=100),'stop','95'),
    (dict(open=90,high=111,low=89,close=100),'stop_gap','90'),
    (dict(open=100,high=111,low=96,close=100),'winstdoel','110'),
])
def test_exit_stop_target_gap_conservative(changes,reason,raw):
    l=positioned();b=bar(0,**changes)
    m=asyncio.run(ExitAgent(DecisionPolicy(),'BTCEUR',b.closed,l,b).run(()))
    assert m.result['action']=='EXIT_CANDIDATE' and m.result['reason']==reason
    assert D(m.result['reference'])==D(raw)
    if reason.startswith('stop'):assert m.result['ambiguous']
    assert l.position is not None


def test_exit_safety_time_and_incomplete():
    l=positioned();b=bar(0,open=100,high=101,low=99,close=100)
    m=asyncio.run(ExitAgent(DecisionPolicy(),'BTCEUR',b.closed,l,b,True).run(()))
    assert m.result['action']=='EXIT_CANDIDATE' and 'veiligheidsstop' in m.result['reason']
    m=asyncio.run(ExitAgent(DecisionPolicy(),'BTCEUR',b.opened,l,b).run(()))
    assert m.result['action']=='HOLD_POSITION' and 'onafgesloten' in m.result['reason']
    b=bar(16,open=100,high=101,low=99,close=100)
    m=asyncio.run(ExitAgent(DecisionPolicy(),'BTCEUR',b.closed,l,b).run(()))
    assert m.result['reason']=='tijdslimiet'


def test_exit_full_workflow_and_no_oversell(store):
    bars=[bar(i) for i in range(-1,18)];bars[2]=bar(1,open=100,high=101,low=99,close=100)
    s=session(store,bars=bars);entry=candidate(evaluate(s));assert s.execution.simulate(entry['id'])['success']
    evaluate(s,AT+timedelta(minutes=15))
    at=AT+timedelta(minutes=30)
    out=evaluate(s,at);exit_review=candidate(out,'EXIT_CANDIDATE')
    assert exit_review['approved'];s.risk.stopped=True
    fill=s.execution.simulate(exit_review['id']);assert fill['success']
    assert s.ledger.position is None and s.ledger.cash<200
    assert s.execution.simulate(exit_review['id'])['replay']
    assert not any(r['approved'] for r in evaluate(s,at)['reviews'])
    s.ledger.reconcile()
    assert not store.list('orders') and not store.list('positions')


def test_closed_holdout_and_frozen_configuration(store):
    s=session(store)
    with pytest.raises(ValueError,match='test gesloten'):evaluate(s,s.plan.independent_test.start)
    assert not store.list('research_exposures')
    with pytest.raises(ValueError,match='bevroren'):
        ResearchTradingSession(store,s.plan,DecisionPolicy(hypothesis='regime_momentum'),'BTCEUR',rules(),s.reports,s.bars)
    s.risk.limits=Limits(trade_risk='.01')
    with pytest.raises(ValueError,match='Risicoconfiguratie'):evaluate(s)
    assert not store.list('orders')


def test_reports_or_candles_cannot_change_after_registration(store):
    s=session(store);s.reports[0].result['fake']=True
    with pytest.raises(ValueError,match='Bevroren'):evaluate(s)


def test_missing_bars_and_invalid_plan_data(store):
    bars=[bar(i) for i in range(-1,18)];bars.pop(3)
    with pytest.raises(ValueError):session(store,bars=bars)
    with pytest.raises(ValueError):session(store,policy=DecisionPolicy(costs=FillCosts(fee='.01')))


def test_agent_does_not_modify_production_or_existing_research(store):
    s=session(store)
    names=('strategies','orders','positions','portfolio_history','proposals','risk_decisions','backtest_runs','research_results','simulation_protocols')
    snapshots={name:store.list(name) for name in names}
    original=Limits().model_dump();evaluate(s)
    assert snapshots=={name:store.list(name) for name in names} and Limits().model_dump()==original
    assert all(r['stage']=='development' for r in store.list('research_exposures'))


def test_read_only_api(store):
    s=session(store);evaluate(s)
    with TestClient(create_app(store)) as client:
        assert len(client.get('/decisions').json())==3
        assert len(client.get('/research-trade-reviews').json())==2
        assert client.get('/research-fills').json()==[]
        for route in ('/decisions','/research-trade-reviews','/research-fills'):
            assert client.post(route,json={}).status_code==405

@pytest.mark.parametrize('values',[dict(planned_risk='.006'),dict(max_consecutive_losses=0),dict(max_consecutive_losses=4),dict(hypothesis='optimized'),dict(stop_atr=3),dict(target=110)])
def test_policy_rejects_unplanned_changes(values):
    with pytest.raises(ValueError):DecisionPolicy(**values)

@pytest.mark.parametrize('pause,reason',[('day_paused','dagverlies'),('drawdown_paused','drawdown')])
def test_existing_pause_blocks_entry(store,pause,reason):
    s=session(store);r=candidate(evaluate(s));s.ledger.observe(AT,D('106.4'))
    setattr(s.ledger,pause,True)
    assert reason in s.execution.reason(Message.model_validate(r['candidate']),s.ledger)


def test_loss_streak_and_daily_drawdown_from_equity(store):
    s=session(store);r=candidate(evaluate(s));m=Message.model_validate(r['candidate'])
    s.ledger.trades=[{'net':'-1'}]*3
    assert s.execution.reason(m,s.ledger)=='verliesreekspauze'
    s.ledger.trades=[];s.ledger.day=AT.date();s.ledger.day_start=D(210)
    assert s.execution.reason(m,s.ledger)=='dagverliespauze'
    s.ledger.day_start=D(200);s.ledger.peak=D(230)
    assert s.execution.reason(m,s.ledger)=='drawdownpauze'


def test_exit_risk_rejects_oversell(store):
    from crypto.research_execution import market_rules
    s=session(store)
    assert 'onvoldoende positie' in s.risk.check_exit(quantity=D(2),price=D(100),available=D(1),
                   rules=market_rules(rules(),AT),timestamp=AT,evaluation_time=AT)


def test_existing_risk_engine_veto_is_final(store,monkeypatch):
    s=session(store)
    monkeypatch.setattr(s.risk,'check',lambda *a,**kw:'test: Risk Engine weigert')
    r=candidate(evaluate(s))
    assert not r['approved'] and r['reason']=='test: Risk Engine weigert'
    with pytest.raises(ValueError,match='goedgekeurd'):s.execution.simulate(r['id'])
    assert s.ledger.cash==200


def test_changed_ledger_cannot_use_old_approval(store):
    s=session(store);r=candidate(evaluate(s))
    s.ledger.day_paused=True
    with pytest.raises(ValueError,match='Ledger gewijzigd'):s.execution.simulate(r['id'])


def test_exit_review_bearish_and_essential_conflict_holds(store):
    from crypto.indicators import classify
    r=report(store).model_copy(deep=True)
    for f in r.data['frames'].values():
        f.update(direction='down',ema_gap='-.01',momentum='-.01',structure='lower_highs_lows',rsi='45',conflicts=[])
    r.result['components']['technical']['frames']=deepcopy(r.data['frames'])
    r.result['components']['regime']['classification']='bearish'
    r.result['components']['multi_timeframe']['directions']={tf:'down' for tf in ('15m','1h','4h')}
    m=decision(r,position=positioned().position)
    assert m.result['action']=='EXIT_REVIEW'
    r.result['conflicts']=['Tegenstrijdig essentieel signaal']
    assert decision(r,position=positioned().position).result['action']=='HOLD'


def test_two_sessions_cannot_overwrite_ledger(store):
    first=session(store)
    second=ResearchTradingSession(store,first.plan,first.policy,first.symbol,first.filters,first.reports,first.bars)
    a=candidate(evaluate(first));b=candidate(evaluate(second))
    assert first.execution.simulate(a['id'])['success']
    # Hetzelfde event wordt herkend; geen tweede afschrijving in de database.
    assert second.execution.simulate(b['id'])['replay']
    assert len(store.list('research_fills'))==1


def test_invalid_source_and_explicit_test_data_rejected(store):
    with pytest.raises(ValueError,match='officiële Binance'):
        session(store,bars=[bar(i,source='https://unknown.example/candles') for i in range(-1,18)])
    p=plan()
    with pytest.raises(ValueError,match='ontwikkeldata'):
        session(store,bars=[bar(i,opened=p.independent_test.start+timedelta(minutes=15*i),closed=p.independent_test.start+timedelta(minutes=15*(i+1))) for i in range(2)])


def test_position_cannot_skip_candles_or_pending_exit(store):
    bars=[bar(i) for i in range(-1,18)];bars[1]=bar(0,open='106.4',high=107,low=95,close=100)
    s=session(store,bars=bars);rev=candidate(evaluate(s));assert s.execution.simulate(rev['id'])['success']
    with pytest.raises(ValueError,match='overslaan'):evaluate(s,AT+timedelta(minutes=30))
    exit_review=candidate(evaluate(s,AT+timedelta(minutes=15)),'EXIT_CANDIDATE')
    assert exit_review['approved']
    with pytest.raises(ValueError,match='overslaan'):evaluate(s,AT+timedelta(minutes=30))
    assert s.execution.simulate(exit_review['id'])['success']
    assert s.ledger.position is None


def test_observation_restores_before_next_exit(store):
    bars=[bar(i) for i in range(-1,18)];bars[2]=bar(1,open=100,high=101,low=99,close=100)
    s=session(store,bars=bars);rev=candidate(evaluate(s));assert s.execution.simulate(rev['id'])['success']
    evaluate(s,AT+timedelta(minutes=15))
    before=ledger_state(s.ledger)
    restored=ResearchTradingSession(store,s.plan,s.policy,s.symbol,s.filters,s.reports,s.bars)
    assert ledger_state(restored.ledger)==before
    rev=candidate(evaluate(restored,AT+timedelta(minutes=30)),'EXIT_CANDIDATE')
    assert restored.execution.simulate(rev['id'])['success']
    restored.ledger.reconcile()
    assert len(restored.ledger.trades)==1
    for event in restored.ledger.events:
        from crypto.sim_execution import digest
        assert event['hash']==digest({k:v for k,v in event.items() if k!='hash'})


def test_invalid_candidate_financials_never_approved(store):
    s=session(store);m=Message.model_validate(candidate(evaluate(s))['candidate']).model_copy(deep=True)
    m.result['quantity']='NaN'
    r=s.execution.review(m)
    assert not r['approved'] and r['reason'].startswith('ongeldig onderzoeksvoorstel')
    assert not store.list('research_fills')


def test_real_archive_smoke_matches_saved_artifact():
    from pathlib import Path
    from scripts.phase5_smoke import smoke
    actual=asyncio.run(smoke())
    saved=json.loads((Path(__file__).parents[1]/'experiments/phase5_smoke.json').read_text())
    assert actual==saved
    assert actual['candles']==252 and actual['network_requests']==0
    assert actual['independent_test_opened'] is False and actual['offline_fills']==0


def test_stop_filter_prevents_unusable_initial_exit(store):
    s=session(store,filters=rules(min_price='104'))
    r=evaluate(s)['messages']['entry:BTCEUR'].result
    assert r['action']=='REJECTED' and r['reason']=='stop_exit_PRICE_FILTER'


def test_production_execution_cannot_receive_research_clock(store):
    from crypto.risk import ExecutionEngine
    s=session(store)
    with pytest.raises(ValueError,match='Historische klok'):
        ExecutionEngine(store,s.risk).propose(None,None,evaluation_time=AT)
    assert not store.list('orders') and not store.list('proposals')
