"""Explicitly approved 2024 descriptive joins. No inferential or order path."""
import argparse,gzip,hashlib,json,resource,signal,sqlite3,time
from array import array
from collections import Counter
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from crypto.data import Candle,SECONDS
from crypto.indicators import IndicatorConfig
from scripts.phase6e_protocol import FIRST,LAST,COINS,utc
from scripts.phase6e_technical import extract_features,feature_names,contrast_family,nearest
from scripts.phase6c_diagnostics import sha
from scripts.phase6b_full_audit import CachedDownloads,MonthlyAuditAdapter

ROOT=Path('experiments/phase6e_descriptive');DB=Path('/workspace/development_2024.sqlite3')
APPROVAL='User Fase 6E: beschrijvende patroonanalyse; expliciete goedkeuring statistische amendering, 2024 BTC/ETH/SOL; geen p-waarden of backtests'
SOURCE=[Path(p) for p in ('PHASE6E_STATISTICAL_AMENDMENT.md','PHASE6E_ANALYSIS_PROTOCOL_PROPOSAL.md','PHASE6E_HYPOTHESES.md',
  'experiments/phase6d/labels.jsonl.gz','experiments/phase6d/registration.json','experiments/phase6e/protocol_proposal.json',
  'experiments/phase6c/ema_trend_baseline_classifications.jsonl.gz',
  'scripts/phase6e_descriptive.py','scripts/phase6e_technical.py','crypto/indicators.py','scripts/phase6b_full_audit.py','crypto/archive.py')]
def save(path,value):
 with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2,default=str);f.write('\n')
def approval_manifest():
 reg=json.loads(Path('experiments/phase6d/registration.json').read_text())
 if sha(reg['manifest'])!=reg['sha256']:raise ValueError('Old manifest changed')
 old=json.loads(Path(reg['manifest']).read_text())
 if sha(DB)!=old['database_sha256']:raise ValueError('Audit DB changed')
 source={str(p):sha(p) for p in SOURCE}
 for coin in COINS:
  for tf in SECONDS:
   url=f'https://data.binance.vision/data/spot/monthly/klines/{coin}/{tf}/{coin}-{tf}-2024-01.zip'
   for suffix in ('','.CHECKSUM'):
    token=hashlib.sha256((url+suffix).encode()).hexdigest()
    p=Path('/workspace/phase6b_archive_cache')/token
    if not p.exists():raise ValueError('Missing official cached January archive')
    source[str(p)]=sha(p)
 m=dict(version='phase6e-descriptive-v3',supersedes_registration='experiments/phase6e_descriptive/registration_v2.json; v2 stopped without result after observed memory growth from Python timegroup sets',approval=APPROVAL,prior_viewed_2024=True,
  original_proposal_status='not_activated',amendment_scope='descriptive_only_this_2024_study',
  contrasts=contrast_family(),coins=COINS,first=FIRST.isoformat(),last=LAST.isoformat(),
  source_sha256=source,database_sha256=old['database_sha256'],database_bytes=DB.stat().st_size,
  old_manifest_sha256=reg['sha256'],no_inference=True,no_orders=True,
  limits=dict(seconds=600,address_space_bytes=1024**3,rss_bytes=805306368))
 raw=json.dumps(m,sort_keys=True,indent=2).encode();h=hashlib.sha256(raw).hexdigest()
 path=ROOT/('manifest_'+h+'.json')
 with path.open('xb') as f:f.write(raw)
 path.chmod(0o444)
 save(ROOT/'registration_v3.json',dict(manifest=str(path),sha256=h,status='approved_descriptive_only_before_comparisons',
    prior_viewed_2024=True,validation_accessed=False,independent_test_opened=False))
 print('registered',h,flush=True)

def check():
 reg=json.loads((ROOT/'registration_v3.json').read_text());m=json.loads(Path(reg['manifest']).read_text())
 if sha(reg['manifest'])!=reg['sha256'] or reg['status']!='approved_descriptive_only_before_comparisons':raise ValueError('Registration changed')
 if m['approval']!=APPROVAL or m['contrasts']!=[list(k) for k in contrast_family()] or not m['no_inference']:raise ValueError('Wrong scope')
 for p,h in m['source_sha256'].items():
  if sha(p)!=h:raise ValueError('Source changed: '+p)
 if sha(DB)!=m['database_sha256']:raise ValueError('DB changed')
 return reg,m

def summaries(values,selected,missing,blocks,groups):
 n=len(values)
 if not n:return dict(n=0,selected=selected,missing=missing,blocks=blocks,timegroups=groups,
   status='empty_group',mean=None,median=None,p10=None,p90=None,min=None,max=None)
 v=sorted(values)
 # Means via fsum, quantiles nearest rank per registered amendment.
 import math
 return dict(n=n,selected=selected,missing=missing,blocks=blocks,timegroups=groups,
   status='ok' if blocks>=20 and groups>=30 and missing*100<=selected else 'insufficient_support',
   mean=math.fsum(v)/n,median=nearest(v,.5),p10=nearest(v,.1),p90=nearest(v,.9),min=v[0],max=v[-1])

def run():
 reg,m=check()
 if (ROOT/'result.json').exists():raise ValueError('Existing results preserved')
 save(ROOT/'access_v3.json',dict(status='2024_previously_viewed_descriptive_only',manifest=reg['sha256'],
  validation_accessed=False,independent_test_opened=False,new_orders=0))
 ema=set()
 with gzip.open('experiments/phase6c/ema_trend_baseline_classifications.jsonl.gz','rt') as f:
  for line in f:
   x=json.loads(line)
   if x['action']=='BUY_CANDIDATE' and utc(x['at'])<=LAST:ema.add((x['coin'],x['at']))
 db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);db.execute('PRAGMA cache_size=-8192');db.execute('BEGIN')
 names=contrast_family();data={sample:{k:[array('d'),array('d')] for k in names} for sample in ('utc4h','overlapping')}
 info={sample:{k:[dict(selected=0,missing=0,blocks=set(),times=0),dict(selected=0,missing=0,blocks=set(),times=0)] for k in names} for sample in data}
 tables={sample:{'all':Counter(),'hold':Counter(),'pause_hold':Counter(),'nonpause_hold':Counter(),
   'coin':{c:Counter() for c in COINS},'regime':{},'ema_candidates':Counter(),
   'aligned_candidates':Counter()} for sample in data}
 count=0;hold=0;ema_matched=0;aligned_matched=0
 def add(sample,key,side,value,t):
  z=info[sample][key][side];z['selected']+=1
  if value is None:z['missing']+=1;return
  data[sample][key][side].append(float(value));z['blocks'].add((t.date()-FIRST.date()).days//7);z['times'] |= 1 << int((t-FIRST).total_seconds()//900)
 with gzip.open('experiments/phase6d/labels.jsonl.gz','rt') as source:
  for coin in COINS:
   rows={tf:[] for tf in SECONDS}
   for (raw,) in db.execute("SELECT payload FROM candles WHERE json_extract(payload,'$.symbol')=?",(coin,)):
    c=Candle.model_validate_json(raw);rows[c.interval].append(c)
   for tf in SECONDS:
    rows[tf].sort(key=lambda c:c.opened)
    # The old runner cached 32 candles, while delta-RSI requires one earlier bar.
    # Retrieve exactly that 2024 bar from the previously checksum-verified January archive.
    start=FIRST-timedelta(seconds=33*SECONDS[tf]);end=start+timedelta(seconds=SECONDS[tf])
    cache=CachedDownloads('/workspace/phase6b_archive_cache',max_requests=0)
    archived=MonthlyAuditAdapter(cache).fetch(coin,tf,start.replace(hour=0,minute=0),end)
    previous=[c for c in archived if c.opened==start and c.closed==end]
    if len(previous)!=1 or rows[tf][0].opened!=end:raise ValueError('Missing extra warmup bar')
    rows[tf].insert(0,previous[0])
   cursors={tf:0 for tf in SECONDS};cache={tf:{} for tf in SECONDS}
   expected=FIRST
   for i in range(34448):
    x=json.loads(next(source));t=utc(x['at'])
    if x['coin']!=coin or t!=expected or x['manifest']!=m['old_manifest_sha256']:raise ValueError('Wrong original label sequence')
    y=x['outcome'];dec=x['decision'];is_hold=dec['action']=='HOLD';is_aligned=dec['action']=='BUY_CANDIDATE';is_ema=(coin,x['at']) in ema
    if is_ema:ema_matched+=1
    if is_aligned:aligned_matched+=1
    report_raw=db.execute("SELECT payload FROM stream_input WHERE kind='report' AND coin=? AND tf='' AND at=?",(coin,x['at'])).fetchone()
    if report_raw is None:raise ValueError('Missing original report')
    report=json.loads(report_raw[0])
    if report['coin']!=coin or utc(report['timestamp'])!=t or report['data']['parameters']!=IndicatorConfig().model_dump(mode='json'):
     raise ValueError('Original report provenance mismatch')
    windows={};recorded=report['data']['frames']
    for tf,seconds in SECONDS.items():
     end=t-timedelta(seconds=int(t.timestamp())%seconds)
     pos=cursors[tf]
     while pos<len(rows[tf]) and rows[tf][pos].closed<=end:pos+=1
     cursors[tf]=pos
     if pos<33:raise ValueError('Incomplete warmup')
     windows[tf]=rows[tf][pos-33:pos]
    rank=report['result']['components']['scanner']['ranking']
    if len(rank)>1 or rank and rank[0]['symbol']!=coin:raise ValueError('Invalid scanner provenance')
    # Each report is coin-scoped: original scores are saved separately. Join by the same t.
    scores={}
    for other in COINS:
     rr=report if other==coin else json.loads(db.execute("SELECT payload FROM stream_input WHERE kind='report' AND coin=? AND tf='' AND at=?",(other,x['at'])).fetchone()[0])
     rank=rr['result']['components']['scanner']['ranking']
     if len(rank)>1 or rank and rank[0]['symbol']!=other or utc(rr['timestamp'])!=t:raise ValueError('Scanner time mismatch')
     scores[other]=rank[0]['score'] if rank else None
    feats=extract_features(coin,t,windows,recorded,scores,score_at=t)
    regime=report['result']['components']['regime']['frames']['1h']['classification']
    pause=t>=utc('2024-01-11T16:00:00+00:00')
    for sample in ('overlapping',)+(('utc4h',) if y['nonoverlap'] else ()):
     tbl=tables[sample];label=y['label'];net=bool(y['net_positive'])
     for key in ('all',)+(('hold',) if is_hold else ())+(('pause_hold' if pause else 'nonpause_hold',) if is_hold else ()):
      tbl[key]['n']+=1;tbl[key][label]+=1;tbl[key]['net_positive']+=net
     tbl['coin'][coin]['n']+=is_hold;tbl['coin'][coin][label]+=is_hold;tbl['coin'][coin]['net_positive']+=is_hold and net
     c=tbl['regime'].setdefault(regime,Counter());c['n']+=is_hold;c[label]+=is_hold;c['net_positive']+=is_hold and net
     tbl['ema_candidates'][coin]+=is_ema;tbl['aligned_candidates'][coin]+=is_aligned
     stratum=('pooled',coin)
     for s in stratum:
      if is_hold:
       for f in feature_names():
        v=feats[f];add(sample,('A',s,f),0 if label=='positive' else 1 if label=='negative' else -1,v,t) if label!='neutral' else None
        add(sample,('B',s,f),0 if net else 1,v,t)
       for lab,val in (('gross_positive',label=='positive'),('net_positive',net)):
        add(sample,('C',s,lab),0 if pause else 1,int(val),t)
      for f in feature_names():
       if is_ema:add(sample,('D',s,f),0,feats[f],t)
       if is_aligned:add(sample,('D',s,f),1,feats[f],t)
    count+=1;hold+=is_hold;expected+=timedelta(minutes=15)
    if count%5000==0:
     if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>805306368:raise MemoryError('RSS early limit')
     print('processed',count,flush=True)
   if expected!=LAST+timedelta(minutes=15):raise ValueError('Incomplete coin')
  if next(source,None) is not None:raise ValueError('Extra labels')
 db.close()
 if count!=103344 or hold!=101391:raise ValueError('Changed label counts')
 # End-to-end contrast inventory. No inferential values are calculated.
 result={}
 for sample in data:
  output={}
  for key in names:
   pair=[]
   for j in range(2):
    z=info[sample][key][j];pair.append(summaries(data[sample][key][j],z['selected'],z['missing'],len(z['blocks']),z['times'].bit_count()))
   a,b=pair;theta=a['mean']-b['mean'] if a['mean'] is not None and b['mean'] is not None else None
   status='empty_group' if theta is None else 'descriptive' if a['status']==b['status']=='ok' else 'insufficient_support'
   output[':'.join(key)]=dict(left=a,right=b,difference_mean=theta,status=status,
    p=None,p_holm=None,confidence_interval=None,significant=None)
  result[sample]=dict(contrasts=output,tables={k:dict(v) if isinstance(v,Counter) else {a:dict(b) if isinstance(b,Counter) else b for a,b in v.items()} for k,v in tables[sample].items()})
 if sha(DB)!=m['database_sha256']:raise ValueError('Database mutated')
 for p,h in m['source_sha256'].items():
  if sha(p)!=h:raise ValueError('Source mutated: '+p)
 save(ROOT/'result.json',dict(status='complete_descriptive_only',manifest=reg['sha256'],labels=count,hold=hold,
   ema_candidate_memberships=ema_matched,aligned_candidate_memberships=aligned_matched,
   contrasts_per_sample=len(names),samples=result,missing_feature_rule='>1pct per group insufficient_support',
   prior_viewed=True,all_p_values_null=True,new_orders=0,validation_accessed=False,independent_test_opened=False))
 print('complete',count,flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('register','run'));mode=parser.parse_args().mode
 resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
 def timeout(*_):raise TimeoutError('Bounded 2024 descriptive study')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(600 if mode=='run' else 300);start=time.perf_counter()
 try:
  approval_manifest() if mode=='register' else run()
  if mode=='run':save(ROOT/'performance.json',dict(elapsed=time.perf_counter()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 except BaseException as e:
  if mode=='run' and not (ROOT/'interruption_v3.json').exists():save(ROOT/'interruption_v3.json',dict(status='incomplete',reason=repr(e),elapsed=time.perf_counter()-start))
  raise
