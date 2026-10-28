"""Bounded January 2024 quality gate, no returns or signal computation."""
import json,hashlib
from pathlib import Path
from datetime import timedelta
from scripts.phase6b_full_audit import CachedDownloads,MonthlyAuditAdapter
from crypto.readiness import dt,validate_frames
COINS=('BTCEUR','ETHEUR','SOLEUR')
START=dt('2024-01-01');ENTRY=dt('2024-01-08');END=dt('2024-02-01')

def audit():
 cache=CachedDownloads('/workspace/phase6b_archive_cache',max_requests=18,max_bytes=40_000_000)
 def bounded(url):
  if not url.endswith(('2024-01.zip','2024-01.zip.CHECKSUM')):raise ValueError('Outside January')
  return cache(url)
 result={'status':'valid','coins':{},'datasets':[],'performance_computed':False}
 for s in COINS:
  prior=json.loads(Path(f'experiments/phase6b_full_quality/{s}_development.json').read_text())
  old=[d for d in prior['days'] if d['start'].startswith('2024-01-')]
  if len(old)!=31 or any(d['status']!='valid' for d in old):raise ValueError('Earlier quality not complete')
  frames={};meta=[]
  for tf in ('15m','1h','4h'):
   a=MonthlyAuditAdapter(bounded);rows=[]
   for i in range(31):rows.extend(a.fetch(s,tf,START+timedelta(days=i),START+timedelta(days=i+1)))
   frames[tf]=rows;meta.extend(a.last_manifest)
  validate_frames(frames,s,START,END,END)
  result['coins'][s]={'counts':{tf:len(rows) for tf,rows in frames.items()},'status':'valid','prior_valid_days':len(old)}
  result['datasets'].extend(meta)
 result['requests']=cache.requests;result['download_bytes']=cache.bytes
 return result
if __name__=='__main__':
 p=Path('experiments/january_pilot/quality.json')
 if p.exists():raise ValueError('Existing audit preserved')
 try:r=audit()
 except Exception as exc:r={'status':'incomplete','reason':str(exc),'performance_computed':False}
 p.write_text(json.dumps(r,indent=2)+'\n');print(r)
