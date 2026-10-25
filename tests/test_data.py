import asyncio
from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from crypto.data import Candle, DataEngine, LocalAdapter, aggregate_4h, validate_series
from crypto.scanner import CoinScanner
from crypto.storage import SQLiteStore
from crypto.orchestrator import Orchestrator,Task
from crypto.api import create_app

START=datetime(2026,1,1,tzinfo=timezone.utc)
END=START+timedelta(days=1)
FIXTURE=Path(__file__).parent/'fixtures/ohlcv.json'

@pytest.fixture
def env():
    store=SQLiteStore()
    engine=DataEngine(store,LocalAdapter(FIXTURE))
    yield store,engine
    store.close()

def rows(): return LocalAdapter(FIXTURE).fetch('BTCEUR','1h',START,END)

@pytest.mark.parametrize('patch',[{'high':1},{'volume':-1},{'close':'NaN'},{'opened':START.replace(tzinfo=None)},{'closed':START},{'opened':START+timedelta(minutes=1)},{'interval':'5m'},{'source':''},{'symbol':'BTCUSDT'},{'opened':START.astimezone(timezone(timedelta(hours=1)))}])
def test_schema(patch):
    with pytest.raises(ValueError): Candle.model_validate(rows()[0].model_dump()|patch)

@pytest.mark.parametrize('bad',[lambda r:r[:-1],lambda r:list(reversed(r)),lambda r:[r[0]]+r[:-1],lambda r:r[:5]+r[6:]])
def test_gaps_order_duplicates(bad):
    with pytest.raises(ValueError): validate_series(bad(rows()),'BTCEUR','1h',START,END,END)

def test_incomplete():
    with pytest.raises(ValueError): validate_series(rows(),'BTCEUR','1h',START,END,END-timedelta(seconds=1))

def test_import_cache(env):
    store,engine=env
    assert engine.load('BTCEUR','1h',START,END,END)==engine.load('BTCEUR','1h',START,END,END)
    assert len(store.list('candles'))==24
    assert len(store.list('datasets'))==1
    with pytest.raises(ValueError): engine.load('BTCEUR','1h',START,END,END-timedelta(hours=1))
    assert len(store.list('data_rejections'))==1

def test_aggregation():
    result=aggregate_4h(rows(),'BTCEUR',START,END,END)
    assert len(result)==6 and result[0].volume==40
    assert result[0].close==rows()[3].close
    with pytest.raises(ValueError): aggregate_4h(rows()[:-1],'BTCEUR',START,END,END)

def test_15m():
    c=rows()[0].model_dump()|dict(interval='15m',closed=START+timedelta(minutes=15))
    assert Candle.model_validate(c).interval=='15m'

def test_historical_ranking_api_dedup(env):
    store,engine=env
    scanner=CoinScanner(engine,END,watchlist=['ETH/EUR','BTC/EUR','SOL/EUR'])
    first=asyncio.run(scanner.run(()))
    second=asyncio.run(scanner.run(()))
    assert first.event_id==second.event_id
    assert len(store.list('scan_runs'))==1
    assert first.result['ranking'][0]['symbol']=='BTCEUR'
    assert first.result['rejections'][0]['symbol']=='SOLEUR'
    assert not first.usable()  # historische data worden niet opnieuw vers gemaakt
    assert not store.list('orders')
    with TestClient(create_app(store)) as client:
        assert client.get('/scanner').json()[0]['usable'] is False
        assert len(client.get('/candles').json())==48
        assert client.get('/data-quality').status_code==200

def test_orchestrator_current_workflow(env):
    from crypto.models import now
    store,engine=env
    # Verschuif uitsluitend synthetische tijden naar het laatste volledige uur.
    end=now().replace(minute=0,second=0,microsecond=0)
    class Shift:
        def fetch(self,symbol,interval,start,stop):
            shift=end-END
            return [Candle.model_validate(c.model_dump()|dict(opened=c.opened+shift,closed=c.closed+shift)) for c in rows()]
    engine.adapter=Shift()
    scanner=CoinScanner(engine,end,watchlist=['BTCEUR'])
    o=Orchestrator(store); o.register('scanner',scanner)
    assert asyncio.run(o.execute([Task('scan','scanner')]))
    assert asyncio.run(o.execute([Task('scan','scanner')]))=={}
    assert len(store.list('results'))==1
    assert not store.list('orders')

def test_stale_and_no_lookahead(env):
    _,engine=env
    m=asyncio.run(CoinScanner(engine,END+timedelta(minutes=30),watchlist=['BTCEUR'],max_age=60).run(()))
    assert m.status=='error'
    with pytest.raises(ValueError): engine.load('BTCEUR','1h',START,END,START)

def test_public_adapter_mock(monkeypatch):
    import io,json
    from crypto.data import PublicDataAdapter
    row=[int(START.timestamp()*1000),'100','102','99','101','10',int(START.timestamp()*1000)+3599999,'1000',4,'2','200','0']
    class Response(io.BytesIO): pass
    monkeypatch.setattr('crypto.data.urlopen',lambda url,timeout:Response(json.dumps([row]).encode()))
    result=PublicDataAdapter().fetch('BTCEUR','1h',START,START+timedelta(hours=1))
    validate_series(result,'BTCEUR','1h',START,START+timedelta(hours=1),END)
    assert result[0].source.startswith('https://data-api.binance.vision/')

def test_public_no_retry_restricted(monkeypatch):
    from urllib.error import HTTPError
    from crypto.data import PublicDataAdapter
    calls=[]
    def denied(url,timeout):
        calls.append(url)
        raise HTTPError(url,451,'Restricted',None,None)
    monkeypatch.setattr('crypto.data.urlopen',denied)
    with pytest.raises(HTTPError): PublicDataAdapter().fetch('BTCEUR','1h',START,START+timedelta(hours=1))
    assert len(calls)==1
