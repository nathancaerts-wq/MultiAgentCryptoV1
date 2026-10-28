"""Read-only independent reconciliation of approved descriptive artifacts."""
import json,math,resource,signal,time
from pathlib import Path
from collections import Counter
from scripts.phase6e_descriptive import ROOT,DB,check,save
from scripts.phase6c_diagnostics import sha
from scripts.phase6e_technical import contrast_family

def verify():
 resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
 def timeout(*_):raise TimeoutError('300 second verification limit')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(300);began=time.perf_counter()
 reg,m=check();r=json.loads((ROOT/'result.json').read_text())
 if r['manifest']!=reg['sha256'] or r['labels']!=103344 or r['hold']!=101391 or r['new_orders']!=0:raise ValueError('Scope mismatch')
 old=json.loads(Path('experiments/phase6d/result.json').read_text())
 checked=0
 for sample in ('utc4h','overlapping'):
  study=r['samples'][sample];table=study['tables']
  for tag in ('all','HOLD'):
   new=table['hold' if tag=='HOLD' else 'all'];original=old['statistics'][sample+':'+tag]
   if new['n']!=original['n'] or new['net_positive']!=original['net_positive'] or any(new.get(x,0)!=original['gross'].get(x,0) for x in ('positive','negative','neutral')):
    raise ValueError('Original label totals changed')
  if sum(x['n'] for x in table['coin'].values())!=table['hold']['n']:raise ValueError('Coin partition mismatch')
  if sum(x['n'] for x in table['regime'].values())!=table['hold']['n']:raise ValueError('Regime partition mismatch')
  if table['pause_hold']['n']+table['nonpause_hold']['n']!=table['hold']['n']:raise ValueError('Pause partition mismatch')
  if len(study['contrasts'])!=332:raise ValueError('Missing contrasts')
  if set(study['contrasts'])!={':'.join(k) for k in contrast_family()}:raise ValueError('Family changed')
  for k,row in study['contrasts'].items():
   checked+=1
   if any(row[x] is not None for x in ('p','p_holm','confidence_interval','significant')):raise ValueError('Inference entered')
   left,right=row['left'],row['right']
   for side in (left,right):
    if side['n']+side['missing']!=side['selected']:raise ValueError('Missingness count')
    if side['n'] and not(side['min']<=side['p10']<=side['median']<=side['p90']<=side['max']):raise ValueError('Quantile ordering')
   expected=None if left['mean'] is None or right['mean'] is None else left['mean']-right['mean']
   if expected!=row['difference_mean']:raise ValueError('Contrast difference')
   expected_status='empty_group' if expected is None else 'descriptive' if left['status']==right['status']=='ok' else 'insufficient_support'
   if row['status']!=expected_status:raise ValueError('Support status')
 if checked!=664 or sha(DB)!=m['database_sha256']:raise ValueError('Audit DB or comparison count')
 if (ROOT/'contrast_summary.csv').read_text().count('\n')!=665:raise ValueError('CSV inventory incomplete')
 out=dict(status='verified_descriptive_only',manifest=reg['sha256'],comparisons=checked,
  original_label_totals_equal=True,all_inference_fields_null=True,
  original_database_sha256=m['database_sha256'],new_orders=0,validation_accessed=False,independent_test_opened=False,
  elapsed=time.perf_counter()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 save(ROOT/'verification.json',out);print(out)
if __name__=='__main__':verify()
