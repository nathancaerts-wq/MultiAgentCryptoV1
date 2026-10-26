# Voortgang — fase 1

## Voltooid

- Python-package met 13 expliciete componentcontracten en afhankelijkheden.
- Centrale asynchrone orchestrator: registratie, DAG-validatie, timeouts,
  pauzeren/hervatten, persistente event-deduplicatie en auditregistratie.
- Pydantic-berichten met UTC, TTL, status en foutvalidatie.
- SQLite-opslag voor alle gevraagde domeinen en transactionele ordervoorstellen.
- Deterministische risicolimieten, noodstop, saldo- en orderfiltercontroles.
- Geïsoleerde onderzoekskandidaten, periodehergebruikcontrole en inactieve goedkeuring.
- Publieke Binance metadata-adapter, EUR-universumselectie en alleen-lezen API.
- Windows-installatie-instructies, dependencyversies en cloud-opstartinstructies.

## Validatie

44 tests geslaagd met Python 3.12 op Linux. Getest: registratie, communicatie,
berichtschema, taakvolgorde/cycli, agentfouten/timeouts, pauzeren/hervatten,
verlopen/toekomstige signalen, dubbele events na databaseheropening,
transactierollback, veiligheidsgrenzen, dubbele ordervoorstellen,
onderzoeksisolatie, Binance fixtureparser, scanner en alle API-endpoints.
Een gevonden herregistratiefout na een herstart is hersteld.
`pip check` meldt geen dependencyconflicten. Installatie is opnieuw uitgevoerd.
De echte HTTP-server is gestart; /health en /portfolio geven de verwachte waarden.

## Beperkingen en openstaande punten

- Publieke Binance-integratie niet live geverifieerd: netwerkproxy geeft 403.
  api.binance.com is toegevoegd aan de concept-omgevingsconfiguratie; toepassen en
  opnieuw controleren is nodig vóór gebruik van echte marktdata.
- Windows 11 is gedocumenteerd maar niet op deze Linux-machine getest.
- Eén externe Starlette/AnyIO-deprecationwaarschuwing; geen testfouten.
- Geen strategieën, LLM-integratie, historische backtestberekening, fills,
  saldoreservering, positiewaardering of grafisch dashboard. Dit zijn volgende fases.
- SQLite gebruikt generieke JSON-records. Getypeerde migraties, grotere datasets,
  concurrente workers en procesisolatie zijn vervolgwerk.
- Goedkeuring is een lokaal Python-contract, zonder geauthenticeerde reviewerworkflow.
- Marktmetadata ondersteunt de basisfilters; volledige Binance-filterdekking moet
  worden uitgebreid voor uitvoeringssimulaties. Geen claim van handelsgereedheid.

Fase 1 vormt een testbare basis voor fase 2. De genoemde integratiebeperkingen
moeten daar expliciet worden afgehandeld. Alleen virtuele voorstellen; geen transacties.

## Fase 2

Marktdata-engine, UTC-OHLCV-validatie, onveranderlijke importcache, volledige
4h-aggregatie, deterministische multi-coin ranking, lokale CLI en alleen-lezen
scanner/data-quality API toegevoegd. Alle 67 tests slagen (44 bestaande + 23 nieuwe).
Geen risico- of handelscode aangepast. Netwerk: api.binance.com geeft HTTP 451;
beide vision-hosts staan niet in de beschikbare allowlist en zijn niet getest.
Actuele EUR-instrumenten en echte historische datasets blijven onbevestigd.
Zie PHASE2_REPORT.md voor volledige oplevering en beperkingen.

## Fase 2B

Officiële dagelijkse Binance Spot ZIP/CSV-adapter toegevoegd met verplichte SHA-256,
exacte ms/us-conversie volgens het gedocumenteerde datumformaat, volledige dagvalidatie
en expliciete officiële 1h/4h-vergelijking. Integreert met Candle en bestaande caching;
datasetrecords bewaren archiefprovenance, checksum en validatiestatus.

96 tests slagen: alle 67 bestaande plus 29 nieuwe archieftests. Echte integratie:
7 kleine archieven via HTTP 200, 276 geldige candles, alle checksums gelijk;
BTCEUR en ETHEUR 1h/4h komen exact overeen. Geen orders aangemaakt.
Beperkingen: uitsluitend dagelijkse expliciete batches van maximaal zeven archieven,
geen automatische verversing van gewijzigde bronbestanden; Windows niet uitgevoerd.
Zie PHASE2B_REPORT.md. Fase 3 niet gestart.

## Fase 3

Vier gespecialiseerde onderzoeksagenten toegevoegd: market regime, technical
analysis, multi-timeframe en news/sentiment. Geïntegreerd met scanner, DAG,
Message-validatie, audit, SQLite en alleen-lezen API. Deterministische EMA/RSI/ATR,
momentum en prijsstructuur; parameters en candleprovenance worden vastgelegd.
Geen betrouwbare nieuwsfeed: expliciet unknown, geen verzonnen sentiment.
Historische replay ververst geen signaal; ontbrekende data/conflicten blijven zichtbaar.

124 tests geslaagd, 0 mislukt (96 bestaande + 28 nieuwe). Zes echte publieke GETs
HTTP 200, 192 candles, twee historische coinrapporten; alle indicatorframes compleet,
regime uncertain, timeframes conflict, rapporten incomplete door ontbrekend nieuws.
Lokale CLI en API eveneens getest. Eén bestaande dependencywaarschuwing.
Beperkingen: geen point-in-time bronversies/publicatielatentie of betrouwbare nieuwsfeed,
Windows niet uitgevoerd, single-process SQLite. Zie PHASE3_REPORT.md.
Geen transacties of parameteroptimalisatie. Fase 4 niet gestart.

## Fase 4

QuantResearcher, ResearchPlan en OfflineResearchOptimizer toegevoegd met vaste
hypotheses, preregistratie, chronologische splits/embargo, walk-forward-planning,
bundelhashcontrole en duurzame registratie van bekeken testperioden.
Kosten- en risicorekeninterfaces: €200 en maximaal 0,5% gepland risico per trade.
Bestaande productiestrategieën, agents en harde grenzen worden niet gewijzigd.

154 tests geslaagd, 0 mislukt (124 bestaande + 30 nieuwe). Geen gevalideerde
fillsimulator aanwezig: prestaties, benchmarks en gevoeligheidsuitkomsten blijven
expliciet niet berekend, met onvoldoende bewijs. Geen winstclaims of transacties.
Zie RESEARCH_PROTOCOL.md en PHASE4_REPORT.md. Fase 5 is niet gestart.

## Fase 4B

Onderbroken ontwikkeling hervat en behouden vanaf da81022303a8300ded72519567114701ff0482a1.
Offline fillsimulator, single-position EUR-ledger en preregistreerde backtestrunner
met kosten, orderfilters, stops/gaps, risico- en verliespauzes, audit-hashketen,
benchmark- en gevoeligheidsscenario's. Onderzoeksopslag en API blijven gescheiden
van papertrading. Bestaande agenten en harde grenzen zijn ongewijzigd.

191 tests geslaagd, 0 mislukt (154 bestaande + 37 nieuwe). De bestaande kleine
BTC/EUR-integratietest is gecontroleerd en opgeslagen in experiments/phase4b_smoke.json;
geen nieuwe historische backtest uitgevoerd bij hervatten. Historische orderfilters
zijn aannames; alle uitkomsten blijven onvoldoende bewijs. De onafhankelijke test
is niet vrijgegeven. Zie PHASE4B_REPORT.md voor alle uitvoeringsaannames en beperkingen.
Fase 5 niet gestart.
