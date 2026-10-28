"""Validate and import only the 108 official 2024 archives, before any returns."""
import calendar
import json
from datetime import timedelta
from pathlib import Path
from crypto.development_2024 import COINS, START, END, SOURCES
from crypto.readiness import validate_frames
from scripts.phase6b_full_audit import CachedDownloads, MonthlyAuditAdapter


def audit(store, progress=lambda *args: None):
    cache = CachedDownloads('/workspace/phase6b_archive_cache', max_requests=0)
    def bounded(url):
        if url.removesuffix('.CHECKSUM') not in SOURCES:
            raise ValueError('Outside 2024 archive whitelist')
        return cache(url)
    result = dict(status='valid', start=START.isoformat(), end=END.isoformat(),
                  datasets=[], months=[], performance_computed=False)
    for symbol in COINS:
        prior = json.loads(Path(f'experiments/phase6b_full_quality/{symbol}_development.json').read_text())
        if len(prior['days']) != 366 or any(d['status'] != 'valid' for d in prior['days']):
            raise ValueError('Prior quality incomplete')
        for month in range(1, 13):
            adapters = {tf: MonthlyAuditAdapter(bounded) for tf in ('15m', '1h', '4h')}
            counts = dict.fromkeys(adapters, 0)
            for day in range(1, calendar.monthrange(2024, month)[1] + 1):
                a = START.replace(month=month, day=day); b = a + timedelta(days=1)
                frames = {tf: adapter.fetch(symbol, tf, a, b) for tf, adapter in adapters.items()}
                validate_frames(frames, symbol, a, b, END)
                with store.transaction():
                    for tf, rows in frames.items():
                        store.add_candles('history', rows)
                        if tf == '15m': store.add_candles('bars', rows)
                        counts[tf] += len(rows)
            for adapter in adapters.values(): result['datasets'].extend(adapter.last_manifest)
            result['months'].append(dict(coin=symbol, month=f'2024-{month:02d}', status='valid', counts=counts))
            progress('quality', symbol, month)
    result.update(requests=cache.requests, download_bytes=cache.bytes)
    return result
