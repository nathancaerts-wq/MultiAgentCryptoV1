# Fase 6E — statistische amendering v1, NIET GEACTIVEERD

Basiscommit: c945709b1b682f94f8705c215432142fcf8f0992.
Dit is een afzonderlijk voorstel. PHASE6E_ANALYSIS_PROTOCOL_PROPOSAL.md en
PHASE6E_HYPOTHESES.md blijven ongewijzigd. De vijf hypotheses, 27 features en
332 contrasten blijven behouden; geen selectie op historische uitkomsten.
Geen historische patroonanalyse, rendementsbacktest, order of 2025/2026-inzage.

## Aanbeveling en besluit

**Voor het reeds bekeken ontwikkeljaar 2024: beschrijvende, tijdgegroepeerde analyse
zonder inferentiële p-waarden, Holm-verwerpingen of betrouwbaarheidsclaims.**
Dit is de aanbevolen veilige amendering, niet automatisch uitgevoerd. De
synthetische validatie ondersteunt geen universeel betrouwbare inferentiemethode
onder de toegestane sterke afhankelijkheid en mogelijke niet-stationariteit.
Meer bootstrapherhalingen lossen die ongeldigheid niet op.

Voor een later, expliciet toegestaan inferentieel onderzoek is een studentized
ratio-/scoretoets met een consistent geschatte langetermijnvariantie (HAC), of een
studentized block/multiplier-bootstrap daarvan, methodologisch beter verdedigbaar
dan een ongekalibreerde gecentreerde verschilverdeling — **onder expliciete
zwakke-afhankelijkheids-, moment- en stabiliteitsaannames**. Dit is geen bewijs
dat het hier geteste vaste HAC-model geschikt is voor alle 2024-regimes. Het heeft
de vooraf gekozen synthetische screening niet gehaald en wordt niet gepromoveerd.
Voor willekeurige regimebreuken kan ook een andere bootstrap geen geldigheid
garanderen zonder een model voor die breuken en een helder estimand.

## Wat precies blijft vaststaan

A=108 featureverschillen positief versus negatief bruto-HOLD;
B=108 netto-positief versus niet-positief HOLD;
C=8 verschillen in bruto-/netto-positieve aandelen tijdens versus buiten pauze;
D=108 verschillen in features van EMA versus aligned_trend BUY-kandidaten.
Pooled/BTC/ETH/SOL, bestaande 27 kenmerken, 4h-labels, kosten, 0,001-coinunit en
bron-/tijdgrenzen blijven exact volgens het bestaande voorstel. Geen nieuwe bins,
beste timeframe, nieuwe coinselectie, wijziging van handelsregels of pauzereset.

Primaire volledige observaties blijven zichtbaar als overlappende beschrijving.
De aparte UTC4h-grid gebruikt alleen beslismomenten met epoch modulo 14.400=0.
Gelijktijdige coins vormen één tijdgroep. Alleen deze grid komt ooit voor inferentie
in aanmerking; er worden geen 15m-waarnemingen als onafhankelijke trades geteld.
De huidige technische capaciteitstests zeggen niets over verhandelbare winst.

## Beoordeling van de oude bootstrap

De formule (1 + #{|θ*−θ|>=|θ|})/(B+1) is correct geïmplementeerd als benaderende
gecentreerde bootstrap-tailkans. Zij is geen exacte permutatie-/randomisatietoets.
Groepsratio's, ongelijke bezetting, endogene HOLD/BUY-/pauzeselectie, lange
geheugenwerking en regimebreuken kunnen de samplingverdeling veranderen.
Circulaire blokken verbinden kunstmatig december met januari. Eén vaste week
vangt niet noodzakelijk alle afhankelijkheid op. De +1-term voorkomt nulschattingen
maar levert op zichzelf geen superuniforme p-waarden onder de nulhypothese.

Holm vereist geldige individuele p-waarden en kan vervolgens afhankelijkheid
**tussen** de 332 toetsen verdragen. Het corrigeert geen ongeldige marginale toets,
postselectie in reeds bekeken 2024 of adaptief gekozen onderzoeksfamilies.
Ook Bonferroni, FDR, meer replicaties of alleen een andere seed repareren dit niet.
Een non-rejection is geen bewijs van afwezigheid van een verband.

## Onderzocht alternatief: gezamenlijke invloedsscore en HAC

Voor een contrast op n UTC4h-tijdgroepen zijn de oorspronkelijke groepssommen en
-aantallen per tijdstip (S_A,t, N_A,t, S_B,t, N_B,t). Coins worden eerst binnen het
tijdstip samengenomen, niet als onafhankelijke clusters geteld.
μ_A=ΣS_A/ΣN_A, μ_B=ΣS_B/ΣN_B, θ=μ_A−μ_B.
De invloedsscore is:

u_t=(S_A,t−μ_A N_A,t)/(ΣN_A/n) − (S_B,t−μ_B N_B,t)/(ΣN_B/n).

Centreer u op zijn steekproefgemiddelde. Definieer
γ_k=Σ[t=k..n−1] u_t u_(t−k)/n.
Bartlett/Newey–West LRV=γ_0+2Σ[k=1..42](1−k/43)γ_k;
SE=sqrt(LRV/n), z=θ/SE, p=erfc(|z|/sqrt(2)).
Het puntgewijze interval is θ ±1,959963984540054 SE.
Lag 42 is vooraf vastgelegd, niet aangepast na de onderstaande uitkomsten.
Geen prewhitening, circular wrap, extra finite-sample-factor of datagedreven lag.

Dit houdt ratio-gewichten, crosscoin-covariantie en overlap tussen groepen A/B
(bijvoorbeeld dezelfde kandidaat in beide D-selecties) in één score bij elkaar.
De relevante theorie vereist onder meer stabiele doelgemiddelden, positieve
limietbezetting, voldoende eindige momenten en afnemende temporele afhankelijkheid.
Voor asymptotische HAC-consistentie moet de bandbreedte passend groeien met n;
een vaste L=42 bij dit eindige n biedt geen universele garantie. Een stationariteitstest
niet verwerpen bewijst deze aannames evenmin. Op pauzeperioden met vrijwel geen
vergelijkbare niet-pauzeobservaties is inferentie sowieso niet geloofwaardig.

Normale staarten worden analytisch met erfc berekend. Er is dan geen discretisatie
van 1/(B+1), maar wel asymptotische model-/staartfout. Een ondergelopen waarde wordt
als begrensde kleinste positieve float met underflowvlag vastgelegd, nooit als exact
p=0. Analytische precisie is dus geen statistische kalibratie.

## Vooraf vastgelegde synthetische validatie

Plan in experiments/phase6e_amendment/synthetic_plan.json, aangemaakt vóór uitvoering.
2.153 tijdgroepen, drie gecorreleerde coins. Per scenario 200 onafhankelijke
synthetische datasets, seed 606100 +1000×scenario-index +dataset-index; burn-in 2.000.
Vier onafhankelijke Gaussische AR(1)-processen met innovatieschaal sqrt(1−rho²):
een gemeenschappelijke factor en drie idiosyncratische factoren.
Coinwaarden: common+id0, 0,5×common+id1, 0,5×common+id2.
Groep A bevat coin0, B coin1/coin2. De nul is het verschil in populatiegemiddelden=0.

Scenario's, in vaste volgorde: rho=0/0,5/0,9/0,98;
variantiebreuk (rho=0,5, alle waarden na halverwege ×4);
random niveauverschuiving (rho=0,5, coin0 na halverwege +één N(0,1)-trekking).
In de laatste case blijft het **onvoorwaardelijke** gemiddelde nul, maar een
persistente random regimeverschuiving schendt de mengings-/stabiliteitsaannames.
Dat is een stresstest buiten het toepassingsgebied, geen bewijs dat HAC onder zijn
reguliere aannames ongeldig is. Hij toont waarom die aannames essentieel zijn.

De oorspronkelijke bootstrap wordt op alleen de eerste twintig datasets per scenario
hergebruikt met 9.999 herhalingen en seed606. Die kleine aantallen zijn een
tegenvoorbeeld-/rooktest, geen nauwkeurige vergelijking van twee rejection rates.
HAC-screen vooraf: bovengrens van het Wilson-95%-interval voor marginale rejection
bij 0,05 moet <=0,10 zijn. Dat is een grove diagnostische afkapregel, **geen**
certificering van exacte 5%-grootte of van de staart 0,05/332. Ook alle gevallen
waar deze ruime screening faalt worden behouden; geen lag/seed/model herafgesteld.

| Scenario | HAC verwerpt bij 0,05 /200 | Wilson 95%, % | HAC bij 0,05/332 /200 | Oude bootstrap bij 0,05 /20 | Screen |
|---|---:|---|---:|---:|---|
| AR0 | 12 | 3,47–10,19 | 0 | 0 | niet gehaald |
| AR0,5 | 7 | 1,71–7,05 | 0 | 1 | gehaald |
| AR0,9 | 20 | 6,57–14,94 | 0 | 4 | niet gehaald |
| AR0,98 | 56 | 22,24–34,59 | 11 | 4 | niet gehaald |
| Variantiebreuk | 17 | 5,37–13,19 | 0 | 1 | niet gehaald |
| Random niveaubreuk | 175 | 82,20–91,39 | 144 | 17 | niet gehaald |

AR0 mist de conservatieve screen nipt door de kleine Monte-Carlo-steekproef;
dat bewijst op zichzelf geen iid-miskalibratie. De sterke afhankelijkheid en
niveauverschuiving geven wel duidelijke waarschuwingen. De oude bootstrap gaf bij
de strengste grens 1/20 verwerpingen voor AR0,98 en 12/20 bij random niveaubreuk.
Er zijn geen gelijktijdige nul-families over vele simulaties getest: geen empirische
FWER-claim. De volledige familie is uitsluitend voor capaciteit/reproduceerbaarheid
uitgevoerd. Zelfs nul verwerpingen in 200 datasets begrenst de werkelijke foutkans
niet nauwkeurig rond 0,00015. Nieuwe historische aannames zijn niet afgeleid uit
deze synthetische resultaten.

## P-waardeprecisie en veilige route voor eventuele latere inferentie

Huidig B=9.999 geeft minimale p=0,0001 versus eerste Holm-grens 0,0001506024.
Slechts nul overschrijdingen kan die eerste grens passeren. Meer trekken vermindert
Monte-Carlo-fout, niet modelbias. Bij de grens bedraagt relatieve MC-SE circa
81,5% (9.999), 25,8% (99.999) en 8,15% (999.999).

Als een toekomstige studentized resamplingtoets eerst inhoudelijk voldoende geldig
wordt bevonden, is dit een **afzonderlijk, niet geactiveerd** precisievoorstel:

- Vaste B=999.999 voor alle 332 toetsen, vaste seed vooraf, geen optioneel stoppen
  na een gunstige p. Geen historische uitvoering zonder apart capaciteitsexperiment.
- Bereken per toets een exacte binomiale Clopper–Pearson-bovengrens op de
  resampling-tailkans met foutbudget η/332, η=0,001. Gebruik de conservatieve
  bovengrenzen voor Holm, met statistisch alpha=0,049. Onder geldige basistoetsen
  geeft de union bound een totaalbudget hoogstens 0,05 inclusief MC-falen.
- Gebruik alleen de bovengrenzen voor eventuele verwerping; overlappende
  Monte-Carlo-onzekerheid met de grens wordt 'onbeslist', nooit een bevestiging.
  Een simultaan bandenschema/sequentiële variant vereist een eigen registratie.
- CP-grenzen, staartinversie en testkalibratie zijn hier niet geïmplementeerd of
  gevalideerd. Het betreft de conditional bootstrap-tailkans; de +1-schatting en
  een valide sampling-p-waarde mogen niet stilzwijgend gelijkgesteld worden.

Deze route verandert expliciet B en verdeelt alpha anders; zij is geen stille
wijziging van het huidige protocol. Op basis van de bestaande meting is alleen
het oude resamplingkernel bij 999.999 al circa 3.706 s (projectie, niet gemeten).
Studentization kan extra tijd kosten. Dat overschrijdt de bestaande 600 s.
Dus nu geen uitvoering, geen budgetverhoging en geen goedkopere asymptotische
p-waarde verkopen als oplossing voor ongeldige inferentie. HAC heeft geen
Monte-Carlo-resolutieprobleem maar faalde de brede betrouwbaarheidstoets.

## Exacte regels van de aanbevolen beschrijvende amendering

1. Na expliciete goedkeuring: gebruik uitsluitend dezelfde 2024-labels en causale
   features, met nieuw uitvoeringsmanifest en oude bron-/configuratiehashcontroles.
   Geen nieuwe horizon, koopregels, uitkomstgrenzen of aanpassing van de vijf hypotheses.
2. Bereken de 332 vooraf bepaalde contrastschattingen voor de oorspronkelijke
   overlappende steekproef en de afzonderlijke UTC4h-grid. Houd beide versies apart;
   geen ranking op effect of selectie van de gunstigste steekproef.
3. Rapporteer per groep n, tijdgroepen, coins, volledige weekdekking, ontbrekendheid,
   gemiddelde, mediaan, p10/p90 en min/max. Gebruik dezelfde nearest-rank-regel.
   Beschrijf tijdvariatie aan de hand van vaste opeenvolgende 42-groepblokken vanaf
   8 januari 00:00; laatste gedeeltelijke blok afzonderlijk. Alle coins blijven samen.
   Die blokbeschrijving is geen nieuwe toetsfamilie en levert geen confidence interval.
4. Geef θ als eindige-steekproefbeschrijving. P, p-Holm, inferentieel interval en
   rejection zijn **null/niet uitgevoerd** voor alle 332 contrasten; reden
   `descriptive_only_prior_view_and_unvalidated_inference`. Geen sterretjes,
   significantiesortering, winstkansen of causale pauze-effecten.
5. Behoud de bestaande minima twintig kalenderblokken/dertig tijdgroepen en
   ontbrekendheid <=1%. Rapporteer bij falen aparte status `insufficient_support`;
   geen inferentie, geen compensatie door overlappende rijen. Een ruwe θ mag alleen
   zichtbaar blijven als expliciet beperkte beschrijving wanneer beide groepsnoemers
   positief zijn. Lege groep/essentiële ontbrekende bron: θ=null, exacte reden.
   D-groepen mogen overlappen; tel groepslidmaatschappen bij hun eigen groep en toon
   beide missing-aantallen. Pas de 1%-grens conservatief op elk van beide groepen toe
   (expliciete verduidelijking ter goedkeuring). Geen selectie op ontbrekende uitkomsten.
6. Geen claims dat een positieve prijsdiagnose uitvoerbaar was; geen som van
   overlappende P&L. De bestaande pauzes, risico- en orderketens blijven bepalend.
7. Budget voor een toekomstige goedgekeurde beschrijving blijft 600 s, 1 GiB
   adresruimte, vroege RSS-stop768 MiB; broncontrole300 s/1 GiB. Limiet of essentiële
   bronfout betekent onvolledige run, geen automatische hervatting vanaf nul.
   De volledige historische reader/extractie is nog niet voor dit amendement gemeten.

Niet-toetsbaar is niet p=1 als onderzoeksconclusie. Alleen in een toekomstig geldig
Holm-pad worden zulke toetsen intern als p=1 meegeteld om de familie332 vast te
houden; zichtbare p blijft null. De aanbevolen beschrijvende route doet geen Holm.
Nieuwe p-waarden/intervalmethodes kunnen niet via een statusvlag worden geactiveerd.

## Middelen, code en integriteit

De synthetische probe had vooraf 300 s hard alarm, 1 GiB adresruimte en RSS-stop
768 MiB; buitenste timeout305 s. Totale probe37,960 s, piek-RSS29,508 MiB.
Een volledige 332-contrast-HAC-familie inclusief synthetische datageneratie kostte
4,397 s; herhaling gaf exact dezelfde resultaatdigest. Geen historische I/O.
Dit is geen schatting van de volledige historische feature-extractiekosten.

Nieuwe losse modules scripts/phase6e_hac.py en phase6e_amendment_probe.py wijzigen
geen bestaande runner, bootstrap, strategie of indicator. Resultaten, bronhashes,
planhash en seeds staan onder experiments/phase6e_amendment/. Het plan is vooraf
op schijf vastgelegd, niet extern/notarieel geregistreerd; geen absolute claim
van onveranderlijkheid. Git legt de uiteindelijke versies vast.

Tests controleren handberekende iid-/Bartlett-varianties, ongelijke noemers via
finite differences, gekoppelde common-factor-annulering, coinduplicatie zonder
pseudo-steekproefgroei, schaal/teken, nulvariatie, ontbrekendheid, p/Holm-randen en
reproduceerbaarheid. Synthetische statistische mislukking blijft een gerapporteerde
methodologische uitkomst, geen weggepoetste softwaretest.

## Eerdere inzage en goedkeuring

2024 was herhaaldelijk bekeken vóór deze amendering. Geen p-correctie maakt
achteraf gekozen onderzoek confirmatoir; 332 corrigeert uitsluitend de vastgelegde
familie, niet alle eerdere of informele keuzes. De vijf hypotheses behouden hun
exploratieve status en rangorde op onderzoekbaarheid. Publiceer alle 332 rijen,
inclusief nulls en onzekere uitkomsten; geen alleen-positieve selectie.
Een toekomstige bevestiging vereist een vooraf geregistreerde, inhoudelijk passende
onafhankelijke onderzoeksopzet en aparte toestemming. 2025 wordt niet achteraf
als onaangeraakt verklaard; 2026 blijft gesloten. Er is nu geen vrijgave voor die
perioden, voor historische patroonanalyse of voor strategiepromotie.

**Ter goedkeuring: de beschrijvende amendering hierboven.** Geen huidige kandidaat
heeft voldoende bewijs voor algemeen geldige inferentie in de gestelde omstandigheden.
Een vervolg naar formele toetsen vereist apart methodologisch werk en een nieuw
besluit. Stop na deze oplevering.

Volledige testsuite: **492 geslaagd, nul mislukt**, alle 480 bestaande behouden plus
12 nieuwe tests. Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. Volledige
bron-/auditintegriteitscontrole in experiments/phase6e_amendment/integrity.json.
