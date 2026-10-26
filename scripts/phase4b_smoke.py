"""Handmatige, kleine officiële ontwikkelingstest; geen onafhankelijke testinzage."""
import asyncio
import json
from datetime import datetime,timedelta,timezone
from tempfile import TemporaryDirectory
from pathlib import Path
from crypto.archive import ArchiveDataAdapter,download
from crypto.analysis import run_research
from crypto.backtest import BacktestRunner,SimulationProtocol,candle_digest
from crypto.data import DataEngine,PublicDataAdapter
from crypto.protocol import ResearchPlan,Period,report_digest
from crypto.sim_execution import SpotFilters,FillCosts,canonical
from crypto.storage import SQLiteStore


async def smoke():
    # Vooraf gekozen kleine steekproef; nooit aanpassen op basis van rendement.
    start=datetime(2025,1,10,tzinfo=timezone.utc);end=start+timedelta(days=1)
    with TemporaryDirectory(prefix='crypto-phase4b-') as temporary:
        store=SQLiteStore(str(Path(temporary)/'research.sqlite3'))
        try:
            analysis_engine=DataEngine(store,PublicDataAdapter())
            reports=[]
            for hour in (12,16):
                reports.extend(await run_research(analysis_engine,start+timedelta(hours=hour),['BTCEUR']))
            archive=DataEngine(store,ArchiveDataAdapter())
            bars={'BTCEUR':archive.load('BTCEUR','1h',start,end,end)}
            bar_hash=candle_digest(bars)
            plan=ResearchPlan(coins=('BTCEUR',),source='Binance Spot, vooraf gekozen BTC/EUR ontwikkelingstest 2025-01-10',dataset_sha256=bar_hash,
                report_hashes=(report_digest(reports),report_digest([]),report_digest([])),
                development=Period(start=start,end=end),
                validation=Period(start=end+timedelta(days=1),end=end+timedelta(days=2)),
                independent_test=Period(start=end+timedelta(days=4),end=end+timedelta(days=5)))
            rule=SpotFilters(symbol='BTCEUR',source='assumption:historical-filters-unavailable',status='assumed',
                note='Alleen simulatie: historische Binance filters niet vastgesteld; tick 0.01 EUR, step 0.00001 BTC, minimum 5 EUR zijn aannames.',
                tick='.01',min_qty='.00001',max_qty='100',step='.00001',min_notional='5')
            spec=SimulationProtocol(costs=FillCosts(fee=plan.fee,slippage=plan.slippage),filters=(rule,),candle_hashes=(bar_hash,candle_digest({}),candle_digest({})))
            runner=BacktestRunner(store);key=runner.register(plan,spec)
            result=runner.run(key,'development',reports,bars)
            summary={'protocol':key,'plan':plan.model_dump(mode='json'),'execution':spec.model_dump(mode='json'),
                     'result_id':result['id'],'candle_count':len(bars['BTCEUR']),'reports':len(reports),
                     'results':{name:({'metrics':value['metrics'],'fills':len(value['trades'])*2,
                                      'rejections':[e['details']['reason'] for e in value['events'] if e['action']=='rejected']})
                                if 'metrics' in value else value for name,value in result['results']['BTCEUR'].items()},
                     'paper_orders':len(store.list('orders')),'independent_test_opened':False,
                     'archive_manifest':next(r['archive_manifest'] for r in store.list('datasets') if r.get('archive_manifest'))}
            return json.loads(canonical(summary))
        finally:store.close()


if __name__=='__main__':
    print(json.dumps(asyncio.run(smoke()),indent=2,ensure_ascii=False))
