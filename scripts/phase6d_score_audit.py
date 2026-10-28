"""Known-at scanner comparison only; no price labels or future winner selection.

The phase6C classifications expose scores only after decision validation. This
separate provenance audit counts the original raw scanner ranks, including HOLD.
It does not alter the preregistered outcome calculation or its output.
"""
import json,resource,signal,sqlite3,time
from pathlib import Path
from decimal import Decimal as D
from crypto.development_2024 import COINS,ENTRY,LAST_ENTRY
from crypto.readiness import dt
from scripts.phase6d_measure import ROOT,DB,save_new,sha

def main():
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
    def timeout(*args):raise TimeoutError('Known-score audit 180 second limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(180);began=time.perf_counter()
    db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);db.execute('PRAGMA cache_size=-8192')
    counts={s:{'observations':0,'higher_known_scanner':0,'ties_for_top':0,'missing_own_score':0,'comparison_unknown':0} for s in COINS}
    previous=None;timestamps=0;current=None;group={}
    def process(at, scores):
        nonlocal timestamps,previous
        t=dt(at);assert ENTRY<=t<=LAST_ENTRY
        if previous:assert (t-previous).total_seconds()==900
        previous=t;timestamps+=1
        assert set(scores)==set(COINS)
        for symbol in COINS:
            c=counts[symbol];c['observations']+=1;score=scores[symbol]
            if score is None:c['missing_own_score']+=1;c['comparison_unknown']+=1;continue
            others=[v for coin,v in scores.items() if coin!=symbol and v is not None]
            higher=any(v>score for v in others);c['higher_known_scanner']+=higher
            c['comparison_unknown']+=not higher and len(others)<2
            c['ties_for_top']+=len(others)==2 and not higher and any(v==score for v in others)
    for at,coin,raw in db.execute("SELECT at,coin,payload FROM stream_input WHERE kind='report' AND tf='' ORDER BY at,coin"):
        if current is not None and at!=current:process(current,group);group={}
        current=at;r=json.loads(raw)
        ranking=r['result']['components']['scanner']['ranking']
        if len(ranking)>1 or ranking and ranking[0]['symbol']!=coin:raise ValueError('Invalid coin-scoped ranking')
        value=D(ranking[0]['score']) if ranking else None
        if value is not None and not value.is_finite():raise ValueError('Nonfinite score')
        group[coin]=value
    if current is not None:process(current,group)
    assert timestamps==34448
    db.close()
    save_new(ROOT/'known_score_audit.json',{'source':'original coin-scoped scanner ranks joined on original decision UTC at each decision t, independent of later DecisionAgent validation',
       'outcome_data_used':False,'timestamps':timestamps,'per_coin':counts,
       'total_with_higher_scanner':sum(x['higher_known_scanner'] for x in counts.values()),
       'script_sha256':sha(__file__),'elapsed':time.perf_counter()-began,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    signal.alarm(0)
if __name__=='__main__':main()
