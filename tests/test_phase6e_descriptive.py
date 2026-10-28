from scripts.phase6e_descriptive import summaries,APPROVAL
from scripts.phase6e_technical import contrast_family
from array import array


def test_descriptive_summaries_and_missing_support():
 a=summaries(array('d',[1,2,3,4]),4,0,21,40)
 assert a['mean']==2.5 and a['median']==2 and a['p10']==1 and a['p90']==4 and a['status']=='ok'
 assert summaries(array('d',[1]),2,1,21,40)['status']=='insufficient_support'
 assert summaries(array('d'),0,0,21,40)['status']=='empty_group'
 assert summaries(array('d',[1]*40),40,0,1,40)['status']=='insufficient_support'


def test_fixed_family_and_scope():
 assert len(set(contrast_family()))==len(contrast_family())==332
 assert 'beschrijvende' in APPROVAL


def test_json_roundtrip_of_fixed_contrast_family():
 import json
 assert json.loads(json.dumps(contrast_family()))==[list(k) for k in contrast_family()]


def test_time_bitmap_counts_distinct_groups():
 bits=0
 for i in (0,0,16,16,32):bits |= 1 << i
 assert bits.bit_count()==3


def test_pause_boundary_uses_pre_settlement_original_decision_state():
 from datetime import datetime,timezone,timedelta
 from scripts.phase6e_descriptive import PAUSE_DECISION_AT
 before=datetime(2024,1,11,16,tzinfo=timezone.utc)
 assert before<PAUSE_DECISION_AT==before+timedelta(minutes=15)
