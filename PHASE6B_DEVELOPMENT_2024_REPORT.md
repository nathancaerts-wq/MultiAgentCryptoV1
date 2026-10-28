# Fase 6B — volledige ontwikkelperiode 2024

Onderzoeksbasis 2cd573a806556998cc91b3a17a2294f828f42fad. Expliciete opdracht
FULL DEVELOPMENT PERIOD BACKTEST en hervattingsopdracht. Alleen BTC/EUR, ETH/EUR
en SOL/EUR, [2024-01-01 00:00, 2025-01-01 00:00) UTC. Warm-up tot 8 januari;
laatste entry uiterlijk 31 december 19:45. Geen validatie of onafhankelijke test.

## Vastlegging en gegevens

experiments/development_2024/protocol.json is vooraf geschreven. Het manifest
bindt volledige bron-/rapporthashes, alle Python-kernmodules, uitvoeringsscripts,
configuraties en de zes afzonderlijke plannen (drie kostenscenario's voor de
primaire strategie en EMA-benchmark). Dit zijn lokale inhoudssnapshots, geen
extern onveranderlijke preregistratie. De eerdere zesmuntenstudie blijft intact.

Alle 108 officiële maand-ZIP's zijn uit de bestaande cache gelezen; volledige
SHA-256 tegen eerder opgeslagen officiële CHECKSUM vóór CSV-verwerking. Alle
12 klinevelden, UTC/milliseconden, afgesloten candles, ontbrekende/dubbele rijen,
volgorde, OHLCV en exacte 15m→1h→4h-consistentie slagen. Per coin: 35.136 kwartier-,
8.784 uur- en 2.196 vieruurcandles. In totaal 138.348 unieke broncandles. Geen
netwerkverzoeken. De ontwikkelworkflow leest geen marktdata vanaf 2025-01-01.
De bestaande tests gebruiken daarnaast hun eerder bekende lokale technische fixtures;
dat is geen nieuwe validatie-/testbacktest. Candledekking bewijst
transacties gedurende 2024, geen exacte listingdatum of historische orderfilters.

## Checkpointkeuze

De oorspronkelijke januari-database blijft behouden. Volledige input-, audit- en
checkpointketen en financiële reconstructie zijn gecontroleerd; oorspronkelijke
bestandshash ongewijzigd. €197,03206319 cash; geen positie of pending order;
drie verliestrades en bijbehorende gezamenlijke verliesreekspauze.

De pilot heeft een vast plan-einde 1 februari, verzegelde maandinvoer en terminale
instapstop. Zonder gewijzigde manifestbindingen is verlenging niet bewezen veilig.
Daarom één afzonderlijke jaarreplay vanaf de oorspronkelijke start; geen resets
tussen maanden. Vóór verwerking ná 1 februari wordt de financiële januariprefix
vergeleken. Een ander plan geeft andere order-ID's; financiële tradevelden worden
exact vergeleken. De andere einddatum kan extra januari-signalen geven in de
oude terminale 4h15m; eventuele verschillen worden onderzocht, niet weggeoptimaliseerd.

## Ongewijzigde uitvoering

Bestaande streamingrunner, analyseketen, aligned_trend, Decision/Entry/Exit,
centrale Risk Engine en Decimal-ledger. Eén gezamenlijke €200-portefeuille;
één positie; maximaal 0,5% gepland risico en 50% exposure bij entry. Dagverlies3%,
drawdown10%, verliesreeks3 en noodstop. Geen maandelijkse herkapitalisatie of reset
van pauzes. Exact 32 afgesloten candles per timeframe, bestaande indicatorparameters.
Geen automatische optimalisatie. Bronselectie is in een aparte 2024-route begrensd;
bestaande januari- en fixture-routes zijn behouden.

Hypothetische filters zijn ongewijzigd: tick €0,01, quantity-stap/minimum 0,00001,
maximum 1.000.000, minimum notional €10, status assumed. Kosten per zijde baseline:
fee0,1%, slippage0,1%, volledige spread0,1%. Slippage-stress: slippage0,2%; alles
dubbel: fee/spread/slippage0,2%. Per scenario sizing, afwijzingen en pauzes opnieuw
met dezelfde regels; geen achteraf herprijzen van uitsluitend de baseline-trades.
Spread/slippage zitten in de fillprijs, fees apart. Historische uitvoerbaarheid
blijft onbewezen; OHLCV bewijst geen exacte intrabarroute of orderboekliquiditeit.

## Budget en opslag

Vooraf: voorbereiding 1.800 s, ieder replay-/verificatieproces 1.800 s; harde
1,5 GiB adresruimte, vroege stop bij 1,2 GiB RSS, minimaal 2 GiB vrije schijf.
Dit budget is gebaseerd op de eerdere maand-/synthetische metingen; het vroegere
45-secondenjaarcriterium wordt niet als geslaagd gepresenteerd. Voorbereiding:
694,180 s, 177,113 MiB piek-RSS, 7.327.088.640 bytes database vóór financiële replay.

Database /workspace/development_2024.sqlite3 bewaart analyses, exacte afwijzingen,
reserveringen, fills, audit en compacte checkpoints. Het grote bestand gaat niet
naar Git. Iedere financiële transactie gebruikt de bestaande atomische SQLite-
route. Een onderbreking bewaart de laatst volledig gecommitte toestand; geen
automatische herstart vanaf nul. Hashes en voortgang staan in experiments/development_2024/.

## Resultaten en eindcontrole

Alle zes vooraf geregistreerde runs zijn volledig verwerkt: januari t/m december.
Geen onvolledige maanden, onderbrekingen of financiële hervattingen. De al voltooide
voorbereiding is bij hervatting hergebruikt; geen nieuwe datasetvoorbereiding vanaf nul.

| Maatstaf baseline | Uitkomst |
|---|---:|
| BUY-kandidaten | 1.953 |
| Goedgekeurde entryreserveringen | 7 |
| Afgewezen BUY-voorstellen | 1.946 |
| Uitvoeringsafwijzingen | 4; ongunstige open boven reservering |
| Gesloten trades / unieke fills | 3 / 6 |
| Winrate / profit factor | 0% / 0 |
| Gemiddelde winst | n.v.t.; geen winnaars |
| Gemiddeld verlies / expectancy per trade | −€0,98931227 |
| Netto EUR / procent | −€2,96793681 / −1,483968405% |
| Eindkapitaal | €197,03206319 |
| Fees | €0,18502791 |
| Conservatieve low-drawdown / close-drawdown | 1,509320075% / 1,483968405% |
| Gemiddelde audit-houdduur | 3 uur 20 minuten |
| Tijdsexposure over alle 366 dagen | 0,11384335% |
| Gemiddelde / maximale kapitaalexposure | 0,01739135% / 20,17355442% |
| Looptijd / piek-RSS baseline | 1.276,873 s / 94,4258 MiB |

Januari −€2,96793681; februari t/m december elk €0. ETH twee trades −€1,98449225,
SOL één trade −€0,98344456; BTC geen trade. Verliesreekspauze vanaf 11 januari
16:00 UTC tot einde studie. Geen dagverlies-, drawdown- of noodstopactivering.
Maximale exposure is op 15m-grenzen gemeten; geen intrabar-exposuregarantie.

Slippage-stress: drie trades, zeven entryreserveringen, vier uitvoeringsafwijzingen;
netto −€2,96880034, eindkapitaal €197,03119966, fees €0,17366454. Looptijd
1.284,714 s, piek-RSS 94,5547 MiB. Kleinere positiegrootte verklaart lagere fees
ondanks hogere slippage. Alle financiële en auditprefixcontroles slagen.

Cashbenchmark €200: netto €0, geen fees/drawdown/exposure. Buy-and-hold-index
niet uitgevoerd: bestaande implementatie vereist zes coins en verdeelt door zes;
geen onjuiste driemuntenbenchmark of vervangende regel gebruikt. EMA is volledig uitgevoerd in de drie geregistreerde kostenscenario’s; zie tabel hieronder.

402 volledige tests geslaagd (389 behouden + 13), één bestaande dependencywaarschuwing.
Aanvullende read-only verificatie in verification_completed_prefix.json: SQLite ok,
geen paperorders, alle fills/fees/cash/risico en checkpointketens exact. De eerste
diagnostische tijdtekstvergelijking is hersteld naar UTC-tijdstempelvergelijking
(Z en +00:00 zijn gelijk); geen wijziging van simulatie of uitkomsten. De gehele
database krijgt pas na stoppen van alle schrijvers een bestandshash.

Drie trades zijn onvoldoende bewijs. Selectie-/survivorshipbias, gereviseerde
archiefversies en aangenomen filters beperken interpretatie. Geen winstclaims.
Kostenstress, maanden en coins zijn beschrijvend, geen parameterselectie.
Rekenkundige verwijdering van nul winnaars laat −€2,96793681 staan; verwijderen
van alle drie verliezers geeft €0. Dit is geen uitvoerbaar tegenfeitelijk rendement
of nieuwe drawdownberekening. Geen validatie of onafhankelijke test uitgevoerd.


## Volledige scenario- en benchmarkuitkomsten

| Strategie / scenario | Trades | Winrate | Netto EUR | Eindkapitaal | Fees | PF | Low-DD % | Tijd s | RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|aligned_trend_baseline|3|0.0000%|-2.96793681|197.03206319|0.18502791|0E+8|1.50932008|1276.873|94.426|
|aligned_trend_slippage_stress|3|0.0000%|-2.96880034|197.03119966|0.17366454|0E+8|1.50877302|1284.714|94.555|
|aligned_trend_double_costs|3|0.0000%|-2.96964210|197.03035790|0.31796090|0E+8|1.50776128|1351.148|93.879|
|ema_trend_baseline|5|20.0000%|0.58224413|200.58224413|0.42692417|1.560060222976338450656864682|0.51552096|1291.483|93.344|
|ema_trend_slippage_stress|5|20.0000%|-0.82194431|199.17805569|0.40047831|0.6283617931105372895686100808|1.01077847|1597.342|88.766|
|ema_trend_double_costs|5|20.0000%|-0.49469584|199.50530416|0.63548374|0.6943490515485431664819770572|0.79401924|1571.956|88.707|

Iedere rij is één afzonderlijke €200-portefeuille over dezelfde ontwikkelperiode.
Alle kostenstressuitkomsten worden getoond; geen selectie van het beste scenario.
Cash: €200, netto €0, risico/exposure/fees nul. De buy-and-hold-index ontbreekt zoals hierboven toegelicht.

| Strategie / scenario | Kandidaten | Entries goedgekeurd | BUY afgewezen | Uitvoering geweigerd | Gem. winst | Gem. verlies | Expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
|aligned_trend_baseline|1953|7|1946|4|None|-0.98931227|-0.98931227|
|aligned_trend_slippage_stress|1953|7|1946|4|None|-0.9896001133333333333333333333|-0.9896001133333333333333333333|
|aligned_trend_double_costs|1953|7|1946|4|None|-0.98988070|-0.98988070|
|ema_trend_baseline|39772|7|39765|2|1.62185399|-0.259902465|0.116448826|
|ema_trend_slippage_stress|39772|10|39762|5|1.38973440|-0.5529196775|-0.164388862|
|ema_trend_double_costs|39772|8|39764|3|1.12380344|-0.40462482|-0.098939168|

`None` betekent niet van toepassing, geen nulwinst. Exacte uitvoeringsafwijzingen:

- aligned_trend_baseline: {'ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging': 4}

- aligned_trend_slippage_stress: {'ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging': 4}

- aligned_trend_double_costs: {'ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging': 4}

- ema_trend_baseline: {'ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging': 2}

- ema_trend_slippage_stress: {'ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging': 5}

- ema_trend_double_costs: {'ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging': 3}

### Maandresultaten (netto equityverschil binnen dezelfde portefeuille)

| Maand | aligned_trend baseline netto | Eindwaarde | EMA baseline netto | Eindwaarde |
|---|---:|---:|---:|---:|
|2024-01|-2.96793681|197.03206319|0.58224413|200.58224413|
|2024-02|0E-8|197.03206319|0E-8|200.58224413|
|2024-03|0E-8|197.03206319|0E-8|200.58224413|
|2024-04|0E-8|197.03206319|0E-8|200.58224413|
|2024-05|0E-8|197.03206319|0E-8|200.58224413|
|2024-06|0E-8|197.03206319|0E-8|200.58224413|
|2024-07|0E-8|197.03206319|0E-8|200.58224413|
|2024-08|0E-8|197.03206319|0E-8|200.58224413|
|2024-09|0E-8|197.03206319|0E-8|200.58224413|
|2024-10|0E-8|197.03206319|0E-8|200.58224413|
|2024-11|0E-8|197.03206319|0E-8|200.58224413|
|2024-12|0E-8|197.03206319|0E-8|200.58224413|

### Coinbijdragen per scenario

| Scenario | Coin | Trades | Netto | Fees | Winrate |
|---|---|---:|---:|---:|---:|
|aligned_trend_baseline|BTCEUR|0|0|0|None|
|aligned_trend_baseline|ETHEUR|2|-1.98449225|0.14384425|0|
|aligned_trend_baseline|SOLEUR|1|-0.98344456|0.04118366|0|
|aligned_trend_slippage_stress|BTCEUR|0|0|0|None|
|aligned_trend_slippage_stress|ETHEUR|2|-1.98513927|0.13407097|0|
|aligned_trend_slippage_stress|SOLEUR|1|-0.98366107|0.03959357|0|
|aligned_trend_double_costs|BTCEUR|0|0|0|None|
|aligned_trend_double_costs|ETHEUR|2|-1.98558088|0.24335368|0|
|aligned_trend_double_costs|SOLEUR|1|-0.98406122|0.07460722|0|
|ema_trend_baseline|BTCEUR|5|0.58224413|0.42692417|0.2|
|ema_trend_baseline|ETHEUR|0|0|0|None|
|ema_trend_baseline|SOLEUR|0|0|0|None|
|ema_trend_slippage_stress|BTCEUR|5|-0.82194431|0.40047831|0.2|
|ema_trend_slippage_stress|ETHEUR|0|0|0|None|
|ema_trend_slippage_stress|SOLEUR|0|0|0|None|
|ema_trend_double_costs|BTCEUR|4|-0.19122224|0.55953814|0.25|
|ema_trend_double_costs|ETHEUR|0|0|0|None|
|ema_trend_double_costs|SOLEUR|1|-0.30347360|0.07594560|0|

### Afwijzingen, exposure en pauzes

Alle individuele coin/tijdstip/score/agentreden/centrale reden zijn in joint_batches
en joint_settlements opgeslagen. HOLD-beoordelingen zijn geen geweigerde orders.
De baseline bevat 103.395 coinbeoordelingen; zeven zijn geselecteerd. Overige redenen:

- onvolledig vergelijkingsuniversum; geen nieuwe instap: 83832.
- Uitsluitend BUY_CANDIDATE wordt beoordeeld: 18590.
- centrale positielimiet: één open positie: 120.
- verliesreekspauze: 793.
- liquiditeit_15m: 53.

| Scenario | Tijdsexposure % | Gem. kapitaalexposure % | Max. kapitaalexposure % | Gem. houdduur s | Close-DD % | Verliesreeks-pauze vanaf UTC |
|---|---:|---:|---:|---:|---:|---|
|aligned_trend_baseline|0.11384335|0.01739135|20.17355442|12000.0|1.48396840|2024-01-11T16:00:00+00:00|
|aligned_trend_slippage_stress|0.11384335|0.01634741|18.68589252|12000.0|1.48440017|2024-01-11T16:00:00+00:00|
|aligned_trend_double_costs|0.11384335|0.01499305|16.83350097|12000.0|1.48482105|2024-01-11T16:00:00+00:00|
|ema_trend_baseline|0.24191712|0.05150601|23.57517462|15300.0|0.49647819|2024-01-09T12:15:00+00:00|
|ema_trend_slippage_stress|0.21914845|0.04375160|21.49890067|13860.0|0.92102870|2024-01-09T13:00:00+00:00|
|ema_trend_double_costs|0.24191712|0.03841279|19.12717825|15300.0|0.74653859|2024-01-09T12:45:00+00:00|

Houdduur gebruikt audit-candlegrenzen; geen exacte intrabar-tijd. Exposure gebruikt
post-batch bezit met voorgaande 15m-close, warm-up telt als nul. Conservatieve
low-drawdown staat los van deze close-metingen. Pauzes lopen door tot einde studie;
checkpointvlaggen en expliciete pause-events staan in verification.json.

### Rekenkundige concentratiediagnoses

- aligned_trend_baseline: {'without_top_3_winners': '-2.96793681', 'without_worst_3_losers': '0E-8', 'removed_winners': 0, 'removed_losers': 3}.
- aligned_trend_slippage_stress: {'without_top_3_winners': '-2.96880034', 'without_worst_3_losers': '0E-8', 'removed_winners': 0, 'removed_losers': 3}.
- aligned_trend_double_costs: {'without_top_3_winners': '-2.96964210', 'without_worst_3_losers': '0E-8', 'removed_winners': 0, 'removed_losers': 3}.
- ema_trend_baseline: {'without_top_3_winners': '-1.03960986', 'without_worst_3_losers': '1.49878795', 'removed_winners': 1, 'removed_losers': 3}.
- ema_trend_slippage_stress: {'without_top_3_winners': '-2.21167871', 'without_worst_3_losers': '1.02959596', 'removed_winners': 1, 'removed_losers': 3}.
- ema_trend_double_costs: {'without_top_3_winners': '-1.61849928', 'without_worst_3_losers': '0.82032984', 'removed_winners': 1, 'removed_losers': 3}.

Geen hersimulatie na verwijderen van trades; geen haalbaar rendement of herberekende drawdown.

## Definitieve technische controle en beperkingen

Alle zes portefeuilles gereconstrueerd, ieder 34.465 aaneengesloten evaluatiegrenzen
en 103.392 uitvoeringscandles; initieel €200 precies eenmaal per scenario. SQLite
integrity_check=ok; nul paperorders; unieke fills, kas, fees, netto, positievolgorde,
0,5%-risico/50%-exposure bij iedere aankoop en volledige audit-/checkpointketens
read-only gecontroleerd. Alle twaalf maandbijdragen en coinbijdragen reconciliëren.
Database: 15057117184 bytes; SHA-256 `fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.

Alle scenarioresultaten, complete 15m-curves (inclusief warm-up) en hashes staan
in experiments/development_2024/. Laatste revision/state-/checkpointhash per scenario
staan in verification.json. De grote volledige SQLite-audit blijft lokaal op
/workspace/development_2024.sqlite3; Git bevat niet de gehele database. Behoud dit
bestand voor herstel; een Git-clone alleen bevat niet de volledige audit/checkpoints.
De oorspronkelijke januari-database is ongewijzigd behouden.

De eerste read-only controle had alleen een UTC-tekstnotatiefout (Z versus +00:00);
de controle vergelijkt nu tijdstempels. Geen financiële replay of regels aangepast.
Geen time-outs of budgetverhogingen. Geen validatie-/testmarktdata in de runs, geen
parameteroptimalisatie, live orders of paperbot. Bestaande technische tests gebruiken
hun reeds bekende fixtures. Alle strategie-/risicomodules van voor deze opdracht
zijn ongewijzigd. Minder dan 30 trades per scenario: onvoldoende bewijs, geen
statistische winst- of superioriteitsclaim. Stop na ontwikkeling 2024.
