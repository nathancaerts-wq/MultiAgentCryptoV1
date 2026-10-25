# Fase 3 — gespecialiseerde onderzoeksagenten

Gebouwd op f7a70eb3ed3c0ad784722508377fce83dd92b012.

## Oplevering en verbindingen

Vier agents in `crypto.analysis` implementeren dezelfde asynchrone Agent.run- en
Pydantic Message-interface als de Coin Scanner:

- TechnicalAnalysisAgent: EMA, RSI, ATR, momentum en prijsstructuur per timeframe.
- MarketRegimeAgent: bullish/bearish/sideways/uncertain, primair op 1h, ook per frame.
- MultiTimeframeAgent: overeenstemming, conflict of incompleet op 15m/1h/4h.
- NewsSentimentAgent: verwisselbare nieuwsadapter; standaard geen betrouwbare data.

`run_research` registreert per coin afzonderlijke agents. De DAG is scanner →
technical → regime en multi_timeframe; scanner → sentiment; alle vier plus scanner
→ CombinedResearchAgent. Het gecombineerde rapport bewaart per coin de scanner-
ranking, afzonderlijke analyses, conflicten en ontbrekende informatie. Het gaat
uitsluitend om beschrijvend onderzoek; er zijn geen BUY/SELL-adviezen of orders.

De AnalysisContext laadt een expliciete snapshot via de bestaande Data Engine,
valideert elk aangevraagd volledig candlebereik en bevat bronnen, bereik,
candleaantal, parameters en SHA-256 van de daadwerkelijk gebruikte candles.
Agenten krijgen de context en afhankelijke berichtkopieën, geen database-schrijf-
interface. De workflow verzorgt opslag en audit. SQLite bewaart geaccepteerde
agentberichten in results, regimes in regimes en eindrapporten in analyses.

## Reproduceerbare berekeningen

Geen nieuwe libraries, AI-aanroepen, optimalisatie of winstkansen. Parameters in
IndicatorConfig zijn configureerbaar en worden bij elk bericht vastgelegd:

| Kenmerk | Standaard / berekening |
|---|---|
| EMA | fast 9, slow 21; SMA-seed, daarna alpha=2/(n+1) |
| RSI | 14; Wilder-gemiddelden van positieve/negatieve closeverschillen |
| RSI randgevallen | volledig vlak=50, uitsluitend stijgend=100, dalend=0 |
| ATR | 14; Wilder van max(high-low, abs(high-prev_close), abs(low-prev_close)) |
| Momentum | close / close 10 candles eerder - 1 |
| Prijsstructuur | vergelijk highs en lows van twee opeenvolgende blokken van 5 candles |
| Zijwaartsgrens | absolute relatieve EMA-gap en momentum maximaal 0,002 |

Bullish vereist EMA-gap boven grens, positief momentum en hogere highs én lows.
Bearish vereist negatieve EMA-gap onder grens, negatief momentum en lagere highs
én lows. Sideways vereist kleine EMA-gap én klein momentum; anders uncertain.
Een ontbrekende warm-up levert incomplete/uncertain, nooit verzonnen indicatoren.
RSI-extremen en EMA/momentum-tegenstellingen blijven expliciete conflicten.

Default lookback is 32 candles per timeframe; expliciet 3..40 ondersteund om
begrensde onderzoeksimports te behouden. De benodigde warm-up volgt uit alle
parameters. Langere geconfigureerde indicatoren met te weinig data blijven
incompleet. De EMA-seed is afhankelijk van het vastgelegde venster; een langer
venster kan dus andere waarden geven. Dit is geen technische of winstvalidatie
van een strategie.

## Tijd, veroudering en look-ahead

Iedere periode eindigt op de eigen laatste afgesloten UTC-grens. Om 12:37 gebruikt
15m uitsluitend data tot 12:30 en 1h/4h tot 12:00. Geen onvolledige hogere candle
wordt gevormd of naar voren doorgetrokken. Afwijkende, oude of toekomstige reeksen
worden door de bestaande engine geweigerd. De volgende 15m-grens begrenst de TTL;
nieuws- en afhankelijkheidsverval kunnen die termijn verder verkorten.

Orchestrator heeft twee optionele, standaard uitgeschakelde uitbreidingen:
evaluation_time voor expliciete historische replay en reuse_results voor
idempotente onderzoeksherhaling. De bestaande standaard beschermt nog steeds tegen
verlopen/duplicate events. Replay beoordeelt geldigheid op het gekozen moment,
controleert ook toekomstige berichten en verandert nooit hun historische timestamp.
Een identiek event wordt alleen hergebruikt als de volledige inhoud gelijk is.
Toekomstige evaluatietijden worden door run_research geweigerd.

De alleen-lezen API `/analyses` toont actuele berichtgeldigheid via usable; een
historische replay krijgt dus geen nieuw actueel signaal. Die vlag betreft alleen
berichtgeldigheid, niet volledigheid of handelsgeschiktheid. Incomplete/unknown
onderzoeksbevindingen zijn geldige beschrijvende berichten en blijven zichtbaar.
Als scanner of afhankelijkheden volledig uitvallen, wordt een blocked eindrapport
met ontbrekende frames bewaard; audit/errors geeft de oorzaak.

Candles moeten gesloten zijn op as_of. De echte integratie gebruikt retrospectief
opgehaalde publieke klines; dit veronderstelt uitsluitend dat de gesloten candle
op die sluitgrens bekend was. Historische broncorrecties en exacte publicatie-
latentie zijn niet gereconstrueerd. Dit is daarom geen point-in-time backtest of
bewijs van uitvoerbaarheid. Dagarchieven mogen niet als live publicatie op de
candlegrens worden voorgesteld. Nieuws controleert zowel publicatie als werkelijke
beschikbaarheid expliciet.

## Nieuws en sentiment

NewsAdapter is een verwisselbaar protocol. NewsItem vereist ID, EUR-paar, HTTPS-
bron, titel, publicatie-, beschikbaarheids- en vervaltijd in UTC. Toekomstige,
verlopen, dubbele, ongeldige of verkeerd gekoppelde items worden afgewezen met
reden. Adapterfouten geven unknown. Standaard NoNews doet geen netwerkverzoeken en
rapporteert letterlijk 'geen betrouwbare data', sentiment unknown.

Er is bewust geen productienieuwsbron geconfigureerd en geen automatisch sentiment-
model. Een toekomstige adapterbeheerder moet bronbetrouwbaarheid en authenticiteit
vaststellen; een correcte URL/tijdschema alleen bewijst die niet. Ook bij aangeleverde
bronitems blijft sentiment unknown: er wordt niets afgeleid of verzonnen.

## Validatie

**124 tests geslaagd, 0 mislukt**: alle 96 bestaande plus 28 nieuwe tests.
De nieuwe tests omvatten bekende EMA/Wilder/RSI/ATR-uitkomsten, stijgende/dalende/
vlakke en onzekere regimes, parametergrenzen en warm-up, ongeldige/oude/toekomstige
candles, UTC en grensuitlijning, nieuws zonder bron, toekomstige/verlopen/dubbele
items, nieuwsverval in afhankelijke rapporten, multi-timeframe-conflict, ontbrekende
4h-data, volledige data-uitval, reproduceerbare herhaling, deduplicatie, API en
prefixinvariantie bij gewijzigde toekomstige candles. Bestaande externe
Starlette/AnyIO-deprecationwaarschuwing blijft; geen testfouten.

Kleine echte integratie via data-api.binance.vision: BTC/EUR en ETH/EUR elk 32
candles op 15m, 1h en 4h, as_of 2025-01-11T00:00:00Z. Alle zes verzoeken HTTP 200,
192 candles, 11 geaccepteerde historische DAG-resultaten en 2 coinrapporten.
Indicatoren zijn voor alle frames compleet; beide primaire regimes uncertain,
timeframes conflict en rapportstatus incomplete wegens ontbrekende nieuwsdata.
Nul orders of voorstellen. Geen claims over winstgevendheid.

De lokale CLI is ook getest met de bestaande fixture van 24 uurcandles. Met de
standaard 32 is het resultaat terecht blocked wegens onvoldoende scannerdata;
met expliciet lookback 24 ontstaat een incomplete analyse met ontbrekende 15m/4h
zichtbaar. De API-test bevestigt dat historische rapporten usable=false tonen.

## Beperkingen en afronding

Geen betaalde bron, taalmodel, echte nieuwsfeed, strategie, handelsadvies of
uitvoering. Windows is niet daadwerkelijk getest; validatie is op Linux.
Single-process SQLite en synchrone data-/bronadapters blijven beperkingen.
Nieuwsadapters moeten zelf een begrensde uitvoertijd bewaken; een blokkerende
Python-functie is niet door asyncio-timeout te onderbreken. De context bevat
voorberekende features; de agents kiezen deterministisch hun onderzoeksweergave.
Risicogrenzen, overige bots en execution-code zijn ongewijzigd.
Fase 4 is niet gestart.
