# Fase 6B — voorstel voor preregistratie gezamenlijke multi-coinbacktest

**Versie:** phase6b-proposal-v1, 27 oktober 2026 (Europe/Brussels).
**Basis:** `58863994285005fe052d9e87acc52eadedcdfe0d`.
**Status:** voorstel, niet goedgekeurd, niet als uitvoerbaar ResearchPlan geregistreerd.
**Rendementsbacktests uitgevoerd in deze opdracht: geen.** Zowel het oude testslot
als de kandidaat-testset 2026 blijven gesloten. Goedkeuring van dit document mag
niet stilzwijgend worden uitgelegd als toestemming om de onafhankelijke test te openen.

## 1. Aanbeveling en afbakening

Gebruik één vooraf vastgelegde primaire strategie: de bestaande `aligned_trend`
met DecisionPolicy `phase5-v1` en JointPolicy `phase6a-v1`. Onderzoek ontwikkeling
in 2024 en validatie vanaf februari 2025; reserveer januari–september 2026 uitsluitend
als **voorlopige** onafhankelijke historische test. Behoud alle oudere registraties.
Deze keuze vermijdt de bekende eerdere januari-2025-inzage en de oude testvergrendeling.
Zij is niet gekozen op grond van nieuwe rendementen: die zijn niet berekend.

De letterlijke indeling “heel 2024 ontwikkeling, heel 2025 validatie,
januari–september 2026 onafhankelijke test” is **niet verenigbaar** met de bestaande
registraties: 15–16 januari 2025 is al gereserveerd als onafhankelijke test voor
BTC/EUR en ETH/EUR. Ook is januari 2025 gedeeltelijk eerder bekeken. Kalenderjaren
laten bovendien geen vier uur embargo tussen validatie en test over.

Dit voorstel legt beslisregels, uitsluitingsregels, benchmarks en meetconventies
vast, maar bevat geen verzonnen corpus- of rapporthashes. Na goedkeuring volgen
uitsluitend de hieronder beschreven implementatie- en data-auditstappen. Een
uitvoerbaar manifest met echte hashes en aantoonbare toestemming blijft verplicht
vóór de eerste rendementsberekening. Bestaande beperkte runners worden niet omzeild.

## 2. Bestaande registraties en eerdere inzage

Alle intervallen zijn halfopen `[start, eind)` in UTC. Datum zonder tijd betekent
00:00 UTC; lokale zomertijd speelt bij onderzoek geen rol.

| Bestaand plan | Munten | Ontwikkeling | Validatie | Onafhankelijke test |
|---|---|---|---|---|
| phase4b_smoke | BTC/EUR | 2025-01-10 → 2025-01-11 | 2025-01-12 → 2025-01-13 | 2025-01-15 → 2025-01-16 |
| phase5_smoke | BTC/EUR, ETH/EUR | 2025-01-10 → 2025-01-12 | 2025-01-13 → 2025-01-14 | 2025-01-15 → 2025-01-16 |

De fingerprints zijn respectievelijk
`abcdf19dac30fe1423b7aacd1de11313a495373af460923a78cf96e3c28695d4` en
`af69653d7015072bec3b75c5b4e19a0328d382f48490d1aa7cc81b22177d5a86`.
Beide artefacten melden dat de onafhankelijke test niet geopend is. De gereserveerde
validatievensters worden niet automatisch als onaangeraakt of als vrijgegeven beschouwd.

| Bekende eerdere blootstelling | Classificatie |
|---|---|
| BTC/EUR 1h, 2024-12-31 → 2025-01-01 | Officiële archieffixture, reeds bekeken; alleen ontwikkeling |
| BTC/EUR en ETH/EUR 15m/1h/4h, 2025-01-10 → 2025-01-11 | Geïmporteerd, gevalideerd en in technische tests gebruikt |
| BTC/EUR en ETH/EUR 4h vanaf 2025-01-05 16:00 tot 2025-01-11 | Eerdere fase-3-indicatorhistorie |
| BTC/EUR en ETH/EUR 1h vanaf 2025-01-09 16:00; 15m vanaf 2025-01-10 16:00; beide tot 2025-01-11 | Eerdere publieke API-imports |
| BTC/EUR mogelijke warm-up vanaf 2025-01-05 04:00 | Afgeleid uit fase-4B-script; tijdelijke database niet hersteld |
| BTC/EUR 2026-01-01 → 2026-01-02, CLI-fixture | Synthetisch, geen inzage in echte Binance-testdata |

`experiments/phase6b_preregistration_audit.json` blijft het eerdere bewijsstuk.
De vier toen aanwezige projectdatabases onder `/tmp` bestaan in de huidige omgeving
niet meer. Hun afwezigheid is geen nieuwe bevestiging van hun oude inhoud en geen
bewijs dat elders geen onderzoek plaatsvond. De huidige broncontrole en exacte
bestands-/codehashes staan in `experiments/phase6b_proposal_sources_20261027.json`.
Geen oud plan of oud resultaat is overschreven.

**Nog te bevestigen:** eerdere inzage buiten deze repository/omgeving. Neem vóór
uitvoering handmatige inzage, andere projecten en eventuele externe registers op
in een duurzaam append-only inzageregister. Tot die bevestiging wordt 2026 alleen
“kandidaat-holdout; onafhankelijkheid niet bewezen” genoemd. Ook de keuze van de
huidige zes munten in 2026 beperkt elke claim van historisch prospectief onderzoek.

## 3. Aanbevolen perioden, warm-up en grenzen

| Onderdeel | Exact UTC-interval | Gebruik |
|---|---|---|
| Ontwikkeling D | `[2024-01-01 00:00, 2025-01-01 00:00)` | Technische en beschrijvende evaluatie, geen parameterselectie |
| Eerste warm-up D | `[2024-01-01 00:00, 2024-01-08 00:00)` | Cash behouden; geen instap; onderdeel van D |
| Quarantaine | `[2025-01-01 00:00, 2025-02-01 00:00)` | Geen rendementsevaluatie; onderstaande warm-up is de enige nieuwe datatoepassing |
| Validatie-warm-up | `[2025-01-25 00:00, 2025-02-01 00:00)` | Alleen kenmerken en toelating; geen rendement of orders |
| Validatie V | `[2025-02-01 00:00, 2025-12-31 20:00)` | Primaire historische evaluatie, eenmaal met bevroren regels |
| Embargo V/T | `[2025-12-31 20:00, 2026-01-01 00:00)` | Geen rendementsevaluatie of open positie uit V |
| Kandidaat-test T | `[2026-01-01 00:00, 2026-10-01 00:00)` | Gesloten; afzonderlijke expliciete toestemming nodig |
| Voorlopige warm-up T | `[2025-12-25 00:00, 2026-01-01 00:00)` | Alleen na afzonderlijke testvrijgave; geen nieuwe trades |

De bestaande test `[2025-01-15, 2025-01-16)` blijft ook uitgesloten van warm-up.
Pas in dit nieuwe voorstel dat slot conservatief op alle zes paren toe; het oude
plan zelf blijft ongewijzigd. Download later voor januari-2025-warm-up alleen de
expliciete dagelijkse bestanden van 25–31 januari, niet het volledige maandarchief.
De HEAD-controle van het januari-maandobject heeft geen candle-inhoud gelezen.

Het nieuwe plan staat los van de oude smoke-plannen; het herlabelt hun perioden
niet. D en V starten ieder één gezamenlijke €200-portefeuille, zonder posities of
pauzes uit de andere deelstudie. Rapporteer D en V afzonderlijk; tel hun resultaten
niet op als één doorlopende investering. Binnen elke deelstudie blijven cash,
verliesreeksen, drawdown, fees en reserves ononderbroken bestaan, ook bij jaar-,
maand-, coin-, downloadbatch- of proceswissels.

**Tijdregels:** evaluatie op elke 15m-UTC-grens `t`. Gebruik per timeframe precies
32 afgesloten candles tot `floor_tf(t)`; herbereken EMA en Wilder op dat vaste
venster zoals de bestaande code doet, niet op een later gekozen langere historie.
De scanner gebruikt eveneens 32 afgesloten 1h-candles en een TTL van 3600 seconden.
De zeven dagen toelatingshistorie veranderen de indicator-lookback niet. Een
kandidaat gebruikt alleen informatie beschikbaar uiterlijk op `t`; fill op open
N+1, nooit op close N. De onmiddellijke beschikbaarheid bij candle-close en fill
op de aansluitende open is een expliciete idealisering, geen gemeten latency.

De bestaande ExitAgent beoordeelt elke volledig afgesloten 15m-bar. Een tijdexit
gebruikt de open van de eerste bar met `opened >= deadline`, maar wordt pas bij
haar close geboekt. Reserveer daarom **4 uur plus 15 minuten** tot het periode-einde:
laatste nieuwe instap `t <= eind − 4h15m`. De reguliere vieruurshorizon en
conservatieve exitregels veranderen niet. Houdduur gebruikt de audit-tijdstempels;
OHLCV levert geen exact intrabar-filltijdstip. Geen nieuwe entry in dezelfde batch
waarin een bestaande positie sluit. Eindcontrole/exits op `eind` mogen alleen de
laatste binnenliggende afgesloten bar gebruiken; geen candle vanaf `eind` lezen.

Bij ontbrekende terminale exitdata/ongeldige verkoopfilters: positie niet fictief
liquideren. Markeer de studie als onvolledig en de primaire uitkomst als niet
betrouwbaar bepaalbaar. Er komt geen willekeurige cash-reset of gunstige eindprijs.

## 4. Datadekking onderzocht zonder handelsuitkomsten

Bron: uitsluitend `https://data.binance.vision/data/spot/monthly/klines/`.
`experiments/phase6b_coverage_metadata_20261027.json` bewaart alle URL's, methode,
HTTP-status, controletijd en relevante responseheaders. De controle liep op
27 oktober 2026, 00:34–00:35 Europe/Brussels (26 oktober 23:34–23:35 UTC).

| Paar | 2024: ZIP 15m / 1h / 4h | 2025: ZIP 15m / 1h / 4h | CHECKSUM-objecten | Bewijsniveau |
|---|---|---|---|---|
| BTC/EUR | 12 / 12 / 12 maanden HTTP 200 | 12 / 12 / 12 HTTP 200 | Alle 72 HTTP 200 | Bestandsmetadata |
| ETH/EUR | 12 / 12 / 12 maanden HTTP 200 | 12 / 12 / 12 HTTP 200 | Alle 72 HTTP 200 | Bestandsmetadata |
| SOL/EUR | 12 / 12 / 12 maanden HTTP 200 | 12 / 12 / 12 HTTP 200 | Alle 72 HTTP 200 | Bestandsmetadata |
| XRP/EUR | 12 / 12 / 12 maanden HTTP 200 | 12 / 12 / 12 HTTP 200 | Alle 72 HTTP 200 | Bestandsmetadata |
| ADA/EUR | 12 / 12 / 12 maanden HTTP 200 | 12 / 12 / 12 HTTP 200 | Alle 72 HTTP 200 | Bestandsmetadata |
| LINK/EUR | 12 / 12 / 12 maanden HTTP 200 | 12 / 12 / 12 HTTP 200 | Alle 72 HTTP 200 | Bestandsmetadata |

864 HEAD-verzoeken: 432 ZIP-objecten en 432 checksum-objecten, allemaal HTTP 200.
Vooraf waren twee HEAD-probes op BTCEUR en LINKEUR 1h januari 2024 eveneens 200:
in totaal 866 netwerkverzoeken, uitsluitend responseheaders. Geen ZIP/CSV-body,
checksumwaarde, prijs, volume, signaal of rendement uit deze nieuwe objecten gelezen.
Geen verzoeken voor 2026, geen actuele exchangeInfo als historisch bewijs gebruikt.

**Beperkingen:** archiefaanwezigheid bewijst geen volledige maanddekking, juiste
checksum, liquiditeit, eerste listingdatum of destijds geldige orderfilters.
Last-Modified/ETag bewijzen geen oorspronkelijke publicatietijd; ETag is geen
SHA-256. De huidige checksum kan een achteraf gereviseerde dataset bevestigen.
Geen paar wordt op basis van HEAD alleen toegelaten en geen ontbrekende handelsdag
wordt als bewezen afwezig geïnterpreteerd. De oude zeven lokale ZIP-fixtures zijn
wel opnieuw door de bestaande automatische tests gevalideerd.

Reproductie van de metadata-inventaris, zonder backtest:

```bash
.venv/bin/python scripts/phase6b_coverage_metadata.py /tmp/phase6b-new-metadata.json
```

Het script weigert een bestaand uitvoerbestand, volgt geen redirects en vraagt
uitsluitend de vaste 2024/2025-objecten op. Een latere controle kan door bronwijzigingen
andere metadata geven; het oorspronkelijke bewijsbestand blijft behouden.

## 5. Toelating, liquiditeit en datakwaliteit

Vaste, niet op rendement geselecteerde watchlist, alfabetisch in het manifest:
`ADAEUR, BTCEUR, ETHEUR, LINKEUR, SOLEUR, XRPEUR`. Geen substitutie door andere
munten en geen uitsluiting van een hele munt/jaar wegens later tegenvallende data.
Het is een door de gebruiker gekozen hedendaagse groep, geen reconstructie van
alle destijds beschikbare EUR-paren. Delistings en verdwenen niet-geselecteerde
munten ontbreken: **survivorship- en universumselectiebias blijven aanwezig**.
Conclusies gelden uitsluitend voor dit vaste universum en deze periode.

Aanbevolen objectieve toelatingsregels op ieder beslismoment `t`:

1. Uitsluitend officiële Spot-candles van het exacte EUR-paar. Geen USDT-proxy,
   futures, synthetische EUR-conversie, forward-fill of samenvoeging van exchanges.
   Een paar mag nooit vóór zijn eerste aantoonbare historische handel worden
   geselecteerd. Vereis 168 opeenvolgende volledige 1h-candles in de voorafgaande
   zeven dagen, overeenkomende 672 15m-candles en de relevante volledige 4h-bars.
   Een eerste archiefmaand is geen listingdatum. Ontbrekende eerdere listingkennis
   blijft expliciet onzeker; candles bewijzen hoogstens eerdere transacties.
2. Verifieer SHA-256 van elk ZIP tegen het officiële CHECKSUM vóór CSV-verwerking;
   log URL, checksum-URL, verwachte/werkelijke hash, UTC-importtijd, bereik, eenheid,
   aantallen, bronversie en validatiestatus. Oude cache nooit stilzwijgend vervangen.
   Alle 12 Binance-klinevelden valideren. Vanaf 2025 Spot-microseconden; daarvoor
   milliseconden volgens bronformaat, exact naar UTC zonder floats. Weiger gemengde
   eenheden, verkeerde grenzen, dubbele/verkeerd geordende of onafgesloten candles,
   niet-eindige/negatieve waarden en OHLC-inconsistentie. Zero-volume is geen
   datacorruptie, maar kan wel een liquiditeitsafwijzing veroorzaken.
3. Vergelijk elke beschikbare officiële 4h-candle met precies vier volledige
   officiële 1h-candles: open eerste, high maximum, low minimum, close laatste,
   volumes/trades opgeteld. Geen gedeeltelijke aggregatie. Vergelijk ook 15m→1h.
   Afwijking blokkeert het betrokken venster; geen keuze voor de gunstigste bron.
4. Voor toelating: som quotevolume van de laatste 24 afgesloten 1h-candles
   **minimaal €100.000**, en quotevolume van de laatste afgesloten 15m-candle
   **minimaal €10.000**. Beide worden uitsluitend achterwaarts berekend.
   Deze nieuwe onderzoeksfilters zijn een vooraf voorgestelde conservatieve
   liquiditeitsaanname: de maximale initiële €100-exposure is daarmee hoogstens
   0,1% respectievelijk 1% van dat vroegere volume. Geen bewijs van orderboekdiepte
   of van de liquiditeit tijdens de toekomstige fill. Geen omzetdrempel afstemmen
   op uitkomsten; wijziging vereist een nieuwe, vooraf goedgekeurde protocolversie.
5. Voor orders uitsluitend historische `SpotFilters(status='validated')` met
   officiële bron, `known_at <= t` en `valid_from <= t < valid_until`. Toets
   PRICE_FILTER, LOT_SIZE, MARKET_LOT_SIZE, MIN_NOTIONAL/NOTIONAL, marktorderflags
   en alle relevante ondersteunde regels. Ontbrekende waarden, onbewezen historische
   geldigheid of vereiste gemiddelde notionalprijzen: **afwijzen**, niet aanvullen
   met actuele filters. Niet ondersteunde verplichte filters blokkeren eveneens.
   Controleer filters opnieuw bij fill én exit. Geen goedkeuring op basis van
   uitsluitend de statusvlag zonder inhoudelijk geverifieerde bron.

Regel 4 en de strengere metadata-eis van regel 5 zijn **voorgestelde nieuwe
onderzoeksvoorwaarden**, geen reeds aanwezige fase-6A-functionaliteit. Ze wijzigen
de hypotheseformule niet, maar kunnen signalen uitsluiten; expliciete goedkeuring
is daarom onderdeel van het voorstel. Er is nu geen filtercode gewijzigd.

Er is nog geen volledige historische filterreeks aangetoond. De aanbevolen primaire
opzet blijft daarom streng: geen aantoonbare filters betekent geen uitvoerbare
kandidaat en mogelijk nul trades. Dat is onvoldoende bewijs, niet een bewezen
nulrendement van de strategie. Een afzonderlijke studie met aangenomen filters
vereist eerst een exact gedateerde filtertabel en afzonderlijke toestemming;
zij is **niet** impliciet toegestaan of onderdeel van deze primaire studie.

**Vast universum behouden:** alle zes coins blijven in de scanner en UTC-tievolgorde.
Ontbrekende essentiële analyses van één coin blokkeren conform fase 6A nieuwe
instappen voor de hele batch. Geldige analyses met een inhoudelijk conflict of
onvoldoende liquiditeit/ordermetadata maken die coin ongeschikt; andere volledig
beoordeelde kandidaten kunnen doorgaan. Een voorheen niet beschikbaar paar wordt
niet achteraf uit het universum verwijderd om toch te kunnen handelen. Dat kan
lange cashperioden veroorzaken en wordt als beperking gerapporteerd.

**Gaten:** kwaliteit uitsluitend beoordelen op informatie tot `t`, geen maand
vooraf verwijderen wegens een gat dat pas later optreedt. Flat plus datagat:
geen entry; hervatten pas na opnieuw zeven dagen volledige toelatingshistorie.
Cash en risicopauzes blijven staan. Datagat in de coin van een open positie:
stop de run met `incomplete_held_position_data`; geen verkoop tegen laatst bekende
prijs, ontbrekende stop negeren of achteraf weer vlak starten. Reeds berekende
prefixen worden als gecensureerd gelogd, niet als een volwaardige periodeprestatie.
Een fout kan pas tot een nieuwe run leiden na gedocumenteerde correctie, nieuw
manifest en zichtbare eerdere inzage; geen selectief verbergen van mislukte runs.

## 6. Strategie, portefeuille en uitvoering

| Instelling | Voorgestelde bevroren waarde |
|---|---|
| Primair | aligned_trend; bullish 1h-regime en alle 15m/1h/4h EMA-richtingen omhoog |
| Overige hypotheses | regime_momentum en sideways_recovery blijven bestaan, worden in dit plan niet uitgevoerd of gekozen |
| Indicatoren | EMA 9/21; RSI 14; ATR 14; momentum 10; structuur 5; sideways 0,002 |
| Indicatorvenster | Steeds 32 volledige candles per timeframe; bestaande EMA/Wilder-seeding |
| Analyseconflicten | Bestaande DecisionAgent-regels; missing/stale/uncertain essentiële data → HOLD |
| Nieuws | NoNews; unknown, nooit positief bewijs; geen nieuwe sentimentbron |
| Startkapitaal | Eén €200-ledger per deelstudie/scenario; geen €200 per munt |
| Posities | Long Spot, geen leverage; maximaal één open positie |
| Risicobudget | Maximaal 0,5% van min(€200, actuele cash), inclusief entry- en stop-exitkosten |
| Exposure bij entry | Maximaal 50%; geen automatische verhoging of herkapitalisatie |
| Bescherming | Dagverlies 3%, drawdown 10%, verliesreeks 3, noodstop; bestaande strengere instellingen blijven geldig |
| Entry | Voorstel met laatste afgesloten 15m-close; uitvoering uitsluitend volgende open na Risk Engine |
| Stop/horizon | 2 × ATR(14) op 1h; deadline +4h; geen winsttarget |
| Kosten per zijde | Fee 0,001; slippage 0,001; volledige spread 0,001 (halve spread per zijde) |
| Numeriek | Decimal-precisie 28; ongunstige tickafronding; quantity omlaag naar gecombineerde lotstap; fee omhoog op €0,00000001 |

De scanner heeft vier gelijke ranggewichten: trend, momentum, lagere volatiliteit
en EUR-quotevolume, elk 25%. Gebruik de bestaande percentielrang inclusief halve
punten bij ties en 32h-lookback. Sorteer kandidaten op score dalend. Bij gelijkheid:
alfabetische vaste zesmuntenlijst cyclisch verschuiven met
`floor(UTC_epoch_seconds(t)/900) modulo 6`. Beoordeel in die volgorde; eerste geldige
kandidaat krijgt cash-, risico-, exposure- en positieplaatsreservering. Bewaar alle
scores, bijdragen, afwijzingen en ties. Geen muntvoorkeur via aankomstvolgorde.

Risk Engine beslist altijd, agents kunnen niet uitvoeren. Gebruik de bestaande
fillsimulator/ledger en atomische deduplicatie. Bij ongunstige open boven de
cashreservering: afwijzen, niet bijstorten of op basis van de nieuwe prijs een
andere coin selecteren. `buy_price = ceil_tick(open × (1 + spread/2 + slippage))`;
`sell_price = floor_tick(raw_exit × (1 − spread/2 − slippage))`.
Fee op iedere zijde apart naar boven afronden. Spread/slippage zitten al in fillprijs;
niet opnieuw als extra fee aftrekken.

Stopgap: `min(open, stop)` vóór ongunstige verkoopimpact. Als stop én target in
een candle mogelijk zijn: stop eerst/ambigu label, hoewel dit plan geen target
heeft. Bestaande veiligheidsstops krijgen hun bestaande conservatieve prioriteit.
Geen nauwkeurige intrabarroute of gedeeltelijke fills claimen. De 3%-dagpauze
vervalt uitsluitend volgens de bestaande UTC-dagwissel; 10%-drawdown, noodstop en
verliesreekspauze worden niet door coinwissel, batch of dag kunstmatig vrijgegeven.
Een resterende verliesreekspauze kan de rest van de deelstudie blokkeren.

## 7. Vooraf vastgelegde benchmarks

Elke benchmark start afzonderlijk met **in totaal €200**. Het zijn vergelijkings-
experimenten, geen extra geld binnen de strategie. Geen reset per coin of maand.
Rapporteer steeds zowel bruto markteffect als netto na de benoemde kosten; de
primaire vergelijking gebruikt netto. Geen rente, belasting, staking of EUR/FX-winst.

### A. Cash

Gedurende exact D respectievelijk V €200 EUR-cash, geen rente/kosten, geen trades.
Rendement en drawdown zijn per definitie nul, exposure nul; trade-afhankelijke
maten zijn niet van toepassing. Dit is een benchmarkdefinitie, geen nu uitgevoerde
historische uitkomst.

### B. Gelijkgewogen buy-and-hold-marktindex

Een afzonderlijke **analytische marktindex**, geen orderroute door JointPortfolio.
Zes vaste allocaties van €200/6; rest-EUR blijft cash. Eén aankoopmoment: D op
2024-01-08 00:00 UTC, V op 2025-02-01 00:00 UTC, met uitsluitend vooraf gesloten
candles voor historische beschikbaarheid, kwaliteit en liquiditeit. Een component
die dan niet voldoet aan regels 1–4 uit §5 blijft de gehele periode cash; geen
latere vervanger, instap of herverdeling over overlevers. Geen filter op het later
bekende eindrendement of op toekomstige datadekking.

Per toegelaten component budget `b = 200/6`, koopimpactprijs
`p = open × (1 + spread/2 + slippage)`. Begin bij `q = floor_step(b / (p × (1 + feepercentage)))`, met vaste
hoeveelheidstap 0,000000000001 coin. Verlaag q zo nodig telkens één stap totdat
`q × p + ceil_0,00000001(q × p × feepercentage) <= b`. Bewaar alle
ongebruikte fracties als centrale EUR-cash. Dit is uitsluitend rekenprecisie voor de index, geen
verzonnen Binance LOT_SIZE. Geen beurs-tickafronding of minimumorderfilters in
steekproefselectie van deze theoretische index; dat verschil expliciet tonen.
Gebruik dezelfde fees, spread en slippage als de strategie, in hetzelfde scenario.
Geen herweging, stop, tijdexit of risicolimieten in deze marktindex.

Waardeer op elke afgesloten 15m-close; eindwaarde op de laatste close vóór `eind`
minus hypothetische verkoopimpact en fee. Dit is een terminale waardering, geen
claim van een uitvoerbare order op die close. Ontbrekende koers van aangehouden
component: index onvolledig, niet achteraf verwijderen/herwegen. Noteer eventuele
listing-/delistingproblemen en gecensureerde dekking.

De index kan zes componenten en bijna 100% exposure hebben, kent geen stop en
geen 0,5%-risicobudget. Het verschil met de strategie is dus mede marktblootstelling.
Dat wordt naast rendement gerapporteerd; hogere/lager uitkomst bewijst geen alpha.
Er wordt geen Risk Engine uitgezet om deze index te berekenen en geen productie-
of onderzoekspositielimiet verhoogd. De bestaande geïsoleerde buy-and-hold-runner
wordt hiervoor niet gebruikt.

### C. Eenvoudige EMA-trendstrategie met gezamenlijke ledger

Dezelfde zes munten, toelatingsregels, 15m-beslisgrenzen, warm-up, periodegrenzen,
€200, één positie, kosten, filters, stops, horizon, reserve-/risicocontroles en pauzes.
Enig directioneel instapcriterium: op de laatst afgesloten 1h-candle
`EMA9 / EMA21 − 1 > 0,002`, berekend over dezelfde vaste 32 1h-candles.
Dit is een toestand, geen verplicht nieuw kruisingsmoment. Geen regime-, RSI-,
nieuws- of multi-timeframe-instapfilter. De overige marktgegevens moeten wel
volledig zijn voor dezelfde toelatings- en risicocontroles.

Bij meerdere kandidaten: hoogste 1h-EMA-gap eerst, bij gelijkheid dezelfde vaste
UTC-rotatie. Geen scannergewicht op momentum/volatiliteit als extra signaal.
Instapgrootte en initiële stop uit dezelfde ATR14(1h) en Entry/Risk-rekenregels.
Exit volgens dezelfde veiligheidsstop, stop en vieruurshorizon; geen extra EMA-
omkeerexit. Na exit opnieuw beoordelen vanaf de volgende batch, nooit onmiddellijk
herinstappen in dezelfde batch. Een bearish EMA sluit niet eerder dan de vaste
exitregels. Alle geweigerde benchmarkorders en redenen worden eveneens opgeslagen.

Dit specificeert de oude eenvoudige EMA-hypothese nu op portefeuilleniveau. Een
aparte geteste onderzoeksinterface is nodig; geen kunstmatig geldig full-agentbericht
maken om de bestaande DecisionAgent te omzeilen. De kosten-/risicosimulator blijft
hetzelfde. De marktindex is een exposurevergelijking; deze EMA-benchmark is de
vergelijking met dezelfde portefeuillerisicoregels.

## 8. Uitkomsten en statistische interpretatie

**Primair:** netto portefeuillerendement na alle kosten op V,
`100 × (eind_liquidatie_equity / 200 − 1)`; ook het verschil in EUR tonen.
D is beschrijvend/technisch. De primaire hypothese wordt niet geselecteerd op
D of V en de oude `selection=net_expectancy_after_costs_then_lower_drawdown`
wordt in dit aparte protocol niet gebruikt als optimizer. Dit is een expliciete
protocolafwijking in uitkomstprioriteit; het oude ResearchPlan blijft ongewijzigd.

| Secundaire maat | Exacte conventie |
|---|---|
| Trades | Aantal volledig gesloten round trips; orders/afwijzingen zijn geen trades |
| Winrate | `aantal net > 0 / aantal gesloten`; break-even telt in noemer maar niet als winst |
| Gemiddelde winst/verlies | Gemiddelde netto-P&L van positieve / negatieve trades; verlies als negatief bedrag |
| Verwachtingswaarde | Som netto-P&L / gesloten trades; geen voorspelde kans |
| Profit factor | Som positieve P&L / absolute som negatieve P&L; zonder verliezen `niet eindig/geen verliezen`, bij geen trades `n.v.t.` |
| Drawdown | Maximale `(lopende piek − liquidatie_equity) / lopende piek`, piek begint op €200 |
| Houdduur | Gemiddelde audit-exittijd − instaptijd; intrabar-tijd onbekend, resolutie 15m |
| Tijdsexposure | Som audit-houdduur / gehele deelperiode; cashpauzes en eerste D-warm-up blijven in noemer |
| Kapitaalexposure | Tijdgewogen gemiddelde en maximum bruto positiewaarde / bruto equity op 15m-close |
| Per coin | Trades, netto-P&L, fees, winrate, expectancy, houdduur, tijdsexposure; P&L-bijdrage ook / €200 |
| Per maand | Verschil liquidatie-equity maandgrenzen binnen dezelfde ledger; geen maandelijkse €200-reset |
| Afwijzingen | Aantal per coin, tijdstip en exacte reden, met oorspronkelijke agent- en centrale afwijsreden |

Sla de volledige 15m-close-equitycurve op, inclusief nul-activiteit/cashperioden.
Liquidatie-equity omvat hypothetische exitkosten, bruto equity niet. Toon naast de
close-drawdown ook de bestaande conservatieve low-gebaseerde risico-drawdown;
noem beide expliciet, vermeng geen intrabar-low met alleen close-benchmarkmetingen.
Low-observaties geven geen kennis van een exacte prijsroute. Posities en per-coin
P&L moeten met het gezamenlijke ledger reconciliëren. Geen afzonderlijke €200-
coinrendementen optellen. Bij nul trades: werkelijke volledige equitycurve kan
€0 P&L tonen, trade-afhankelijke maten blijven n.v.t.; dat is geen toets van edge.
Bij een onvolledige run blijven primaire rendementen niet betrouwbaar bepaalbaar.

**Kleine steekproef:** minder dan 30 gesloten trades op V betekent altijd
`onvoldoende bewijs`; hetzelfde geldt voor claims per coin met minder dan 30
trades. Ook boven 30 is onafhankelijkheid niet gegarandeerd. Rapporteer aantal
kalenderdagen, dagen met exposure, regimes, concentratie en pauzeduur.
Gecorreleerde coins, overlappende signalen en opeenvolgende trades leveren geen
extra onafhankelijke experimenten op. Een positieve point estimate, profit factor
boven 1 of een gewonnen benchmarkvergelijking is geen bewijs van superioriteit.

**Meervoudig toetsen:** precies één primaire strategie; geen selectie uit drie
hypothesen × zes coins. Cash, marktindex en EMA zijn drie vooraf benoemde beschrijvende
vergelijkingen. Per-coin, maanden, kostenstress en outlierdiagnoses zijn secundair,
niet alsnog primaire succescriteria. Toon alle uitkomsten, ook ontbrekende/negatieve,
en tel alle uitgevoerde runs/versies mee in het inzageregister. Oude experimenten
verdwijnen niet uit de onderzoeksgeschiedenis.

Aanbevolen inferentiebeleid voor deze fase: **geen p-waarden, significantieclaims
of statistische promotie**. De oude Bonferroni-familie blijft bij haar eigen plan;
ze verleent dit nieuwe portfolio-onderzoek geen nominale alpha of vrijbrief om
achteraf een gunstige vergelijking te kiezen. Voor formele superioriteitsclaims
is een afzonderlijk vooraf goedgekeurd analyseplan nodig met de hele studiefamilie,
correctie voor de drie vergelijkingen/andere runs, block-bootstrap of gelijkwaardig
voor afhankelijkheid en werkelijk onafhankelijke bevestiging. Die uitbreiding
is niet impliciet opgenomen en de huidige holdout blijft dicht. Het resultaat
van deze fase kan dus beschrijvend en reproduceerbaar zijn, zonder statistisch
bewijs van winstgevendheid te leveren.

## 9. Vaste gevoeligheidsanalyses

Geen parametergrid; onderstaande drie scenario's, allemaal rapporteren, nooit de
beste kiezen. Voor elke strategie/benchmark dezelfde scenariokosten:

| Scenario | Fee per zijde | Volledige spread | Slippage per zijde |
|---|---:|---:|---:|
| Baseline | 0,001 | 0,001 | 0,001 |
| Slippage-stress | 0,001 | 0,001 | 0,002 |
| Alle kosten dubbel | 0,002 | 0,002 | 0,002 |

Hersimuleer later vanaf exact dezelfde €200, brondata, toelating, indicatoren,
prioriteitsregels en signalen. Herbereken positieomvang en risicotoetsen met de
hogere kosten; gewijzigde fills, afwijzingen, pauzes en trade-aantallen zijn onderdeel
van de uitkomst. Geen baseline-trades simpelweg herprijzen en dat een nieuwe
portefeuillesimulatie noemen. Cashbenchmark blijft cash. Indexhoeveelheden worden
per scenario opnieuw uit hetzelfde budget bepaald. Strategieparameters blijven gelijk.

Daarnaast alleen rekenkundige concentratiediagnoses op de gesloten **baseline**-
trades: verwijder afzonderlijk de maximaal drie grootste positieve netto-P&L's;
verwijder afzonderlijk de maximaal drie meest negatieve netto-P&L's. Sorteer bij
exact gelijke bedragen op exit-UTC, coin, entry-ID. Als er minder dan drie zijn,
gebruik alle betreffende trades en rapporteer hun aantal. Toon som netto-P&L
voor/na en verschil gedeeld door €200. Geen hersimulatie, geen nieuwe drawdown of
haalbare rendementclaim: cash-/pauze-effecten van weggelaten trades ontbreken.
Geen winnaar/verliezer uitkiezen met een achteraf aangepast aantal. Vermeld beide
diagnoses ook wanneer ze de conclusie verzwakken.

## 10. Uitvoering, registratie en nog noodzakelijke implementatie

Dit document is bewust geen vals uitvoerbaar manifest. De bestaande ResearchPlan
vereist drie data-/rapporthashes en kent andere primaire selectievelden; de
JointPortfolio/DecisionAgent/ResearchExecutionEngine laten uitsluitend ontwikkeling
tot 192 candles per coin toe. De dagelijkse archiefadapter verwerkt maximaal zeven
bestanden per verzoek. De nieuwe HEAD-inventaris maakt hem niet automatisch tot
maandimporter of jaarbacktestrunner. De primaire strenge historische filters,
liquiditeitsregels, gezamenlijke EMA-benchmark en analytische marktindex zijn nog
geen geïmplementeerde evaluatieworkflow.

Vereiste volgorde, pas na expliciete goedkeuring:

1. Bevestig de keuzes in §11; leg dit voorstel, goedkeuringsreferentie en codecommit
   onveranderlijk vast in een nieuw, gescheiden protocolregister. Consolidatie van
   eerdere inzage gaat vóór claims over onafhankelijkheid. Geen fictieve nulhash
   invullen om de oude ResearchPlan-validator tevreden te stellen.
2. Bouw en test een afzonderlijk onderzoeksmanifest met expliciete `locked`
   teststatus en aanvankelijk ontbrekende testdatahashes. Een testdeel mag zijn
   hashes pas krijgen na afzonderlijke vrijgave. Bestaande registraties blijven
   geldig; goedkeuring van D/V verleent geen toegang tot T. Controleer slots ook
   op download-, warm-up-, dataset-, rapport- en evaluatieniveau.
3. Test de benodigde lange replay, chronologische deelperioden, centrale ledger,
   historische toelating, metrics en benchmarks uitsluitend met deterministische
   fixtures. Geen renaming van validatie naar ontwikkeling en geen per-coin-ledgers
   als vervanging voor gezamenlijke uitvoering. Eén writer, transacties, hashketen
   en expliciete dataset-/reportvolgorde moeten herstartbare uitkomsten geven.
4. Verzamel daarna alleen goedgekeurde D/V- en warm-updata in begrensde dagelijkse
   batches (maximaal zeven per adapterverzoek), met caching en een downloadbudget
   van exact de vastgelegde paren, dagen en intervallen. Geen maanddownload die een
   beschermd venster bevat. De historische kwaliteits-/filteraudit mag uitsluitend
   deze datakwaliteitsregels toepassen; geen signalen/rendementen bekijken om grenzen
   of liquiditeitsdrempels aan te passen. Onvoldoende bewijs blijft onvoldoende.
5. Bevries het corpusmanifest vóór uitkomstberekening: codecommit, dependencyversies,
   Decimal-context, protocolhash, alle officiële SHA-256's, bron-/importtijden,
   gescheiden warm-up/evaluatiedekking, filterbewijzen, uitsluitingslog en hashes
   van de exacte toegestane rapportbundels. Het mechanisch hashen van data/rapporten
   is geen toestemming voor menselijke inspectie van validatiesignalen of resultaten.
6. Controleer alle locks en hashbindingen. Registreer toestemming, run-ID, stage,
   dataversies en bekeken bereiken duurzaam **vóór** berekening; een mislukte run
   telt als inzage zodra relevante data/resultaten toegankelijk zijn geweest.
   Maak iedere herhaling zichtbaar, ook na een bugfix. Geen parameterbijstelling.
7. Voer uitsluitend de expliciet toegestane D/V-runs/scenario's uit, bewaar alle
   rejections, orders/fills, per-coinbijdragen, equitycurves en auditlog. Vergelijk
   identieke heruitvoeringen inclusief herstart, met apart niet-deterministisch
   wallclock-auditveld. T blijft gesloten; geen automatische vervolgfase.

## 11. Openstaande goedkeuringskeuzes en conflicten

| Keuze/conflict | Aanbevolen besluit vóór implementatie/evaluatie |
|---|---|
| Heel 2025 als validatie overlapt oude test en inzage | Gebruik V vanaf 1 februari, eind 31 december 20:00; januari-quarantaine plus uitsluitend genoemde warm-up |
| 2026 onaangeraakt niet extern bewezen | Voorlopig reserveren, inzageregister aanvullen; apart expliciet toestemming vragen voor latere opening |
| Jaarbacktest en validatie niet ondersteund | Afzonderlijke geteste onderzoeksuitbreiding; geen omzeiling huidige checks |
| Zes huidige munten geven selectie-/survivorship bias | Vaste zes behouden, beperk claims; geen ex-post uitbreiding naar winnaars |
| Nieuwe liquiditeitsdrempels en strengere metadata | €100.000/24h, €10.000/laatste 15m en uitsluitend bewezen historische filters expliciet goedkeuren; geen aannamesarm automatisch toevoegen |
| Buy-and-hold wijkt af van positie-/risicolimiet | Analytische marktindex met expliciete exposureverschillen, buiten orderroutes |
| Oude selectiecriterium expectancy, nieuw primair rendement | Nieuw protocol: netto portefeuillerendement primair; geen optimizerselectie, oude plannen intact |
| Meerdere hypotheses/statistische claims | Alleen aligned_trend; overige hypotheses niet uitvoeren; beschrijvende vergelijkingen, onvoldoende bewijs waar toepasselijk |

Met deze aanbevolen besluiten zijn de keuzes inhoudelijk gespecificeerd; zij zijn
**nog niet aangenomen**. Ontbrekende historische metadata mag niet worden verzonnen
om het plan uitvoerbaar te laten lijken. Als bovenstaande voorwaarden geen valide
trades toelaten, rapporteer dat en laat risicogrenzen intact.

## 12. Verificatie van deze oplevering

`.venv/bin/python -m pytest -q`: **287 geslaagd, 0 mislukt**, één bestaande
Starlette/AnyIO-deprecationwaarschuwing. De bestaande lokale archieffixtures en
synthetische protocoltests zijn opnieuw gebruikt; geen echte onafhankelijke test
is hierdoor geopend. De HEAD-inventaris is afzonderlijk op aantal, unieke URL's,
methoden, host, perioden en response-bodytellers gecontroleerd.

Geen handelscode, bots, risicoconfiguraties, oude preregistraties of oude uitkomsten
gewijzigd. Alleen dit voorstel, bijbehorende metadata/bronbewijzen, het begrensde
HEAD-script en voortgangsdocumentatie toegevoegd/bijgewerkt. Geen performance-
resultaten, signalen of nieuwe prijsreeksen berekend. **Stop na commit/push;
wacht op expliciete goedkeuring vóór historische rendementsbacktests.**
