import copy
from datetime import timedelta
from decimal import Decimal as D
import pytest
from crypto.missed_opportunity import *
from crypto.sim_execution import FillCosts

AT=START+timedelta(days=7)
def batch():
 return dict(id='b',portfolio='p',at=AT.isoformat(),candidates=[dict(symbol=s,selected=i==0,eligible=True,score=str(70-i),risk_approved=i==0,reason='reserved' if i==0 else 'verliesreekspauze',agent_reason='eligible',decision=dict(coin=s,timestamp=AT.isoformat(),result={'action':'BUY_CANDIDATE'})) for i,s in enumerate(COINS)])
def settlement(success):return dict(portfolio='p',batch='b',coin=COINS[0],side='buy',success=success,reason='fill' if success else 'gap')
def candles(last=100):
 return [Candle(symbol='BTCEUR',interval='15m',opened=AT+timedelta(minutes=15*i),closed=AT+timedelta(minutes=15*(i+1)),open=100,high=max(100,last),low=min(99,last),close=last if i==15 else 100,volume=1,quote_volume=100,source='fixture:labels') for i in range(16)]

@pytest.mark.parametrize('success,category',[(True,'executed_entry'),(False,'approved_execution_rejected')])
def test_classify_partition_and_known_ranking(success,category):
 b=batch();before=copy.deepcopy(b);r=classify_batch(b,settlement(success))
 assert r[0]['category']==category and r[1]['category']=='blocked_candidate'
 assert r[1]['higher_known_score_coins']==['BTCEUR'] and b==before
 assert len({tuple(x['key']) for x in r})==3 and all(x['retrospective_label'] is None for x in r)

def test_no_buy_moments_included():
 b=batch();b['candidates'][0].update(selected=False,eligible=False)
 b['candidates'][0]['decision']['result']['action']='HOLD'
 assert classify_batch(b)[0]['category']=='not_selected_no_buy'

@pytest.mark.parametrize('change',['future','duplicate','settlement','closed'])
def test_invalid_decision_identity(change):
 b=batch();s=None
 if change=='future':b['candidates'][0]['decision']['timestamp']=(AT+timedelta(minutes=15)).isoformat()
 if change=='duplicate':b['candidates'][1]['symbol']=COINS[0]
 if change=='settlement':s=settlement(True);s['batch']='wrong'
 if change=='closed':b['at']='2026-01-01T00:00:00+00:00'
 with pytest.raises(ValueError):classify_batch(b,s)

@pytest.mark.parametrize('last,label',[(110,'later_rise'),(90,'later_fall'),(100,'flat')])
def test_synthetic_labels_and_costs(last,label):
 r=fixture_outcome(candles(last),'BTCEUR',AT,D(1))
 assert r['label']==label and not r['executable']
 assert r['hypothetical_net'] < D(last)-100
 assert r['minimum_from_entry']<=0
 assert fixture_outcome(candles(last),'BTCEUR',AT,1,costs=FillCosts(fee=0,spread=0,slippage=0))['hypothetical_net']==D(last)-100

def test_price_rise_is_not_profit():
 r=fixture_outcome(candles(D('100.10')),'BTCEUR',AT,1)
 assert r['label']=='later_rise' and r['hypothetical_net']<0

@pytest.mark.parametrize('bad',['missing','duplicate','historical','boundary','size'])
def test_incomplete_or_unapproved_label_refused(bad):
 rows=candles();at=AT;q=1
 if bad=='missing':rows.pop()
 if bad=='duplicate':rows[-1]=rows[0]
 if bad=='historical':rows[0]=rows[0].model_copy(update={'source':'https://data.binance.vision/real'})
 if bad=='boundary':at=END
 if bad=='size':q=0
 with pytest.raises(ValueError):fixture_outcome(rows,'BTCEUR',at,q)

def test_labels_cannot_change_decisions_or_streak():
 before=classify_batch(batch(),settlement(True))
 fixture_outcome(candles(110),'BTCEUR',AT,1)
 fixture_outcome(candles(90),'BTCEUR',AT,1)
 assert classify_batch(batch(),settlement(True))==before
 ts=[dict(net='-1',exited_at=(AT+timedelta(hours=i)).isoformat()) for i in range(3)]
 assert trailing_losses(ts)==3
 assert trailing_losses(ts+[dict(net='0',exited_at=(AT+timedelta(days=1)).isoformat())])==0
 with pytest.raises(ValueError):trailing_losses(list(reversed(ts)))

def test_fixture_horizon_frozen_and_utc():
 with pytest.raises(ValueError):FixtureLabelSpec(hours=1)
 with pytest.raises(ValueError):fixture_outcome(candles(),'BTCEUR',AT.replace(tzinfo=None),1)
