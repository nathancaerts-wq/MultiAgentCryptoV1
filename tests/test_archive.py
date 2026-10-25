import csv
import hashlib
import io
import zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

import pytest
from crypto.archive import ArchiveDataAdapter, decode_archive, verify_4h
from crypto.data import DataEngine
from crypto.storage import SQLiteStore

ROOT=Path(__file__).parent/'fixtures/archive'
DAY=datetime(2025,1,10,tzinfo=timezone.utc)
END=DAY+timedelta(days=1)


def fixture_download(url):
    return (ROOT/url.rsplit('/',1)[-1]).read_bytes()


def package(rows, symbol='BTCEUR', interval='1h', day=DAY):
    name=f'{symbol}-{interval}-{day.date()}.zip'
    buf=io.BytesIO()
    text=io.StringIO(); csv.writer(text,lineterminator='\n').writerows(rows)
    with zipfile.ZipFile(buf,'w') as z: z.writestr(name[:-4]+'.csv',text.getvalue())
    blob=buf.getvalue()
    return blob, f'{hashlib.sha256(blob).hexdigest()}  {name}\n'.encode()


def original_rows():
    with zipfile.ZipFile(ROOT/'BTCEUR-1h-2025-01-10.zip') as z:
        return list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())))


@pytest.mark.parametrize('symbol',['BTCEUR','ETHEUR'])
@pytest.mark.parametrize('interval,expected',[('15m',96),('1h',24),('4h',6)])
def test_real_fixtures(symbol,interval,expected):
    adapter=ArchiveDataAdapter(downloader=fixture_download)
    rows=adapter.fetch(symbol,interval,DAY,END)
    assert len(rows)==expected
    assert adapter.last_manifest[0]['timestamp_unit']=='us'
    assert adapter.last_manifest[0]['validation_status']=='checksum_and_full_day_validated'
    assert rows[0].opened==DAY and rows[-1].closed==END


def test_ms_boundary_exact():
    day=datetime(2024,12,31,tzinfo=timezone.utc)
    adapter=ArchiveDataAdapter(downloader=fixture_download)
    rows=adapter.fetch('BTCEUR','1h',day,day+timedelta(days=1))
    assert adapter.last_manifest[0]['timestamp_unit']=='ms'
    assert rows[-1].closed==datetime(2025,1,1,tzinfo=timezone.utc)


@pytest.mark.parametrize('mutation',[
    lambda r:r[:-1], lambda r:r+[r[-1]], lambda r:r[::-1],
    lambda r:[r[0]]+r[:-1],
    lambda r:[r[0][:6]+[str(int(r[0][6])-1)]+r[0][7:]]+r[1:],
    lambda r:[r[0][:1]+['-1']+r[0][2:]]+r[1:],
    lambda r:[r[0][:5]+['NaN']+r[0][6:]]+r[1:],
    lambda r:[[str(int(x)//1000) if i in (0,6) else x for i,x in enumerate(row)] for row in r],
    lambda r:[r[0][:9]+['-1']+r[0][10:]]+r[1:],
])
def test_corrupt_records(mutation):
    blob,checksum=package(mutation(original_rows()))
    with pytest.raises((ValueError,OverflowError)):
        decode_archive(blob,checksum,'BTCEUR','1h',DAY,'fixture',END)


def test_checksum_before_zip():
    with pytest.raises(ValueError,match='checksum mismatch'):
        decode_archive(b'not a zip',b'0'*64+b'  BTCEUR-1h-2025-01-10.zip','BTCEUR','1h',DAY,'fixture',END)


def test_corrupt_zip_valid_checksum():
    blob=b'broken zip'
    cs=hashlib.sha256(blob).hexdigest().encode()+b'  BTCEUR-1h-2025-01-10.zip'
    with pytest.raises(zipfile.BadZipFile): decode_archive(blob,cs,'BTCEUR','1h',DAY,'fixture',END)


def test_checksum_filename():
    blob,cs=package(original_rows())
    with pytest.raises(ValueError,match='checksumrecord'):
        decode_archive(blob,cs.replace(b'BTCEUR',b'ETHEUR'),'BTCEUR','1h',DAY,'fixture',END)


def test_unclosed_archive():
    blob,cs=package(original_rows())
    with pytest.raises(ValueError,match='Onvolledige'):
        decode_archive(blob,cs,'BTCEUR','1h',DAY,'fixture',END-timedelta(seconds=1))


def test_limit_and_invalid_request():
    adapter=ArchiveDataAdapter(downloader=lambda url:pytest.fail('Geen netwerk verwacht'))
    for symbol,interval,start,end in [('BTCUSDT','1h',DAY,END),('BTCEUR','5m',DAY,END),('BTCEUR','1h',DAY,END+timedelta(days=7)),('BTCEUR','1h',END,DAY),('BTCEUR','1h',DAY.replace(tzinfo=None),END)]:
        with pytest.raises(ValueError): adapter.fetch(symbol,interval,start,end)


def test_engine_persistence_and_overlap(tmp_path):
    calls=[]
    def transport(url): calls.append(url); return fixture_download(url)
    path=tmp_path/'test.sqlite3'
    s=SQLiteStore(path); e=DataEngine(s,ArchiveDataAdapter(downloader=transport))
    e.load('BTCEUR','1h',DAY,END,END)
    e.load('BTCEUR','1h',DAY+timedelta(hours=1),END,END)
    assert len(calls)==2 and len(s.list('candles'))==24
    assert s.list('datasets')[0]['archive_manifest'][0]['sha256']
    s.close()
    s=SQLiteStore(path)
    e=DataEngine(s,ArchiveDataAdapter(downloader=lambda url:pytest.fail('Persistente cache verwacht')))
    assert len(e.load('BTCEUR','1h',DAY,END,END))==24
    assert len(s.list('datasets'))==2
    s.close()


@pytest.mark.parametrize('symbol',['BTCEUR','ETHEUR'])
def test_verify_4h(symbol):
    s=SQLiteStore()
    e=DataEngine(s,ArchiveDataAdapter(downloader=fixture_download))
    assert verify_4h(e,symbol,DAY,END,END)['candles']==6
    assert 'valid=True' in s.audits()[-1]['details']
    assert not s.list('orders')
    s.close()


def test_4h_mismatch():
    s=SQLiteStore()
    class Engine:
        store=s
        def load(self,symbol,interval,start,end,as_of):
            rows=ArchiveDataAdapter(downloader=fixture_download).fetch(symbol,interval,start,end)
            if interval=='4h': rows[0]=rows[0].model_copy(update={'volume':rows[0].volume+1})
            return rows
    with pytest.raises(ValueError,match='wijken af'): verify_4h(Engine(),'BTCEUR',DAY,END,END)
    assert 'valid=False' in s.audits()[-1]['details']
    s.close()


def test_mixed_time_units():
    rows=original_rows()
    for i in (0,6): rows[1][i]=str(int(rows[1][i])//1000)
    blob,cs=package(rows)
    with pytest.raises(ValueError): decode_archive(blob,cs,'BTCEUR','1h',DAY,'fixture',END)


def test_unexpected_zip_member():
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z: z.writestr('../escape.csv','bad')
    blob=buf.getvalue()
    cs=hashlib.sha256(blob).hexdigest().encode()+b'  BTCEUR-1h-2025-01-10.zip'
    with pytest.raises(ValueError,match='ZIP-inhoud'):
        decode_archive(blob,cs,'BTCEUR','1h',DAY,'fixture',END)


def test_engine_no_partial_import_on_corruption():
    s=SQLiteStore()
    def corrupt(url): return b'0'*64+b'  BTCEUR-1h-2025-01-10.zip' if url.endswith('CHECKSUM') else b'broken'
    e=DataEngine(s,ArchiveDataAdapter(downloader=corrupt))
    with pytest.raises(ValueError): e.load('BTCEUR','1h',DAY,END,END)
    assert not s.list('datasets') and not s.list('candles')
    assert len(s.list('data_rejections'))==1
    s.close()


def test_partial_day_cannot_hide_missing_records():
    blob,cs=package(original_rows()[:-1])
    def transport(url): return cs if url.endswith('CHECKSUM') else blob
    with pytest.raises(ValueError,match='Ontbrekende'):
        ArchiveDataAdapter(downloader=transport).fetch('BTCEUR','1h',DAY,DAY+timedelta(hours=1))
