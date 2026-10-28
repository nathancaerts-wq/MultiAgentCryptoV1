# Fase 6E — afzonderlijk analyseprotocol, voorstel v1

Status: **voorgesteld, niet geactiveerd**. Basiscommit
`2a7efedaefd755bcc7ae190102fd0fba015e1725`. De opdracht Fase 6E geeft opdracht tot
patroononderzoek, maar vereist expliciet een stop vóór nieuwe uitkomstvergelijkingen
als de preregistratie onvoldoende is. Die voorwaarde is van toepassing.
Dit voorstel en de bijbehorende hashes registreren een ontwerp, geen toestemming
voor uitvoering. Eerst expliciete goedkeuring van deze nieuwe vergelijkingen;
daarná een uitvoeringsmanifest met implementatiehashes en broncontrole vóór inzage.

## Waarom een afzonderlijk protocol nodig is

Fase 6D registreerde bestaande 1h-regime-/EMA-richtingsgroepen en gemiddelden van
RSI, momentum en relatieve ATR per bruto-label. Niet geregistreerd: RSI-verandering,
volume, EMA-afstanden, aanvullende timeframegroepen, een pauzestatus per HOLD,
EMA-selectievergelijkingen en een afhankelijke-steekproefmethode met een volledige
familie van vergelijkingen. RESEARCH_PROTOCOL.md vereist een uitgebreid plan bij
extra plannen, benchmarks en selectie-effecten. De oude registratie blijft intact.
2024 en de fase-6D-tabellen zijn al bekeken: ook dit ontwerp is **exploratief**,
geen preregistratie vóór de allereerste inzage en geen nieuwe onafhankelijke dataset.

## Bronnen, eenheid en horizon (ongewijzigd)

Alleen de bestaande 103.344 fase-6D-labels voor BTC/EUR, ETH/EUR en SOL/EUR:
2024-01-08 00:00 t/m 2024-12-31 19:45 UTC, inclusief laatste beslisgrens.
Horizon [t,t+4h), volgende 15m-open op t, laatste close op t+4h. Laatste markering
31 december 23:45. Geen nieuwe prijslabels, geen 2025-/2026-query en geen download.
Fase-6D-manifest `933be8ac13e01a7dd4e4a749291306e2f026a87bf92431f17a3163f83a98e779`.
Bruto >0/<0/=0; netto >0 versus <=0 met dezelfde 0,001 coin, tick 0,01,
fee 0,1% per zijde, spread 0,1%, slippage 0,1% per zijde en Decimal-afrondingen.
Geen nieuwe winstgrens of andere horizon. Geen optelling van hypothetische EUR-P&L.

Primair inhoudelijk universum: oorspronkelijke aligned_trend DecisionAgent HOLD.
Alle overlappende momenten blijven een afzonderlijke beschrijvende tabel.
Onzekerheidsberekening uitsluitend op de bestaande UTC-vieruursgrid
(epoch-seconden modulo 14.400 =0). Gelijktijdige coins blijven bij resampling samen.
Pooled-statistieken zijn gelijke gewichten per beschikbare coinobservatie; daarnaast
alle drie coins apart. Geen selectie of weging op toekomstig rendement.

## Kenmerken vóór het beslismoment

Gebruik oorspronkelijke gevalideerde onderzoeksrapporten en officieel gevalideerde
2024-candles uit dezelfde database, alleen gesloten op of vóór t. Voor timeframe f:
e=floor_f(t), C=close van de candle die eindigt op e. Bestaande 32-candlewindow,
EMA9/21, RSI14, ATR14 en alle overige IndicatorConfig-waarden blijven gelijk.
Geen doorlopende EMA met andere initialisatie dan de oorspronkelijke rapporten.

Acht numerieke kenmerken per timeframe 15m, 1h en 4h (24 totaal):

1. RSI uit het oorspronkelijke rapport op e.
2. ΔRSI = RSI(e) − RSI(e−duur(f)); beide met eigen exact 32 afgesloten candles.
   De vorige RSI eventueel met bestaande technical() reconstrueren, nooit met een
   later venster. Reconstructie op e moet eerst exact het opgeslagen rapport matchen.
3. Getekende EMA-afstand: EMA9 / EMA21 −1.
4. Trendsterkte: absolute waarde van die EMA-afstand; geen winstgetrainde schaal.
5. Prijsafstand: C / EMA21 −1.
6. Relatieve ATR: ATR14 / C van hetzelfde timeframe. Dit is expliciet een nieuwe
   featuredefinitie; de oude 6D-ATR/laatste-15m-close wordt niet vervangen.
7. Volumeratio: base-volume laatste gesloten candle / gemiddelde base-volume van
   de twintig direct voorafgaande candles van hetzelfde timeframe.
8. Volumeverandering: laatste base-volume / vorige base-volume −1.

Drie extra kenmerken: oorspronkelijke scannerscore; vergelijkingsrang
1 + aantal coins met strikt hogere score (gelijke scores gelijke rang);
aantal timeframes met bestaande EMA-richting up (0..3). Totaal **27 kenmerken**.
Score uit alle drie oorspronkelijke coinrapporten op t samenvoegen; geen ranking
uit latere prestaties. Een afwijkende score-rang is geen wijziging van de werkelijke
UTC-tiebreaker voor portefeuilletoewijzing. Geen optimizerzoeklus of combinaties.

Categorisch uitsluitend bestaande 1h-regimes bullish/bearish/sideways/uncertain,
bestaande up/down/flat per timeframe en agreement/conflict. Tabellen per coin en
steekproef, geen datagedreven bins, splitsingen of regime×indicator-zoekrooster.
Andere kenmerken of subgroepen vereisen een nieuwe protocolversie vóór vergelijking.

## Datakwaliteit en ontbrekende waarden

Sleutel (coin,t) uniek, volledige 34.448 tijden per coin; originele labels, acties en
bronhashes exact verifiëren. Label ontbreekt/afwijkt, tijd buiten bereik, corrupte
rapporten, dubbele candles, datagat, ongeldige OHLCV of niet-afgesloten timeframe:
stop de vergelijking en rapporteer onvolledige voorbereiding. Geen interpolatie.
Elke feature krijgt bron/tijdgrens; frames eindigen exact op floor_f(t).
Voor ΔRSI is één extra oude candle nodig: 33 candles tot e, binnen de bestaande
2024-warm-up. Geen eerdere jaren inladen. Ontbrekende warm-up stopt die studie.

Nul als volumedeler of ontbrekende oorspronkelijke scannerregel is een expliciete
ontbrekende feature, geen nulscore of nulvolume. Rapporteer per feature/coin/groep
het ontbrekend aantal; alleen die featurecontrast krijgt complete-case verwerking.
Bij >1% ontbrekende waarden in een contrast of één ontbrekende coin in de gepoolde
scorevergelijking: contrast niet toetsbaar, geen impliciete gunstige selectie.
Candlevolume nul op zichzelf is toegestaan; negatieve/niet-eindige waarden niet.

## Vooraf vastgelegde contrastfamilie en onzekerheid

Geen nieuwe resultaten in deze fase. Voor een latere, goedgekeurde uitvoering:

- A: verschil in gemiddelde feature tussen bruto positieve en bruto negatieve
  oorspronkelijke HOLDs (neutrale labels tellen apart, niet in dit contrast).
  27 kenmerken × vier strata (pooled/BTC/ETH/SOL) =108 contrasten.
- B: hetzelfde tussen netto positieve en netto niet-positieve HOLDs: 108.
- C: verschil in bruto-positief aandeel en netto-positief aandeel tijdens versus
  buiten oorspronkelijke aligned_trend-verliesreekspauze: 2 × vier strata =8.
- D: verschil in gemiddelde feature tussen oorspronkelijke EMA BUY_CANDIDATE en
  aligned_trend BUY_CANDIDATE, binnen exact hetzelfde 6D-tijduniversum, ongeacht
  latere goedkeuring/fill; een moment dat in beide sets zit, blijft in beide sets.
  Geen HOLD-filter voor D. 27 × vier strata =108.

Vaste familie **332 contrasten**. Beide steekproefversies krijgen aantallen,
mediaan, p10/p90 en min/max (nearest-rank-kwantielen ceil(p*n), min bij p=0).
Alleen UTC4h krijgt inferentie. Categorische tabellen en de overlappende versie
zijn beschrijvend, zonder extra toetsen of selectie van een 'beste' patroon.

Voorgestelde resampling: circulaire moving-block-bootstrap van zeven aaneengesloten
UTC-dagen, 42 opeenvolgende vieruurstijdgroepen. Resample tijdgroepen met alle drie
coins, alle features, labels en oorspronkelijke pauze-/selectievlaggen samen.
Trek starts uniform op de vaste tijdindex, voeg blokken samen en kap op oorspronkelijke
lengte af. Circulair om identieke randkansen te houden; geen candleherberekening op
synthetische grenzen. 9.999 replicaties, seed 606, Python random.Random; afhankelijkheden
vastpinnen in uitvoeringsmanifest. Geen alternatieve bloklengtes achteraf proberen.

Per contrast: θ is het verschil van groepsgemiddelden/aandelen. Rapporteer het
95%-percentielinterval van θ* en de benaderende tweezijdige gecentreerde bootstrap-
p-waarde (1 + aantal |θ*−θ| >= |θ|) / 10.000. Pas Holm toe op de **volledige 332**
p-waarden, familie-alpha 0,05. Niet-toetsbare contrasten tellen mee als p=1 in de
correctie, maar tonen p/interval als 'niet berekend'. De 95%-intervallen zijn
puntgewijs, niet simultaan: geen losse interval- of ongecorrigeerde p-waarde als
bewijs aanmerken. Bootstrap en Holm herstellen eerdere onderzoeksselectie niet.

Minimaal twintig verschillende vaste zevendaagse kalenderblokken met observaties
in **elk** van beide groepen (anker 2024-01-08 00:00), en minimaal dertig
vieruurstijdgroepen per groep. Nulvariatie/ongedefinieerde standaarduitkomst of
ook maar één replicatie met lege groep: niet toetsbaar, niet eindeloos opnieuw trekken.
Voor pauzevergelijking is de korte periode vóór de pauze naar verwachting onvoldoende;
geen versoepeling om toch significantie te krijgen. Regimewisselingen en niet-
stationariteit beperken ook bij voldoende aantallen de bootstrapbenadering.
Geen causale of onafhankelijke voorspellingsclaim op dit al bekeken jaar.

## Pauze en EMA: betekenis vastleggen

Pauze(t) uit oorspronkelijke ledgerprefix **op het moment van de entrybeoordeling**:
minimaal drie achtereenvolgende negatieve gesloten trades, na verwerking van de
op t gesloten uitvoeringscandle. Bevestig de exacte runner-eventvolgorde met audit-
IDs; bij ambiguïteit stoppen. Geen toekomstige tradeprefix, geen reset, geen
herberekende counterfactual-portefeuille. Tijdstip derde verlies is bekend uit 6C;
het aantal expliciete pauze-afwijzingen is niet het aantal HOLDs tijdens pauze.
Nieuwe tellingen/labelvergelijkingen wachten op dit protocol.

EMA-selectie wordt uit bewaarde oorspronkelijke BUY-acties gehaald. Houd stages
apart: kandidaat, entry akkoord, execution geweigerd/gevuld. Kosten, blootstelling,
regimes en risicoblokkeringen alleen uit bestaande baseline-resultaten/audits;
geen nieuwe EMA-backtest. Reconcileer selectie eerst met eerder gerapporteerde
jaartotalen; terminale 51 coinmomenten buiten het 6D-instapuniversum apart houden.
Nieuwe labeljoin gebruikt alleen (coin,t) en dezelfde 6D-labels, nooit een nieuwe
EMA-horizon of beste latere munt. Vergelijking D gaat over kenmerken, niet winst.

## Uitvoering, registratie en beslisregels

Een volgende run heeft vooraf een eigen goedgekeurde protocolhash, bronhashes,
code-/dependencyhashes, goedkeuringsreferentie en status '2024 eerder bekeken'.
Bewaar oude onderzoekregisters; registreer het hergebruik apart, zonder onafhankelijkheid
te claimen of 2025/2026 vrij te geven. Geen activatie via alleen een JSON-statuswijziging.

Voorbereiding en broncontrole maximaal 300 s / 1 GiB adresruimte; goedgekeurde
latere analyse maximaal 600 s / 1 GiB, vroege RSS-stop bij 768 MiB. Resample
blokaggregaten om geheugen te begrenzen; eerst synthetische technische tests.
Timeout/limiet/essentiële hashfout: incomplete analyse, geen automatische herstart,
geen ander seed of minder correcties. Reproduceerbare tussenbestanden alleen met
volledige bron-/configuratiebinding, geen gedeeltelijk resultaat als definitief.

Maximaal vijf hypothesen, gerangschikt op meetbaarheid en bronkwaliteit. Zie
PHASE6E_HYPOTHESES.md. Zelfs een Holm-gecorrigeerd verband bewijst geen uitvoerbare
winst. Iedere eventuele strategietoets vraagt een apart protocol en expliciete
historische toestemming; huidige strategie, Risk Engine en optimizerpromotie blijven
ongewijzigd. Validatie en onafhankelijke test blijven gesloten.
