"""Expliciete offline onderzoeksimport: python -m crypto.scan --help."""
import argparse
import asyncio
from datetime import datetime
from .data import LocalAdapter, DataEngine, WATCHLIST
from .scanner import CoinScanner
from .storage import SQLiteStore
from .orchestrator import Orchestrator, Task


def main():
    p=argparse.ArgumentParser(description='Scan lokale OHLCV JSON; plaatst geen transacties')
    p.add_argument('--fixture',required=True)
    p.add_argument('--as-of',required=True,help='UTC ISO 8601, bijvoorbeeld 2026-01-02T00:00:00Z')
    p.add_argument('--db',default='crypto.sqlite3')
    p.add_argument('--watchlist',nargs='+',default=WATCHLIST)
    p.add_argument('--interval',choices=['15m','1h','4h'],default='1h')
    args=p.parse_args()
    store=SQLiteStore(args.db)
    try:
        scanner=CoinScanner(DataEngine(store,LocalAdapter(args.fixture)),datetime.fromisoformat(args.as_of.replace('Z','+00:00')),interval=args.interval,watchlist=args.watchlist)
        orchestrator=Orchestrator(store)
        orchestrator.register('scanner',scanner)
        accepted=asyncio.run(orchestrator.execute([Task('scan','scanner')]))
        print(f'Scans opgeslagen: {len(store.list("scan_runs"))}; verse geaccepteerde signalen in deze run: {len(accepted)}')
    finally:
        store.close()


if __name__=='__main__': main()
