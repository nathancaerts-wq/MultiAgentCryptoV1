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

Baseline en slippage-stress zijn volledig verwerkt: januari t/m december.
De overige geregistreerde runs zijn nog in uitvoering; geen jaarresultaat daarvoor geclaimd.

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
geen onjuiste driemuntenbenchmark of vervangende regel gebruikt. EMA nog lopend.

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
