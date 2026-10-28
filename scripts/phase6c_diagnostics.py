"""Bounded saved-decision audit. Never reads future bars or runs a portfolio."""
import gzip, hashlib, json, resource, signal, sqlite3, time
from collections import Counter
from pathlib import Path
from crypto.missed_opportunity import classify_batch, trailing_losses
from crypto.readiness import dt

OUT=Path('experiments/phase6c'); DB=Path('/workspace/development_2024.sqlite3')
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 if (OUT/'diagnostics.json').exists():raise ValueError('Existing evidence preserved')
 resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
 def timeout(*args):raise TimeoutError('300-second diagnostic budget')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(300);began=time.perf_counter()
 old=json.loads(Path('experiments/development_2024/verification.json').read_text())
 artifacts={str(p):sha(p) for p in Path('experiments/development_2024').iterdir() if p.is_file()}
 assert sha(DB)==old['database_sha256']
 db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);db.execute('PRAGMA cache_size=-8192');db.execute('BEGIN')
 output=dict(scope='saved_2024_baseline_decisions_only',forward_labels_computed=False,
             forward_protocol_status='proposal_requires_approval',studies={})
 for name in ('aligned_trend_baseline','ema_trend_baseline'):
  saved=json.loads(Path(f'experiments/development_2024/{name}.json').read_text());key=saved['portfolio']['portfolio']
  settlements={row[0]:json.loads(row[1]) for row in db.execute("SELECT id,payload FROM joint_settlements WHERE json_extract(payload,'$.portfolio')=?",(key,))}
  counts=Counter();reasons=Counter();higher=0;rows=0;buy=0;timeline=[];last_at=None
  dest=OUT/(name+'_classifications.jsonl.gz')
  with gzip.open(dest,'wt') as stream:
   for batch_id,raw in db.execute("SELECT id,payload FROM joint_batches WHERE json_extract(payload,'$.portfolio')=? ORDER BY json_extract(payload,'$.at')",(key,)):
    b=json.loads(raw);b['id']=batch_id;at=dt(b['at'])
    if last_at is not None:assert (at-last_at).total_seconds()==900
    last_at=at
    for r in classify_batch(b,settlements.get(batch_id)):
     stream.write(json.dumps(r,sort_keys=True)+'\n');rows+=1;counts[r['category']]+=1
     buy+=r['action']=='BUY_CANDIDATE';higher+=bool(r['higher_known_score_coins']);reasons[r['reason']]+=1
  trades=[json.loads(r[0]) for r in db.execute("SELECT payload FROM stream_history WHERE portfolio=? AND kind='trades' ORDER BY seq",(key,))]
  assert trades==saved['trade_records']
  for i,t in enumerate(trades):timeline.append(dict(at=t['exited_at'],coin=t['symbol'],net=t['net'],cash_after=str(200+sum(__import__('decimal').Decimal(x['net']) for x in trades[:i+1])),trailing_losses=trailing_losses(trades[:i+1])))
  months={};state_count=0;final=None
  for (raw,) in db.execute('SELECT payload FROM stream_states WHERE portfolio=? ORDER BY revision',(key,)):
   s=json.loads(raw);state_count+=1;final=s
   # The prefix counts, not future trade suffix, reconstruct the risk at this checkpoint.
   n=s['ledger']['trades']['count'];streak=trailing_losses(trades[:n])
   if s['at'][8:10]=='01' and s['at'][11:19]=='00:00:00':
    months[s['at']]=dict(cash=s['ledger']['cash'],position=s['ledger']['position'],pending=s['pending'],
     losses=streak,loss_pause=streak>=3,day_paused=s['ledger']['day_paused'],drawdown_paused=s['ledger']['drawdown_paused'],emergency=s['stopped'])
   if name=='aligned_trend_baseline' and n>=3:
    assert streak==3 and not s['ledger']['position'] and not s['pending']
  assert buy==saved['candidate_signals'] and rows==34465*3
  assert counts['executed_entry']==saved['trades'] and counts['approved_execution_rejected']==sum(saved['rejected_executions'].values())
  output['studies'][name]=dict(rows=rows,categories=dict(counts),reasons=dict(reasons),buy_candidates=buy,
   higher_known_score_rows=higher,higher_score_is_not_future_profit=True,trades=timeline,monthly_risk=months,
   state_count=state_count,final_hash=final['hash'],classifications_sha256=sha(dest))
 db.close()
 assert sha(DB)==old['database_sha256']
 assert artifacts=={str(p):sha(p) for p in Path('experiments/development_2024').iterdir() if p.is_file()}
 output.update(database_sha256=old['database_sha256'],existing_artifacts_unchanged=True,
               elapsed=time.perf_counter()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               limits=dict(seconds=300,address_space_bytes=1024**3),validation_accessed=False,independent_test_opened=False)
 (OUT/'diagnostics.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
 signal.alarm(0)
if __name__=='__main__':main()
