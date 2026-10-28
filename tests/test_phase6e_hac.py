import math
import pytest
from scripts.phase6e_hac import ratio_hac
from scripts.phase6e_amendment_probe import sample,wilson
from scripts.phase6e_technical import holm


def test_iid_mean_hand_calculation():
    r=ratio_hac([(0,1,0,1),(2,1,0,1)],lag=0)
    assert r['theta']==1 and r['se']==math.sqrt(.5)
    assert r['p']==pytest.approx(.15729920705028513)


def test_bartlett_lag_one_hand_calculation():
    r=ratio_hac([(0,1,0,1),(2,1,0,1)],lag=1)
    assert r['se']==.5
    assert r['p']==pytest.approx(.04550026389635844)


def test_unequal_counts_paired_influence_matches_finite_difference():
    rows=[(2,1,3,2),(8,3,1,1),(4,2,10,3)]
    theta=lambda w:sum(w[i]*r[0] for i,r in enumerate(rows))/sum(w[i]*r[1] for i,r in enumerate(rows))-sum(w[i]*r[2] for i,r in enumerate(rows))/sum(w[i]*r[3] for i,r in enumerate(rows))
    eps=1e-6;base=theta([1]*3);u=[]
    for i in range(3):
        w=[1]*3;w[i]+=eps;u.append(3*(theta(w)-base)/eps)
    r=ratio_hac(rows,lag=0)
    assert r['se']==pytest.approx(math.sqrt(sum(x*x for x in u)/9),rel=1e-6)


def test_paired_common_component_cancels():
    rows=[(float(i),1,float(i),1) for i in range(100)]
    assert ratio_hac(rows)['status']=='zero_or_invalid_variance'


def test_scale_sign_and_replication_invariance():
    rows=sample('ar05',123,n=100)
    r=ratio_hac(rows)
    scaled=[(-5*a,b,-5*c,d) for a,b,c,d in rows]
    assert ratio_hac(scaled)['p']==pytest.approx(r['p'])
    # Duplicating coins within a simultaneous timegroup must not increase n.
    assert ratio_hac([tuple(3*x for x in row) for row in rows])['p']==pytest.approx(r['p'])


@pytest.mark.parametrize('rows,lag',[([],42),([(1,1,0,1)],0),([(float('nan'),1,0,1)]*50,42),([(1,-1,0,1)]*50,42)])
def test_invalid_data(rows,lag):
    with pytest.raises(ValueError):ratio_hac(rows,lag)


def test_missing_and_zero_variance_no_false_positive():
    assert ratio_hac([],eligible=False)['p'] is None
    assert ratio_hac([(0,0,1,1)]*50)['status']=='empty_group'
    assert ratio_hac([(1,1,0,1)]*50)['p'] is None
    assert holm([None]*332)==[None]*332


def test_generator_and_estimator_repeat_without_history():
    for case in ('ar0','ar05','ar09','ar098','variance_break','random_level_break'):
        assert sample(case,7,n=50)==sample(case,7,n=50)
        assert ratio_hac(sample(case,7,n=50))==ratio_hac(sample(case,7,n=50))


def test_wilson_tail_resolution_and_zero_count():
    lo,hi=wilson(0,200)
    assert abs(lo)<1e-15 and hi>.05/332
    assert holm([.0001]+[None]*331)[0]<.05
    assert holm([.0002]+[None]*331)[0]>.05
