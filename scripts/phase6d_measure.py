"""Sealed registration then a bounded read-only phase6D diagnostic, never orders."""
import argparse,gzip,hashlib,json,os,resource,signal,sqlite3,time
from collections import Counter,deque
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from crypto.opportunity_measurement import *
from crypto.models import Message
from crypto.readiness import dt
from scripts.phase6c_diagnostics import sha

ROOT=Path('experiments/phase6d');DB=Path('/workspace/development_2024.sqlite3')
FILES=['experiments/phase6d/protocol.json','crypto/opportunity_measurement.py','scripts/phase6d_measure.py']
SOURCES=[p for folder in ('experiments/development_2024','experiments/phase6c') for p in sorted(Path(folder).iterdir()) if p.is_file()]

def hashes():return {str(p):sha(p) for p in SOURCES+[Path(p) for p in FILES]}
def save_new(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,default=str);f.write('\n')

def register():
    old=json.loads(Path('experiments/development_2024/verification.json').read_text())
    assert sha(DB)==old['database_sha256']
    db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
    exposures=[json.loads(x[0]) for x in db.execute('SELECT payload FROM research_exposures')];db.close()
    assert len(exposures)==6 and all(x['stage']=='development' and dt(x['period']['start'])==dt('2024-01-01') and dt(x['period']['end'])==END for x in exposures)
    m={'version':'phase6d-v1','protocol':json.loads((ROOT/'protocol.json').read_text()),'files':hashes(),
       'database_sha256':old['database_sha256'],'database_bytes':DB.stat().st_size,'prior_exposures':exposures,
       'integrity':'Content-addressed exclusive creation, read-only mode and preregistration Git commit; not immutable against an administrator rewriting files/history'}
    raw=json.dumps(m,sort_keys=True,indent=2).encode();h=hashlib.sha256(raw).hexdigest()
    path=ROOT/('manifest_'+h+'.json')
    with path.open('xb') as f:f.write(raw)
    path.chmod(0o444)
    save_new(ROOT/'registration.json',{'manifest':str(path),'sha256':h,'status':'registered_before_labels','independent_test_opened':False})
    print(path)

def empty():return {'n':0,'gross':Counter(),'net_positive':0,'gross_positive_net_positive':0,'minima':[],'gross_values':[],
 'regime':{},'direction':{},'features':{},'higher_score':0,'reasons':Counter(),'categories':Counter(),'reason_outcomes':{},'category_outcomes':{}}
def add(stats,y,x,features):
    stats['n']+=1;stats['gross'][y['label']]+=1;stats['net_positive']+=y['net_positive']
    for field,value in (('reason_outcomes',x['reason']),('category_outcomes',x['category'])):
        v=stats[field].setdefault(value,Counter());v[y['label']]+=1;v['net_positive']+=y['net_positive']
    stats['gross_positive_net_positive']+=y['label']=='positive' and y['net_positive']
    stats['minima'].append(y['minimum']);stats['gross_values'].append(y['gross'])
    stats['higher_score']+=bool(x['higher_known_score_coins']);stats['reasons'][x['reason']]+=1;stats['categories'][x['category']]+=1
    for field in ('regime','direction'):
        v=stats[field].setdefault(features[field],Counter());v[y['label']]+=1
    f=stats['features'].setdefault(y['label'],{'n':0,'rsi':D(0),'momentum':D(0),'atr':D(0)})
    f['n']+=1
    for key in ('rsi','momentum','atr'):f[key]+=features[key]
def finish(s):
    for key in ('minima','gross_values'):
        a=sorted(s[key]);s[key]={'min':a[0] if a else None,'median':(a[(len(a)-1)//2]+a[len(a)//2])/2 if a else None,'max':a[-1] if a else None}
    for f in s['features'].values():
        for key in ('rsi','momentum','atr'):f[key]/=f['n']
    return s

def run():
    reg=json.loads((ROOT/'registration.json').read_text());p=Path(reg['manifest']);raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==reg['sha256'];m=json.loads(raw)
    assert hashes()==m['files'] and sha(DB)==m['database_sha256']
    if (ROOT/'labels.jsonl.gz').exists() or (ROOT/'result.json').exists():raise ValueError('Existing run preserved')
    save_new(ROOT/'access.json',{'stage':'development','manifest':reg['sha256'],'prior_viewed':True,'kind':'new_price_labels_not_new_portfolio_backtest','validation_accessed':False,'independent_test_opened':False})
    db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);db.execute('PRAGMA cache_size=-8192');db.execute('BEGIN')
    stats={};count=0;known_orders=[]
    stored=json.loads(Path('experiments/development_2024/aligned_trend_baseline.json').read_text())
    for coin in COINS:
        # At most seventeen candles retained. Past feature and future-label inputs stay separate.
        bars=iter(Candle.model_validate_json(raw) for (raw,) in db.execute("SELECT payload FROM stream_input WHERE kind='bars' AND coin=? AND tf='15m' AND at>=? AND at<? ORDER BY at",(coin,(ENTRY-timedelta(minutes=15)).isoformat(),END.isoformat())))
        previous=next(bars);window=deque(next(bars) for _ in range(16))
        expected=ENTRY
        with gzip.open('experiments/phase6c/aligned_trend_baseline_classifications.jsonl.gz','rt') as f, gzip.open(ROOT/'labels.jsonl.gz','at' if count else 'wt') as out:
            for line in f:
                x=json.loads(line);at=dt(x['at'])
                if x['coin']!=coin or at>LAST_ENTRY:continue
                assert at==expected
                raw_report=db.execute("SELECT payload FROM stream_input WHERE kind='report' AND coin=? AND tf='' AND at=?",(coin,at.isoformat())).fetchone()
                if not raw_report:raise ValueError('Missing report')
                features=known_features(Message.model_validate_json(raw_report[0]),coin,at,previous)
                y=measure(window,coin,at)
                row={'coin':coin,'at':at.isoformat(),'decision':x,'known_features':features,'outcome':y,'manifest':reg['sha256']}
                out.write(json.dumps(row,sort_keys=True,default=str)+'\n');count+=1
                for sample in ('overlapping',)+(('utc4h',) if y['nonoverlap'] else ()):
                    for group in ('all',)+(('HOLD',) if x['action']=='HOLD' else ()):
                        add(stats.setdefault(sample+':'+group,empty()),y,x,features)
                        add(stats.setdefault(sample+':'+group+':'+coin,empty()),y,x,features)
                if count%1000==0:
                    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>805306368:raise MemoryError('RSS limit')
                    print(coin,at.isoformat(),count,flush=True)
                expected+=timedelta(minutes=15);previous=window.popleft()
                if expected<=LAST_ENTRY:window.append(next(bars))
        assert expected==LAST_ENTRY+timedelta(minutes=15)
    # Only recorded ex-ante approved entry chains: no invented permission for HOLD.
    for (raw,) in db.execute("SELECT payload FROM joint_settlements WHERE json_extract(payload,'$.portfolio')=?",(stored['portfolio']['portfolio'],)):
        e=json.loads(raw)
        if e.get('side')=='buy':known_orders.append(e)
    assert count==103344 and len(known_orders)==7
    db.close();assert sha(DB)==m['database_sha256'] and hashes()==m['files']
    save_new(ROOT/'result.json',{'status':'complete','labels':count,'manifest':reg['sha256'],
        'statistics':{k:finish(v) for k,v in stats.items()},'missing_features':0,'missing_windows':0,
        'recorded_order_outcomes':known_orders,'recorded_trades':stored['trade_records'],
        'new_order_simulations':0,'orders_note':'Existing ex-ante risk and fillsimulator outcomes retained; other labels have no new permission or shadow portfolio',
        'old_data_and_results_unchanged':True,'labels_sha256':sha(ROOT/'labels.jsonl.gz'),
        'validation_accessed':False,'independent_test_opened':False})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
    def timed_out(*args):raise TimeoutError('Phase6D 600 second limit; preserve partial output')
    signal.signal(signal.SIGALRM,timed_out);signal.alarm(600);began=time.perf_counter()
    try:
        register() if args.mode=='register' else run()
        if args.mode=='run':save_new(ROOT/'performance.json',{'elapsed':time.perf_counter()-began,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limit_seconds':600,'address_space_bytes':1024**3})
    except BaseException as exc:
        if args.mode=='run' and not (ROOT/'interruption.json').exists():save_new(ROOT/'interruption.json',{'status':'incomplete','reason':repr(exc),'elapsed':time.perf_counter()-began})
        raise
    finally:signal.alarm(0)
