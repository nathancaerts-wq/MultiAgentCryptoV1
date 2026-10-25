"""Officiële dagelijkse Binance Spot-klines; uitsluitend begrensde imports."""
import csv
import hashlib
import io
import re
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.request import urlopen

from .data import Candle, SECONDS, aggregate_4h, utc, validate_series
from .models import now

FORMAT_REFERENCE = 'https://github.com/binance/binance-public-data#spot'
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MICROSECONDS_FROM = datetime(2025, 1, 1, tzinfo=timezone.utc)
MAX_BYTES = 2_000_000


def download(url):
    # Geen alternatieve hosts, credentials of retries bij toegangsweigeringen.
    with urlopen(url, timeout=20) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Archief of checksum overschrijdt downloadlimiet')
    return data


def decode_archive(blob, checksum, symbol, interval, day, source, as_of):
    """Controleer checksum vóór ZIP/CSV-decodering; valideer de volledige UTC-dag."""
    utc(day); utc(as_of)
    if day != day.replace(hour=0, minute=0, second=0, microsecond=0):
        raise ValueError('UTC-daggrens vereist')
    if interval not in SECONDS or not re.fullmatch(r'[A-Z0-9]+EUR', symbol):
        raise ValueError('Alleen ondersteunde EUR-klines')
    filename = f'{symbol}-{interval}-{day.date()}.zip'
    parts = checksum.decode('ascii').split()
    if len(parts) != 2 or not re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]) or parts[1].lstrip('*') != filename:
        raise ValueError('Ongeldig officieel checksumrecord')
    digest = hashlib.sha256(blob).hexdigest()
    if digest != parts[0].lower():
        raise ValueError('SHA-256 checksum mismatch')
    if len(blob) > MAX_BYTES:
        raise ValueError('Te groot archief')
    # Binance documenteert ms vóór 2025-01-01 en us vanaf die datum.
    # Geen magnitude-gok: verwisselde/gemengde eenheden falen bereikvalidatie.
    factor = 1_000_000 if day >= MICROSECONDS_FROM else 1_000
    end = day + timedelta(days=1)
    rows = []
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        infos = archive.infolist()
        if len(infos) != 1 or infos[0].filename != filename.removesuffix('.zip')+'.csv' or infos[0].file_size > MAX_BYTES:
            raise ValueError('Onverwachte ZIP-inhoud')
        content = archive.read(infos[0])  # ZIP CRC wordt eveneens gecontroleerd.
        for row in csv.reader(io.StringIO(content.decode('utf-8'))):
            if len(row) != 12 or not all(re.fullmatch(r'\d+', row[i]) for i in (0, 6, 8)):
                raise ValueError('Ongeldig CSV-record')
            opened, closed = int(row[0]), int(row[6])
            if closed-opened+1 != SECONDS[interval]*factor:
                raise ValueError('Verkeerde tijdseenheid of candleduur')
            op = EPOCH + timedelta(microseconds=opened*(1_000_000//factor))
            cl = EPOCH + timedelta(microseconds=(closed+1)*(1_000_000//factor))
            volume, quote, taker, taker_quote = [Decimal(row[i]) for i in (5,7,9,10)]
            if not all(v.is_finite() for v in (volume,quote,taker,taker_quote)) or not 0 <= taker <= volume or not 0 <= taker_quote <= quote:
                raise ValueError('Ongeldige volumes')
            rows.append(Candle(symbol=symbol, interval=interval, opened=op, closed=cl,
                               open=row[1], high=row[2], low=row[3], close=row[4],
                               volume=volume, quote_volume=quote, source=source))
    validate_series(rows, symbol, interval, day, end, as_of)
    metadata = dict(source=source, checksum_source=source+'.CHECKSUM', sha256=digest,
                    start=day.isoformat(), end=end.isoformat(), timestamp_unit='us' if factor==1_000_000 else 'ms',
                    format_reference=FORMAT_REFERENCE, validation_status='checksum_and_full_day_validated')
    return rows, metadata


class ArchiveDataAdapter:
    """DataAdapter.fetch; maximaal zeven UTC-dagarchieven per expliciete aanvraag.

    Subdagbereiken zijn toegestaan; volledige archiefdagen worden altijd gevalideerd.
    last_manifest is alleen geldig na een succesvolle fetch en wordt mee opgeslagen.
    """
    BASE = 'https://data.binance.vision'

    def __init__(self, downloader=download, clock=now):
        self.downloader, self.clock = downloader, clock
        self.last_manifest = []
        self._cache = {}

    def fetch(self, symbol, interval, start, end):
        self.last_manifest = []
        utc(start); utc(end)
        if not re.fullmatch(r'[A-Z0-9]+EUR', symbol) or interval not in SECONDS:
            raise ValueError('Ongeldig EUR-paar of interval')
        day = start.replace(hour=0, minute=0, second=0, microsecond=0)
        if start >= end or end > self.clock() or start.microsecond or end.microsecond or any(int(t.timestamp()) % SECONDS[interval] for t in (start,end)):
            raise ValueError('Ongeldig of onafgesloten bereik')
        if end-day > timedelta(days=7):
            raise ValueError('Maximaal zeven dagarchieven per aanvraag')
        all_rows, manifest = [], []
        while day < end:
            filename = f'{symbol}-{interval}-{day.date()}.zip'
            url = f'{self.BASE}/data/spot/daily/klines/{symbol}/{interval}/{filename}'
            if url not in self._cache:
                checksum = self.downloader(url+'.CHECKSUM')
                blob = self.downloader(url)
                # Cache uitsluitend volledig gevalideerde archieven.
                rows, meta = decode_archive(blob,checksum,symbol,interval,day,url,self.clock())
                self._cache[url] = rows,meta
            rows, meta = self._cache[url]
            validate_series(rows,symbol,interval,day,day+timedelta(days=1),self.clock())
            all_rows.extend(c for c in rows if start <= c.opened < end)
            manifest.append(dict(meta))
            day += timedelta(days=1)
        validate_series(all_rows,symbol,interval,start,end,self.clock())
        self.last_manifest = manifest
        return all_rows


def verify_4h(engine, symbol, start, end, as_of):
    """Vergelijk alle OHLCV-velden exact; mismatch wordt gelogd en afgewezen."""
    hourly = engine.load(symbol,'1h',start,end,as_of)
    official = engine.load(symbol,'4h',start,end,as_of)
    computed = aggregate_4h(hourly,symbol,start,end,as_of)
    fields = ('opened','closed','open','high','low','close','volume','quote_volume')
    valid = [tuple(getattr(c,f) for f in fields) for c in computed] == [tuple(getattr(c,f) for f in fields) for c in official]
    engine.store.audit('archive_4h_validation', f'{symbol} {start.isoformat()} {end.isoformat()} valid={valid}')
    if not valid:
        raise ValueError('Officiële 4h-candles wijken af van vier volledige 1h-candles')
    return {'symbol':symbol,'start':start.isoformat(),'end':end.isoformat(),'candles':len(official),'validation_status':'1h_4h_exact_match'}
