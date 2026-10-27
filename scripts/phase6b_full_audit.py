"""Volledige toegestane data-audit; geen indicators of rendementen."""
import hashlib
import json
import io,zipfile,csv,calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from crypto.archive import decode_archive
from pathlib import Path
from urllib.parse import urlsplit
from crypto.archive import ArchiveDataAdapter, download
from crypto.data import WATCHLIST
from crypto.readiness import quality_report, dt, permitted

class CachedDownloads:
 def __init__(self,path,max_requests=26000,max_bytes=1_000_000_000):
  self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
  self.requests=0;self.bytes=0;self.failures=0;self.max_requests=max_requests;self.max_bytes=max_bytes
 def __call__(self,url):
  if urlsplit(url).hostname!='data.binance.vision': raise ValueError('Alleen officiële archiefhost')
  token=url.split('/')[-1].split('.zip')[0]
  monthly='/monthly/' in url
  day=dt(token[-7:]+'-01') if monthly else dt(token[-10:])
  from datetime import timedelta
  # Exacte laatste validatiedag mag tot, nooit over, de testgrens lezen.
  if monthly:
   stop=(day.replace(day=28)+timedelta(days=4)).replace(day=1)
   if day!=dt('2025-12-01'): permitted(day,stop)
  elif day!=dt('2025-12-31'): permitted(day,day+timedelta(days=1))
  key=self.path/hashlib.sha256(url.encode()).hexdigest()
  if key.exists(): return key.read_bytes()
  if self.failures>=3: raise RuntimeError('Netwerkcircuit open na drie fouten; niet onderzocht')
  if self.requests>=self.max_requests or self.bytes+2_000_001>self.max_bytes: raise RuntimeError('Downloadbudget bereikt; niet onderzocht')
  self.requests+=1
  try: data=download(url)
  except Exception:
   self.failures+=1;raise
  self.bytes+=len(data)
  tmp=key.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(key)
  return data

class MonthlyAuditAdapter:
 def __init__(self,cache): self.cache=cache;self.month=None;self.rows={};self.last_manifest=[]
 def fetch(self,symbol,tf,start,end):
  # Warm-up January 2025 blijft dagelijks: de gesloten dag wordt nooit gelezen.
  if start.year==2025 and start.month==1:
   a=ArchiveDataAdapter(downloader=self.cache);rows=a.fetch(symbol,tf,start,end);self.last_manifest=a.last_manifest;return rows
  key=(symbol,tf,start.year,start.month)
  if key!=self.month:
   filename=f'{symbol}-{tf}-{start:%Y-%m}.zip'
   url=f'https://data.binance.vision/data/spot/monthly/klines/{symbol}/{tf}/{filename}'
   record=self.cache(url+'.CHECKSUM').decode().split();blob=self.cache(url)
   if len(record)!=2 or record[1].lstrip('*')!=filename or hashlib.sha256(blob).hexdigest()!=record[0].lower(): raise ValueError('Officiële maandchecksum mismatch')
   with zipfile.ZipFile(io.BytesIO(blob)) as z:
    info=z.infolist()
    if len(info)!=1 or info[0].filename!=filename[:-4]+'.csv' or info[0].file_size>20_000_000: raise ValueError('ZIP-inhoud')
    records=list(csv.reader(io.StringIO(z.read(info[0]).decode())))
   count=86400//{'15m':900,'1h':3600,'4h':14400}[tf]
   days=calendar.monthrange(start.year,start.month)[1]
   if len(records)!=count*days: raise ValueError('Onvolledige maand')
   self.rows={}
   for i in range(days):
    day=start.replace(day=1)+timedelta(days=i);name=f'{symbol}-{tf}-{day:%Y-%m-%d}.zip'
    content=io.StringIO();csv.writer(content).writerows(records[i*count:(i+1)*count])
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(name[:-4]+'.csv',content.getvalue())
    derived=out.getvalue();check=(hashlib.sha256(derived).hexdigest()+'  '+name).encode()
    rows,meta=decode_archive(derived,check,symbol,tf,day,url,dt('2026-01-01'))
    self.rows[day]=rows
   self.meta=dict(source=url,sha256=record[0].lower(),validation_status='official_month_checksum_verified_daily_slices_validated',derived_daily_checksums='internal_only')
   self.month=key
  self.last_manifest=[self.meta]
  return [c for c in self.rows[start.replace(hour=0)] if c.closed<=end]

def main():
 cache=CachedDownloads('/workspace/phase6b_archive_cache')
 out=Path('experiments/phase6b_full_quality');out.mkdir(exist_ok=True)
 summary=[]
 def work(symbol):
  for period in ('development','validation','validation_warmup'):
   adapters={tf:MonthlyAuditAdapter(cache) for tf in ('15m','1h','4h')}
   class Routed:
    last_manifest=[]
    def fetch(self,s,tf,a,b):
     rows=adapters[tf].fetch(s,tf,a,b);self.last_manifest=adapters[tf].last_manifest;return rows
   adapter=Routed()
   result=quality_report(adapter,symbol,period)
   file=out/f'{symbol}_{period}.json';file.write_text(json.dumps(result,indent=2)+'\n')
   summary.append(dict(symbol=symbol,period=period,status=result['status'],valid_days=sum(r['status']=='valid' for r in result['days']),total_days=len(result['days'])))
   print(symbol,period,summary[-1]['valid_days'],flush=True)
 with ThreadPoolExecutor(max_workers=3) as pool:
  list(pool.map(work,WATCHLIST))
 summary.sort(key=lambda r:(r['symbol'],r['period']))
 (out/'summary.json').write_text(json.dumps(dict(reports=summary,requests=cache.requests,bytes=cache.bytes,network_failures=cache.failures,performance_computed=False),indent=2)+'\n')
if __name__=='__main__': main()
