# Fase 6E — beschrijvende patroonanalyse 2024

Alleen de vooraf geregistreerde BTC/EUR-, ETH/EUR- en SOL/EUR-gegevens uit 2024.
Dit is een exploratieve beschrijving van **reeds bekeken** 2024-data. De vijf
hypotheses en 332 contrasten staan vooraf vast; er is geen nieuwe drempel, coin of
winnaar achteraf gekozen. De studie heeft geen p-waarden, Holm-verwerpingen,
inferentiële intervallen, causale claims of nieuwe handelsautorisatie.

## Registratie en integriteit

De expliciete gebruikersgoedkeuring is vóór uitkomstverwerking geregistreerd in
manifest `846c00564aae6e402fb3a343abea38140d4050aec87a8b6c47e7245c37a451ce`. De inhoudsgebonden manifestbestanden bevatten de
oude databasehash, fase-6D-labels, officiële gecachete januariarchieven,
indicatorcode, oorspronkelijke protocolversie, vijf hypotheses, goedgekeurde
beschrijvende amendering en de vaste 332 contrasten. De oorspronkelijke documenten
zijn niet overschreven. Het bestaande ontwikkelregister kende 2024 al als bekeken.
Een eerdere registratie stopte vóór uitkomstverwerking bij een tuple/JSON-controle;
een volgende poging werd op basis van oplopend geheugen gecontroleerd onderbroken
zonder definitief resultaat. Beide logs/registraties zijn behouden. De gecorrigeerde
versie is eveneens vóór haar resultaten op main gezet.

De oorspronkelijke datasetcache bevatte slechts 32 candles per timeframe. Voor
ΔRSI is de ene extra oudere 2024-candle per coin en timeframe gelezen uit hetzelfde
reeds officieel SHA-256-gecontroleerde maandarchief. Geen netwerkdownload of
andere periode. De werkelijke prijslabels zijn niet opnieuw berekend: exact de
bestaande 103.344 fase-6D-rijen zijn verbonden met kenmerken die op hun
beslismoment bekend konden zijn. De oude indicatoruitkomsten zijn per venster
exact gereproduceerd voordat de nieuwe beschrijving werd opgeslagen.

## Omvang en kostencontext

De vaste primaire vergelijking is de UTC4h-grid; de overlappende kwartiermomenten
staan afzonderlijk. Per coin raken de 4h-vensters elkaar alleen op hun grenzen;
gelijktijdige coins en opeenvolgende regimes blijven afhankelijk. De netto-labels
gebruiken de reeds vastgelegde vaste 0,001-coinprijsdiagnose met 0,1% fee per zijde,
0,1% volledige spread en 0,1% slippage per zijde. Het zijn geen uitvoerbare orders
of EUR-gelijkgewogen portefeuillewinsten.

### UTC4h (primair)

| Groep | N | Bruto + | Bruto − | Neutraal | Netto + |
|---|---:|---:|---:|---:|---:|
|Alle coinmomenten|6459|3344|3110|5|2013|
|Oorspronkelijke HOLD|6307|3261|3041|5|1959|
|HOLD tijdens pauze|6243|3227|3011|5|1931|
|HOLD buiten pauze|64|34|30|0|28|


### Overlappende 15m-momenten (afzonderlijk)

| Groep | N | Bruto + | Bruto − | Neutraal | Netto + |
|---|---:|---:|---:|---:|---:|
|Alle coinmomenten|103344|53454|49811|79|31366|
|Oorspronkelijke HOLD|101391|52483|48829|79|30721|
|HOLD tijdens pauze|100377|51900|48400|77|30275|
|HOLD buiten pauze|1014|583|429|2|446|


Per coin, uitsluitend HOLD op UTC4h:

| Groep | N | Bruto + | Bruto − | Neutraal | Netto + |
|---|---:|---:|---:|---:|---:|
|BTCEUR|2119|1110|1009|0|564|
|ETHEUR|2114|1084|1028|2|613|
|SOLEUR|2074|1067|1004|3|782|


## Vooraf vastgelegde hypothesen

Alle tabellen hieronder gebruiken de UTC4h-grid. `A` vergelijkt bruto positieve
versus bruto negatieve HOLDs; `B` netto positieve versus netto niet-positieve HOLDs;
`C` vergelijkt pauze versus daarbuiten; `D` EMA versus aligned_trend BUY-kandidaten.
Een verschil is uitsluitend het verschil van de twee getoonde groepsgemiddelden.
Mediaan en p10–p90 zijn empirische spreidingsmaten, geen betrouwbaarheidsinterval.
De volledige uitwerking van alle 332 contrasten, voor beide steekproeven en met
n, ontbrekendheid, minimum/maximum en status per groep, staat in
`experiments/phase6e_descriptive/contrast_summary.csv` en `result.json`.

### 1. Oorspronkelijke scannerscore en rang

| Contrast (links − rechts) | Stratum | n links/rechts | Verschil gemiddelde | Mediaan links/rechts | p10–p90 links/rechts | Status |
|---|---|---:|---:|---:|---|---|
|A: scanner_score|pooled|3261/3041|-0.0362982|50/50|25–75/25–75|descriptive|
|A: scanner_score|BTCEUR|1110/1009|0.123885|66.6667/66.6667|50–83.3333/50–83.3333|descriptive|
|A: scanner_score|ETHEUR|1084/1028|-0.139304|50/50|33.3333–66.6667/33.3333–66.6667|descriptive|
|A: scanner_score|SOLEUR|1067/1004|-0.693936|33.3333/33.3333|16.6667–50/16.6667–50|descriptive|
|B: scanner_score|pooled|1959/4348|-2.83004|50/50|16.6667–75/25–75|descriptive|
|B: scanner_score|BTCEUR|564/1555|0.68442|66.6667/66.6667|50–83.3333/50–83.3333|descriptive|
|B: scanner_score|ETHEUR|613/1501|0.387326|50/50|33.3333–66.6667/33.3333–66.6667|descriptive|
|B: scanner_score|SOLEUR|782/1292|-1.24428|33.3333/33.3333|16.6667–50/16.6667–50|descriptive|
|B: scanner_rank|pooled|1959/4348|0.108174|2/2|1–3/1–3|descriptive|
|B: scanner_rank|BTCEUR|564/1555|-0.018019|1/1|1–2/1–2|descriptive|
|B: scanner_rank|ETHEUR|613/1501|-0.0307647|2/2|1–3/1–3|descriptive|
|B: scanner_rank|SOLEUR|782/1292|0.0546843|3/3|2–3/1–3|descriptive|


Een hogere score is slechts informatie die destijds beschikbaar was; geen
Risk-goedkeuring of aanwijzing dat een andere munt uitvoerbaar winstgevender was.

### 2. RSI-niveau en verandering

| Contrast (links − rechts) | Stratum | n links/rechts | Verschil gemiddelde | Mediaan links/rechts | p10–p90 links/rechts | Status |
|---|---|---:|---:|---:|---|---|
|A: 1h:rsi|pooled|3261/3041|-1.56359|49.6789/51.6009|34.5059–65.6528/35.8451–66.9157|descriptive|
|A: 1h:rsi|BTCEUR|1110/1009|-1.65758|50.1233/52.2049|34.8226–66.732/36.4223–67.2869|descriptive|
|A: 1h:rsi|ETHEUR|1084/1028|-1.16207|49.7728/51.584|34.9664–65.6656/34.8456–66.8658|descriptive|
|A: 1h:rsi|SOLEUR|1067/1004|-1.90105|48.9822/50.5986|33.3437–64.5325/36.3384–66.0501|descriptive|
|A: 1h:delta_rsi|pooled|3261/3041|-0.526589|-0.41267/0.234979|-6.20221–5.67838/-5.46761–5.70131|descriptive|
|A: 1h:delta_rsi|BTCEUR|1110/1009|-0.624015|-0.497885/0.455584|-6.01737–5.9684/-5.17646–5.73364|descriptive|
|A: 1h:delta_rsi|ETHEUR|1084/1028|-0.598269|-0.409337/0.237948|-6.68594–5.71006/-5.56198–5.70236|descriptive|
|A: 1h:delta_rsi|SOLEUR|1067/1004|-0.355479|-0.300837/0.0409781|-6.11391–5.51316/-5.46312–5.70131|descriptive|
|B: 1h:delta_rsi|pooled|1959/4348|-0.547605|-0.52913/0.0807668|-6.73104–5.83182/-5.4779–5.63143|descriptive|
|B: 1h:delta_rsi|BTCEUR|564/1555|-0.537274|-0.62555/0.120056|-6.58714–6.1848/-5.53322–5.63749|descriptive|
|B: 1h:delta_rsi|ETHEUR|613/1501|-0.608238|-0.633404/0.117066|-7.29724–5.77644/-5.56979–5.63694|descriptive|
|B: 1h:delta_rsi|SOLEUR|782/1292|-0.498955|-0.448067/0.0452938|-6.51794–5.53664/-5.20675–5.60238|descriptive|


ΔRSI gebruikt een volledig eerder 32-candlevenster. Een verschil hier is geen
nieuwe RSI-grens of voorspellingsbewijs; ook 15m en 4h staan in de volledige tabel.

### 3. EMA-afstanden en selectie

| Contrast (links − rechts) | Stratum | n links/rechts | Verschil gemiddelde | Mediaan links/rechts | p10–p90 links/rechts | Status |
|---|---|---:|---:|---:|---|---|
|B: 1h:ema_gap|pooled|1959/4348|-0.000866894|-0.000249202/0.000315765|-0.0108778–0.0107736/-0.00829085–0.00955064|descriptive|
|B: 1h:ema_gap|BTCEUR|564/1555|-0.000809136|-4.91695e-05/0.000452544|-0.0088435–0.00869219/-0.00615153–0.00760811|descriptive|
|B: 1h:ema_gap|ETHEUR|613/1501|-0.000553057|-0.000108881/0.000314293|-0.0100725–0.0100988/-0.00781311–0.00825023|descriptive|
|B: 1h:ema_gap|SOLEUR|782/1292|-0.00115939|-0.000530071/8.18989e-05|-0.0131889–0.0123972/-0.0109891–0.013222|descriptive|
|B: up_count|pooled|1959/4348|-0.0125097|1/1|0–2/0–2|descriptive|
|B: up_count|BTCEUR|564/1555|0.0174363|1/1|0–2/0–2|descriptive|
|B: up_count|ETHEUR|613/1501|0.00881087|1/1|0–2/0–2|descriptive|
|B: up_count|SOLEUR|782/1292|-0.0895814|1/1|0–2/0–3|descriptive|
|D: 1h:ema_gap|pooled|2491/152|0.000499011|0.00613749/0.00574579|0.00260451–0.0152539/0.00236497–0.0152373|descriptive|
|D: 1h:ema_gap|BTCEUR|773/34|0.00122783|0.00521265/0.0042848|0.00247806–0.0124156/0.00224939–0.00982206|descriptive|
|D: 1h:ema_gap|ETHEUR|822/39|0.00149766|0.00553947/0.00565226|0.00250077–0.0133279/0.00242432–0.00945875|descriptive|
|D: 1h:ema_gap|SOLEUR|896/79|0.000568793|0.00809059/0.0073413|0.00289936–0.0185494/0.00236497–0.0177402|descriptive|
|D: up_count|pooled|2491/152|-0.882778|2/3|1–3/3–3|descriptive|
|D: up_count|BTCEUR|773/34|-0.92238|2/3|1–3/3–3|descriptive|
|D: up_count|ETHEUR|822/39|-0.907543|2/3|1–3/3–3|descriptive|
|D: up_count|SOLEUR|896/79|-0.825893|2/3|1–3/3–3|descriptive|


Bestaande kandidaat-aantallen in dit exacte instapuniversum, UTC4h:
{'BTCEUR': 773, 'ETHEUR': 822, 'SOLEUR': 896} voor EMA; {'BTCEUR': 34, 'ETHEUR': 39, 'SOLEUR': 79} voor
aligned_trend. Overlappend: {'BTCEUR': 12304, 'ETHEUR': 13140, 'SOLEUR': 14328} en
{'BTCEUR': 381, 'ETHEUR': 542, 'SOLEUR': 1030}. Beide selecties gebruiken hetzelfde
beslismoment; `D` beschrijft hun kenmerken. Oorspronkelijke aparte jaarruns
hadden respectievelijk vijf en drie virtuele trades en verschillende blootstelling
aan de markt; hun rendement is hier niet opnieuw getest. Sommige momenten kunnen
in beide kandidaatsets zitten. Er is geen nieuwe EMA-run uitgevoerd.

### 4. Volatiliteit en volume

| Contrast (links − rechts) | Stratum | n links/rechts | Verschil gemiddelde | Mediaan links/rechts | p10–p90 links/rechts | Status |
|---|---|---:|---:|---:|---|---|
|B: 1h:relative_atr|pooled|1959/4348|0.00183154|0.0100547/0.00836638|0.00587665–0.017807/0.00493541–0.0150933|descriptive|
|B: 1h:relative_atr|BTCEUR|564/1555|0.00129485|0.0076622/0.00670042|0.00487447–0.0130915/0.00409515–0.0111807|descriptive|
|B: 1h:relative_atr|ETHEUR|613/1501|0.00146699|0.00904752/0.00790357|0.00566871–0.015853/0.00509515–0.0129202|descriptive|
|B: 1h:relative_atr|SOLEUR|782/1292|0.00113782|0.0126273/0.0118733|0.00869971–0.0220479/0.00788987–0.0191708|descriptive|
|B: 1h:volume_ratio|pooled|1959/4348|0.125956|0.840948/0.773306|0.284355–2.32502/0.248482–1.9909|descriptive|
|B: 1h:volume_ratio|BTCEUR|564/1555|0.146025|0.905628/0.783957|0.270267–2.45563/0.203952–2.1106|descriptive|
|B: 1h:volume_ratio|ETHEUR|613/1501|0.192916|0.823292/0.76199|0.260017–2.42996/0.235557–1.93507|descriptive|
|B: 1h:volume_ratio|SOLEUR|782/1292|0.0651638|0.817033/0.771096|0.315323–2.10314/0.314004–1.88034|descriptive|
|B: 1h:volume_change|pooled|1959/4348|0.0470978|-0.059714/-0.0794142|-0.583108–1.28654/-0.603601–1.21372|descriptive|
|B: 1h:volume_change|BTCEUR|564/1555|0.0562072|-0.0338449/-0.0761575|-0.567134–1.39988/-0.585889–1.24281|descriptive|
|B: 1h:volume_change|ETHEUR|613/1501|0.110515|-0.0679173/-0.0885246|-0.600566–1.28654/-0.635651–1.0832|descriptive|
|B: 1h:volume_change|SOLEUR|782/1292|0.0020767|-0.0673728/-0.0793892|-0.571594–1.19679/-0.58023–1.25843|descriptive|


Deze kenmerken zijn beschrijvend. Een nulvolumedeler wordt als ontbrekend geteld;
geen volumefilter of stopafstand is aangepast. 15m en 4h staan in de volledige tabel.

### 5. Verliesreekspauze

| Contrast (links − rechts) | Stratum | n links/rechts | Verschil gemiddelde | Mediaan links/rechts | p10–p90 links/rechts | Status |
|---|---|---:|---:|---:|---|---|
|C: gross_positive|pooled|6243/64|-0.0143511|1/1|0–1/0–1|insufficient_support|
|C: gross_positive|BTCEUR|2097/22|0.115945|1/0|0–1/0–1|insufficient_support|
|C: gross_positive|ETHEUR|2093/21|-0.155439|1/1|0–1/0–1|insufficient_support|
|C: gross_positive|SOLEUR|2053/21|-0.00944031|1/1|0–1/0–1|insufficient_support|
|C: net_positive|pooled|6243/64|-0.128194|0/0|0–1/0–1|insufficient_support|
|C: net_positive|BTCEUR|2097/22|-0.0525643|0/0|0–1/0–1|insufficient_support|
|C: net_positive|ETHEUR|2093/21|-0.284281|0/1|0–1/0–1|insufficient_support|
|C: net_positive|SOLEUR|2053/21|-0.0520493|0/0|0–1/0–1|insufficient_support|


De pauzestatus is afgeleid uit de onveranderde oorspronkelijke ledgerprefix vanaf
de derde verliesexit op 11 januari 2024 om 16:00 UTC, na verwerking van die candle.
De oude 793 expliciete pauze-afwijzingen zijn **niet** hetzelfde als alle HOLDs
tijdens de pauze. De pauze verdeelt dit jaar sterk naar kalenderperiode en
marktomgeving. Een positief prijslabel tijdens een veto was geen toegestane trade.
`insufficient_support` betekent geen robuuste basis voor zelfs een latere
inferentiële vergelijking; de ruwe beschrijving blijft transparant zichtbaar.

## Marktregimes op de primaire grid

Oorspronkelijk 1h-regime bij HOLD, zonder nieuwe regimegrenzen:

| Groep | N | Bruto + | Bruto − | Neutraal | Netto + |
|---|---:|---:|---:|---:|---:|
|bearish|1122|628|493|1|415|
|bullish|1230|598|630|2|380|
|sideways|318|162|156|0|71|
|uncertain|3637|1873|1762|2|1093|


Regimes zijn ook op het beslismoment bekend. Bruto/netto aandelen verschillen
mogelijk omdat kosten kleine stijgingen uitfilteren. Deze tabellen zeggen niets
over een causaal effect van regime of pauze.

## Ontbrekende gegevens en steun

| Steekproef | Vaste contrasten | Statusverdeling | Ontbrekende featurelidmaatschappen* |
|---|---:|---|---:|
| UTC4h | 332 | {'descriptive': 324, 'insufficient_support': 8} | 4 |
| Overlappend | 332 | {'descriptive': 324, 'insufficient_support': 8} | 44 |

* Een ontbrekende feature kan in meer dan één vooraf vastgelegd contrast vallen;
dit is geen aantal unieke missende candles. Beide groepen tonen afzonderlijk
`selected`, `missing`, `n`, aantal tijdgroepen en zevendaagse kalenderblokken.
Essentiële ontbrekende bronnen, duplicaten en indicatorafwijkingen zouden de run
hebben gestopt. Groepen met minder dan twintig kalenderblokken, dertig tijdgroepen
of meer dan 1% ontbrekendheid krijgen expliciet onvoldoende steun. Een lege groep
heeft geen ingevuld gemiddelde of verschil. Er is nergens een ontbrekende waarde
op nul gezet of met een later candle aangevuld.

## Grenzen van de conclusies en vervolg

Deze patronen zijn op een eerder bekeken ontwikkeljaar beschreven. Grote aantallen
kwartierlabels zijn overlappend en drie coins bewegen samen. De UTC4h-grid verwijdert
binnen-coin-overlap, maar maakt de tijdgroepen niet onafhankelijk. Dit rapport trekt
geen significantie-, effectiviteits-, voorspellings- of winstconclusie. De 332
beschrijvingen zijn niet gerangschikt op het grootste verschil. Geen parameterzoektocht,
strategiepromotie, automatische paperorders, risk-reset of backtest uitgevoerd.

Maximaal drie prioritaire vervolgonderzoeken, naar bronkwaliteit en toetsbaarheid:

1. Controleer of oorspronkelijke scannerherkomst en rang in een nieuwe,
   afzonderlijk geregistreerde dataset volledig en tijdig reproduceerbaar zijn.
2. Onderzoek onder een nieuw protocol welke volume-/ATR-metingen stabiel blijven
   buiten deze eerdere 2024-inzage, met expliciete datagaten- en coinafhankelijkheid.
3. Beoordeel eerst de eventvolgorde en voldoende niet-gepauzeerde vergelijkingsduur
   voordat een afzonderlijke pauzevraag wordt overwogen; geen versoepeling nu.

Validatie 2025 en onafhankelijke test 2026 blijven gesloten. De code voor strategie,
indicatoren, uitvoering en risico is byte-identiek gebleven; alle oude financiële
resultaten en auditlogs blijven behouden. De run gebruikte een limiet van 600 s,
1 GiB adresruimte en een vroege stop bij 768 MiB. Uitvoeringstijd
277.776 s, piek-RSS 297.855 MiB.
Volledige onafhankelijke artifact-/broncontrole staat in
`experiments/phase6e_descriptive/verification.json`.
