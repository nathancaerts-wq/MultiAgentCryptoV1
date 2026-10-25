"""Expliciete onderzoeksworkflow, zonder handelsuitvoering."""
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
import json
from .analysis import run_research
from .archive import ArchiveDataAdapter
from .data import DataEngine,LocalAdapter,PublicDataAdapter
from .indicators import IndicatorConfig
from .storage import SQLiteStore


def main():
    parser=argparse.ArgumentParser(description='Vier analyseagenten en scanner; uitsluitend onderzoek')
    parser.add_argument('--source',choices=['fixture','public','archive'],required=True)
    parser.add_argument('--fixture')
    parser.add_argument('--as-of',required=True,help='Expliciete UTC ISO 8601 evaluatietijd')
    parser.add_argument('--coins',nargs='+',required=True)
    parser.add_argument('--db',default='crypto.sqlite3')
    parser.add_argument('--lookback',type=int,default=32)
    parser.add_argument('--config',help='JSON-bestand met IndicatorConfig; geen optimalisatie')
    args=parser.parse_args()
    if args.source=='fixture' and not args.fixture: parser.error('--fixture vereist bij fixturebron')
    adapter=LocalAdapter(args.fixture) if args.source=='fixture' else PublicDataAdapter() if args.source=='public' else ArchiveDataAdapter()
    config=IndicatorConfig.model_validate(json.loads(Path(args.config).read_text())) if args.config else IndicatorConfig()
    at=datetime.fromisoformat(args.as_of.replace('Z','+00:00'))
    store=SQLiteStore(args.db)
    try:
        reports=asyncio.run(run_research(DataEngine(store,adapter),at,args.coins,config,args.lookback))
        for report in reports:
            print(json.dumps(dict(coin=report.coin,event_id=str(report.event_id),result=report.result,usable_now=report.usable()),ensure_ascii=False))
    finally: store.close()


if __name__=='__main__': main()
