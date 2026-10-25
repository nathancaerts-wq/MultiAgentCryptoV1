# Fase 2 — marktdata-engine en deterministische scanner

## Gerealiseerd

Gebouwd op commit 2067c3b. Fase-1-risicolimieten en execution zijn ongewijzigd.
De nieuwe engine gebruikt het bestaande SQLite-opslagpatroon en voegt datasets,
data_rejections en scan_runs toe. Imports zijn transactioneel, bevatten SHA-256,
bron en importtijd en worden bij een identieke aanvraag uit cache geladen.
Candle-identiteit voorkomt dubbele opslag van dezelfde candle met dezelfde bron.
De cache is een onveranderlijke momentopname: gebruik een nieuwe fixturelocatie
of adapteridentiteit voor gewijzigde brondata. Broncorrecties worden niet stil
overschreven. Er is geen automatische achtergrondimport.

`DataAdapter` is verwisselbaar; `LocalAdapter` leest JSON en `PublicDataAdapter`
ondersteunt expliciete publieke kline-batches van 1..1000 candles van
https://data-api.binance.vision/api/v3/klines. TLS-verificatie blijft ingeschakeld.
Timeout 15 seconden; maximaal drie pogingen bij netwerkfouten, 429 en tijdelijke
5xx; geen retry of hostfallback bij 451/403. Grotere imports worden bewust niet
automatisch gepagineerd. Geen credentials, betaalde aanroepen of orderverzoeken.

UTC, candlegrenzen, OHLC, niet-negatieve volumes, volledigheid, exacte volgorde,
duplicaten en gaten worden gecontroleerd over het volledige aangevraagde bereik.
Ontbrekende data worden niet geïnterpoleerd. 15m/1h/4h zijn schema-intervallen;
4h-aggregatie vereist vier volledige 1h-candles per UTC-blok. Geen gedeeltelijke
laatste candle, geen look-ahead voorbij as_of.

## Scanner en integratie

Configureerbare watchlist: BTC/EUR, ETH/EUR, SOL/EUR, XRP/EUR, ADA/EUR, LINK/EUR.
Per paar gebruikt de scanner standaard 24 afgesloten candles. Trend is laatste
close / gemiddelde close - 1; momentum laatste / eerste close - 1; volatiliteit
is de populatiestandaardafwijking van eenvoudige rendementen. Liquiditeit is
uitsluitend het opgetelde historische EUR-quotevolume, geen actuele spread of
diepte. Vier gelijk gewogen relatieve rangen bepalen score 0..100. Lagere
volatiliteit scoort hoger; ties krijgen gelijke rangen en symbolen bepalen de
stabiele sorteervolgorde. Een score is geen voorspelde winstkans. De score hangt
af van de onderzochte watchlist en is niet absoluut vergelijkbaar tussen universa.
Per paar zijn componenten en uitleg aanwezig; ongeschikte paren krijgen een reden.

De scanner implementeert Agent.run en Message. Event-ID volgt deterministisch uit
het resultaat; dubbele signalen worden door SQLite/orchestrator afgewezen.
Timestamp is het einde van marktdata, niet importtijd. Historische resultaten
blijven beschikbaar in scan_runs; verlopen berichten worden door de orchestrator
niet geaccepteerd en de API vermeldt usable=false. Alleen-lezen endpoints:
/scanner, /candles en /data-quality naast de bestaande API. De CLI in crypto.scan
is een handmatige import/onderzoeksworkflow. Geen handelsvoorstellen of transacties.

## Netwerk en datasetbeschikbaarheid

Tijdens fase 2 geeft api.binance.com/api/v3/ping HTTP 451 (locatiebeperking).
De uitgelezen omgevingsconfiguratie staat uitsluitend api.binance.com toe als
Binance-host. data-api.binance.vision en data.binance.vision zijn daarom niet
benaderd en niet automatisch toegevoegd. Geen omzeiling uitgevoerd.

De werkelijke beschikbaarheid van EUR-datasets en actieve instrumenten op deze
hosts is dus **niet vastgesteld**. De bestaande exchangeInfo-adapter blijft
beschikbaar maar wordt niet als bewezen instrumentregister gebruikt. De scanner
markeert beschikbaarheid als historical_data_only_unverified_tradability.
Een historisch bestand bewijst geen actuele verhandelbaarheid. De officiële
archiefhost data.binance.vision is een mogelijk volgend integratiepunt; ZIP/CSV,
checksums en microseconde-tijdstempels zijn in deze fase niet geïmplementeerd.

## Tests en beperkingen

67 tests slagen: de oorspronkelijke 44 plus 23 nieuwe schema-, datakwaliteits-,
cache-, aggregatie-, ranking-, verlopen-signaal-, orchestrator-, API- en publieke
adaptertests met mocks. Twee kleine synthetische EUR-reeksen zijn expliciet als
fixtures gemarkeerd. De lokale CLI is tevens uitgevoerd met een tijdelijke database.
Geen internetintegratie als geslaagd aangemerkt. Eén bestaande dependency-
deprecationwaarschuwing. Windows 11 is nog niet daadwerkelijk uitgevoerd.

Geen historische Binance-data bewezen, orderboekdata, actief instrumentregister,
archiefdownloader, strategie, backtest of automatische handelslus. Single-process
SQLite en volledige JSON-cache zijn geschikt voor deze basis, niet grote datasets.
Netwerkfouten worden per paar opgeslagen, zodat andere paren kunnen doorgaan.
De basis is bruikbaar voor fase 3 met fixtures; echte datasetvalidatie vereist
expliciete hosttoestemming en succesvolle officiële metadata/data-controles.
