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
