import json
import math
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
import pytest
from crypto.data import Candle, SECONDS
from crypto.indicators import IndicatorConfig, technical
from crypto.analysis import boundary
from scripts.phase6e_protocol import FIRST, LAST, COINS
from scripts.phase6e_technical import *


def checked_extract(coin, at, candles, recorded, scores):
    return extract_features(coin, at, candles, recorded, scores, score_at=at)


def fixture(at=FIRST, flat=False):
    frames={}; saved={}
    for tf,seconds in SECONDS.items():
        end=boundary(at,tf);rows=[]
        for i in range(33):
            value=D(100) if flat else D(99+i)
            t=end-timedelta(seconds=(33-i)*seconds)
            rows.append(Candle(symbol='BTCEUR',interval=tf,opened=t,closed=t+timedelta(seconds=seconds),
                open=value,close=value,high=value+1,low=value-1,volume=i+1,quote_volume=1000,source='fixture:6e'))
        frames[tf]=rows
        saved[tf]=technical(rows[1:],IndicatorConfig())|dict(count=32,end=end.isoformat())
    return frames,saved


def test_27_features_exact_saved_linear_reference():
    f,s=fixture();x=checked_extract('BTCEUR',FIRST,f,s,dict(zip(COINS,['5','5','3'])))
    assert set(x)==set(feature_names()) and len(x)==27
    for tf in SECONDS:
        # Existing phase3 Synthetic linear case: closes 100..131, RSI100, ATR2.
        assert D(s[tf]['ema_fast'])==127
        assert D(s[tf]['ema_slow'])==121
        assert x[tf+':rsi']==100 and x[tf+':delta_rsi']==0
        assert x[tf+':relative_atr']==D(2)/131
        assert x[tf+':volume_ratio']==D(33)/(sum(range(13,33))/D(20))
        assert x[tf+':volume_change']==D(33)/32-1
    assert x['scanner_rank']==1 and x['up_count']==3


@pytest.mark.parametrize('at',[FIRST,FIRST+timedelta(minutes=15),FIRST+timedelta(hours=3,minutes=45),LAST])
def test_all_frame_boundaries_and_reproduction(at):
    f,s=fixture(at)
    assert len(checked_extract('BTCEUR',at,f,s,dict.fromkeys(COINS,'1')))==27
    for tf,seconds in SECONDS.items():
        assert f[tf][-1].closed==boundary(at,tf)<=at
        assert f[tf][0].opened>=FIRST.replace(day=1)


def test_frozen_nonlinear_reference():
    golden=json.loads(Path('tests/fixtures/phase6e_indicator_reference.json').read_text())
    for tf in SECONDS:
        f,s=fixture()
        f[tf]=[c.model_copy(update={'open':D(100+i%7),'close':D(100+i%7),
            'high':D(102+i%7),'low':D(98+i%7)}) for i,c in enumerate(f[tf])]
        actual=technical(f[tf][1:],IndicatorConfig())
        assert actual==golden['current']
        assert technical(f[tf][:-1],IndicatorConfig())==golden['previous']
        s[tf]=actual|dict(end=boundary(FIRST,tf).isoformat(),count=32)
        x=checked_extract('BTCEUR',FIRST,f,s,dict.fromkeys(COINS,'1'))
        assert x[tf+':delta_rsi']==D(golden['current']['rsi'])-D(golden['previous']['rsi'])


@pytest.mark.parametrize('case',['future','duplicate','gap','recorded','missing_frame','missing_score','nan_score','before','after'])
def test_feature_rejections(case):
    f,s=fixture();scores=dict.fromkeys(COINS,'1');at=FIRST
    if case=='future': f['4h'][-1]=f['4h'][-1].model_copy(update={'closed':FIRST+timedelta(hours=4)})
    if case=='duplicate': f['1h'][-1]=f['1h'][-2]
    if case=='gap':f['15m'].pop(1)
    if case=='recorded':s['1h']['rsi']='99'
    if case=='missing_frame':del f['4h']
    if case=='missing_score':del scores['SOLEUR']
    if case=='nan_score':scores['SOLEUR']='NaN'
    if case=='before':at=FIRST-timedelta(minutes=15)
    if case=='after':at=LAST+timedelta(minutes=15)
    with pytest.raises(ValueError):checked_extract('BTCEUR',at,f,s,scores)


def test_zero_volume_and_absent_score_are_missing_not_zero():
    f,s=fixture(flat=True)
    f={tf:[c.model_copy(update={'volume':D(0)}) for c in rows] for tf,rows in f.items()}
    x=checked_extract('BTCEUR',FIRST,f,s,dict(BTCEUR=None,ETHEUR='1',SOLEUR='2'))
    assert x['scanner_score'] is None and x['scanner_rank'] is None
    assert x['1h:volume_ratio'] is None and x['1h:volume_change'] is None
    assert x['1h:rsi']==50
    assert missing_eligible(1,100) and not missing_eligible(2,100)
    assert not missing_eligible(0,0) and not missing_eligible(0,100,False)


def test_holm_known_values_none_ties_and_invalid():
    assert holm([.01,.04,.03])==pytest.approx([.03,.06,.06])
    assert holm([.01,None,.01])==[.03,None,.03]
    assert holm([None]*332)==[None]*332
    assert holm([.0001]+[None]*331)[0]==pytest.approx(.0332)
    for v in (-1,1.1,float('nan')):
        with pytest.raises(ValueError):holm([v])


def test_centered_p_and_nearest_rank_exact():
    assert centered_p(2,[0,1,2,3])==2/5
    assert centered_p(0,[-1,0,1])==1
    assert centered_p(2,[2,2,2])==1/4
    assert nearest([4,1,3,2],.025)==1 and nearest([4,1,3,2],.975)==4


def test_family_size_unique_and_fixed():
    f=contrast_family()
    assert len(f)==len(set(f))==332
    assert {k:sum(x[0]==k for x in f) for k in 'ABCD'}==dict(A=108,B=108,C=8,D=108)


def test_bootstrap_matches_expanded_circular_samples_and_shared_draws():
    data=[(float(i),1,float(i%3),1) for i in range(85)]
    starts=bootstrap_starts(85,40)
    result=block_bootstrap(data,starts)
    estimates=[]
    for draw in starts:
        indices=[(start+j)%85 for start in draw for j in range(42)][:85]
        estimates.append(sum(data[i][0]-data[i][2] for i in indices)/85)
    theta=sum(r[0]-r[2] for r in data)/85
    assert result['p']==centered_p(theta,estimates)
    assert result['interval']==pytest.approx([nearest(estimates,.025),nearest(estimates,.975)])
    assert block_bootstrap(data,bootstrap_starts(85,40))==result


def test_degenerate_insufficient_and_empty_replicate():
    assert block_bootstrap([],[],eligible=False)['status']=='insufficient_groups'
    assert block_bootstrap([(0,0,1,1)]*84,bootstrap_starts(84,3))['status']=='empty_group'
    assert block_bootstrap([(1,1,1,1)]*84,bootstrap_starts(84,3))['status']=='zero_variation'
    rows=[(1,1,0,0)]*42+[(0,0,1,1)]*42
    assert block_bootstrap(rows,[[0,0]])['status']=='empty_replicate'


def test_timegroup_eligibility_overlap_and_shared_coins():
    times=[FIRST+timedelta(hours=4*i) for i in range(42*21)]
    left=[(1,2,None)]*len(times);right=[(None,3,4)]*len(times)
    a,ok=aggregate_groups(times,left,right)
    assert ok and a[0]==(3,2,7,2)
    assert not aggregate_groups(times[:50],left[:50],right[:50])[1]
    assert not aggregate_groups(times,[(None,)*3]*len(times),right)[1]
    times[1]=times[0]+timedelta(minutes=15)
    with pytest.raises(ValueError):aggregate_groups(times,left,right)


def test_scanner_future_snapshot_and_precision_rejected():
    from decimal import localcontext
    f,s=fixture()
    with pytest.raises(ValueError):
        extract_features('BTCEUR',FIRST,f,s,dict.fromkeys(COINS,'1'),score_at=FIRST+timedelta(minutes=15))
    with localcontext() as ctx:
        ctx.prec=18
        with pytest.raises(ValueError):checked_extract('BTCEUR',FIRST,f,s,dict.fromkeys(COINS,'1'))


def test_unequal_group_weights_match_explicit_row_sampling():
    rows=[(float(i*(1+i%3)),1+i%3,float((i%5)*(1+i%2)),1+i%2) for i in range(84)]
    starts=bootstrap_starts(84,31)
    r=block_bootstrap(rows,starts)
    theta=sum(x[0] for x in rows)/sum(x[1] for x in rows)-sum(x[2] for x in rows)/sum(x[3] for x in rows)
    reps=[]
    for draw in starts:
        selected=[rows[(start+j)%84] for start in draw for j in range(42)]
        sums=[sum(x[k] for x in selected) for k in range(4)]
        reps.append(sums[0]/sums[1]-sums[2]/sums[3])
    assert r['p']==centered_p(theta,reps)
    assert r['interval']==pytest.approx([nearest(reps,.025),nearest(reps,.975)])
