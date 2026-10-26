# MultiAgentCryptoV1

Fase 1 van een modulair onderzoeks- en paper-tradingplatform voor Binance Spot.
Startsaldo: **€200 virtueel**. Er is geen live orderadapter, geen sleutelconfiguratie,
geen strategieactivatie en geen volledige paperbot.

## Installeren op Windows 11

Python 3.12 of hoger is vereist. Vanuit de repository, in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.lock
.\.venv\Scripts\python -m pip install --no-deps -e .
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m crypto --db crypto.sqlite3
```

Linux/cloud: vervang `.\.venv\Scripts\python` door `.venv/bin/python`;
maak de omgeving met `python3 -m venv .venv`.
De API bindt uitsluitend aan loopback, poort 8000. OpenAPI is beschikbaar op `/docs`.
Stop met Ctrl+C. De SQLite-database blijft behouden; processen niet.

## Backendinterfaces

Alle endpoints zijn alleen-lezen: `/health`, `/agents`, `/coins`, `/market`,
`/signals`, `/research`, `/portfolio`, `/risk-limits`, `/audit`, `/errors`.
Lege resultaten betekenen dat er nog geen gegevens zijn ingelezen. De catalogus
van 13 componenten is geen claim dat 13 strategieagenten al draaien.

Agenten implementeren de asynchrone `Agent.run(inputs)`-interface en leveren een
`Message`. Registreer ze via `Orchestrator.register` en voer een DAG van `Task`
uit. Alleen de orchestrator schrijft ontvangen resultaten naar de opslag.
Injecteer geen database of bestandsrechten in onderzoeksagenten.

`BinancePublic.exchange_info()` gebruikt uitsluitend het publieke HTTPS endpoint
`/api/v3/exchangeInfo`. Geen account nodig. De parser accepteert uitsluitend
actieve EUR-spotparen met relevante filters. Werkelijke beschikbaarheid moet
opnieuw worden gecontroleerd wanneer netwerktoegang beschikbaar is.

Zie [ARCHITECTURE.md](ARCHITECTURE.md), [PROGRESS.md](PROGRESS.md) en
[NEXT_STEPS.md](NEXT_STEPS.md). De tests gebruiken uitsluitend lokale testdata.

## Fase 2: marktdata en Coin Scanner

Reproduceerbare lokale workflow (gebruik op Windows het Python-pad hierboven):

```bash
.venv/bin/python -m crypto.scan --fixture tests/fixtures/ohlcv.json --as-of 2026-01-02T00:00:00Z --watchlist BTCEUR ETHEUR SOLEUR
.venv/bin/python -m crypto --db crypto.sqlite3
```

Deze fixture is **synthetisch**, geen historische Binance-opname. De scan wordt
als historisch onderzoek opgeslagen. Een historische scan levert geen vers signaal
op. De API toont `/scanner` met `usable`, `/candles` en `/data-quality`.
`/signals` blijft de door de orchestrator geaccepteerde berichten tonen.

De watchlist is configureerbaar; de standaardvoorbeelden zijn geen bewijs van
actuele verhandelbaarheid. Zie [PHASE2_REPORT.md](PHASE2_REPORT.md) voor methode,
netwerkbeperkingen en grenzen van de implementatie.

## Fase 2B: officiële dagarchieven

Gebruik de nieuwe adapter rechtstreeks met dezelfde Data Engine:

```python
from datetime import datetime, timezone, timedelta
from crypto.archive import ArchiveDataAdapter, verify_4h
from crypto.data import DataEngine
from crypto.storage import SQLiteStore

start = datetime(2025, 1, 10, tzinfo=timezone.utc)
end = start + timedelta(days=1)
store = SQLiteStore('crypto.sqlite3')
engine = DataEngine(store, ArchiveDataAdapter())
candles = engine.load('BTCEUR', '1h', start, end, end)
comparison = verify_4h(engine, 'BTCEUR', start, end, end)
store.close()
```

Dit importeert alleen een expliciet opgegeven historische dag. Maximaal zeven
dagarchieven per aanvraag. Officiële checksums worden vóór verwerking gecontroleerd.
Zie [PHASE2B_REPORT.md](PHASE2B_REPORT.md) voor validatie, caching en testresultaten.

## Fase 3: gespecialiseerde analyses

Expliciete historische onderzoeksworkflow met kleine publieke datasets:

```bash
.venv/bin/python -m crypto.research_run --source public --as-of 2025-01-11T00:00:00Z --coins BTCEUR ETHEUR --db crypto.sqlite3
```

Ook `--source archive` en `--source fixture --fixture bestand.json` zijn beschikbaar.
Gebruik `--lookback` voor het onderzoeksvenster (default 32) en eventueel `--config`
met een JSON IndicatorConfig. Dit is handmatige configuratie, geen optimalisatie.
Rapporten staan in de alleen-lezen API `/analyses`; regimes ook in `/market`.
Onvolledige gegevens en conflicten blijven zichtbaar, nieuws is standaard unknown.
Zie [PHASE3_REPORT.md](PHASE3_REPORT.md) voor indicatorformules en tijdsbeperkingen.

## Fase 4: begrensd offline onderzoek

`crypto.protocol.ResearchPlan` legt hypotheses, parameters, chronologische perioden,
data- en rapporthashes vast. Registreer dit via
`crypto.offline_optimizer.OfflineResearchOptimizer.register(plan)` vóór inzage.
`inspect(plan_id, stage, reports, dataset_sha256)` valideert bestaande fase-3-
berichten en bewaart onderzoeksselecties en expliciet onbekende prestaties.
Stages: development, validation, independent_test. Gebruik `report_digest` voor
de vooraf vastgelegde bundelhash per stage. Er is geen optimizer-zoeklus of promotie.

Lees [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) en
[PHASE4_REPORT.md](PHASE4_REPORT.md): betrouwbare backtests wachten op een
gevalideerde fillsimulator en ledger. Huidige prestatievelden zijn bewust null.

## Fase 4B: offline simulatie

`crypto.backtest.BacktestRunner` koppelt ResearchPlan aan een vooraf vastgelegd
SimulationProtocol met kosten, filters en candlehashes. Resultaten en audits staan
in aparte onderzoekstabellen; alleen-lezen API: `/backtests` en `/simulation-protocols`.
De onafhankelijke test is standaard gesloten. De simulator gebruikt één positie
per afzonderlijk €200 coin/hypothese-experiment, maximaal 0,5% gepland risico.

Lees [PHASE4B_REPORT.md](PHASE4B_REPORT.md) voor alle uitvoeringsaannames en
beperkingen. De eerder uitgevoerde kleine historische ontwikkelingstest staat in
[experiments/phase4b_smoke.json](experiments/phase4b_smoke.json).
`scripts/phase4b_smoke.py` beschrijft de handmatige reproductie; wordt niet automatisch gestart.

## Fase 5: gecontroleerde Decision/Entry/Exit-agenten

`crypto.trade_agents` levert vaste onderzoeksbeslissingen; `ResearchTradingSession`
in `crypto.research_execution` verbindt deze met orchestrator, Risk Engine en de
bestaande offline ledger. `evaluate()` maakt alleen berichten en beoordelingen.
Een fill vereist een afzonderlijke expliciete `execution.simulate(review_id)`-aanroep;
er ontstaan geen paper-orders. De onafhankelijke test blijft gesloten.

Lees PHASE5_REPORT.md voor beslisregels, grenzen, gebruiksvoorwaarden en beperkingen.
De kleine archieftest gebruikt alleen al aanwezige bestanden:

```bash
PYTHONPATH=. .venv/bin/python scripts/phase5_smoke.py
.venv/bin/python -m pytest -q
```

Resultaten: alleen-lezen `/decisions`, `/research-trade-reviews` en `/research-fills`.
Stop na fase 5; geen automatische activatie of volgende fase.
