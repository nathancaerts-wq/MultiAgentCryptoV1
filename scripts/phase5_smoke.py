"""Kleine lokale integratietest met bestaande officiële Binance-archieven.

Geen netwerk, geen parameterzoektocht en geen historische testset. Uitvoer is JSON.
Run: PYTHONPATH=. .venv/bin/python scripts/phase5_smoke.py
"""
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from crypto.analysis import run_research
from crypto.archive import ArchiveDataAdapter
from crypto.data import DataEngine
from crypto.protocol import ResearchPlan, Period, report_digest
from crypto.research_execution import ResearchTradingSession
from crypto.sim_execution import SpotFilters, digest
from crypto.storage import SQLiteStore
from crypto.trade_agents import DecisionPolicy

ROOT = Path(__file__).resolve().parents[1]/'tests/fixtures/archive'
DAY = datetime(2025,1,10,tzinfo=timezone.utc)
END = DAY+timedelta(days=1)


async def smoke():
    policy = DecisionPolicy()  # Vastgelegd vóór gegevensverwerking; nooit optimaliseren.
    store = SQLiteStore()
    adapter = ArchiveDataAdapter(downloader=lambda url:(ROOT/url.rsplit('/',1)[-1]).read_bytes())
    engine = DataEngine(store,adapter)
    rows, manifests = {}, []
    candle_count = 0
    try:
        for coin in ('BTCEUR','ETHEUR'):
            for frame in ('15m','1h','4h'):
                series=engine.load(coin,frame,DAY,END,END)
                manifests.extend(adapter.last_manifest)
                candle_count += len(series)
                if frame=='15m': rows[coin]=series
        # Zes 4h-candles passen in de ene aanwezige dag. Indicatorparameters blijven
        # ongewijzigd: bewust onvoldoende warm-up -> HOLD, nooit een verzonnen signaal.
        reports=await run_research(engine,END,('BTCEUR','ETHEUR'),lookback=6)
        plan=ResearchPlan(coins=('BTCEUR','ETHEUR'),source='Bestaande officiële Binance Spot-archiefbestanden',
                          dataset_sha256=digest(manifests),report_hashes=(report_digest(reports),report_digest([]),report_digest([])),
                          development=Period(start=DAY,end=DAY+timedelta(days=2)),
                          validation=Period(start=DAY+timedelta(days=3),end=DAY+timedelta(days=4)),
                          independent_test=Period(start=DAY+timedelta(days=5),end=DAY+timedelta(days=6)))
        decisions={}
        for coin in plan.coins:
            filters=SpotFilters(symbol=coin,source='fixture:assumed_metadata',status='assumed',
                                note='Geen historische beursfilterclaim; geen orders bij ontbrekende analyses',
                                tick='.01',min_qty='.00001',max_qty='100',step='.00001',min_notional='5')
            session=ResearchTradingSession(store,plan,policy,coin,filters,reports,rows[coin])
            result=await session.evaluate(END)
            decisions[coin]={name:m.result for name,m in result['messages'].items()}
            assert result['messages']['decision:'+coin].result['action']=='HOLD'
            assert not any(r['approved'] for r in result['reviews'])
        exposed=any(e['stage']=='independent_test' for e in store.list('research_exposures'))
        assert not exposed and not store.list('orders') and not store.list('research_fills')
        return dict(test='phase5-official-archive-fixtures',network_requests=0,plan=plan.model_dump(mode='json'),
                    policy=policy.model_dump(mode='json'),policy_sha256=policy.fingerprint,
                    archives=manifests,candles=candle_count,decisions=decisions,
                    independent_test_opened=exposed,paper_orders=len(store.list('orders')),
                    offline_fills=len(store.list('research_fills')),
                    limitation='Eén dag bevat onvoldoende indicator-warm-up; correcte veilige HOLD. Geen prestatiemeting.')
    finally:
        store.close()


if __name__=='__main__':
    print(json.dumps(asyncio.run(smoke()),indent=2,sort_keys=True,default=str))
