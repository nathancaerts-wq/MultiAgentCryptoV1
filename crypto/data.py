"""UTC OHLCV-imports. Geen order- of accountendpoints."""
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from pydantic import AwareDatetime, Field, model_validator
from .models import Model

SECONDS = {'15m': 900, '1h': 3600, '4h': 14400}
WATCHLIST = ('BTCEUR', 'ETHEUR', 'SOLEUR', 'XRPEUR', 'ADAEUR', 'LINKEUR')


def utc(value):
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError('Expliciete UTC vereist')
    return value


class Candle(Model):
    symbol: str = Field(pattern=r'^[A-Z0-9]+EUR$')
    interval: Literal['15m', '1h', '4h']
    opened: AwareDatetime
    closed: AwareDatetime  # exclusief einde
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0)
    quote_volume: Decimal = Field(ge=0)
    source: str = Field(min_length=1)

    @model_validator(mode='after')
    def valid(self):
        utc(self.opened); utc(self.closed)
        seconds = SECONDS[self.interval]
        if self.opened.microsecond or int(self.opened.timestamp()) % seconds or self.closed-self.opened != timedelta(seconds=seconds):
            raise ValueError('Ongeldige candlegrenzen')
        if not self.low <= min(self.open,self.close) <= max(self.open,self.close) <= self.high:
            raise ValueError('Ongeldige OHLC')
        return self


def validate_series(rows, symbol, interval, start, end, as_of):
    for t in (start,end,as_of): utc(t)
    seconds = SECONDS[interval]
    if start >= end or start.microsecond or end.microsecond or int(start.timestamp()) % seconds or int(end.timestamp()) % seconds:
        raise ValueError('Ongeldig interval')
    expected = int((end-start).total_seconds())//seconds
    if len(rows) != expected:
        raise ValueError('Ontbrekende candles of duplicaten')
    for i,c in enumerate(rows):
        if c.symbol != symbol or c.interval != interval or c.opened != start+timedelta(seconds=i*seconds):
            raise ValueError('Verkeerd instrument, volgorde, duplicaat of datagat')
        if c.closed > as_of:
            raise ValueError('Onvolledige of toekomstige candle')
    return rows


class DataAdapter(Protocol):
    def fetch(self, symbol, interval, start, end) -> list[Candle]: ...


class LocalAdapter:
    def __init__(self, path): self.path = Path(path)

    def fetch(self, symbol, interval, start, end):
        rows = [Candle.model_validate(r) for r in json.loads(self.path.read_text())]
        return [r for r in rows if r.symbol == symbol and r.interval == interval and start <= r.opened < end]


class PublicDataAdapter:
    """Alleen gebruiken wanneer data-api.binance.vision expliciet is toegestaan.

    Eén begrensd verzoek (maximaal 1000 candles); grotere imports moeten expliciet
    in aaneengesloten batches worden gepland. Geen automatische hostfallback.
    """
    BASE = 'https://data-api.binance.vision'

    def fetch(self, symbol, interval, start, end):
        utc(start); utc(end)
        count = int((end-start).total_seconds())//SECONDS[interval]
        if not 1 <= count <= 1000:
            raise ValueError('Batch moet 1..1000 candles bevatten')
        query = urlencode(dict(symbol=symbol, interval=interval, startTime=int(start.timestamp()*1000), endTime=int(end.timestamp()*1000)-1, limit=count))
        url = self.BASE+'/api/v3/klines?'+query
        for attempt in range(3):
            try:
                with urlopen(url, timeout=15) as response:
                    data = json.loads(response.read(2_000_001))
                break
            except HTTPError as exc:
                if exc.code not in (429,500,502,503,504) or attempt == 2: raise
                time.sleep(2**attempt)
            except URLError:
                if attempt == 2: raise
                time.sleep(2**attempt)
        result=[]
        for row in data:
            if len(row) != 12 or row[6] != row[0]+SECONDS[interval]*1000-1:
                raise ValueError('Ongeldig Binance-record')
            result.append(Candle(symbol=symbol,interval=interval,opened=datetime.fromtimestamp(row[0]/1000,timezone.utc),closed=datetime.fromtimestamp((row[6]+1)/1000,timezone.utc),open=row[1],high=row[2],low=row[3],close=row[4],volume=row[5],quote_volume=row[7],source=url))
        return result


class DataEngine:
    def __init__(self, store, adapter): self.store,self.adapter=store,adapter

    def record_scan(self, message):
        key=str(message.event_id)
        if not self.store.db.execute('SELECT 1 FROM scan_runs WHERE id=?',(key,)).fetchone():
            with self.store.transaction():
                self.store.put('scan_runs',key,message.model_dump(mode='json'))
                self.store.audit('scan_recorded',key)

    def load(self, symbol, interval, start, end, as_of):
        # Exacte aanvraag bepaalt cache; bronadapter maakt deel uit van identiteit.
        key=hashlib.sha256(f'{type(self.adapter).__name__}:{getattr(self.adapter,"path",getattr(self.adapter,"BASE",""))}:{symbol}:{interval}:{start}:{end}'.encode()).hexdigest()
        cached = next((x for x in self.store.list('datasets') if x['id']==key),None)
        try:
            rows = [Candle.model_validate(r) for r in cached['rows']] if cached else self.adapter.fetch(symbol,interval,start,end)
            validate_series(rows,symbol,interval,start,end,as_of)
            if not cached:
                payload=[r.model_dump(mode='json') for r in rows]
                digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
                with self.store.transaction():
                    self.store.put('datasets',key,{'rows':payload,'sha256':digest,'imported_at':datetime.now(timezone.utc).isoformat()})
                    for r in rows:
                        cid=hashlib.sha256(json.dumps(r.model_dump(mode='json'),sort_keys=True).encode()).hexdigest()
                        if not self.store.db.execute('SELECT 1 FROM candles WHERE id=?',(cid,)).fetchone():
                            self.store.put('candles',cid,r.model_dump(mode='json'))
                    self.store.audit('data_import',key)
            return rows
        except Exception as exc:
            from uuid import uuid4
            self.store.put('data_rejections',uuid4(),{'symbol':symbol,'interval':interval,'at':datetime.now(timezone.utc).isoformat(),'reason':str(exc),'adapter':type(self.adapter).__name__})
            raise


def aggregate_4h(rows, symbol, start, end, as_of):
    validate_series(rows,symbol,'1h',start,end,as_of)
    if int(start.timestamp()) % 14400 or int(end.timestamp()) % 14400: raise ValueError('Volledige 4h-blokken vereist')
    result=[]
    for i in range(0,len(rows),4):
        block=rows[i:i+4]
        result.append(Candle(symbol=symbol,interval='4h',opened=block[0].opened,closed=block[-1].closed,open=block[0].open,high=max(c.high for c in block),low=min(c.low for c in block),close=block[-1].close,volume=sum(c.volume for c in block),quote_volume=sum(c.quote_volume for c in block),source='aggregate:'+','.join(sorted({c.source for c in block}))))
    return result
