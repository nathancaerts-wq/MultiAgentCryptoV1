import asyncio
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D

import pytest
from crypto.protocol import ResearchPlan,Period,report_digest,planned_size,round_trip_net,unavailable_performance
from crypto.offline_optimizer import OfflineResearchOptimizer
from crypto.quant import QuantResearcher
from crypto.storage import SQLiteStore
from crypto.analysis import run_research
from crypto.data import DataEngine,Candle,SECONDS
from crypto.indicators import IndicatorConfig
from crypto.models import Limits

START=datetime(2025,1,1,tzinfo=timezone.utc)

def plan(**changes):
    fields=dict(coins=('BTCEUR','ETHEUR'),dataset_sha256='a'*64,source='fixture:quant-v1',report_hashes=(report_digest([]),)*3,
                development=Period(start=START,end=START+timedelta(days=30)),
                validation=Period(start=START+timedelta(days=31),end=START+timedelta(days=40)),
                independent_test=Period(start=START+timedelta(days=41),end=START+timedelta(days=50)))
    return ResearchPlan(**(fields|changes))

@pytest.fixture
def store():
    s=SQLiteStore();yield s;s.close()

class Data:
    def fetch(self,symbol,interval,start,end):
        result=[]
        for i in range(int((end-start).total_seconds())//SECONDS[interval]):
            t=start+timedelta(seconds=i*SECONDS[interval]);v=D(100+i)
            result.append(Candle(symbol=symbol,interval=interval,opened=t,closed=t+timedelta(seconds=SECONDS[interval]),open=v,high=v+1,low=v-1,close=v,volume=10,quote_volume=1000,source='fixture:quant-v1'))
        return result

def report(store,at=START+timedelta(days=1)):
    return asyncio.run(run_research(DataEngine(store,Data()),at,['BTCEUR']))[0]

@pytest.mark.parametrize('change',[dict(starting_cash='1000'),dict(planned_risk='.006'),dict(planned_risk=0),dict(fee=-1),dict(slippage='NaN'),dict(hypotheses=()),dict(hypotheses=('aligned_trend','aligned_trend')),dict(coins=('BTCUSDT',)),dict(coins=('ETHEUR','BTCEUR')),dict(minimum_trades=5),dict(report_hashes=('wrong',)*3)])
def test_invalid_plan(change):
    with pytest.raises(ValueError):plan(**change)

@pytest.mark.parametrize('offset',[0,29,30])
def test_overlap_or_embargo(offset):
    with pytest.raises(ValueError): plan(validation=Period(start=START+timedelta(days=offset),end=START+timedelta(days=40)))

def test_timezone():
    with pytest.raises(ValueError):Period(start=START.replace(tzinfo=None),end=START+timedelta(days=1))

def test_walk_forward():
    p=plan();folds=p.walk_forward()
    assert len(folds)==3
    for f in folds:
        train,val=Period.model_validate(f['train']),Period.model_validate(f['validation'])
        assert train.end+timedelta(hours=4)==val.start
        assert val.end<=p.development.end<p.independent_test.start
    assert plan(walk_train_days=40).walk_forward()==[]

def test_costs():
    assert round_trip_net(1,100,110,0,0)==10
    assert round_trip_net(1,100,100,'.001','.001')==D('-.400000')
    assert round_trip_net(1,100,110,'.002','.002')<round_trip_net(1,100,110,'.001','.001')

def test_risk_budget():
    q=planned_size(200,100,95,'.001','.001')
    assert q*(D(5)+D('.4'))<=D(1)
    assert q*D('100.2')<=100
    with pytest.raises(ValueError): planned_size(200,100,95,0,0,'.01')

def test_metrics_not_fabricated():
    result=unavailable_performance()
    assert result['evidence']=='insufficient_evidence'
    assert all(v is None for v in result['metrics'].values())

def test_preregister_immutable(store):
    o=OfflineResearchOptimizer(store);p=plan();key=o.register(p)
    assert o.register(p)==key and len(store.list('research_plans'))==1
    with pytest.raises(ValueError): p.planned_risk=D('.1')
    changed=plan(fee='.002')
    assert changed.fingerprint!=key
    assert o._plan(key).fee==D('.001')

def test_independent_test_consumed_before_view_and_reopen(tmp_path):
    path=tmp_path/'study.sqlite3';s=SQLiteStore(path);o=OfflineResearchOptimizer(s);p=plan();key=o.register(p)
    first=o.inspect(key,'independent_test',[],p.dataset_sha256)
    assert first['independent_first_view'] and not first['independent_test_untouched']
    s.close();s=SQLiteStore(path);o=OfflineResearchOptimizer(s)
    assert not o.inspect(key,'independent_test',[],p.dataset_sha256)['independent_first_view']
    with pytest.raises(ValueError):o.register(plan(dataset_sha256='b'*64))
    s.close()

def test_prior_validation_forbids_new_plan(store):
    o=OfflineResearchOptimizer(store);p=plan();key=o.register(p)
    o.inspect(key,'validation',[],p.dataset_sha256)
    with pytest.raises(ValueError):o.register(plan(fee='.002'))

def test_unregistered_and_dataset_mismatch(store):
    o=OfflineResearchOptimizer(store)
    with pytest.raises(KeyError): o.inspect('missing','validation',[],'a'*64)
    p=plan();key=o.register(p)
    with pytest.raises(ValueError):o.inspect(key,'validation',[],'b'*64)
    assert not store.list('research_exposures')

def test_quant_reproducible_and_parameter_isolation(store):
    r=report(store);p=plan(report_hashes=(report_digest([r]),report_digest([]),report_digest([])))
    snapshots={name:store.list(name) for name in ('agents','strategies','orders','proposals','risk_decisions','portfolio_history')}
    before=Limits().model_dump()
    o=OfflineResearchOptimizer(store);key=o.register(p)
    result=o.inspect(key,'development',[r],p.dataset_sha256)
    again=o.inspect(key,'development',[r],p.dataset_sha256)
    assert result['selections']==again['selections']
    assert result['selections'][0]['hypotheses']['aligned_trend']['eligible'] is True
    assert result['performance']['BTCEUR']['aligned_trend']['metrics']['net_result'] is None
    assert result['multiple_testing']['planned_family_size']==6
    assert snapshots=={name:store.list(name) for name in snapshots}
    assert Limits().model_dump()==before
    with pytest.raises(ValueError): QuantResearcher(plan(indicators=IndicatorConfig(slow=25))).evaluate(r,START+timedelta(days=1))

def test_hash_rejects_modified_report(store):
    r=report(store);p=plan(report_hashes=(report_digest([r]),report_digest([]),report_digest([])))
    o=OfflineResearchOptimizer(store);key=o.register(p)
    altered=r.model_copy(deep=True);altered.result['fake']=True
    with pytest.raises(ValueError,match='Rapportinhoud'):o.inspect(key,'development',[altered],p.dataset_sha256)

def test_lookahead_stale_gap_and_component_conflict(store):
    r=report(store);at=START+timedelta(days=1);q=QuantResearcher(plan())
    with pytest.raises(ValueError):q.evaluate(r,at-timedelta(seconds=1))
    with pytest.raises(ValueError):q.evaluate(r,at+timedelta(hours=1))
    for field,value in [('end',(at+timedelta(hours=1)).isoformat()),('status','incomplete'),('count',1)]:
        bad=r.model_copy(deep=True);bad.data['frames']['1h'][field]=value
        with pytest.raises(ValueError):q.evaluate(bad,at)

def test_outside_test_period_still_consumes_holdout(store):
    r=report(store)
    p=plan(report_hashes=(report_digest([]),report_digest([]),report_digest([r])))
    o=OfflineResearchOptimizer(store);key=o.register(p)
    result=o.inspect(key,'independent_test',[r],p.dataset_sha256)
    assert result['rejections'] and not result['selections']
    assert not result['independent_test_untouched']

def test_external_exposure_and_walk_config_locked(store):
    o=OfflineResearchOptimizer(store);p=plan()
    o.mark_external_view(p.coins,p.independent_test,'Eerder handmatig onderzocht')
    with pytest.raises(ValueError):o.register(p)
    assert plan(walk_train_days=8).fingerprint!=p.fingerprint


def test_horizon_does_not_cross_split(store):
    at=plan().validation.end-timedelta(hours=1)
    r=report(store,at)
    p=plan(report_hashes=(report_digest([]),report_digest([r]),report_digest([])))
    o=OfflineResearchOptimizer(store);key=o.register(p)
    result=o.inspect(key,'validation',[r],p.dataset_sha256)
    assert not result['selections'] and result['rejections']

def test_holdout_status_tracks_external_view_after_registration(store):
    o=OfflineResearchOptimizer(store);p=plan();key=o.register(p)
    o.mark_external_view(['BTC/EUR'],p.independent_test,'Externe inzage na preregistratie')
    result=o.inspect(key,'development',[],p.dataset_sha256)
    assert result['independent_test_untouched'] is False
    assert not o.inspect(key,'independent_test',[],p.dataset_sha256)['independent_first_view']
