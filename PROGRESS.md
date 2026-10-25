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
