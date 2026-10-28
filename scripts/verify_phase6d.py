"""Independent artifact/financial arithmetic check; no new forward-price query."""
import gzip,json,hashlib,resource,signal
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from crypto.opportunity_measurement import Q,TICK,COSTS,ENTRY,LAST_ENTRY,COINS
from crypto.readiness import dt
from datetime import timedelta
from scripts.phase6d_measure import ROOT,DB,hashes,save_new
from scripts.phase6c_diagnostics import sha


def verify():
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
    def timeout(*args):raise TimeoutError('Verification 300 second limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
    reg=json.loads((ROOT/'registration.json').read_text());raw=Path(reg['manifest']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==reg['sha256'];m=json.loads(raw);assert hashes()==m['files']
    r=json.loads((ROOT/'result.json').read_text());assert r['manifest']==reg['sha256']
    assert sha(ROOT/'labels.jsonl.gz')==r['labels_sha256']
    old=json.loads(Path('experiments/development_2024/manifest.json').read_text())
    for p,h in old['files'].items():assert sha(p)==h,p
    def originals():
        for coin in COINS:
            with gzip.open('experiments/phase6c/aligned_trend_baseline_classifications.jsonl.gz','rt') as f:
                for line in f:
                    x=json.loads(line)
                    if x['coin']==coin and dt(x['at'])<=LAST_ENTRY:yield x
    source=iter(originals());counts=Counter();labels=Counter();nets=Counter();seen=0;expected={c:ENTRY for c in COINS}
    with gzip.open(ROOT/'labels.jsonl.gz','rt') as f:
        for line in f:
            x=json.loads(line);coin=x['coin'];t=dt(x['at']);assert t==expected[coin];expected[coin]+=timedelta(minutes=15)
            assert x['manifest']==reg['sha256'] and x['decision']==next(source)
            y=x['outcome'];a=D(y['entry_open']);b=D(y['valuation_close']);g=b/a-1
            assert D(y['gross'])==g and y['label']==('positive' if g>0 else 'negative' if g<0 else 'neutral')
            buy,sell=COSTS.price(a,'buy',TICK),COSTS.price(b,'sell',TICK)
            fees=COSTS.charge(Q,buy)+COSTS.charge(Q,sell);net=Q*(sell-buy)-fees
            assert D(y['fees'])==fees and D(y['hypothetical_net'])==net and y['net_positive']==(net>0)
            assert not y['executable'] and y['nonoverlap']==(int(t.timestamp())%14400==0)
            assert D(y['minimum'])<=0
            for sample in ('overlapping',)+(('utc4h',) if y['nonoverlap'] else ()):
                for group in ('all',)+(('HOLD',) if x['decision']['action']=='HOLD' else ()):
                    key=sample+':'+group;counts[key]+=1;labels[key,y['label']]+=1;nets[key]+=net>0
            seen+=1
    assert next(source,None) is None and seen==r['labels']==103344
    assert all(t==LAST_ENTRY+timedelta(minutes=15) for t in expected.values())
    for k,n in counts.items():
        s=r['statistics'][k];assert s['n']==n and s['net_positive']==nets[k]
        assert all(s['gross'].get(label,0)==labels[k,label] for label in ('positive','negative','neutral'))
    assert counts['utc4h:all']==6459
    sc=json.loads((ROOT/'known_score_audit.json').read_text());assert sc['total_with_higher_scanner']==r['statistics']['overlapping:all']['higher_score']
    assert sha(DB)==m['database_sha256']
    save_new(ROOT/'verification.json',{'verified':True,'labels':seen,'original_decisions_unchanged':True,
        'cost_arithmetic_exact':True,'counts_reconciled':True,'nonoverlap_observations':counts['utc4h:all'],
        'old_source_files_and_database_unchanged':True,'manifest_sha256':reg['sha256'],
        'database_sha256':m['database_sha256'],'new_portfolio_orders':0,'validation_accessed':False,'independent_test_opened':False,
        'verifier_sha256':sha(__file__)})
    signal.alarm(0);print('verified',seen)
if __name__=='__main__':verify()
