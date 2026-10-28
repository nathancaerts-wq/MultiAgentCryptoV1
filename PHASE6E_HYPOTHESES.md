# Fase 6E — vijf toetsbare onderzoeksvoorstellen

**Voorstellen, geen ontdekte nieuwe patronen, geen strategieaanpassingen.**
Nieuwe fase-6E-uitkomstvergelijkingen zijn wegens de ontbrekende preregistratie niet
uitgevoerd. Rangorde op bronkwaliteit, eenvoudige toetsbaarheid en beperkingen;
niet op historisch rendement. Dit zijn inhoudelijke voorstellen voor het bestaande
ResearchOptimizer-proces. `candidate()` en `approve()` zijn niet aangeroepen;
de optimizer slaat voorstellen op maar bewijst zelf geen statistisch verband.
Geen bestaande onderzoeksdatabase of actieve configuratie is gewijzigd.

Alle toetsen hieronder vereisen eerst goedkeuring van
PHASE6E_ANALYSIS_PROTOCOL_PROPOSAL.md. Ze gebruiken alleen de vaste 6D-labels en
vallen binnen de 332 vooraf beschreven contrasten. Ze zijn na eerdere 2024-inzage
geformuleerd en blijven exploratief. Een mislukte of niet-toetsbare hypothese blijft
in de rapportage; geen vervanging door een gunstiger variant.

## 1. Bekende scannerscore onderscheidt prijslabels

- Patroon: oorspronkelijke score en relatieve rang verschillen tussen later
  positieve en negatieve HOLD-labels, ook na vaste kosten. Richting niet vooraf
  als bewezen of positief aannemen.
- Relevantie: de bestaande selectie gebruikt die score al; meet eerst of deze
  ordening informatie bevat buiten louter beschikbaarheid en risicoblokkeringen.
- Gegevens: drie oorspronkelijke scannerregels op t, vaste bruto-/nettolabels,
  coin, UTC4h-grid. Geen toekomstige winnaar kiezen.
- Toets: A/B-contrasten voor score en rang, pooled en per coin, volledige
  Holm-familie; overlap alleen beschrijvend. Geen nieuwe scorewegingen zoeken.
- Overfitting: 2024 is bekeken, score is samengesteld en coins zijn gecorreleerd;
  een verschil kan alleen een verschil tussen munten/regimes weerspiegelen.
- Minimale bewijslast: volledige herkomst en ontbrekendheidscontrole, voldoende
  tijdblokken en Holm-gecorrigeerde uitkomst; eventuele strategiewijziging vraagt
  daarna een afzonderlijke uitvoerbaarheidstoets en onafhankelijk bewijs met
  expliciete toestemming. Een hoge score is geen Risk-goedkeuring.

## 2. RSI-niveau en verandering hebben verschillende samenhang

- Patroon: ΔRSI op een volledig afgesloten timeframe onderscheidt labels anders
  dan RSI-niveau. Geen veronderstelde winstgrens of automatisch koopniveau.
- Relevantie: bestaande 6D-gemiddelden zijn niveauverschillen; ze bewijzen geen
  omslag of herstel. De nieuwe vraag is strikt afgebakend tot één eerdere TF-candle.
- Gegevens: oorspronkelijke RSI14 en dezelfde bestaande berekening met een eigen
  voorafgaand 32-candlewindow, alle drie timeframes, 6D-labels.
- Toets: A/B voor RSI en ΔRSI volgens het vaste protocol; geen beste timeframe
  promoveren of gecombineerde RSI-regel afstemmen.
- Overfitting: veel verwante indicatoren en de bekende oude RSI-gemiddelden; rolling
  initialisatie kan schijnbare veranderingen geven zonder marktregimewisseling.
- Minimale bewijslast: exacte reproductie van opgeslagen RSI, causale warm-up,
  voldoende blokken, volledige multipliciteitscorrectie en latere afzonderlijke
  bevestiging. Geen wijziging van RSI14 of actieve grenzen in deze fase.

## 3. EMA-afstanden, timeframe-overeenstemming en EMA-selectie

- Patroon: afstand tot EMA21, EMA9/21-afstand en het aantal up-timeframes verschillen
  tussen HOLD-labelgroepen en tussen de oorspronkelijke twee kandidaatselecties.
- Relevantie: aligned_trend vereist meerdere analyses; EMA Trend selecteert via
  een eenvoudiger bestaand criterium. Frequentieverschil is nog geen kwaliteitsverschil.
- Gegevens: oorspronkelijke gesloten frames, regimes, beide BUY_CANDIDATE-sets,
  fase-6D-labels; kandidaat, goedkeuring en fill afzonderlijk houden.
- Toets: geregistreerde A/B/D-contrasten, bestaande categorische tabellen slechts
  beschrijvend. Geen nieuwe combinaties, grenswaarden of EMA-perioden testen.
- Overfitting: sterk gecorreleerde EMA-features en verschillende risicotrajecten;
  vijf EMA-trades bewijzen geen superieure strategie.
- Minimale bewijslast: exacte stage- en tijdjoin, blokdekking en gecorrigeerde
  contrasten; vervolgens afzonderlijk goedgekeurd bewijs over uitvoerbaarheid,
  kosten en exposure. Geen keuze op het hoogste 2024-rendement.

## 4. Volatiliteit en volume beschrijven verschillende labelomgevingen

- Patroon: ATR/close en voorafgaand volume verschillen tussen positieve en
  negatieve bruto-/nettolabels. Grote bewegingen kunnen tegelijk grotere nadelige
  excursies hebben; een positief endpoint is geen stopbestendige trade.
- Relevantie: vaste kosten verwijderen veel kleine positieve koersbewegingen.
  Volatiliteit en volume kunnen dit beschrijven, zonder een winstfilter te vormen.
- Gegevens: ATR14, timeframe-eigen close, laatste/voorgaande volumes, exact twintig
  voorafgaande volumeobservaties, reeds opgeslagen prijslabels.
- Toets: A/B voor relatieve ATR, volumeratio en volumeverandering, alle timeframes
  en strata. Niet zoeken naar gunstige quantielbins of volumegrenzen.
- Overfitting: afhankelijkheid van coin en schaal, extreme volumes, nuldelers,
  staartgebeurtenissen en retrospectieve featurekeuze.
- Minimale bewijslast: valide volumebronnen, vaste missing-regels, blokdekking,
  multipliciteitscorrectie; zelfstandige liquiditeits- en uitvoeringsvalidatie
  blijft nodig. Geen nieuwe minnotional- of liquiditeitsparameter activeren.

## 5. Pauzeperiode heeft andere labels, zonder effect van versoepeling te claimen

- Patroon: vaste bruto-/netto-positieve HOLD-aandelen tijdens en buiten de
  oorspronkelijke verliesreekspauze verschillen.
- Relevantie: onderscheid tijd besteed in pauze van expliciete pauze-afwijzingen;
  een positief label tijdens pauze was geen toegestane instap.
- Gegevens: oorspronkelijke ledgerprefix en eventvolgorde op t, HOLD-acties en
  bestaande labels. Geen reset, schaduwportefeuille of nieuw orderpad.
- Toets: uitsluitend de acht C-contrasten. De korte niet-gepauzeerde periode zal
  vermoedelijk de minimumblokregel niet halen: dan aantallen/verdelingen en
  'onvoldoende bewijs', geen p-waarde of aangepaste drempel.
- Overfitting: pauze is endogeen aan eerdere verliezen en bijna identiek aan
  kalenderperiode; een vergelijking identificeert geen causaal pauze-effect.
- Minimale bewijslast: eventreconstructie en voldoende beide-groepdekking. Zelfs
  een verband rechtvaardigt geen risicoversoepeling. Een eventuele counterfactual
  vereist een afzonderlijk expliciet protocol en toestemming; hier niet voorzien.

## Voorwaarde vóór iedere wijziging

Geen van deze vijf voorstellen is een gevalideerde verbetering. Geen positieve
verwachtingswaarde of verhandelbare winst geclaimd. Voldoende onafhankelijke
waarnemingen, stabiele onzekerheid, correcte meervoudige toetsing en een valide
ordersimulatie zijn afzonderlijke vereisten; de oude minimumgrens van dertig trades
is slechts noodzakelijk, nooit afdoende. Deze fase geeft geen toestemming voor
inzage in validatie 2025 of de onafhankelijke test 2026.
