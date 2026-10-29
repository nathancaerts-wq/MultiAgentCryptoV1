import hashlib,json,resource,signal,subprocess,time,sys
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timedelta
resource.setrlimit(resource.RLIMIT_AS,(1610612736,)*2);signal.alarm(180);start=time.monotonic()
from scripts.phase6h_b_replay import checked_manifest,make_plan,sha,OUT,DB,ORIGINAL
from crypto.historical_recovery import RecoveryStore,HistoricalRecoveryRunner
from crypto.development_2024 import policy,filters,END
from crypto.sim_execution import digest
m=checked_manifest();assert (OUT/'result.json').exists()
x=json.loads((OUT/'result.json').read_text());assert x['status']=='complete'
s=RecoveryStore(DB);r=HistoricalRecoveryRunner(store=s,plan=make_plan(m),policy=policy('baseline'),filters=filters())
st,l=r._read();r.verify_history();l.reconcile();trades=list(l.trades)
assert len(trades)==x['trades'] and l.position is None and st['pending'] is None
assert st['at']==END.isoformat() and D(x['equity'])==l.cash==D(200)+l.realized
assert sum((D(t['net']) for t in trades),D(0))==l.realized
assert sum((D(t['fees']) for t in trades),D(0))==l.fees==D(x['fees'])
assert len({t['entry_id'] for t in trades})==len(trades)==len({t['exit_id'] for t in trades})
previous=None;revisions=0;expiry=0
for (raw,) in s.db.execute('SELECT payload FROM stream_states WHERE portfolio=? ORDER BY revision',(r.key,)):
 c=json.loads(raw);v=c['recovery'];n=v['processed'];prefix=trades[:n]
 assert v['prefix']==digest(prefix) and len(prefix)==n
 streak=0
 for trade in prefix[v['epoch_anchor']:]:streak=streak+1 if D(trade['net'])<0 else 0
 assert streak==v['loss_count']
 if v['pause_until']:
  assert streak==3 and datetime.fromisoformat(v['pause_until'])==datetime.fromisoformat(prefix[-1]['exited_at'])+timedelta(hours=24)
 if c['kind']=='cooldown_expired':
  assert previous and previous['recovery']['pause_until']
  assert datetime.fromisoformat(c['at'])>=datetime.fromisoformat(previous['recovery']['pause_until'])
  assert v['epoch']==previous['recovery']['epoch']+1 and v['loss_count']==0 and v['epoch_anchor']==n
  for field in ('cash','fees','realized','peak','day_start','day_paused','drawdown_paused','position','events','trades','ids'):
   if field=='events':continue # expiry adds exactly one audit event
   assert c['ledger'][field]==previous['ledger'][field],field
  assert c['stopped']==previous['stopped'] and c['pending'] is None
  expiry+=1
 previous=c;revisions+=1
assert expiry==x['cooldown_expiries']
# Validate no original code/result/audit artifact changed since the original preflight.
blocked=json.loads(Path(json.loads((OUT/'registration.json').read_text())['manifest']).read_text())
assert all(sha(p)==h for p,h in blocked['tracked_source_sha256'].items())
assert sha(ORIGINAL)==m['original_database_sha256'];assert Path(str(ORIGINAL)+'-wal').stat().st_size==0
s.close()
out=dict(verified=True,scope='single_recovery24h_baseline_costs_2024_only',revisions=revisions,unique_trades=len(trades),expiry_transitions_verified=expiry,ledger_reconciles=True,full_audit_and_checkpoint_chains_verified=True,original_files_unchanged=len(blocked['tracked_source_sha256']),original_database_sha256=m['original_database_sha256'],validation_accessed=False,independent_test_opened=False,baseline_replayed=False,elapsed_seconds=time.monotonic()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(OUT/'verification_approved.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
