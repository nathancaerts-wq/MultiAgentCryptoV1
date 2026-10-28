# Fase 6C — risicopauze en niet-geselecteerde momenten

28 oktober 2026. Basis 86596f90d2ab53434912fce5972a660470e32a9b, schone werkmap
bij start. Alleen reeds opgeslagen ontwikkelbeslissingen voor BTC/EUR, ETH/EUR,
SOL/EUR in 2024. Geen nieuwe rendementsbacktest, downloads of nieuwe toekomstige
koerslabels. Validatie 2025 en onafhankelijke test 2026 blijven gesloten.

**Conclusie: de langdurige verliesreekspauze is correct bedoeld gedrag binnen het
bevroren protocol.** Er is geen fout in de verwerking van de drie verliezen gevonden.
Historische 'gemiste winst' en 'terecht vermeden daling' zijn nog niet vastgesteld:
de daarvoor benodigde meetregistratie ontbreekt. De expliciete stopvoorwaarde
uit de opdracht is voor die nieuwe uitkomsten toegepast. Geen risicologica gewijzigd.

## Exacte oorzaak en herstelvoorwaarden

ResearchExecutionEngine._reason telt de negatieve suffix van alle gesloten trades
in dezelfde ledger, in omgekeerde volgorde. Een nettoresultaat >=0 onderbreekt de
reeks. Bij losses >= DecisionPolicy.max_consecutive_losses (standaard 3) wordt iedere
nieuwe ENTRY_CANDIDATE geweigerd met `verliesreekspauze`. JointPortfolio._risk_reason
roept deze centrale controle aan; StreamingFixtureRunner behoudt deze methode en
controleert daarvóór de trailing datatoelating.

| UTC-exit | Coin | Netto EUR | Cash na exit | Verliesreeks |
|---|---|---:|---:|---:|
|2024-01-09 00:45|ETH/EUR|−0,99591459|199,00408541|1|
|2024-01-10 13:00|ETH/EUR|−0,98857766|198,01550775|2|
|2024-01-11 16:00|SOL/EUR|−0,98344456|197,03206319|3|

Vanaf de derde exit blijft elke volgende opgeslagen state vlak, zonder pending
order, met drie negatieve trades als suffix. Alle maandgrenzen februari t/m
1 januari 2025 tonen exact €197,03206319 en dezelfde reeks. Dagverlies- en
drawdownvlaggen zijn false, centrale noodstop false: dit is geen permanente
noodstop en geen dagverliespauze. Verliesreekspauze wordt afgeleid uit de historie;
een afzonderlijke `loss_pause`-vlag of resetdatum bestaat niet. Het diagnostische
maandoverzicht bevat een afgeleide vlag, zonder die in de ledger te schrijven.

Een niet-negatieve gesloten trade zou de suffix resetten, maar zonder bestaande
positie kan de runner na de pauze geen nieuwe trade starten om die te verkrijgen.
Er is geen automatische herstart na tijd, dag, maand, coinwissel, procesherstart of
verbeterd regime. Nieuwe onafhankelijke studies beginnen wel met een eigen ledger;
zo'n nieuwe studie is geen herstel binnen de lopende portefeuille en geen toegestane
manier om de pauze tijdens 2024 te omzeilen. Historie wissen, een fictieve winnaar
invoegen of bestaande parameters wijzigen is geen herstelprocedure.

Het protocolvoorstel §6 zegt expliciet dat deze pauze de rest van de deelstudie kan
blokkeren; de drie-muntenamendering behoudt dat. Het woord 'pauze' kan operationeel
een tijdelijke onderbreking suggereren, maar code en onderzoeksprotocol beschrijven
hier een blijvende blokkering binnen dezelfde studie. Dat is een ontwerplimiet,
geen aangetoonde implementatiefout. De afzonderlijke dagverliespauze kan in
OfflineLedger.observe bij een UTC-dagwissel vervallen; die reset geldt niet voor
de verliesreeks. Risicolimieten blijven €200 start, 0,5% gepland risico, één positie,
50% entry-exposure, 3% dagverlies, 10% drawdown en drie opeenvolgende verliezen.

## Offline analyzer en categorieën

crypto/missed_opportunity.py classificeert uitsluitend opgeslagen beslissingen en
settlements. scripts/phase6c_diagnostics.py opent de bestaande database mode=ro.
Unieke sleutel: portefeuille, UTC-grens, coin. JSONL-gzip bevat elke beoordeling,
ook HOLD, agentreden, centrale reden, riskresultaat, uitvoeringsreden en andere
coins met strikt hogere toen bekende score. Geen toekomstige prijsinput in de
beslisclassificatie. Per baseline 34.465 grenzen × drie coins = 103.395 rijen.
De laatste grens is een terminale waarderingsgrens, geen extra instapcandle;
voor toekomstige labels worden terminale grenzen uitgesloten volgens het voorstel.

| Exclusieve basiscategorie | aligned_trend | EMA Trend |
|---|---:|---:|
| Uitgevoerde entry, gekoppeld aan gesloten trade |3|5|
| Goedgekeurd, bij uitvoering geweigerd |4|2|
| BUY/eligible-kandidaat niet geselecteerd |1.946|39.765|
| Overige niet-geselecteerde momenten, geen BUY |101.442|63.623|
| Onopgeloste geselecteerde entry |0|0|
| Totaal |103.395|103.395|

De geblokkeerde categorie bevat naast portefeuille/risico ook data-, entry- en
selectieblokkeringen; de exacte reden blijft bewaard. Geen verkoopexit dubbel als
nieuwe entry geteld. De vier aligned_trend-fillafwijzingen zijn de reeds onderzochte
ongunstige opens boven de vooraf gereserveerde cash, geen nieuwe technische fout.
Zie PHASE6B_JANUARY_DIAGNOSTICS.md.

De volgende redenen gelden voor **alle niet-geselecteerde coinbeoordelingen**, dus
niet uitsluitend voor BUY-kandidaten; zij vormen geen extra onafhankelijke trades:

| Reden | aligned_trend | EMA |
|---|---:|---:|
| Onvolledig vergelijkingsuniversum |83.832|51|
| Alleen BUY_CANDIDATE wordt beoordeeld |18.590|63.560|
| Centrale positielimiet |120|255|
| Cash/plaats voor hogere kandidaat gereserveerd |0|2|
| Gepland risico boven 0,5% (Entry) |0|30.481|
| Verliesreekspauze (centrale controle) |793|8.776|
| Liquiditeit 15m |53|259|
| Stop-exit minimum notional |0|4|

De pauze kan dus actief zijn zonder dat zij de primaire afwijsreden op iedere rij
wordt. Eerdere data- of Entry-filters kunnen al HOLD/REJECTED geven. Vooral bij EMA
is de sizing op actuele cash gebaseerd, terwijl Entry het geplande risico begrenst
op 0,5% van min(€200,cash). Na een winst boven €200 kunnen daardoor voorstellen
vroeg worden afgewezen. Dat is een aantoonbaar verschil tussen de budgetbasis van sizing en die van de
striktere controle. Of die mismatch bedoeld was, is niet expliciet gedocumenteerd;
geen overschrijding of versoepeling van risico en hier niet aangepast. Het verklaart
mede waarom men 8.776 pauzemeldingen niet als de totale duur van de pauze kan lezen.

### Nog niet berekende uitkomstcategorieën

- Niet-geselecteerd en later gestegen: niet berekend.
- Niet-geselecteerd en later gedaald: niet berekend.
- Financieel aantrekkelijkere alternatieve coin: niet vastgesteld.

Bij 60.924 aligned_trend-rijen en 68.896 EMA-rijen had een andere coin een strikt
hogere bekende score. Dit betreft alle categorieën, inclusief uitgevoerde entries,
en zegt niets over haar risicotoelaatbaarheid of latere winst. Het zijn geen aantallen
gemiste trades. Een hoge score kan ongeschikt zijn wegens andere filters.

Toekomstlabels zijn een aparte as naast de exclusieve basiscategorieën en mogen
niet daarbij worden opgeteld. Overlappende 15m-vensters en gelijktijdige coins zijn
afhankelijk. De analyzer kent geen toekomstige winnaar aan een oorspronkelijke
beslissing toe. fixture_outcome accepteert uitsluitend `fixture:`-candles en gebruikt
de bestaande adverse FillCosts-rekenregels. Hij laat in tests zien dat een bruto
stijging na kosten negatief kan zijn. Dit is een hypothetische horizonwaardering,
geen stop-/portefeuillesimulatie en geen uitvoerbaarheidsbewijs.

De bestaande 4h-strategiehorizon bepaalt niet automatisch de hoeveelheid of stop
voor een HOLD, of de selectie van onafhankelijke onderzoeksvensters. Daarom is
PHASE6C_MEASUREMENT_PROPOSAL.md een **niet-geactiveerd voorstel**. Nieuwe historische
uitkomstberekeningen stoppen totdat horizon, waardering, sizing, overlap en betekenis
van 'betere coin' vooraf bevestigd zijn. Er is geen 'gemiste winst' verzonnen en geen
risicoveto op grond van toekomstige koersen opgeheven. Feitelijke risicowaarborgen
waren correct; of zij achteraf winstgevende of verliesgevende situaties vermeden,
is zonder goedgekeurde meting onbekend.

## Waarom EMA in de opgeslagen baseline hoger eindigt

| Maatstaf | aligned_trend | EMA Trend |
|---|---:|---:|
| BUY-kandidaten |1.953|39.772|
| Goedgekeurde entries |7|7|
| Uitgevoerde gesloten trades |3|5|
| Uitvoeringsafwijzingen |4|2|
| Winrate |0%|20%|
| Netto EUR |−2,96793681|+0,58224413|
| Fees EUR |0,18502791|0,42692417|
| Tijdsexposure jaar |0,11384335%|0,24191712%|
| Gemiddelde kapitaalexposure |0,01739135%|0,05150601%|
| Maximale kapitaalexposure op meetgrenzen |20,17355442%|23,57517462%|
| Blijvende pauze vanaf UTC |11 januari 16:00|9 januari 12:15|

Aligned_trend vereist bullish 1h-regime en uitgelijnde EMA-richtingen op 15m/1h/4h,
plus bestaande analysevalidatie. EMA gebruikt uitsluitend EMA9/EMA21−1 >0,002 op
het vaste 32h-venster als directionele filter, hoogste gap eerst; de overige
kwaliteits-, sizing-, risico-, stop- en horizonregels blijven hetzelfde. Andere
instapmomenten en prioriteiten geven een andere beperkte transactieprefix.

EMA-baseline bevat uitsluitend BTC-trades met netto achtereenvolgens
−0,29803399; +1,62185399; −0,39778090; −0,12306604; −0,22072893 EUR, allemaal tijdexits.
De winsttrade reset de reeks naar nul; daarna blokkeren drie verliezen opnieuw.
De ene winst van €1,62185399 verklaart het positieve eindresultaat; de vier verliezen
zijn samen −€1,03960986. Dat toont concentratie, geen structurele voorsprong.
Aligned_trend heeft twee ETH-stops en één SOL-stop, geen winnaar.

EMA presteert dus niet beter doordat zijn pauze wordt opgeheven: hij pauzeert zelfs
eerder. Hij verdiende vóór die pauze op één ander historisch moment. Kostenstress
in de bestaande resultaten: EMA-slippage −€0,82194431 en EMA-dubbel −€0,49469584;
aligned_trend respectievelijk −€2,96880034 en −€2,96964210. Geen nieuwe backtest.
Er is onvoldoende bewijs voor superioriteit, winstgevendheid of een te kiezen strategie.

## Vier toetsbare verbeterhypotheses — voorstellen, niet activeren

1. Een vooraf gespecificeerde cooldown na drie verliezen, gevolgd door volledig
   dezelfde risico-/datacontroles, verhoogt de evaluatie-exposure zonder de bestaande
   drawdownlimiet te overschrijden. Vergelijk met huidige blijvende blokkering;
   cooldownduur, herstelcriteria en verliesbudget eerst registreren. Geen huidige reset.
2. Sizing direct begrenzen op min(€200,cash) reduceert Entry-afwijzingen boven €200
   zonder het maximale geplande risico te verhogen. Eerst alleen synthetische
   technische vergelijking; geen gewijzigde 2024-resultaten in deze fase.
3. Het apart rapporteren van datavaliditeit en inhoudelijke analyseconflicten
   verklaart de grote groep onvolledige-universum-HOLDs beter. Meet oorzaakfrequenties
   vóór een voorstel om voorwaarden te veranderen; geen filter uitschakelen.
4. De ervaren positieve EMA-baseline is geconcentreerd in één trade en niet robuust
   voor de vastgelegde kostenstress. Een vooraf geregistreerde onafhankelijke
   vergelijking zou moeten aantonen of dit standhoudt; deze fase verleent geen
   toestemming om validatie of test te openen of EMA te promoveren.

## Integriteit, tests en beperkingen

Database-SHA vóór en na read-only diagnose is identiek aan de bestaande verificatie:
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.
Alle bestaande experiments/development_2024-bestanden blijven byte-identiek.
Daarmee blijven financiële resultaten, auditlogs en checkpoints behouden. Geen
bestaande trading-, risico-, uitvoeringsmodule of configuratie gewijzigd; alleen
nieuwe diagnostiek. Bron: bestaande rapporten/protocol, research_execution.py,
trade_agents.py, joint_portfolio.py, streaming.py, sim_execution.py en opgeslagen
baselinebatches, settlements, tradeprefixen en checkpoints.

Diagnosebudget vooraf in script: 300 s, 1 GiB adresruimte. Werkelijk 64,870 s en
44,660 MiB piek-RSS. Volledige classificaties en hashes staan in experiments/phase6c/.
Geen historische candles voor toekomstige labels uitgelezen. Een eindgrens op
1 januari 2025 in checkpointmetadata is geen inzage in validatiemarktdata.

Tests: 18 nieuwe deterministische tests voor classificatie, identiteit, UTC/grenzen,
kosten, ontbrekende/duplicaatcandles, toekomstinformatie, fixture-only labels en
verliesreeks. Volledige suite: **420 geslaagd, 0 mislukt** (402 behouden + 18), één bestaande Starlette/AnyIO-waarschuwing. Geen labels als onafhankelijke
trades optellen; geen werkelijk uitvoerbare winst claimen met aangenomen filters.
Archiefrevisies, universumselectie, OHLCV-intrabarbeperkingen en kleine steekproeven
blijven gelden. De vier verbeterhypotheses komen ná inzage in 2024 en zijn dus
exploratief, niet prospectief bewijs.

Volgende fase: eerst de open meetkeuzes en een aparte onderzoeksregistratie
besluiten; dan uitsluitend de expliciet goedgekeurde uitkomstlabels, nog zonder
risicoregels te versoepelen. Geen automatische activatie door Research Optimizer.
Stop na deze diagnose en het veiligstellen ervan.


De stopregel komt rechtstreeks uit deze gebruikersopdracht: “Als hiervoor nieuwe
keuzes nodig zijn, documenteer ze en stop vóór het berekenen van die resultaten.”
Daarom wachten historische forward-labels op bevestiging van het meetvoorstel;
deze stop betreft niet de reeds toegestane reconstructie van opgeslagen beslissingen.

Historische manifesten bewaren hun oorspronkelijke bestandenset. Nieuwe aanvullende
modules worden niet achteraf in die manifesten geschreven. Hun oude bestanden zijn
individueel op hun geregistreerde hashes gecontroleerd; een integrale directory-
vergelijking met de later uitgebreide bronboom is geen controle van dezelfde versie.
