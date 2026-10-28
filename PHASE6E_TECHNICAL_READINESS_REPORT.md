# Fase 6E — technische uitvoerbaarheidscontrole

Basiscommit `2f0a021eed1b3102e6f00af9843237d2f5a773de`.
Bij aanvang schone werkmap. De onderbroken controle hervat met behoud van code,
referentiewaarden en beide capaciteitsmetingen. Geen onderzoeksproces meer actief.

**Conclusie: feature- en statistiekkern technisch werkend en reproduceerbaar;
geen vrijgave voor historische patroonanalyse.** De 9.999-herhalingenberekening past
ruim binnen de limieten, maar de p-waarderesolutie is onvoldoende voor robuuste
beslissingen rond de strengste Holm-grens. Daarvoor is een expliciete methodologische
keuze nodig. De bestaande protocol- en hypothesedocumenten zijn ongewijzigd.
Geen nieuwe historische kenmerken met prijslabels vergeleken; geen backtest of
nieuwe analyse van validatie 2025 of onafhankelijke test 2026.

## 27 kenmerken en causaliteit

scripts/phase6e_technical.py bevat geïsoleerde onderzoeksfuncties, zonder historische
reader, orders, optimizerpromotie of wijziging van productieconfiguraties.
Acht kenmerken per timeframe plus drie gezamenlijke kenmerken:

| Kenmerken | Benodigde, vooraf beschikbare informatie | Controle |
|---|---|---|
| RSI, ΔRSI (6) | Twee eigen 32-candlevensters tot e en e−TF | Bestaande technical(), 33 candles totaal |
| EMA-gap, absolute gap, close/EMA21−1 (9) | Gesloten close, EMA9 en EMA21 tot e | Originele rolling initialisatie, exacte bronreproductie |
| ATR/close (3) | ATR14 en close van hetzelfde timeframe | Geen vervanging door laatste 15m-close |
| Volumeratio, volumeverandering (6) | Laatste volume, twintig voorafgaande volumes, vorige volume | Geen toekomstige volumes; nuldelers expliciet ontbrekend |
| Score, rang, aantal up-timeframes (3) | Scores van drie coins op t, huidige frame-richtingen | Snapshot-tijd exact t, gelijke scores gelijke rang |

Totaal 27. Alle financiële/indicatorberekeningen blijven Decimal met precisie 28;
een andere actieve precisie wordt geweigerd. Float64 wordt alleen voor statistische
sommen en bootstrap gebruikt, nooit om bestaande fills of financiële resultaten te
herberekenen. Volumeratio gebruikt base-volume, niet quote-volume.

Elke broncandle wordt opnieuw met Candle gevalideerd. Exact 33 chronologische,
volledige, aaneengesloten bars vereist; symbol, timeframe, UTC, OHLCV en grenzen
worden gecontroleerd. Voor actuele indicatoren worden alleen de laatste 32 gebruikt;
voor de vorige RSI de eerste 32. Ontbrekende/gap-/duplicaat-/toekomstige data of
een afwijkende opgeslagen indicator veroorzaken een fout. Geen interpolatie.
Een ontbrekende scannerwaarde blijft None; zonder alle drie scores is de rang
onbekend, geen nulrang. Compleetheid van de gepoolde scorevergelijking is verplicht.

Dit bewijst berekenbaarheid en de extractiecontracten met synthetische input.
Een historische extractie/volledigheidscontrole van alle nieuwe features is bewust
niet uitgevoerd. De latere adapter moet reportparameters en bronhashes verifiëren,
scoremetadata op t samenvoegen en de labelvrije extractie verzegelen vóór een join.
Een zelf aangeleverde correcte tijdstempel alleen bewijst geen bronherkomst.

## Tijdsgrenzen

Voor ieder TF eindigt de actuele candle op e=floor_TF(t), nooit op de eerstvolgende
hogere grens. Candles vertegenwoordigen [open,close), met close als exclusief einde.
Voorbeelden, uitsluitend UTC:

| Beslismoment | 15m-einde | 1h-einde | 4h-einde |
|---|---|---|---|
| 8 januari 00:00 | 00:00 | 00:00 | 00:00 |
| 8 januari 00:15 | 00:15 | 00:00 | 00:00 |
| 8 januari 03:45 | 03:45 | 03:00 | 00:00 |
| 31 december 19:45 | 19:45 | 19:00 | 16:00 |

De vroegste benodigde 4h-warm-up begint 2 januari 12:00 (33×4h vóór 8 januari),
volledig binnen 2024. Vensters tot en met de vorige TF-grens worden met hun eigen
rolling seed berekend. De laatste beslisgrens blijft 31 december 19:45; voor de
bestaande labels is de horizonmarkering 23:45. Geen nieuwe labels berekend.
De bootstrap accepteert uitsluitend opeenvolgende UTC4h-tijdgroepen; 15m-overlap,
dubbele tijdgroepen, gaten of los resamplen van coins worden geweigerd.

## Exacte oorspronkelijke indicatorreproductie

De bestaande crypto/indicators.py is byte-identiek aan de basis. De extractor
vergelijkt RSI, EMA-fast/slow/gap, ATR en richting exact met de meegegeven
opgeslagen bronwaarden. Geen alternatieve indicatorimplementatie of seed.

Twee referenties:

- Reeds bestaande fase-3-lineaire synthetische reeks close=100..131:
  RSI=100, EMA9=127, EMA21=121, ATR14=2. Flat-case RSI=50.
- Niet-lineaire synthetische reeks close=100+(i modulo 7), high=close+2,
  low=close−2, vastgelegd met de originele indicatorcode uit de basiscommit.
  Volledige huidige/vorige uitkomsten staan in
  tests/fixtures/phase6e_indicator_reference.json. Voor huidige 32 bars:
  RSI=53.79062621576983463274597875;
  EMA9=102.9032241066218387074798934;
  EMA21=102.9028699546721886899869631;
  ATR=4.500978253244363822535736427.

De vorige RSI is 52.34119640874684880626264781; de extractor reproduceert ook het
exacte verschil. Deze niet-lineaire golden reference is een regressiereferentie van
de originele code, geen onafhankelijk bewijs van een externe RSI-conventie. De
lineaire handcontrole levert daarnaast een onafhankelijk controleerbare uitkomst.
Geen nieuwe historische indicator-/labelvergelijking uitgevoerd. De eerste nieuwe
test faalde op het aantal geschreven eindnullen in een Decimal-string; de numerieke
controle is hersteld naar Decimal-gelijkheid. Geen indicatorcode gewijzigd.

## Bootstrap en Holm: implementatiecontrole

- Exacte familie: A=108, B=108, C=8, D=108; totaal 332 unieke identiteiten.
- Eén random.Random(606)-drawmatrix voor alle contrasten. Per replicatie uniforme
  circulaire blokstarts, bloklengte 42 UTC4h-tijdgroepen, laatste blok afgeknipt.
  Alle drie coins en beide groepen behouden dezelfde resamplingindices.
- Blok-prefixsommen van vier voldoende statistieken: som/count links en rechts.
  Eerst sommen en aantallen resamplen, daarna groepsgemiddelden delen. Geen
  onjuiste gelijke weging van groepsgemiddelden bij verschillende groepsgrootte.
  D mag hetzelfde coinmoment in beide groepen hebben; de koppeling blijft behouden.
- Expliciete, langzame expansie van de individuele tijdindices geeft dezelfde
  uitkomsten bij een gedeeltelijk laatste blok en bij exact deelbare bloklengte,
  ook met ongelijke groepsgewichten. Herhaling met dezelfde seed geeft gelijk resultaat.
- p=(1+#{|θ*−θ|>=|θ|})/(B+1), inclusief gelijkheid en de +1-term, handmatig getoetst.
- Holm sorteert alle 332 p-waarden, vermenigvuldigt met het resterende familieaantal,
  neemt cumulatief maximum en kapt op 1. Ontbrekende toetsen participeren als 1,
  maar blijven zichtbaar als None. Bekende voorbeelden, ties en ongeldige p's getest.
- Minimum twintig vaste zevendaagse blokken én dertig tijdgroepen in beide groepen;
  lege groep, lege replicatie, nulvariatie: niet toetsbaar. Geen nieuwe replicatie
  trekken om een ongunstige lege groep weg te werken. Ontbrekend >1% of onvolledig
  pooled-score-universum maakt een contrast niet toetsbaar.

Implementatie en formules zijn volgens het voorstel getest. Dit is **geen bewijs
dat de bootstrap-p-waarden exact uniform onder iedere nulhypothese zijn**. De
gecentreerde, niet-gestudentiseerde block-bootstrap is een asymptotische benadering;
ratio's, kleine groepen, endogene selectie en niet-stationaire regimes kunnen de
kalibratie verstoren. De +1-term maakt dit niet tot een exacte randomisatietoets.
Holm beheerst family-wise error onder willekeurige afhankelijkheid alleen wanneer
de afzonderlijke p-waarden geldig/superuniform zijn; het repareert geen foutieve
bootstrapkalibratie, historische featureselectie of de eerdere 2024-inzage.

Zevendaagse blokken ondervangen niet gegarandeerd langere afhankelijkheid. De
circulaire verbinding jaar-einde/jaar-begin is een bootstrapaanname, geen echte
historische overgang. Puntgewijze 95%-percentielintervallen zijn niet simultaan.
Nearest-rank wordt voor percentielen gebruikt; dit expliciete uitvoeringsdetail
moet in een later goedgekeurd manifest staan. Geen zoektocht naar een gunstige
kwantielmethode. Float-sommen kunnen afwijken op machineprecisie; exacte financiële
Decimal-gelijkheid wordt hiermee niet vervangen.

## P-waarderesolutie: noodzakelijke keuze vóór inferentiële claims

Vastgelegde B=9.999 geeft resolutie 1/(B+1)=0,0001.
De eerste Holm-grens bij 332 toetsen is 0,05/332=0,0001506024.
Alleen **nul** bootstrapoverschrijdingen geeft een p die die eerste grens passeert;
één overschrijding geeft 0,0002 en passeert niet. Dat is technisch berekenbaar,
maar onvoldoende nauwkeurig voor robuuste uitspraken rond deze grens.

Zelfs nul overschrijdingen geeft een eenzijdige 95%-bovengrens voor de onderliggende
bootstrap-tailkans van circa 0,00029956, boven de Holm-grens. Dit is alleen
Monte-Carlo-onzekerheid voor de bootstrapverdeling, geen interval voor de werkelijke
nul-p-waarde. Bij de grens is de relatieve Monte-Carlo-standaardfout circa 81,5%.
Berekening staat in experiments/phase6e_technical/p_resolution.json.

Niet-geactiveerde opties voor een nieuwe protocolbeslissing:

| B | Resolutie | Relatieve MC-SE bij strengste grens | Lineaire projectie statistiekkern |
|---|---:|---:|---:|
| 9.999, huidig | 0,0001 | 81,5% | 37,06 s gemeten |
| 99.999 | 0,00001 | 25,8% | circa 371 s, niet gemeten |
| 999.999 | 0,000001 | 8,15% | circa 3.706 s, niet gemeten |

Voor hoogstens 10% relatieve MC-SE bij die grens zijn theoretisch minimaal 663.900
replicaties nodig. Dit is een voorgesteld precisiedoel, geen bestaand criterium.
Meer replicaties verhelpen bootstrapbias niet. 999.999 past op basis van deze
projectie niet binnen de huidige 600 seconden. Geen budget verhoogd, familie
verkleind, B aangepast of nieuwe grote meting gestart.

Aanbevolen besluit: houd B=9.999 alleen voor expliciet beschrijvende verkenning
zonder robuuste significantieclaims nabij de Holm-grens; voor inferentiële conclusies
eerst een afzonderlijk goedgekeurde protocolwijziging met precisiedoel, methode
voor Monte-Carlo-onzekerheid/kalibratie, B en passend getest uitvoeringsbudget.
Dit rapport activeert geen van beide routes. Een sequentiële stopregel zou eveneens
een nieuwe registratie vereisen; niet alsnog doorrekenen tot een gunstige p.

## Capaciteit en reproduceerbaarheid

Geen nieuwe capaciteitsrun nodig bij hervatting; beide opgeslagen resultaten behouden.
Synthetisch jaarformaat: 2.153 tijdgroepen × drie gekoppelde coins, 332 contrasten,
9.999 replicaties per contrast, seed 606. Alle contrasten doorlopen de statistiekkern.

| Opgeslagen meting | Tijd | Piek-RSS |
|---|---:|---:|
| Eerste volledige meting | 37,695 s | 29,516 MiB |
| Herhaling, met bronhashbinding | 37,060 s | 29,484 MiB |

Beide resultaatdigests identiek:
`89f816fe2a09f20c8f319f8e4d6f1c983026fa84b6836f356bbb2fc2b26a5019`.
De tweede meting volgde op de scanner-snapshotguard, met ongewijzigde statistiekkern;
geen historische labels gebruikt. Capaciteitsbestanden worden exclusief aangemaakt
om bestaande resultaten niet te overschrijven. Python 3.12.14; geen nieuwe dependency.
Limieten: 600 s hard alarm, 1 GiB adresruimte, vroege RSS-stop bij 768 MiB,
buitenste timeout 605 s als opruimbeveiliging.

Dit is capaciteit van de volledige 332-contraststatistiekkern op synthetische,
vooraf geaggregeerde data. Het meet niet de volledige historische reportextractie,
bron-I/O, featurejoin of kwaliteit van werkelijke groepen. Geen claim dat die hele
latere pipeline al binnen 600 s is gevalideerd. Basale feature-extractie is functioneel
getest; een historische reader/orchestrator voor dit onderzoek is niet geactiveerd.

## Controles en vervolg

480 tests geslaagd, nul mislukt: alle 456 bestaande plus 24 nieuwe deterministische
gevallen; volledige suite 16,80 s. Eén bestaande Starlette/AnyIO-waarschuwing.
Getest: exacte referenties, timeframegrenzen/warm-up, future/gap/duplicate,
ontbrekende waarden, nulvolume, precisie, scoretimestamp, lege/kleine/constante
of overlappende groepen, bootstrapreferentie, onregelmatige groepsgewichten,
Holm en reproduceerbaarheid. Bestaande suite gebruikt uitsluitend haar reeds
vastgelegde fixtures; geen nieuwe historische validatie-/testanalyse.

Eindintegriteit en bronhashes staan in experiments/phase6e_technical/integrity.json.
Bestaande resultaten, checkpoints, auditdatabase, oorspronkelijke voorstellen en
alle strategie-/risicomodules blijven behouden. PROGRESS.md en NEXT_STEPS.md geven
deze technische fase weer, zonder oude registraties te herschrijven.

**Stop voor expliciete goedkeuring.** Nog te besluiten: uitsluitend beschrijvende
historische analyse volgens de vaste labels, of eerst een wijzigingsvoorstel voor
voldoende nauwkeurige inferentie. Voor een historische run blijven een expliciete
uitvoeringsgoedkeuring, labelvrije bronvalidatie, een volledige read-only adapter en
code-/configuratie-/datasetmanifest vereist. Deze technische controle verleent die
historische toestemming niet. 2025 en 2026 blijven gesloten.
