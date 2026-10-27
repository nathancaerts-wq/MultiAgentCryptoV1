# Fase 6B — resterende blokkeringen

Basis c0618c9c6cd7d435c20231e41b26612c76a185ff. Geen historische
rendementen berekend; oude onafhankelijke test en kandidaat-test 2026 blijven gesloten.

## Uitgevoerde data-audit

`scripts/phase6b_full_audit.py` voert uitsluitend kwaliteitscontrole uit voor de zes
EUR-paren. De officiële maand-ZIP wordt vóór verwerking met de officiële SHA-256
gecontroleerd. Vervolgens worden dagsegmenten naar de bestaande strikte decoder
geleid. Hun interne checksums zijn afgeleid, geen officiële dagchecksums; de
provenance bewaart de oorspronkelijke maandchecksum. Alle maandcandles worden
gecontroleerd, inclusief UTC, volgorde, duplicaten, gaten, gesloten OHLCV en volumes.
15m→1h→4h wordt per dag exact vergeleken. Januari-2025-warm-up blijft dagelijks;
er worden geen maandarchieven met het oude testslot gelezen. De laatste vier uur
van december 2025 worden uitsluitend gedecodeerd, niet als validatie-uitkomst gebruikt.

De adapter voegt geen handelsresultaten, indicatoren of selectie op rendement toe.
Schijfcache: /workspace/phase6b_archive_cache (niet in Git). Per bestand maximaal
2 MB download; totaalbudget per uitvoering 26.000 verzoeken/1 GB, maximaal drie
parallelle coins. Na drie netwerkfouten opent een circuitbreker. Budget/circuit-
afwijzingen betekenen niet onderzocht, geen bewezen ontbrekende marktdata. Een
cachehit wordt opnieuw op checksum en inhoud gecontroleerd. Hervatting leest
gecachete bestanden; bestaande brondownloads blijven bewaard.

De volledige dagrapporten, officiële archiefhashes en periodegrenzen staan in
experiments/phase6b_full_quality/. De samenvatting hieronder wordt uit die rapporten
gegenereerd. Archiefdekking bewijst handel in de historische candles, geen exacte
listing-/delistingtijd, continu verhandelbare status of oorspronkelijke publicatietijd.
Een huidige checksum kan latere archiefrevisies authenticeren; point-in-time
bronversies zijn niet gereconstrueerd.

## Historische orderfilters

De officiële documentatie is nu bereikbaar (HTTP 200); URL's, bronhashes en relevante
passages staan in experiments/phase6b_filter_research.json. Binance noemt exchangeInfo
expliciet **current exchange trading rules and symbol information**. De onderzochte
klinearchieven bevatten geen historische filterreeks. Dit bewijst niet dat elders
geen historische snapshots bestaan; er is hier geen verifieerbare tijdreeks gevonden.

Voor alle zes munten geldt:

- Historisch bewezen filters: geen volledige geverifieerde reeks beschikbaar.
- Onbevestigd: actuele of ongedateerde snapshots; niet toepassen als historisch feit.
- Aangenomen: uitsluitend apart voorgesteld hypothetisch model; niet geactiveerd.

Voorgesteld alternatief voor latere afzonderlijke goedkeuring: één vaste
hypothetische EUR-markt met tick €0,01, quantity-stap 0,00001 coin, minimumnotional
€10, geen leverage; fee/spread/slippage alle 0,2%, de reeds beschreven stresskosten.
Dezelfde bestaande 0,5%-risicogrens, €200 en één positie blijven gelden. Deze regels
zijn geen Binance-filterreconstructie en kunnen juist voor goedkope coins sterk
vertekenen. Niet vergelijken alsof historische uitvoerbaarheid bewezen is. Geen
alternatieve configuratie of orderroute geactiveerd; eerst een apart gedateerd plan.

## Benchmarks

De kalenderfunctie bindt cash, marktindex en EMA aan exact ontwikkeling
[2024-01-01,2025-01-01) en validatie [2025-02-01,2025-12-31 20:00), UTC.
Indexinstap respectievelijk 2024-01-08 en 2025-02-01; laatste strategie-entry
uiterlijk 4h15m vóór het einde. Teststage wordt geweigerd. Parameters zijn gelijk
gebleven. Cash/indexrekenfuncties en EMA-fixturepad zijn behouden; de volledige
historische benchmarkregisseur met bron- en toelatingsbewijs blijft een blokkering.
Er is geen historische rendementsvergelijking uitgevoerd.

## Schaalmeting

De echte FixtureJointRunner kreeg zes synthetische munten met ieder 35.136
15m-candles (366 dagen). Geen historische koersen of winstresultaten gebruikt.
Een subprocess heeft een geheugenlimiet van 1,5 GB en tijdlimiet van 45 seconden.
De meting zonder complete agentrapporten is een ondergrens van de werkelijke last.

Voor de optimalisatie: checkpoint na één batch op circa 28 seconden, piek-RSS
777.604 KiB; geen voltooide jaarreplay binnen 45 seconden.
Na memoization van vaste candlehashes en een tijdindex: checkpoint na 101 batches
op circa 31 seconden, piek-RSS 784.656 KiB; opnieuw geen voltooide jaarreplay binnen
45 seconden. Exacte meetbestanden bewaren de checkpoints, niet de laatste stand op
afbreektijd: het werkelijke aantal batches na het laatste checkpoint is onbekend.
Dit levert **geen** bevestiging van één jaar volledige verwerking, reproduceerbaarheid
of risicogedrag op jaarschaal. De bestaande en nieuwe fixtures controleren wel de
centrale ledger, risicobeveiligingen, herstart en chronologische afwijzingen.

Optimalisatie verandert geen regels: Candle-objecten zijn frozen; de hash/index
wordt per tuple hergebruikt en bij vervanging opnieuw gebouwd. De volledige
state/auditketen, JSON-ledgers en historie groeien nog steeds. Een geteste
incrementele opslag-/replayarchitectuur blijft nodig; die is niet veilig vervangen
door simpelweg integriteitscontroles uit te schakelen.

## Blokkeringen en conclusie

| Blokkering | Status |
|---|---|
| Reproduceerbare audit met schijfcache en budget | Opgelost |
| Volledige inhoudelijke corpusvalidatie | Zie gegenereerde audituitkomsten hieronder |
| Historische filter- en listingstatusreconstructie | Niet opgelost |
| Eenduidige benchmarkperioden | Opgelost; kalender getest |
| Volledige historische benchmarkregisseur | Niet opgelost |
| Jaarreplay zes munten: tijd, geheugen en reproduceerbaarheid | Niet opgelost; begrensde meting voltooit niet |
| Extern inzageregister / onafhankelijkheid | Niet opgelost |
| Testvergrendeling en bestaande risicogrenzen | Behouden |

**Uitgebreide historische backtests zijn nog niet betrouwbaar technisch uitvoerbaar.**
Toestemming voor rendementsevaluatie ontbreekt bovendien. Deze opdracht opent
geen historische uitvoering en activeert geen hypothetisch filtermodel.

## Onderzoek naar timeframe-afwijkingen

Voorbeelden staan in experiments/phase6b_timeframe_differences.json. Bij XRP, ADA
en LINK bevat de eerste 15m-subcandle van de onderzochte afwijkende uurcandle geen
volume. Haar carry-forward OHLC kan afwijken van de officiële uur-open/high.
Dit is een concreet verschil tussen geverifieerde archieven, geen checksumfout en
geen bewezen ontbrekende candle. De voorbeelden verklaren niet automatisch elke
afgekeurde dag. De preregistreerde exacte vergelijking blijft gehandhaafd; er is
geen stilzwijgende uitzondering voor lege subcandles ingevoerd. Een eventuele
alternatieve aggregatieconventie vereist vooraf een afzonderlijke protocolkeuze.

## Definitieve corpusuitkomsten

Alle aangevraagde perioden zijn doorlopen. Goedgekeurde dagen / totaal:

| Paar | Ontwikkeling | Validatie | Validatiewarm-up |
|---|---|---|---|
|BTCEUR|366/366|334/334|7/7|
|ETHEUR|366/366|334/334|7/7|
|SOLEUR|366/366|334/334|7/7|
|XRPEUR|359/366|334/334|7/7|
|ADAEUR|274/366|334/334|7/7|
|LINKEUR|180/366|307/334|4/7|

De audit is uitgevoerd; volledige strikte kwaliteit voor alle zes munten is **niet opgelost**.
Afwijkende dagen blijven uitgesloten, zonder perioden op rendement te selecteren.
Laatste hervatte uitvoering: 884 nieuwe verzoeken, 17990012 bytes, 0 netwerkfouten. Eerdere succesvolle downloads zijn hergebruikt; deze tellers zijn niet cumulatief over onderbroken uitvoeringen.

**317 tests geslaagd, 0 mislukt** (310 behouden plus 7 nieuwe); één bestaande Starlette/AnyIO-waarschuwing. Geen historische rendementsrun.
