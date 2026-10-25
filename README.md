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
