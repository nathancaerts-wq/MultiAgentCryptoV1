from datetime import timedelta
from decimal import Decimal as D
import pytest
from crypto.opportunity_measurement import *
from test_missed_opportunity import candles,AT
from test_joint_portfolio import reports_at
from test_trade_agents import FixtureData

@pytest.mark.parametrize('end,label',[(110,'positive'),(90,'negative'),(100,'neutral')])
def test_labels_costs_and_nonoverlap(end,label):
    y=measure(candles(end),'BTCEUR',AT)
    assert y['label']==label and y['nonoverlap'] and not y['executable']
    assert y['hypothetical_net']<Q*(D(end)-100)
    assert y['minimum']<=0

def test_costs_turn_small_rise_negative_and_fixed_quantity():
    y=measure(candles(D('100.1')),'BTCEUR',AT)
    assert y['label']=='positive' and not y['net_positive']
    assert y['fees']==COSTS.charge(Q,COSTS.price(D(100),'buy',TICK))+COSTS.charge(Q,COSTS.price(D('100.1'),'sell',TICK))

@pytest.mark.parametrize('case',['missing','duplicate','future','closed','naive'])
def test_bounds_and_missing(case):
    rows=candles();t=AT
    if case=='missing':rows.pop()
    if case=='duplicate':rows[-1]=rows[0]
    if case=='future':rows[-1]=rows[-1].model_copy(update={'closed':rows[-1].closed+timedelta(minutes=15)})
    if case=='closed':t=END
    if case=='naive':t=AT.replace(tzinfo=None)
    with pytest.raises(ValueError):measure(rows,'BTCEUR',t)

def test_last_entry_boundary():
    shift=LAST_ENTRY-AT
    rows=[c.model_copy(update={'opened':c.opened+shift,'closed':c.closed+shift}) for c in candles()]
    assert not measure(rows,'BTCEUR',LAST_ENTRY)['nonoverlap']
    with pytest.raises(ValueError):measure(rows,'BTCEUR',LAST_ENTRY+timedelta(minutes=15))

def test_known_features_not_changed_by_future_outcomes():
    from test_trade_agents import AT as OLD
    r=reports_at(OLD)[0];past=FixtureData().fetch('BTCEUR','15m',OLD-timedelta(minutes=15),OLD)[0]
    original=known_features(r,'BTCEUR',OLD,past)
    measure(candles(110),'BTCEUR',AT);measure(candles(90),'BTCEUR',AT)
    assert known_features(r,'BTCEUR',OLD,past)==original
    r.data['frames']['1h']['end']=(OLD+timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError):known_features(r,'BTCEUR',OLD,past)

def test_grid_not_rolling_resampling():
    assert all(int((AT+timedelta(hours=4*i)).timestamp())%14400==0 for i in range(6))
    assert int((AT+timedelta(minutes=15)).timestamp())%14400!=0
