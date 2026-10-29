# Fase 6H-B — voltooide hypothetische Risk Recovery-vergelijking 2024

Uitsluitend BTC/EUR, ETH/EUR en SOL/EUR, aligned_trend, baselinekosten en de
vooraf vastgelegde 24u-verliesreekspauze. **2024 is reeds onderzocht; dit is geen
onafhankelijke validatie en geen bewijs van historische orderuitvoerbaarheid.**
Geen ATR-kostenstrategie, optimalisatie, extra kostenscenario, echte of paper-order.

## Registratie, toestemming en technische adapter

De oorspronkelijke metadata-stop is behouden in BLOCKED_METADATA_REPORT.md en
de preflightregistratie. De gebruiker gaf daarna expliciet toestemming voor exact
dezelfde hypothetische historische orderfilters als de gecontroleerde baseline.
Zij blijven `assumed`, zonder bewezen known_at/validiteitsperiode. Geen actuele
filters als historische feiten gebruikt. Volledige filterobjecten en kosten staan
in het manifest; tick 0,01 EUR, quantity-stap/minimum 0,00001, maximum 1.000.000,
minimum notional 10 EUR, fee 0,1% per zijde, spread 0,1% volledig, slippage 0,1%
per zijde. Decimal, nadelige tickafronding en fees omhoog op 1e-8 EUR behouden.

De geïsoleerde HistoricalRecoveryRunner hergebruikt de bestaande streamingrunner,
ledger, fillsimulator, analyses en centrale Risk Engine. Alleen het verliesreeksveto
wordt via dezelfde review als fase 6H-A vervangen door de opgeslagen timer/epoch.
De historische toelatings-/liquiditeitsgate is exact overgenomen en getest. Eén
gezamenlijke €200-portefeuille, één positie, maximaal 0,5% gepland risico en 50%
exposure; dagverlies 3%, drawdown 10% en noodstop blijven van kracht.

Aparte database: /workspace/phase6h_b_recovery.sqlite3. De oude auditdatabase wordt
uitsluitend via een uri=True, read-only/query-only verbinding gelezen. Bestaande
inputs worden in blokken van 256 rijen gekopieerd; de volledige inputseal is exact
gelijk. Geen downloads, nieuwe historische analyserapporten of baseline-replay.
De actieve bot, Risk Engine, strategieën en oude auditdatabase zijn ongewijzigd.

V1 van de voorbereiding stopte vóór kopiëren of financiële berekeningen door een
SQLite-URI-ATTACH-fout. De lege database, foutregistratie en oude manifestversie
zijn bewaard. Na een geteste technische kopieerreparatie is V2 opnieuw geregistreerd
vóór financiële uitvoering. Geen parameter, dataset of uitkomstdefinitie veranderde.
Preregistratiecommits e288d61 en c20fafc staan vóór de run op main.
Geldig manifest: `16aeac432cb79b0d1a87aa027acef6c20cdf815da6455f27ece7a576c87534b4`.
Het is inhoudsgebonden en read-only; Git maakt de eerdere versie controleerbaar,
maar is geen extern onveranderlijke WORM-opslag.

## Periode, causaliteit en checkpoints

Data [2024-01-01, 2025-01-01) UTC; warm-up 1–7 januari; eerste entry 8 januari
00:00, laatste entry 31 december 19:45. Alle twaalf maanden zijn volledig verwerkt,
met dezelfde gesloten 15m/1h/4h-bronnen, candlegrenzen en indicatorparameters.
De eindgrens 2025-01-01 is uitsluitend een terminale waardering van 2024-candles;
er is geen candle uit 2025 gelezen. Validatie 2025 en onafhankelijke test 2026
blijven gesloten. Stop 2 ATR, horizon 4 uur, entry open N+1, conservatieve stops/gaps.

De eerste drie financiële trade-records zijn vóór enige hervatting exact vergeleken
met de baseline, afgezien van plan-afhankelijke order-ID's. Saldo op de derde close:
197,03206319 EUR. De nieuwe verlieshistorie is nooit weggegooid of teruggezet.
Timer en epoch, cash, fees, positie, pending, risicoflags en auditanker worden samen
gecheckpoint. Na afloop geeft een heropende runner exact dezelfde toestand.

## Resultaten

| Maat | A: permanente pauze | B: herstel 24 uur |
|---|---:|---:|
|Startkapitaal EUR|200|200|
|Eindkapitaal EUR|197,03206319|179,92423059|
|Nettoresultaat EUR|-2,96793681|-20,07576941|
|Netto portefeuillerendement %|-1,48396840500|-10,03788470500|
|Gesloten trades|3|85|
|Winstpercentage %|0|31,76470588235294117647058824|
|Fees EUR|0,18502791|6,99473531|
|Spread EUR|0,0925116807000000|3,4973604835000000|
|Slippage EUR|0,1850233614000000|6,9947209670000000|
|Tickafronding EUR|0,0024592579000000|0,1117190495000000|
|Totale gemodelleerde frictie EUR|0,4650222100000000|17,5985358100000000|
|Maximale close-grid-drawdown %|1,48396840500|10,03788470500|
|Aanvullende conservatieve drawdown %|1,50932007500|10,03788470500|
|BUY-kandidaatsignalen|1953|1953|
|Geselecteerde/goedgekeurde entries|7|161|
|Geblokkeerde BUY-voorstellen|1946|1792|
|Geweigerde uitvoeringen|4|76|
|Unieke fills|6|170|
|Geactiveerde verliesreekspauzes|1|12|
|Afgeronde timer-expiries|n,v,t,|12|
|Tijd in verliesreekspauze, seconden|30700800,0|1036800,0|

Verschil B minus A in netto portefeuillerendement:
**-8,55391630000 procentpunt**.
Dit is een beschrijving van deze ene hypothetische ontwikkelproef; geen causale,
significantie- of winstclaim. Andere trades veroorzaken ook een andere blootstelling
én een ander pad van risicoblokkeringen. Geen theoretische koerslabels opgeteld.

Fees zijn apart geboekt; spread, slippage en tickafronding zitten al in de fills.
De totale gemodelleerde frictie is een diagnostische optelling en is niet opnieuw
van het nettoresultaat afgetrokken. Het effect van marktrisico en stopuitkomsten
is niet uitsluitend een kostenverschil. Gepland risico is geen garantie tegen
grotere gerealiseerde gapverliezen. Close-grid-drawdown en aanvullende conservatieve
candle-drawdown blijven afzonderlijke maten; de bestaande risicocontrole blijft leidend.

| Coin | A trades | A netto EUR | B trades | B netto EUR |
|---|---:|---:|---:|---:|
|BTCEUR|0|0|27|-6,99814758|
|ETHEUR|2|-1,98449225|18|-7,52939068|
|SOLEUR|1|-0,98344456|40|-5,54823115|

| Maand | B netto EUR | B gesloten trades |
|---|---:|---:|
|2024-01|-3,05573629|11|
|2024-02|-1,70945034|9|
|2024-03|-4,07205436|17|
|2024-04|-2,09524355|7|
|2024-05|-0,54988930|4|
|2024-06|-0,76189893|2|
|2024-07|-2,37068498|15|
|2024-08|-1,55611812|6|
|2024-09|-1,54414890|9|
|2024-10|-2,36054464|5|
|2024-11|0E-8|0|
|2024-12|0E-8|0|

## Risicoblokkeringen, kandidaten en uitvoering

De volledige redenverdeling per coin staat in result.json. BUY-kandidaat is een
voorstel; geselecteerde entry is toestemming met reservering; pas een geslaagde
simulatorfill is uitvoering. Een afgewezen uitvoering is geen gesloten trade.
Bestaande niet-BUY-HOLD-beoordelingen staan apart van geblokkeerde BUY-voorstellen.

B uitvoeringsweigeringen: `{"ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging": 76}`.
B afwijsredenen van niet-geselecteerde coinbeoordelingen:
`{"onvolledig vergelijkingsuniversum; geen nieuwe instap": 82827, "Uitsluitend BUY_CANDIDATE wordt beoordeeld": 16124, "centrale positielimiet: één open positie": 4083, "positieplaats en cash gereserveerd voor hoger gerangschikte kandidaat": 15, "liquiditeit_15m": 16, "verliesreekspauze": 58, "drawdownpauze": 111}`.
Andere geactiveerde ledger-risicobeveiligingen in B:
`{"daily_loss_pause": 0, "drawdown_pause": 1, "joint_emergency_stop": 0}`.
Deze gebeurtenissen worden niet opgeteld als onafhankelijke trades.

A heeft een permanente verliesreekspauze: de getoonde tijd loopt vanaf de derde
geboekte close tot periode-einde en is geen 24u-timer. B-tijd is de som van vaste
24u-intervallen, afgeknipt op einde ontwikkeling. Intervallen en epoch staan in
result.json. De derde oude close was 11 januari 16:00; de beslissing om 16:00
lag nog vóór afrekening, de eerstvolgende beslissing kende de pauze om 16:15.
Alle expiry-checkpoints zijn apart gecontroleerd op behoud van cash/fees/posities,
dagverlies-/drawdownstatus en noodstop.

## Tests, financiële verificatie en limieten

**536 tests geslaagd**, alle 534 bestaande behouden plus twee nieuwe tests voor
de exacte 1.937 grenzen en afwijzing van herstart/andere checkpoints; 0 mislukt,
één bestaande Starlette/AnyIO-waarschuwing. Volledige suite 22,44 s. Tests omvatten financiële gelijkheid, read-only inputkopie,
reeks-/epochherstel, heropening, rollback, deduplicatie, toelatingsgate en scope.
Geen nieuwe historische integratierun buiten de ene geautoriseerde jaarvergelijking.

Voorbereiding 43.699 s en 54.965 MiB piek-RSS.
Hervatsegment inclusief primaire resultaatverwerking 209.535 s en
46.594 MiB piek-RSS vóór de laatste heropening. Oorspronkelijke fasebudgetten
1800 s; afzonderlijk goedgekeurd hervatbudget 300 s. Ongewijzigd: 1,5 GiB
adresruimte, RSS-stop 1.288.490.188 bytes, 2 GiB vrije schijf, nul netwerk.
Tests 180 s/1,5 GiB. De oorspronkelijke 1.800s-stop is gerespecteerd; uitsluitend het expliciet
goedgekeurde aanvullende 300s-hervatbudget is gebruikt. Geen financiële run is
opnieuw vanaf nul gestart.

Onafhankelijke afsluitcontrole: 34724 checkpoints, 85
unieke gesloten trades en 12 expiry-overgangen;
volledige financiële/audit/checkpointketen gecontroleerd. Cash = 200 + gerealiseerd
resultaat, fees = som tradefees, geen eindpositie/pending, unieke entry-/exit-ID's.
Alle 392 oorspronkelijke gevolgde bestanden en de
volledige oorspronkelijke database blijven byte-identiek. Database-SHA-256:
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`. Bewijs in verification_approved.json.

## Beperkingen en open vervolgvragen

Dezelfde drie geselecteerde munten en één reeds bekeken ontwikkeljaar; afhankelijkheid
tussen coins en tijd, regimeverschillen en selectie-effecten beperken iedere
statistische conclusie. De oude baseline had slechts drie trades; meer trades in
B herstellen de onafhankelijkheid niet. Geen p-waarden of automatische promotie.
Hypothetische filters, vaste frictie en OHLCV-stopvolgorde bewijzen geen werkelijke
historische uitvoerbaarheid. Dit resultaat rechtvaardigt geen aanpassing van de
24 uur of een keuze van een nieuw filter achteraf.

Open vragen zijn uitsluitend vervolgvoorstellen: stabiliteit onder een later
expliciet toegestaan onafhankelijk ontwerp, uitvoeringsgevoeligheid bij beter
historisch metadatabewijs, en de scheiding tussen extra blootstelling en herstel-
mechanisme. Geen nieuwe periode, kostenvariant of ATR-filter is geactiveerd.
Stop na deze vergelijking; vervolgonderzoek vereist afzonderlijke toestemming.

## Expliciet goedgekeurde éénmalige hervatting

De oorspronkelijke 1.800s-run stopte op 11 december 2024 19:45 UTC. Het volledige
checkpoint en oude rapport zijn behouden; het rapport staat ook onder
resume_300/PREVIOUS_CHECKPOINT_REPORT.md. De gebruiker autoriseerde daarna exact
één aanvullende hervatting van maximaal 300 s. Preflight controleerde bronhashes,
configuratie, inputseal, cash/fees/posities, checkpoint en auditketen vóór de poging.
Deze registratie is vóór hervatting vastgelegd in commit 15987e9.

Nieuw hervatmanifest: `93d571082e54d2cbfe8d819668f67f48f91ab20e4a16a56efd78f2eed8daced5`. Een exclusief aangemaakt attempt.json
voorkomt een tweede poging. Er is exact één poging geweest: 1.937 resterende
grenzen, uitsluitend vanaf 11 december 20:00 UTC tot de eindgrens. De interne
realtimeklok omvat initialisatie, verwerking, resultaatverwerking en heropening;
voltooid in **209.538 s**, onder 300 s. Volledige poging piek-RSS
**53.059 MiB**. Het resultaatbestand meet RSS vóór de laatste
heropening; completion.json bevat het hogere volledige procespiekgetal.

Er is niet opnieuw vanaf januari gestart. De drawdownpauze bleef actief; er zijn
geen nieuwe trades, fills of fees toegevoegd na het startcheckpoint. Alle
34.465 replay-grenzen zijn nu afgehandeld; alle maanden zijn compleet en er
blijft geen resterende grens over. De eindtoestand heeft geen positie, pending
of reservering. Noodstop en overige risicoregels zijn ongewijzigd.

De onafhankelijke afsluitcontrole gebruikte een apart verificatieproces
(180 s/1,5 GiB) en voerde geen replay of nieuwe simulatie uit. De oorspronkelijke
auditdatabase en baseline-uitkomsten zijn byte-identiek. De nieuwe volledige
SQLite-database blijft in de workspace; Git bevat resultaten, curve, manifesten,
controlebewijs en checkpointidentificatie. Geen botactivatie of nieuwe onderzoeksfase.
