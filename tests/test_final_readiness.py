from datetime import timedelta
import pytest
from crypto.research_benchmarks import benchmark_calendar
from crypto.readiness import dt
from scripts.phase6b_full_audit import CachedDownloads

@pytest.mark.parametrize('stage,start,end,entry',[
 ('development','2024-01-01','2025-01-01','2024-01-08'),
 ('validation','2025-02-01','2025-12-31T20:00','2025-02-01')])
def test_benchmark_calendar(stage,start,end,entry):
 c=benchmark_calendar(stage)
 assert (c['start'],c['end'],c['index_entry'])==(dt(start),dt(end),dt(entry))
 assert c['latest_entry']==dt(end)-timedelta(hours=4,minutes=15)

def test_test_benchmark_locked():
 with pytest.raises(ValueError):benchmark_calendar('independent_test')

def test_disk_cache_and_budget(tmp_path,monkeypatch):
 monkeypatch.setattr('scripts.phase6b_full_audit.download',lambda url:b'fixture')
 c=CachedDownloads(tmp_path,max_requests=1)
 u='https://data.binance.vision/data/spot/daily/klines/BTCEUR/1h/BTCEUR-1h-2024-01-01.zip'
 assert c(u)==c(u)==b'fixture' and c.requests==1
 with pytest.raises(RuntimeError):c(u.replace('01-01','01-02'))
 assert CachedDownloads(tmp_path,max_requests=0)(u)==b'fixture'

def test_cache_cannot_read_holdout(tmp_path):
 c=CachedDownloads(tmp_path)
 for date in ['2025-01-15','2026-01-01']:
  with pytest.raises(ValueError):c('https://data.binance.vision/x/BTCEUR-1h-'+date+'.zip')
 assert c.requests==0

def test_circuit_breaker(tmp_path,monkeypatch):
 def fail(url):raise OSError('network blocked')
 monkeypatch.setattr('scripts.phase6b_full_audit.download',fail)
 c=CachedDownloads(tmp_path)
 for _ in range(3):
  with pytest.raises(OSError):c('https://data.binance.vision/x/BTCEUR-1h-2024-01-01.zip')
 with pytest.raises(RuntimeError):c('https://data.binance.vision/x/BTCEUR-1h-2024-01-01.zip')
 assert c.requests==3

def test_monthly_checksum_and_daily_validation():
 import csv,io,zipfile,hashlib
 from scripts.phase6b_full_audit import MonthlyAuditAdapter
 start=dt('2024-01-01');epoch=dt('1970-01-01')
 content=io.StringIO();w=csv.writer(content)
 for i in range(31*24):
  t=start+timedelta(hours=i);ms=int((t-epoch).total_seconds())*1000
  w.writerow([ms,100,100,100,100,1,ms+3600000-1,100,1,1,100,0])
 blob=io.BytesIO()
 with zipfile.ZipFile(blob,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('BTCEUR-1h-2024-01.csv',content.getvalue())
 raw=blob.getvalue()
 def cache(u):return (hashlib.sha256(raw).hexdigest()+'  BTCEUR-1h-2024-01.zip').encode() if u.endswith('CHECKSUM') else raw
 adapter=MonthlyAuditAdapter(cache)
 rows=adapter.fetch('BTCEUR','1h',start,start+timedelta(days=1))
 assert len(rows)==24 and rows[0].opened==start
 assert adapter.last_manifest[0]['sha256']==hashlib.sha256(raw).hexdigest()
 bad=MonthlyAuditAdapter(lambda u: b'0'*64+b'  BTCEUR-1h-2024-01.zip' if u.endswith('CHECKSUM') else raw)
 with pytest.raises(ValueError):bad.fetch('BTCEUR','1h',start,start+timedelta(days=1))
