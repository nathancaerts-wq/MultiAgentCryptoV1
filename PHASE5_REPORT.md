# Fase 5 — Decision, Entry en Exit

Gebouwd vanaf `5838a350f3a9254646c4317fe42a3a5fb248db98` op 26 oktober 2026.
De werkmap was bij aanvang schoon. Alle bestaande agents, onderzoeksresultaten,
archieven en bots zijn behouden. Dit is een technische onderzoeksworkflow,
geen geactiveerde handelsstrategie.

## Onderdelen en scheiding

`crypto.trade_agents` bevat DecisionPolicy, DecisionAgent, EntryAgent en ExitAgent.
`crypto.research_execution` bevat ResearchTradingSession en ResearchExecutionEngine.
De session gebruikt de bestaande Message-contracten, Orchestrator, SQLiteStore,
ResearchPlan, QuantResearcher, RiskEngine en OfflineLedger/FillCosts/SpotFilters.

Een fase-3-rapport bindt Scanner, Regime, Technical, Multi-Timeframe en Sentiment
met bronvermelding, candlegrenzen en analyseparameters. De Decision Agent leest
deze vooraf geregistreerde snapshot. In de orchestrator is Decision afhankelijk
van die meegegeven analysesnapshot en Entry afhankelijk van Decision. Exit draait
zelfstandig, zodat een onbruikbaar instapsignaal de bewaking niet blokkeert.
Agents ontvangen kopieën en produceren alleen onderzoeksberichten.

`evaluate()` maakt beslissingen en afzonderlijke risicobeoordelingen. Het maakt
geen orders en voert geen fills uit. Alleen een expliciete Python-aanroep van
`session.execution.simulate(review_id)` kan een offline onderzoeksfill boeken.
Deze methode eist een opgeslagen, goedgekeurde beoordeling en het exacte
orchestratorbericht, controleert opnieuw risico en ledger, en schrijft uitsluitend
naar onderzoeksopslag. De paper-route `propose()` is op deze adapter geblokkeerd.
Er is geen muterende API-route, netwerkclient, API-sleutel of live uitvoering.

## Vooraf vastgelegde beslisregels — phase5-v1

| Uitkomst | Voorwaarden |
|---|---|
| BUY_CANDIDATE | Geen bestaande positie; geldige scannerselectie; alle essentiële analyses compleet, actueel en consistent; geen indicator- of timeframeconflict; vooraf gekozen hypothese eligible. |
| EXIT_REVIEW | Bestaande positie van deze coin; geldige, niet-conflicterende analyses met bearish 1h-regime. Uitsluitend een onderzoekswaarneming; geen automatische exit. |
| HOLD | Ontbrekende, ongeldige, verouderde of tegenstrijdige essentiële informatie, uncertain regime, bestaande positie zonder exitreview, of niet-passende hypothese. |

DecisionPolicy is immutable en wordt vóór evaluatie opgeslagen. Standaard wordt
`aligned_trend` getoetst. Alleen de drie bestaande hypotheses uit RESEARCH_PROTOCOL.md
zijn selecteerbaar, en uitsluitend als zij in ResearchPlan zijn opgenomen. Er is
geen automatische keuze van de beste variant, zoekgrid of aanpassing aan resultaten.
De aanvullende veiligheidsfilters maken fase-5-selecties niet identiek aan de
ruwe fase-4-hypotheseselecties. Bestaande backtests worden niet opnieuw geïnterpreteerd.

Het beslismoment moet een afgesloten UTC-15m-grens zijn. QuantResearcher controleert
de historische beschikbaarheid, TTL, indicatorparameters, timeframe-dekking en
consistentie. Aanvullend worden scanner-eindtijd, nieuwsitems, numerieke indicatoren
 en timeframeconflicten gecontroleerd. Elk besluit bevat bijdragen, ontbrekende
analyses, conflicten, hypothese, beleids-ID en bronbericht-ID; ook HOLD blijft zichtbaar.

Onbekend sentiment is een expliciete onzekerheid en levert geen positieve bijdrage.
Geen nieuwsitems is toegestaan als neutraal/onbekend, want de bestaande hypotheses
vereisen geen nieuws. Een ontbrekende sentimentmodule, ongeldige/toekomstige items
of een niet-onderbouwde positieve/negatieve classificatie blokkeert een instap.
Er is geen sentimentscore, voorspelde winstkans of LLM-aanroep.

## Instap, omvang en risico

Entry beoordeelt uitsluitend BUY_CANDIDATE. Referentie is de laatste afgesloten
15m-close; initiële stop is 2 × reeds bekende 1h-ATR onder die referentie, naar
beneden op tick afgerond. Deadline is vier uur na het beslismoment. De bestaande
hypotheses activeren geen target. De Exit Agent kan een vooraf aanwezige target
van een gesimuleerde positie wel bewaken; dat wordt met fixtures getest.

Het voorstel gebruikt Decimal en de bestaande ongunstige FillCosts-afronding:
standaard 0,1% fee per zijde, 0,1% volledige spread en 0,1% slippage per zijde.
Fee wordt naar boven op 0,00000001 EUR afgerond. Beide zijden kosten, de stopfill,
hoeveelheidsstappen, min/max-notional, marktorderfilters en saldo tellen mee.
Ook een initiële stopuitvoering die al niet aan de filters voldoet wordt afgewezen.

Startkapitaal is €200 per geïsoleerd experiment. Gepland risico is maximaal
0,5% van min(€200, beschikbare cash), dus aanvankelijk maximaal €1. Exposure blijft
maximaal 50%. Er is maximaal één positie per experiment; bestaande exposure
blokkeert een tweede instap. Verschillende coins hebben afzonderlijke experimenten;
de resultaten zijn geen gezamenlijke multi-coinportefeuille.

Een signaal op het sluiten van N kan pas op de open van N+1 simuleren. De instapkeuze
 en vooraf berekende hoeveelheid gebruiken nooit high/low/close van N+1. Bij de
werkelijke simulatie-open worden prijs, kosten, risico, filters en cash opnieuw
gecontroleerd; een ongunstige gap kan het voorstel alsnog ongeldig maken.

De bestaande RiskEngine.check blijft doorslaggevend. Hij heeft een optionele,
expliciete onderzoeks-evaluatieklok gekregen; standaard blijft de echte klok gelden.
De bestaande paper-ExecutionEngine weigert deze historische klok. Harde Limits
blijven ongewijzigd; alleen dit onderzoekspad gebruikt de strengere 0,5%-tradegrens.
De voorafgaande kostengevoelige controle en de ledger kunnen aanvullend weigeren.

3% dagverlies en 10% drawdown uit fase 4B blijven gelden. Dagverlies pauzeert tot
de volgende UTC-dag; drawdown tot het einde van het experiment. In de basiscode
bestond nog geen verliesreeksteller. Daarom voegt het bevroren onderzoeksbeleid
conservatief een pauze na drie opeenvolgende verliestrades toe (vooraf alleen
verlaagbaar naar één of twee). Deze pauze herstelt niet automatisch binnen de
sessie. Noodstop en onzekerheid verhinderen nieuwe instap. Een gap kan het werkelijk
verlies boven het geplande risico brengen; €1 is geen gegarandeerd maximaal verlies.

## Uitstap en boekhouding

Exit geeft EXIT_CANDIDATE of HOLD_POSITION met exacte reden. Het beoordeelt alleen
een reeds afgesloten 15m-candle van een virtuele onderzoekspositie. Volgorde:
expliciete noodstop/bestaande risicopauze, reeds bij open verstreken deadline,
stop, target, en een tijdens deze candle geconstateerde portefeuillelimiet.
Stop vóór target bij onbekende intrabarvolgorde; die uitkomst wordt ambigu genoemd.
Een stopgap gebruikt min(open, stop); een target krijgt geen gunstige gapverbetering.
Een veiligheidsliquidatie gebruikt conservatief de laagste candleprijs, plus kosten.

Een EXIT_REVIEW uit Decision verandert de vooraf vastgelegde stop/horizon niet.
Hierdoor wordt geen nieuw bearish-regime-exitgedrag aan de oude hypotheses toegevoegd.
Tijd- en stopvoorwaarden zijn vóór de candle bekend. Verwerking en audit vinden
bij candle-close plaats; een gebruikte intrabarprijs is een OHLC-simulatieaanname,
geen nauwkeurig gereconstrueerde uitvoering of achteraf uitvoerbaar live advies.

Voor een open positie moet iedere volgende afgesloten 15m-candle worden beoordeeld.
Overslaan, achteruit evalueren of doorgaan voorbij een nog niet afgehandelde
exitkandidaat wordt geweigerd. HOLD-waarnemingen bewaren waardering en risico-status;
zij zijn geen fills. Er is geen automatisch uitvoeringsproces.

RiskEngine.check_exit controleert hoeveelheden, bezit, filters en tijdstempels.
Risicoverlagende exits blijven mogelijk tijdens een noodstop of verliespauze.
Een geweigerde exit behoudt de positie. De ResearchExecutionEngine hercontroleert
het bezit, gebruikt de bestaande OfflineLedger.sell en kan nooit meer verkopen
dan de gehele aanwezige positie. Stabiele uitvoeringssleutels voorkomen dubbele fills.

Beginbalans, observaties, afwijzingen, fills, kosten en eindstaat zijn herleidbaar.
Ledger- en auditgegevens worden transactioneel in SQLite bewaard; daarna pas wordt
de geheugenstaat vervangen. Heropening herstelt Decimal-bedragen, positie, pauzes,
order-ID's en hashketen. Een gewijzigde ledger maakt oude goedkeuring ongeldig.
Een andere schrijvende sessie kan een nieuwere staat niet overschrijven. Dit blijft
één schrijvende workflow, geen gedistribueerde broker of beveiligd auditregister.

## Opslag, API en protocolvergrendeling

Nieuwe tabellen: decision_protocols, trade_decisions, research_trade_reviews,
research_fills en research_ledger_states. Zij staan los van orders, proposals,
positions, portfolio_history en bestaande backtestresultaten. Alleen-lezen routes:
`/decisions`, `/research-trade-reviews`, `/research-fills`.

Een sessie bindt beleidsinhoud, ResearchPlan, filters, exacte rapportbundelhash en
uitvoeringscandlehash. Wijziging achteraf voor hetzelfde plan/coin wordt geweigerd.
Alleen ontwikkeling is bereikbaar, met maximaal 192 aaneengesloten 15m-candles
per coin. Rapport én volledige uitkomsthorizon moeten binnen ontwikkeling vallen.
Validatie en onafhankelijke test hebben geen vrijgavepad in deze fase-5-interface.
Alleen ontwikkelblootstelling wordt geregistreerd. De bestaande fase-4B-protocollen
 en historische onderzoeksresultaten zijn niet aangepast.

## Tests en kleine integratie

**251 tests geslaagd, 0 mislukt**: alle 191 bestaande plus 60 nieuwe.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing.

Nieuwe controles omvatten reproduceerbaarheid, multi-coinwatchlist, vijf ontbrekende
analysecomponenten, conflicten, ongeldige indicatoren, toekomstig nieuws, verlopen
signalen, UTC/candlegrenzen, filter- en saldoafwijzing, kosten/risico, noodstop,
verliesreeksen, dagverlies/drawdown, koersgaps, onafhankelijke Risk Engine-veto,
stop/target-ambiguïteit, oversell, deduplicatie, stateherstel, hashketen, verplichte
candlevolgorde, onafhankelijke testvergrendeling en productie-isolatie.
Tijdens ontwikkeling gevonden herstel- en cachefouten zijn opgelost; de uiteindelijke
suite heeft geen resterende mislukte tests.

`scripts/phase5_smoke.py` gebruikt uitsluitend de bestaande lokale officiële
Binance-archieven voor BTC/EUR en ETH/EUR van 2025-01-10. Zes archieven, 252 candles
op 15m/1h/4h, met officiële opgeslagen SHA-256-checksums en volledige dagvalidatie.
Geen netwerkverzoek of nieuwe download. Eén dag biedt slechts zes 4h-candles:
met ongewijzigde indicatorparameters ontbreekt voldoende warm-up. Beide coins
geven terecht HOLD, Entry REJECTED en Exit HOLD_POSITION. Nul paper-orders,
nul offline fills in deze archieftest en geen onafhankelijke testinzage.

Het volledige resultaat staat in `experiments/phase5_smoke.json`; een test vergelijkt
heruitvoering exact met dit artefact. De succesvolle BUY/stop/exit/ledger-keten is
met kleine deterministische synthetische fixtures getest. Er zijn geen uitgebreide
backtests, nieuwe prestatieclaims of parameteroptimalisatie uitgevoerd.

## Resterende beperkingen

- Geen bewezen strategie, positieve expectancy of statistisch winstbewijs.
- Historische beursfilters kunnen slechts expliciete aannames zijn. Bron-URL's en
  lokale hashes vervangen geen onafhankelijke authenticiteitscontrole; de importer
  blijft verantwoordelijk voor betrouwbare, bij elkaar horende analyses en candles.
- Geen betrouwbare nieuwsfeed; onbekend sentiment levert geen positieve informatie.
- Alleen long Spot, één positie per geïsoleerd coin-experiment, vaste volledige fills;
  geen gecombineerde multi-assetportefeuille, orderboek, deeluitvoering of latentie.
- OHLC kent het werkelijke intrabarpad niet. Kosten, spread, liquiditeit en gapregels
  blijven aannames; onvoldoende gegevens resulteren in HOLD of een expliciete weigering.
- Handmatig aangeroepen Python-onderzoeksworkflow; geen live-/papertradingplanner,
  operationeel alarmkanaal of publieke schrijf-API. De lokale procesgrens is geen
  beveiliging tegen willekeurige Python-code of handmatige SQLite-wijzigingen.
- Windows is niet uitgevoerd. De bestaande dependencywaarschuwing blijft aanwezig.

Fase 5 eindigt hier. Geen automatische start van een volgende fase.
