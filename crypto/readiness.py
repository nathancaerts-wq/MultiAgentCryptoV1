"""Fase 6B: data-audit en inhoudsgebonden manifest; geen rendementsevaluatie."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
import hashlib
from .data import Candle, validate_series, WATCHLIST
from .archive import ArchiveDataAdapter
from .sim_execution import digest


def dt(s): return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
PERIODS = {
 'development': (dt('2024-01-01'), dt('2025-01-01')),
 'development_warmup': (dt('2024-01-01'), dt('2024-01-08')),
 'validation': (dt('2025-02-01'), dt('2025-12-31T20:00')),
 'validation_warmup': (dt('2025-01-25'), dt('2025-02-01')),
}
LOCKS = ((dt('2025-01-15'),dt('2025-01-16')), (dt('2026-01-01'),dt('2026-10-01')))


def permitted(start,end):
 from .data import utc
 utc(start); utc(end)
 if start>=end or any(start<b and a<end for a,b in LOCKS):
  raise ValueError('Gesloten of ongeldig bereik')
 if not any(a<=start<end<=b for a,b in PERIODS.values()):
  raise ValueError('Buiten toegestane data-auditperioden')


def consistent(lower, higher):
 for h in higher:
  part=[c for c in lower if h.opened<=c.opened<h.closed]
  if not part: raise ValueError('Ontbrekende subcandles')
  validate_series(part,h.symbol,part[0].interval,h.opened,h.closed,h.closed)
  expected=(part[0].open,max(c.high for c in part),min(c.low for c in part),part[-1].close,
            sum(c.volume for c in part),sum(c.quote_volume for c in part))
  if expected!=(h.open,h.high,h.low,h.close,h.volume,h.quote_volume):
   raise ValueError('Timeframe OHLCV mismatch')


def validate_frames(frames,symbol,start,end,as_of):
 for tf in ('15m','1h','4h'):
  rows=[Candle.model_validate(c.model_dump() if isinstance(c,Candle) else c) for c in frames[tf]]
  validate_series(rows,symbol,tf,start,end,as_of)
 consistent(frames['15m'],frames['1h']); consistent(frames['1h'],frames['4h'])


def quality_report(adapter,symbol,period):
 """Dagelijkse validatie, maximaal één archief per fetch; rapporteert ook falende dagen."""
 if symbol not in WATCHLIST: raise ValueError('Buiten watchlist')
 start,end=PERIODS[period]; permitted(start,end)
 result=dict(symbol=symbol,period=period,start=start.isoformat(),end=end.isoformat(),days=[],performance_computed=False)
 day=start
 while day<end:
  stop=min(day+timedelta(days=1),end)
  # De adapter leest volledige archiefdagen: controleer óók het fysieke bereik.
  if not (period=='validation' and stop==end):
   permitted(day,day+timedelta(days=1))
  # Laatste validatiedag eindigt fysiek exact bij de gesloten testgrens.
  # De laatste vier uur worden uitsluitend gedecodeerd, niet geëvalueerd.
  item=dict(start=day.isoformat(),end=stop.isoformat(),archives=[])
  try:
   frames={}
   for tf in ('15m','1h','4h'):
    frames[tf]=adapter.fetch(symbol,tf,day,stop)
    item['archives'].extend(adapter.last_manifest)
   validate_frames(frames,symbol,day,stop,stop)
   item.update(status='valid',counts={tf:len(v) for tf,v in frames.items()})
  except Exception as exc:
   item.update(status='invalid',reason=str(exc))
  result['days'].append(item); day+=timedelta(days=1)
 result['status']='valid' if all(d['status']=='valid' for d in result['days']) else 'incomplete'
 return result


def admission(frames,symbol,at):
 """Alleen trailing zeven dagen. Geen latere gaps of volumes gebruiken."""
 end=at.replace(minute=0,second=0,microsecond=0)
 start=end-timedelta(days=7)
 hourly=[c for c in frames['1h'] if start<=c.opened<end]
 quarter=[c for c in frames['15m'] if at-timedelta(days=7)<=c.opened<at]
 validate_series(hourly,symbol,'1h',start,end,at)
 validate_series(quarter,symbol,'15m',at-timedelta(days=7),at,at)
 if sum(c.quote_volume for c in hourly[-24:])<D(100000): return 'liquiditeit_24h'
 if quarter[-1].quote_volume<D(10000): return 'liquiditeit_15m'
 return None


def metadata_evidence(filters,at):
 if filters is None or filters.status!='validated': return 'historische_filters_onbewezen'
 if not filters.known_at<=at or not filters.valid_from<=at<filters.valid_until:
  return 'historische_filters_buiten_geldigheid'
 if filters.avg_price_mins: return 'historische_gemiddelde_prijs_ontbreekt'
 return None


def manifest(paths,configuration,datasets):
 files={str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
 body=dict(version='phase6b-readiness-v1',configuration=configuration,configuration_sha256=digest(configuration),
           files=files,datasets=datasets,performance_authorized=False,independent_test_authorized=False,
           integrity='hash snapshot; writable files are not immutable')
 return dict(body,sha256=digest(body))


def verify_manifest(value):
 if digest({k:v for k,v in value.items() if k!='sha256'})!=value['sha256']: raise ValueError('Manifest gewijzigd')
 for p,h in value['files'].items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h: raise ValueError('Bestand gewijzigd: '+p)
 if value['performance_authorized'] or value['independent_test_authorized']: raise ValueError('Geen rendementsautorisatie')
