# Fase 6B — schaalbaarheid en resterende groei

27 oktober 2026. Basis bfb764613059ebcc484dab434b2c62c5eff279d3; schone werkmap
bij aanvang. Alleen deterministische synthetische BTC/EUR-, ETH/EUR- en SOL/EUR-data.
Geen historische rendementsbacktest, geen onafhankelijke testdata, geen jaarprobe.

## Uitkomst

De volledige gemeten analyse-opbouw plus gezamenlijke replay van 1.000 stappen
daalt van 75,814 naar 57,100 seconden. De stapkosten groeien nog en het geheugen
blijft sterk toenemen. De runner is beter geschikt voor een **begrensde** langere
synthetische test, maar een volledig jaar is met de huidige in-memoryopslag niet
verantwoord. Er is geen handels-, indicator-, kosten- of risicoparameter aangepast.

De 2.000-stappenrun is niet gestart: de kleinere metingen geven onvoldoende
geheugen-/tijdmarge. Dit is de expliciet gevraagde conditionele toegangspoort,
geen verzwegen of geslaagde 2.000-stappentest.

## Meetopzet en interpretatie

scripts/measure_scalability.py gebruikt dezelfde synthetische formule als de
vorige fase, cProfile, perf_counter, SQLite-trace en resource.ru_maxrss. Per geval
maximaal 180 seconden via een begrensd subprocess. Alleen 100, 500 en 1.000 stappen
zijn werkelijk gestart. De oorspronkelijke jaargrens van 45 seconden is niet
verhoogd en wordt niet vervangen door deze diagnostische limiet.

De checkpointcode is opnieuw gemeten uit een geïsoleerde git-archive, met dezelfde
harness en interpreter. De nieuwe metingen bewaren de volledige functieprofielen,
callcounts en SQL-payloadgroottes. De omgeving is niet exclusief gereserveerd;
metingen kunnen door hostbelasting variëren. Cumulatieve functietijden overlappen.

**Volledige analyseketen** betekent hier per 15m-stap de scanner en alle vijf
analyse-/rapportagenten per coin, daarna Decision/Entry en de gezamenlijke runner.
De huidige architectuur bouwt eerst de volledige rapportbundel en speelt die daarna
af. De tijd van de eerste/laatste 100 stappen is de som van hun afzonderlijk gemeten
analyse- en replaytijden; setup en bundelinitialisatie zijn alleen in totaal opgenomen.
Dit is geen meting van een reeds bestaande streamingimplementatie.

Zoals in de eerdere performancefixtures ontbreekt een complete toelatingshistorie
voor uitvoerbare instappen; de metingen hebben nul trades en geen actieve Exit-keten.
Ze bewijzen de analyse-/beslis-/administratielast, niet de jaarsnelheid met actieve
posities en exits. Actieve fills, stops, pauzes en audit blijven afzonderlijk via
exacte referentietests gedekt. Dit onderscheid beperkt iedere jaarverwachting.

## Aangetoonde knelpunten

Het profiel vóór wijziging bij 1.000 stappen toont onder andere:

- _validate 17,425 s cumulatief, 5.006 calls; de eventketen werd bij herhaalde reads
  van dezelfde al geverifieerde state opnieuw gecontroleerd.
- _read 20,227 s, 4.005 calls; deze tijd omvat bovenstaande controles.
- Orchestrator.execute 22,268 s; afhankelijkheden worden diep gekopieerd voor
  agentisolatie. Dit is duur, maar niet zonder meer overbodig.
- run_research 29,782 s en DataEngine.load 9,204 s. Veel 1h-/4h-vensters blijven
  tussen 15m-stappen gelijk, terwijl candles opnieuw gedecodeerd en indicatoren
  opnieuw berekend werden.
- _evaluate doorliep voor rapportselectie de hele vooraf gebonden bundel per coin
  en opnieuw voor de gelijktijdige scannercontrole.

De indicatorwiskunde op zichzelf is geen primaire bottleneck. Daarom is geen
andere EMA/Wilder-formule of oneindig doorlopende indicatorstaat ingevoerd.

## Gerichte wijzigingen

### Inhoudsgebonden auditbewijs

JointPortfolio bewaart maximaal acht reeds volledig gecontroleerde statehashes.
Elke nieuwe _save valideert de complete eventketen. Alleen bij herlezing van exact
zo'n geverifieerde state vervalt de herhaalde eventhashlus. De gewone statehash-/
revision-/prefix-/anchorcontrole blijft vóór dit gebruik actief. Bij andere inhoud
ontstaat een andere statehash en volgt volledige auditvalidatie; heropening begint
zonder dit geheugenbewijs. Financiële reconciliatie, fees, trades, cash, posities
 en reserveringen worden ook bij een cachehit gecontroleerd.

Dit bewijs is niet alleen gebaseerd op lengte, laatste event of een bestandsnaam.
Tests wijzigen bewust een oud event én berekenen de buitenste statehash opnieuw:
de corrupte auditketen wordt nog steeds afgewezen. Nieuwe saves, rollback en
reconstructie houden de oorspronkelijke controles. De persistente audit/state-
inhoud en hashformules zijn ongewijzigd; dit is geen sandbox tegen code die interne
cacheobjecten en controles zelf manipuleert.

### Rapportselectie

Een tijdindex op de rapportbundel vervangt de herhaalde volledige scans. Hij wordt
na elke geregistreerde bundelmutatie/vervanging opnieuw opgebouwd en pas na de
bestaande manifestcontrole gebruikt. Groepen zijn tuples; de keuzevolgorde en
scannerafhankelijkheden blijven gelijk. Er is geen hergebruik van een oud signaal
met een nieuwe timestamp of TTL.

### Causale featurecache

AnalysisContext laadt en valideert de candles eerst en berekent hun exacte bestaande
vensterhash. Een LRU van maximaal 128 entries bindt de pure technical-uitkomst aan
vensterinhoud inclusief coin/tijd/source, alle indicatorparameters en de gebruikte
compute-functie. Iedere teruggegeven featurestructuur is geïsoleerd van de cache.
Nieuwe as_of, bericht-ID, dependencies, sentiment en TTL worden normaal opgebouwd.

De berekening blijft steeds de originele EMA/Wilder-seeding over exact 32 candles.
Een gewijzigde bron, parameter, candle of implementatiefunctie invalideert de cache.
Toekomstige/extreme candles kunnen een oude analyse niet wijzigen; dit wordt getest.

### Cache van gevalideerde candles

SQLiteStore.get_payload leest bij iedere aanvraag de actuele tekstpayload via de
primaire sleutel. Een begrensde cache van maximaal 128 records hergebruikt alleen
frozen Candle-objecten als die volledige payloadtekst exact gelijk is aan de eerder
gevalideerde versie. Bij gewijzigde inhoud wordt opnieuw gedecodeerd/gevalideerd.
Er wordt geen declared SHA-veld of vermeende file-onveranderlijkheid vertrouwd om
gewijzigde database-inhoud over te slaan.

De caller krijgt een onafhankelijke lijst. validate_series met het actuele as_of
loopt altijd door, ook bij een hit. Andere opslagimplementaties zonder get_payload
houden het bestaande get-pad. Bronfileverversing volgt nog de bestaande expliciete
importidentiteit; deze wijziging geeft geen historische re-import automatisch vrij.

### Wat bewust behouden bleef

Alle agenten en orchestrator-auditgebeurtenissen worden nog per stap uitgevoerd.
De afhankelijke berichten blijven geïsoleerd: circa 11 s bij 1.000 stappen zit nog
in de deepcopy van orchestrator-inputs. Deze isolatie zonder COW-/immutable-
contract overslaan zou financieel gedrag kunnen beïnvloeden. Er zijn geen
transactiegrenzen samengevoegd of auditregels verwijderd om sneller te lijken.

## Functionele gelijkheid en tests

Een afzonderlijke 100-stappenreferentie is uitgevoerd tegen de checkpointcode en
de nieuwe code. Alle results, analyses, regimes, scan_runs, joint_states,
joint_batches, joint_settlements en persistente audit zijn **byte-exact gelijk**
na deterministische JSON-normalisatie. Alleen de audit-wallclock is voor beide
runs gelijk vastgezet. De huidige code wordt bovendien in een regressietest
opnieuw tegen deze oude referentie uitgevoerd.

De bestaande golden tests voor actieve fills, kosten, stop-loss, muntwissels,
noodstop, dagverlies, drawdown, verliesreeks, rollback en herstart blijven slagen.
Nieuwe tests controleren onder meer cache-isolatie/-begrenzing, parameter- en
bronwijzigingen, implementatie-identiteit, extreme toekomstige candles, ongeldige
oude events met herberekende statehash en mutatie van de rapport-tijdindex.

**353 tests geslaagd, 0 mislukt**: alle 340 bestaande plus dertien nieuwe.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. Geen historische testperiode
is vrijgegeven; synthetische testdatums vormen geen toegang tot echte testdata.

## Definitieve metingen

| Variant | Stappen | Totaal s | Gemiddeld s/stap | Eerste 100 s | Laatste 100 s | Piek-RSS MiB |
|---|---:|---:|---:|---:|---:|---:|
|before|100|4.921|0.04921|4.503|4.503|85.3|
|before|500|30.103|0.06021|4.407|6.857|324.3|
|before|1000|75.814|0.07581|4.476|9.793|675.6|
|after|100|4.221|0.04221|3.868|3.868|93.3|
|after|500|25.630|0.05126|4.105|5.327|328.2|
|after|1000|57.100|0.05710|3.948|6.631|685.2|

Bij 100 stappen zijn de eerste en laatste 100 vanzelf dezelfde groep. De
herhaalmeting tijdens de eerste optimalisatiestap staat apart in after_stage1;
alleen after bevat de definitieve candlecache. Er is geen betere run geselecteerd
op financiële uitkomsten.

| Grootste applicatiefuncties, nieuwe 1.000-run | Calls | Cumulatief s |
|---|---:|---:|
|run_research|1000|28.026|
|FixtureJointRunner.run|1000|24.607|
|Orchestrator.execute|2000|22.307|
|JointPortfolio.evaluate|1000|20.434|
|JointPortfolio._evaluate|1000|20.269|
|<genexpr>|52000|11.130|
|AnalysisContext.__init__|3000|9.815|
|JointPortfolio._save|1001|7.795|
|DataEngine.load|12000|7.170|
|JointPortfolio._read|4005|6.311|

De auditvalidatie daalt van 17,425 naar circa 3,6 s; aanroepen van de algemene
digest-helper dalen van circa 2,52 miljoen naar 0,52 miljoen. De 9.000 oorspronkelijke technische
berekeningen worden 3.939 cachemisses plus 5.061 veilige hergebruikacties. Alle
analyse-agenten blijven draaien. De grootste resterende kosten zitten in JSON/
berichtisolatie, datasetverwerking en het opslaan/lezen van complete statepayloads.

## Groei en beslissing over 2.000 stappen

De gezamenlijke statepayload groeit van 1.925.619 bytes bij 100 naar 44.302.219
bij 500 en 175.347.971 bij 1.000. Verdubbeling 500→1.000 geeft bijna viermaal zoveel
stateopslag. Deze payloadgroottes zijn vóór en na exact gelijk: de volledige
historie is niet weggegooid. De nieuwe caches verminderen werk, niet dit opslagformaat.
Het bewijst een resterend O(n²)-achtig opslagpatroon, geen volledig lineaire runner.

De gate voor 2.000 gebruikt de bestaande diagnostische tijdsbegroting 180 s en een
conservatief geheugenbudget 1,5 GiB. Viermaal de gemeten 1.000-run (worst-case bij
kwadratische groei) geeft circa 228 s en 2,68 GiB RSS. Beide overschrijden de
begroting. De tijdguard is bewust conservatiever dan de driepuntsfit; de
geheugenoverschrijding is op zichzelf al voldoende reden om te stoppen. Daarom
**2.000 niet uitgevoerd**. Dit budget is een selectievoorwaarde,
geen claim dat de eerdere runs onder een gemeten harde RSS-limiet zijn afgedwongen.

## Verwachting voor een volledig jaar

Een synthetisch schrikkeljaar bevat 35.136 kwartierstappen. Een volledig lineaire
projectie van de nieuwe 1.000-run zou circa 33 minuten geven. Die projectie is
optimistisch en past niet bij de gemeten groeiende stap- en opslagkosten.

Een exacte interpolatie T(n)=c+a*n+b*n² door de drie nieuwe metingen geeft op
35.136 stappen circa **4,05 uur geprofileerde wandtijd onder dezelfde modelaannames**.
Dit is een rekenmodel op drie punten, geen gemeten jaarresultaat, statistisch
interval of betrouwbare SLA. De negatieve kleine fitted intercept wordt niet
fysisch geïnterpreteerd. Hostbelasting, actieve posities en volledige toelatings-
historie kunnen de tijd verhogen. De daadwerkelijke huidige in-memoryrunner zal
waarschijnlijk eerder tegen het geheugenbudget lopen: het statepayloadmodel alleen
komt uit op circa **214 GB** JSON, nog zonder andere tabellen, objecten en SQLite-
overhead. Er bestaat dus geen verantwoorde claim dat de huidige configuratie dit
jaar werkelijk zou afmaken in vier uur.

**Advies:** wel klaar voor een volgende gecontroleerde *kleine uitbreiding* tot
maximaal 1.250 synthetische stappen, met timeout 180 s, geheugenbewaking en een
harde address-spacegrens van 1,5 GiB. Stop eerder bij circa 1,2 GiB RSS. Dit is een
voorgestelde vervolgtest, niet uitgevoerd in deze opdracht. Eerst dezelfde
correctheid-/causaliteitscontroles en een actieve-positievariant toevoegen. Voor
een jaarprobe is nog geen verantwoorde nieuwe tijdslimiet vrij te geven; eerst
stateopslag normaliseren of streamen met gelijkwaardig audit-/herstartbewijs.
De oorspronkelijke 45-secondenvoorwaarde wordt niet als geslaagd gepresenteerd.

## Oplevering en resterend werk

Aangepast: crypto/analysis.py, crypto/data.py, crypto/storage.py en
crypto/joint_portfolio.py. Indicator-, scanner-, strategie-, kosten- en risico-
formules zijn behouden. Profielen, gecomprimeerde referenties, hashes en de
machineleesbare beslissing staan in experiments/scalability/.

De volledige jaarcapaciteit en een lange actieve handelsketen zijn nog niet
bewezen. Historische rendementsevaluatie en de onafhankelijke test blijven gesloten.
PROGRESS.md en NEXT_STEPS.md zijn bijgewerkt. Geen volgende fase automatisch gestart.
