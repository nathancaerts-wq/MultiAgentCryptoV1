# Fase 6F — onderzoeksplan en beslispunten

Status: **onderzoeksvoorbereiding afgerond; alle zes ontwerpen inactief**.
Basiscommit: `4f3e9a2675cca3ce6015609145380f3c161d4cc9`.
Opdracht: fase 6F Risk Recovery & Strategy Research, inclusief de vervolgopdracht
om opgeslagen werkzaamheden te hervatten en de voorstellen af te ronden.
Deze toestemming dekt documenten en controles, niet implementatie of varianttests.

Lees samen met `PHASE6F_RISK_RECOVERY_PROPOSAL.md` en
`PHASE6F_STRATEGY_CANDIDATES.md`. De oorspronkelijke protocollen, vijf fase-6E-
hypotheses, 332 contrasten, resultaten en actieve regels blijven bewaard.

## Onderzoeksbasis en registratie

De werkmap was schoon op de opgegeven commit. Bij hervatting stonden alleen de
twee nieuwe voorstellen en de fase-6F-controlebestanden lokaal; die zijn behouden.
Er liep geen onderzoeks- of testproces meer. De derde tekst, dit plan, voltooit de
oplevering. Geen nieuw marktarchief, label, indicator of rendement berekend.

Alle inhoudelijke bevindingen komen uit de bestaande beschrijving van BTC/EUR,
ETH/EUR en SOL/EUR in 2024. De bestaande ontwikkelperiode is
[2024-01-01 00:00, 2025-01-01 00:00) UTC, warm-up 1–7 januari,
instapmomenten 8 januari 00:00 t/m 31 december 19:45. Deze vermelding autoriseert
geen herberekening. De 103.344 oude prijslabels zijn geen 103.344 onafhankelijke
of uitvoerbare trades. De primaire UTC4h-steekproef telt 6.459 coinmomenten.

De fase-6E-registratie verwijst naar manifest
`0d606b4adabd4ef611f855934baa0ae175560777138f93935edf730caab28dd2`.
De bytes van dit manifest en alle tien eindartefacten uit de oude finalization
zijn gecontroleerd. De nulmeting bindt daarnaast alle 370 reeds gevolgde bestanden
met SHA-256. Oude protocolbestanden met historische status 'niet geactiveerd'
blijven staan; de afzonderlijke v4-registratie documenteert de toen goedgekeurde
beschrijvende uitvoering. Fase 6F verleent geen nieuwe uitvoeringsmachtiging.

De bestaande audit-/financiële database `/workspace/development_2024.sqlite3`
heeft SHA-256
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.
De nulmeting vergelijkt de volledige bytes met de reeds geregistreerde hash;
de afsluitcontrole herhaalt die vergelijking. De WAL is leeg. Hiervoor wordt het
bestand alleen als bytes gelezen: geen nieuwe query, replay, labelvergelijking of
opening van 2025/2026-datasets. Dit bewijst behoud van het eerdere auditbestand,
niet een nieuwe volledige inhoudelijke audit van alle oude transacties.

`experiments/phase6f/baseline_integrity.json`, `verification.json`, `tests.txt` en
`proposal_registration.json` leggen bronnen, behoud, testbewijs en de hashes van
de drie voorstellen vast. Dit is een versiegebonden onderzoeksregistratie in Git,
geen onveranderlijke WORM-opslag. Er wordt geen oud onderzoeksregister overschreven.

## Aangetroffen beperking in de oude export

De CSV `experiments/phase6e_descriptive/contrast_summary.csv` heeft 33 kopkolommen,
88 datarijen met 33 velden en 576 met 34 velden. De renderer gebruikt
`k.split(':')`; timeframekenmerken zoals `1h:rsi` worden daardoor over twee
kolommen verdeeld. JSON en de rapporttabellen houden het volledige kenmerk intact.
De oorspronkelijke CSV, renderer, hashes en resultaten zijn in deze fase **niet
gewijzigd**. De voorstellen lezen de reeds beschreven JSON-/rapportwaarden, niet
verschuivende CSV-kolommen. Een later automatisch onderzoek mag deze CSV niet
stilzwijgend als correcte tabel importeren. Eerst afzonderlijk een versiegebonden
exportcorrectie en een test op kolomaantal/JSON-reconciliatie laten goedkeuren.
Dit exportprobleem blokkeert zo'n import, niet het huidige documentvoorstel.

De eindresultaten bevatten aantallen kalenderblokken, maar geen volledige reeks
contrastuitkomsten per week. Die ontbrekende verdelingen worden nu niet aangevuld.
Ook de inferentiële beperkingen uit de statistische amendering blijven gelden:
geen automatisch geldige p-waarde door meer bootstrapherhalingen, geen bevestiging
op reeds bekeken 2024, geen effectieve onafhankelijkheid door drie coins samen
te voegen. De acht pauzecontrasten hebben onvoldoende steun.

## Vergelijking van de herstelontwerpen

Volgorde betreft technische onderzoekbaarheid, niet verwacht rendement.
Alle herstelvarianten vereisen een expliciete toekomstige wijziging van het
verliesreeksveto in een geïsoleerde onderzoeksinterface; geen ervan bestaat al.

| Ontwerp | Uitvoerbaarheid | Risicobeheersing | Reproduceerbaarheid | Overfittingrisico | Afzonderlijke validatie |
|---|---|---|---|---|---|
| R1: 24 uur, één proef | Eenvoudigste toestandsmachine; atomisch proefrecht nodig | Alle veto's blijven; één proef met 0,5%/50%, daarna sluiten bij mislukking | Vaste UTC-duur en ledger-event | Beperkt aantal ontwerpkeuzes, maar wachttijd onbewezen | Goede technische referentie; meerdere nieuwe pauze-episodes nodig |
| R3: 24 uur, kleinere proef | R1 plus bevroren sizing-toestand | 0,25%/25%; minnotional kan deelname verhinderen | Vaste halvering, Decimal en dezelfde cash | Minder omvang is geen bewijs van herstel; één winst is toeval mogelijk | Later apart tegenover R1, dezelfde bronnen en kosten |
| R2: twee UTC4h-bevestigingen | Meer marktdata, grens- en crashlogica | Geen reset van dagverlies/drawdown; één proef | Exacte twee opeenvolgende snapshots van dezelfde coin | Meer selectie-effecten, gecorreleerde bevestiging | Moeilijker wegens regimeafhankelijkheid en schaarse episodes |

Aanbeveling: eerst toestemming voor uitsluitend synthetisch ontwerp-/herstelbewijs
van R1 vragen; R3 daarna als kleinere proefvariant. Dit selecteert nog geen
herstelbeleid. R2 blijft een afzonderlijke mogelijkheid. Succes van één proef is
geen statistische veiligheidswaarborg. Geen automatische nieuwe proef na mislukking.

## Vergelijking van de strategieontwerpen

Alle drie houden de volledige bullish/EMA-overeenstemming van aligned_trend aan.
Geen variant maakt een bestaande HOLD alsnog BUY door een veiligheidsvoorwaarde
weg te laten. Ze voegen elk één afzonderlijke conjunctie toe; geen combinatierooster.

| Ontwerp | Uitvoerbaarheid | Risicobeheersing | Reproduceerbaarheid | Overfittingrisico | Afzonderlijke validatie |
|---|---|---|---|---|---|
| S3: hoogste gelijktijdige score | Drie score-snapshots nodig; gate vóór selectie | Geen terugval naar lagere coin, huidige risk blijft | Bestaande score en tiebreak; missing = HOLD | Coinbias en samenstelling; geen universeel positief 6E-verband | Eenvoudig te onderscheiden van bestaande ranking |
| S2: ATR/close boven kostenfractie | Bestaande ATR/close en vaste kostenformule | Hoge ATR vergroot stoprisico; sizing niet aanpassen | Economisch vastgelegde grens, geen quantielen | Een ATR is geen verwachte winst; mogelijk weinig extra selectie | Apart vergelijken met dezelfde kosten/exposure-rapportage |
| S1: RSI <= 50 en dalende RSI | Extra oude candle voor exacte vorige RSI | Alle basisveto's en stop blijven | Vast RSI-midden en nulgrens | Samengestelde post-hoc-hypothese; combinatie kan leeg zijn | Eerst synthetische verenigbaarheid, nooit drempel verruimen bij schaarste |

Aanbeveling: S3 eerst voor herkomst-/selectielogica, S2 daarna voor de koppeling
aan frictie, S1 daarna voor de samengestelde voorwaarde. Deze volgorde steunt op
controleerbaarheid; niet op de grootte of het teken van een 2024-rendement.
Geen van de drie is als verbetering aangetoond. Meer of minder kandidaten is op
zichzelf geen winst, veiligheid of onafhankelijke bevestiging.

## Gefaseerde vrijgave, nog niet verleend

1. **Keuze en ontwerpbevriezing.** Keur expliciet een R- of S-voorstel goed voor
   technische implementatie, inclusief timer/marktreeks, proefafhandeling en
   sizing of de exacte conjunctie. Registreer code-, configuratie- en bronhashes,
   gelijke kosten en oorspronkelijke baseline. Kies niet achteraf een andere
   regel wanneer een groep leeg blijft. Geen combinatie van R en S in de eerste
   evaluatie; dat zou hun bijdragen vermengen.
2. **Synthetisch bewijs.** Alleen na toestemming: grensgevallen, chronologie,
   dubbele voorstellen, reserveringen, crashes, checkpoints, nul/negatieve cash,
   verliesreeksen, daggrens, drawdown en noodstop. Controleer dat de baseline
   dezelfde financiële uitkomsten en audit-events houdt. Elke afwijking vereist
   onderzoek voordat historische verwerking wordt toegestaan.
3. **Apart historisch onderzoeksprotocol.** Dataset, periode, eerdere inzage,
   watchlist/toelating, gaps/warm-up, kosten, hypothesefamilie, meetregels en
   tijd-/geheugenlimieten moeten vooraf expliciet worden goedgekeurd. 2024 is
   reeds bekeken: hoogstens exploratieve ontwikkeling, nooit onafhankelijke
   bevestiging door het in nieuwe blokken te hernoemen. Geen huidige toestemming
   voor een counterfactual, nieuwe 2024-strategierun, validatie 2025 of test 2026.
4. **Onafhankelijke beoordeling.** Eerst een werkelijk nieuwe, expliciet toegestane
   steekproef bepalen na controle van het inzageregister. Bestaande 2025-inzage
   verhindert mogelijk een volledig onafhankelijke validatie; 2026 blijft
   vergrendeld en wordt niet alvast als beschikbare test beloofd. Tijdafhankelijkheid,
   coin-correlatie en meerdere nieuwe voorstellen vereisen een apart gekalibreerd
   statistisch plan. Geen automatische promotie bij een gunstig resultaat.

Een latere evaluatie moet alle vooraf geregistreerde kandidaten en afwijzingen,
nettoresultaat na kosten, trades, geplande/gerealiseerde verliezen, gapoverschrijdingen,
exposure, drawdown, daglimieten, pauzeduur, aantal herstelpogingen en per-coin-/periode-
uitkomsten rapporteren. Cash en de bevroren baseline zijn referenties; EMA alleen
met dezelfde gevalideerde uitvoeringsaannames. Geen zesmunten-buy-and-hold-index
stilzwijgend vervangen door een driemuntenindex. Een technisch ongeldige run wordt
niet als nulrendement gerapporteerd. Onder 30 trades of te weinig onafhankelijke
pauze-episodes: onvoldoende bewijs; boven 30 is bewijs evenmin automatisch genoeg.
Geen gevolgtrekking uit het optellen van overlappende koerslabels.

## Controles in deze fase en limieten

- Alle **497 bestaande tests geslaagd**, nul mislukt, één bestaande
  Starlette/AnyIO-deprecationwaarschuwing, 18,73 seconden. Bewijs in `tests.txt`.
  Geen onderzoeksinterface geïmplementeerd: daarom geen nieuwe tests toegevoegd.
  De bestaande suite bevat reeds bekende fixtures, waaronder oudere technische
  testfixtures met 2025-datums; dat is geen nieuwe analyse van validatie 2025.
- Tests onder harde wall-clocklimiet 180 s en adresruimtelimiet 1,5 GiB.
  Integriteitscontroles afzonderlijk maximaal 180 s en 1 GiB adresruimte,
  streaming SHA-256 in blokken van 1 MiB. Nulmeting: 42,80 s, 12,26 MiB piek-RSS.
  Geen capaciteitsprobe of financiële historische run uitgevoerd.
- Alle 370 oude gevolgde bestanden, inclusief strategieën, indicators, tests,
  protocollen, financiële resultaten en audit-artefacten blijven byte-identiek.
  De afsluitcontrole controleert ook opnieuw de volledige auditdatabase en lege WAL.
  Exacte afsluitmetingen staan in `verification.json`.
- Nieuwe artefacten uitsluitend de drie voorstellen en fase-6F-controlebewijs.
  Geen broncode, productieconfiguratie, onderzoekresultaat of auditlog gewijzigd.
  Geen nieuwe orders, sleutelgebruik of marktdata-download. Validatie 2025 en
  onafhankelijke test 2026 blijven gesloten.

De voorstellen zijn gereed voor inhoudelijke beoordeling, niet voor automatische
uitvoering. Open keuzes zijn welke R/S-variant(en) u wilt onderzoeken, of de
expliciete proefafhandeling aanvaardbaar is, en later de onafhankelijke dataset en
statistische opzet. Stop na commit/push van deze voorbereiding; wacht op afzonderlijke
goedkeuring voor implementatie en tests van nieuwe varianten.
