"""Eenmalige, begrensde HEAD-inventaris; leest geen ZIP/CSV of rendementen.

Uitvoeren vanuit de repository: python scripts/phase6b_coverage_metadata.py OUTPUT.json
Alleen 2024/2025, zes vooraf gekozen EUR-paren, drie timeframes. Geen redirects,
geen retry/fallback naar koersdata en geen verzoeken voor de kandidaat-testset 2026.
Een nieuwe uitvoering vereist een nieuw uitvoerbestand; eerdere bewijsstukken blijven staan.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


SYMBOLS = ('ADAEUR', 'BTCEUR', 'ETHEUR', 'LINKEUR', 'SOLEUR', 'XRPEUR')
INTERVALS = ('15m', '1h', '4h')
HOST = 'https://data.binance.vision'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def targets():
    for symbol in SYMBOLS:
        for year in (2024, 2025):
            for month in range(1, 13):
                period = f'{year}-{month:02d}'
                for interval in INTERVALS:
                    base = f'{HOST}/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{period}.zip'
                    for kind, suffix in (('archive', ''), ('checksum', '.CHECKSUM')):
                        yield dict(symbol=symbol, month=period, interval=interval,
                                   kind=kind, url=base+suffix)


def inspect(target):
    row = dict(target, method='HEAD', checked_at=utc_now(), body_bytes_read=0)
    opener = build_opener(NoRedirect())
    try:
        with opener.open(Request(target['url'], method='HEAD'), timeout=20) as response:
            row.update(http_status=response.status, headers={
                k: response.headers.get(k) for k in
                ('Content-Length', 'Content-Type', 'Last-Modified', 'ETag')})
    except HTTPError as exc:
        row.update(http_status=exc.code, error='HTTP error; response body not read')
        exc.close()
    except (URLError, TimeoutError, OSError) as exc:
        row.update(http_status=None, error=str(exc))
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    # Reserve the new artifact before any requests; never replace an old inventory.
    with args.output.open('x', encoding='utf-8') as output:
        started = utc_now()
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(inspect, targets()))
        counts = dict(Counter(str(r['http_status']) for r in rows))
        json.dump(dict(schema='phase6b-metadata-only-v1', started_at=started,
                       completed_at=utc_now(), symbols=SYMBOLS, intervals=INTERVALS,
                       years=[2024, 2025], requests=len(rows), http_status_counts=counts,
                       data_bodies_read=0, checksum_values_read=False,
                       independent_test_results_accessed=False,
                       limitation='HEAD availability only; no candle, checksum integrity, listing-time or liquidity verification',
                       rows=rows), output, indent=2, sort_keys=True)
        output.write('\n')
    print(json.dumps(dict(requests=len(rows), http_status_counts=counts,
                         output=str(args.output))))


if __name__ == '__main__':
    main()
