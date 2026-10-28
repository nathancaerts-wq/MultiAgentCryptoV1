# Fase 6D — Missed Opportunity Measurement

28 oktober 2026. Basis afce39d0c87bff9002a91339514cf99b6b697ff2.
Expliciete gebruikersgoedkeuring “Fase 6D: Missed Opportunity Measurement”.
**Volledig afgeronde prijsdiagnose, geen nieuwe portefeuillebacktest of handelsadvies.**
Alleen BTC/EUR, ETH/EUR en SOL/EUR, ontwikkeldata 2024. Geen validatie of test.

## Registratie vóór uitkomsten

Commit 0ba9995 is vóór uitvoering naar main gepusht, nadat alle 432 tests slaagden.
protocol.json en het inhoudsgebonden manifest leggen definities, bronbestanden,
configuratie en expliciete onderzoeksgoedkeuring vast. Manifest-SHA-256:
`933be8ac13e01a7dd4e4a749291306e2f026a87bf92431f17a3163f83a98e779`.
Het bestand is exclusief aangemaakt, read-only gemaakt, met hash en Git-versie
gebonden; iedere run controleert die hash en alle bronnen vóór en na verwerking.
De Git-commit identificeert onveranderlijke inhoud. De werkboom is geen externe
WORM-opslag: een beheerder kan bestanden/referenties herschrijven, wat deze lokale
binding niet onder hetzelfde manifest kan legitimeren. Geen absolute claim dat
het lokale bestand door niemand kan worden veranderd.

Het bestaande register bevat zes eerdere ontwikkelstudies; 2024 was al bekeken in
fase 6B en 6C. Nieuwe analyse en toegang zijn afzonderlijk in registration.json en
access.json geregistreerd. Oude registraties zijn niet overschreven, uitkomsten
niet als onafhankelijke nieuwe trades geteld. 2025/2026 kregen geen vrijgave.

## Exacte meetdefinities

Alle opgeslagen kwartierbeslismomenten t van 8 januari 00:00 tot en met
31 december 19:45 UTC. Per coin 34.448 momenten. De oude terminale grenzen zonder
nieuwe instap zijn uitgesloten; geen selectie op rendement of uitsluitend BUY.
Een signaal gebruikt candles gesloten op t; de volgende candle opent op t.
De zestien volledige bars in [t,t+4h) geven entry-open en laatste close op t+4h.
Laatste waardering is 31 december 23:45; geen bar uit 2025 nodig.

Bruto = eindclose / entry-open −1, zonder afgestemde drempel. Minimum = laagste low
van de zestien bars / entry-open −1. Dat is een negatieve excursie vanaf raw entry,
geen maximale drawdown langs een bekende intrabarroute.
Vaste hoeveelheid **0,001 coin per munt**, gekozen vóór uitkomstberekening;
geen gelijk EUR-gewicht of positie volgens een €200-portefeuille. Tick €0,01 uit het
bestaande hypothetische model. Fee 0,1% per zijde, volledige spread 0,1%, slippage
0,1% per zijde. Bestaande FillCosts: koopprijs omhoog en verkoopprijs omlaag naar
tick; fee per zijde omhoog op €0,00000001. Netto = q×(sell−buy)−beide fees.
Spread/slippage zitten in die prijzen en worden niet dubbel afgetrokken.

Deze vaste unit faalt bijvoorbeeld vaak het aangenomen minimum notional voor ETH
of SOL. Dat is bewust een prijsdiagnose zonder orderfilter- of cashgoedkeuring,
geen bewering dat de unit verhandelbaar was. Verschillende EUR-notionals betekenen
ook dat men de bruto EUR-labels niet als crosscoin-selectiescore moet gebruiken.

De horizon-close is een hypothetische liquidatiewaardering, geen uitvoerbare order
op dezelfde close. De bestaande tijdexit kan pas op de open na de deadline en bij
die bar-close worden geboekt; de horizonmarkering en echte simulatie-trade zijn dus
verschillende grootheden. Stopverliezen en koersgaten blijven voor orderstudies
onder de ongewijzigde simulator vallen, niet onder deze endpointmarkering.

Primaire analyse: alle overlappende momenten. Secundair: t_epoch modulo 14.400 =0,
dus UTC 00:00/04:00/08:00/12:00/16:00/20:00 binnen de entrygrenzen. Per coin raken
vensters elkaar alleen op hun grens. Gelijktijdige coins en opeenvolgende regimes
blijven afhankelijk; deze steekproef levert geen formeel onafhankelijke trades op.

Ontbrekende, dubbele, verkeerd geordende/onafgesloten bars of ontbrekende/corrupte
bekende rapporten stoppen de run als onvolledig. Geen forward-fill, prijsverzinsel,
stilzwijgende uitsluiting of nieuwe vensterkeuze. Werkelijk: nul ontbrekende vensters
en nul ontbrekende numerieke kenmerken. Alle brondata zijn de eerder officieel
gevalideerde 2024-archiefdata in de hash-gecontroleerde database.

## Aantallen en kosteninvloed

HOLD betekent uitsluitend de oorspronkelijke DecisionAgent-actie HOLD, niet alle
niet-geselecteerde BUY-kandidaten. Elke coin/tijdstip-combinatie heeft één label.

| Steekproef | N | Bruto positief | Bruto negatief | Neutraal | Netto positief vaste unit |
|---|---:|---:|---:|---:|---:|
|overlapping:all|103344|53454|49811|79|31366|
|overlapping:HOLD|101391|52483|48829|79|30721|
|utc4h:all|6459|3344|3110|5|2013|
|utc4h:HOLD|6307|3261|3041|5|1959|

Van de 52483 bruto positieve HOLD-vensters blijven er
30721 positief na de vaste kosten; 21762
zijn na kosten nul of negatief. Over alle momenten zijn dat respectievelijk
53454, 31366 en
22088. Dit zijn prijslabels, geen aantallen
haalbare trades en geen gerealiseerde gemiste portefeuillewinst.

De 48829 negatieve HOLD-vensters zijn mogelijke vermeden dalingen
onder deze markeerdefinitie. Ze bewijzen niet dat een toegestane trade verlies had
geleden: een stop, andere exit of onmogelijke instap kan een andere uitkomst geven.
Er worden **geen hypothetische P&L's opgeteld**.

### Per coin (alle overlappende momenten / oorspronkelijke HOLD)

| Groep | N | Positief | Negatief | Neutraal | Netto positief |
|---|---:|---:|---:|---:|---:|
|BTCEUR all|34448|18093|16354|1|8898|
|BTCEUR HOLD|34067|17894|16172|1|8801|
|ETHEUR all|34448|17757|16686|5|9967|
|ETHEUR HOLD|33906|17523|16378|5|9820|
|SOLEUR all|34448|17604|16771|73|12501|
|SOLEUR HOLD|33418|17066|16279|73|12100|

### Verdelingen in procenten

| Groep | Bruto min | Mediaan | Max | Minimum-low-excursie min | Mediaan | Max |
|---|---:|---:|---:|---:|---:|---:|
|overlapping:all|-17.579465|0.037051|21.093439|-25.037083|-0.684685|0.000000|
|overlapping:HOLD|-17.579465|0.037820|21.093439|-22.664304|-0.680414|0.000000|
|utc4h:all|-17.019283|0.048968|12.865882|-25.037083|-0.700647|0.000000|
|utc4h:HOLD|-14.008124|0.047723|12.865882|-19.495667|-0.696821|0.000000|

Zelfs later positieve bewegingen kunnen onderweg hun oorspronkelijke ATR-stop
raken. De endpointlabels rekenen geen stops weg en zeggen niets over beschikbare
cash, orderboek, fillkans of historische Binance-filters. Extreme lows blijven
zichtbaar; meerdere overlappende vensters kunnen dezelfde gebeurtenis bevatten.

## Risicopauze en afzonderlijke orderketen

| Oorspronkelijke primaire reden | N | Later bruto positief | Later negatief | Netto positieve unit |
|---|---:|---:|---:|---:|
|onvolledig vergelijkingsuniversum; geen nieuwe instap|83781|43416|40300|25095|
|Uitsluitend BUY_CANDIDATE wordt beoordeeld|18590|9596|8980|5976|
|centrale Risk Engine akkoord; cash en positieplaats gereserveerd|7|3|4|3|
|centrale positielimiet: één open positie|120|26|94|21|
|verliesreekspauze|793|384|409|247|
|liquiditeit_15m|53|29|24|24|

De verliesreekspauze bleef vanaf 11 januari 16:00 actief. De 793 expliciete
pauzeafwijzingen zijn mogelijke BUY/Entry-signalen die tot deze controle kwamen:
384 later bruto positief, 409 negatief, 247 netto positief in de vaste unitdiagnose.
Niet iedere pauzeminuut verschijnt als pauze-afwijzing: andere filters geven eerder
HOLD of REJECTED. De 247 mogen niet als 247 uitvoerbare gemiste winsten worden geteld.
Zij zouden minstens een hypothetische versoepeling vereisen, die hier niet plaatsvindt.

Afzonderlijke orderlaag: zeven oorspronkelijke ex-ante goedgekeurde entries,
met bestaande ATR-stop, sizing en Risk/Execution-hercontrole. Vier bij de volgende
open geweigerd, drie daadwerkelijk virtueel uitgevoerd en gesloten volgens de
bestaande fillsimulator. Hun oorspronkelijke trades zijn ongewijzigd opgenomen in
result.json: netto −€2,96793681. Geen nieuwe orders of schaduwportefeuille berekend.
Voor HOLD ontbreekt een geldige BUY-/Risk-goedkeuringsketen; die wordt niet achteraf
verzonnen omdat de koers later steeg. ATR-data alleen is geen handelsautorisatie.
De orderanalyse hergebruikt daarom uitsluitend de reeds beschikbare simulator-
uitkomsten; zij is geen nieuwe counterfactual-simulatie van ieder HOLD-moment.

## Indicator- en regimeverbanden

Alle kenmerken komen uit het oorspronkelijke rapport op t, met 32 afgesloten
candles per timeframe en de bevroren parameters. Frame-eindgrenzen worden getoetst
tegen floor_tf(t). Toekomstige candles worden pas daarna aan de afzonderlijke
labelfunctie gegeven. Geen indicatorherberekening met een later venster.

### 1h-regime en bestaande EMA-richting (overlappend, beschrijvend)

| Kenmerk | Waarde | Positief | Negatief | Neutraal |
|---|---|---:|---:|---:|
|regime|uncertain|30247|27789|44|
|regime|bearish|9748|8128|16|
|regime|sideways|2743|2748|1|
|regime|bullish|10716|11146|18|
|direction|flat|14816|14394|14|
|direction|down|18696|15618|34|
|direction|up|19942|19799|31|

| Achteraf bruto-label | N | Gemiddelde vooraf bekende RSI | Momentum | ATR / voorafgaande close |
|---|---:|---:|---:|---:|
|negative|49811|51.432080|0.00178235|0.00992777|
|positive|53454|50.518223|0.00036101|0.01019827|
|neutral|79|50.262025|0.00095332|0.01175834|

Dit zijn conditionele beschrijvingen, geen voorspelde winstkansen, causale effecten
of gekozen indicatorgrenzen. Aanvullende per-coin/HOLD/UTC4h-tabellen staan in
result.json. Kleine verschillen tussen gemiddelden zijn geen validatie van een
nieuwe regel; overlap, coin-correlatie en eerdere 2024-inzage blijven bestaan.

## Andere coin op hetzelfde beslismoment

De primaire vergelijking gebruikt uitsluitend toen bekende scannerscores. De
aparte known_score_audit voegt de coin-specifieke rapportregels samen op t; hij leest
geen uitkomstdata. Alle 34.448 tijdstippen hebben drie beschikbare scores.
Bij 60.924 van 103.344 coinmomenten had een andere coin een strikt hogere score:
BTC 6.144, ETH 24.148, SOL 30.632. Dit bevestigt exact de primaire classificatie.
Gelijke scores tellen niet als hoger; de bestaande UTC-tievolgorde blijft intact.
Hogere score betekent niet betere uitvoerbaarheid, toestemming of toekomstig rendement.
Er is geen toekomstige winnaar gekozen, ook niet als secundaire handelsbeslissing.

De aanvullende scorecontrole verwachtte aanvankelijk ten onrechte dat één rapport
alle rankingrijen bevatte. Dat rapport bevat alleen de eigen coin. De controle is
hersteld naar samenvoegen van drie oorspronkelijke regels; prijslabels en de
preregistratie zijn niet gewijzigd of opnieuw uitgevoerd. Dit was een fout in de
nieuwe scorecontrole, niet in de bestaande strategie of historische resultaten.

## Integriteit, middelen en afronding

Alle 103344 labels volledig voltooid. Tijd 75.503 s;
piek-RSS 72.887 MiB; limiet 600 s, 1 GiB adresruimte en
vroege RSS-stop bij 768 MiB. Scorecontrole 5.258 s binnen 180 s / 1 GiB.
Oorspronkelijke databasehash vóór en na identiek:
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.
Alle fase6B/6C-bestandshashes identiek; geen audit-/checkpoint-/resultaatmutaties.
Labels en samenvatting: experiments/phase6d/; het grote bronbestand blijft lokaal.

Alle 432 tests geslaagd: 420 behouden plus twaalf deterministische tests voor
labels, kosten, horizon, UTC, ontbrekende/duplicaat/toekomstige candles, vaste
hoeveelheid, niet-overlappende grid en causale scheiding van kenmerken en uitkomsten.
Eén bestaande Starlette/AnyIO-waarschuwing. Geen strategie-, Risk Engine-, optimizer-
promotie- of executiewijzigingen. Geen nieuwe 2025-/2026-analyse, echte of paperorders,
risicoreset of parameteroptimalisatie.

## Mogelijke volgende onderzoekshypotheses

1. Verschillen in netto-positieve labelaandelen tussen bestaande regimes blijven
   zichtbaar op de vaste UTC4h-steekproef; onderzoek alleen met vooraf vastgelegde
   afhankelijke-steekproefmethoden, zonder drempels op 2024 af te stellen.
2. Veel van de 247 netto-positieve pauzelabels zouden door tussentijdse excursies
   toch hun ATR-stop kunnen raken; dat is hier nog geen gemeten trade-uitkomst. Dat vergt een aparte,
   vooraf geregistreerde counterfactual-studie; huidige risicoregels blijven gelden.
3. Een hogere toenmalige scannerscore is niet noodzakelijk gekoppeld aan een betere
   stop-gecorrigeerde uitvoering. Een aparte onderzoeksvraag moet eerst de
   vergelijkingsmaat en gedeelde portefeuille expliciet vastleggen; geen oracle-selectie.

Deze hypotheses zijn na inzage geformuleerd, exploratief en niet geactiveerd.
Theoretische koersbewegingen blijven prijslabels, geen werkelijk haalbaar rendement.
Stop na fase 6D. Validatie en onafhankelijke test blijven gesloten.


Onafhankelijke eindcontrole: scripts/verify_phase6d.py vergelijkt ieder label met
zijn oorspronkelijke fase6C-beslissing, controleert alle bruto-/kostenformules en
steekproeftellingen opnieuw en toetst de oude bron- en databasehashes. Er worden
geen nieuwe toekomstige prijsreeksen opgevraagd. Uitkomst in verification.json.
