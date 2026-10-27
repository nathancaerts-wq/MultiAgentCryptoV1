# Fase 6B — oorzaakanalyse trage replay

Basiscommit c680510057bef3f2cdc320c27c3075eadf4826e9. Uitsluitend diagnostiek:
geen handels-/runnerlogica gewijzigd, geen commit, geen jaarprobe, geen historische
koersen of rendementen en geen toegang tot de onafhankelijke testperiode.

**Conclusie:** voor de oorspronkelijke lege replay is het herhaald deep-copyen van
volledige, groeiende ledgers de primaire gemeten oorzaak (35,577 van 58,120 s bij
200 stappen). Bij volledige analyses komen herhaalde rapportbundelhashes en het
uitlezen van de hele dataset-cache als grote afzonderlijke oorzaken erbij. De
indicatorwiskunde zelf is in de gemeten 50-stappenketen ongeveer 1% van de tijd.

## Onderzoeksopzet

Deterministische synthetische BTC/EUR, ETH/EUR en SOL/EUR, beslisgrenzen vanaf
2024-01-08 in UTC. De waarden volgen een vaste formule op absolute tijd; dezelfde
candle krijgt in overlappende aanvragen dezelfde waarden. Maximaal 200 stappen
per uitvoering, 15m/1h/4h, standaardindicatorparameters. Datums van gesloten
perioden komen alleen als planmetadata voor, er wordt daar geen candle gelezen.

Twee workloads zijn bewust onderscheiden:

- **chain:** eerst alle analyseberichten opbouwen met de bestaande run_research,
  daarna de bestaande FixtureJointRunner met de gebonden rapportbundel uitvoeren.
  Dit volgt de huidige interface die de volledige bundel vooraf vastlegt. Het is
  geen streamingimplementatie. Hashen van de bundel gebruikt geen toekomstige
  kenmerken bij een eerdere beslissing; de runner selecteert op exact as_of.
- **empty:** dezelfde portfolio-replay zonder analyserapporten, zoals de eerdere
  capaciteitsscreening. Hier worden geen indicatoren of analyseagenten uitgevoerd.
  De kosten van de analyseketen mogen niet als oorzaak van deze lege replay worden
  gepresenteerd.

De nieuwe diagnostische harness staat in experiments/bottleneck/diagnose.py. cProfile
meet functieaanroepen, eigen tijd en cumulatieve tijd; perf_counter meet de fasen
en iedere voltooide stap. Een transparante telwrapper rond technical delegeert naar
de ongewijzigde functie en telt exacte vensters/candlebezoeken. SQLite trace telt
SQL-statements; cProfile telt daarnaast echte Connection.execute-aanroepen.
Trace-aantallen kunnen herhaalde triggertrace en transactiestatements bevatten en
zijn dus niet gelijk aan het aantal applicatiequeries. Initialisatieschemaqueries
zitten wel in de cProfile-execute-teller en niet in de later aangezette trace.

Runs zijn sequentieel gestart: eerst 50, vervolgens 100 en maximaal 200. De chain-
aanroepen hebben een veiligheidslimiet van 300 seconden, de lege replay 180 seconden.
Dit zijn uitsluitend diagnostische limieten voor hoogstens 200 stappen, geen nieuwe
norm voor de vergrendelde 45-secondenjaarcontrole. Er is geen jaarcontrole gestart.
Cumulatieve tijden overlappen en mogen niet worden opgeteld over ouder-/kindfuncties.
De top tien van alle functies bevat vooral asyncio-omhulsels; daarom zijn zowel
alle functies als de tien duurste applicatiefuncties in de meetbestanden opgenomen.

## Belangrijkste aangetoonde oorzaak

**Herhaald verwerken van volledige verzamelingen in plaats van het gevraagde
record of nieuwe verschil.** In de analyseketen is het grootste gemeten individuele
werkpakket het opnieuw serialiseren/hashen van de hele rapportbundel. Een tweede
onafhankelijke kostenpost is het volledig uitlezen/JSON-decoderen van de groeiende
dataset-tabel bij elke cachezoekactie.

In de volledige 50-stappenmeting:

- Totaal 54,217 s; analyse-opbouw 27,011 s, replay 26,604 s.
- report_digest: 208 aanroepen, 21,403 s cumulatief. _read wordt 203 maal aangeroepen;
  _frozen bouwt daarbij steeds een manifest met dezelfde volledige rapportbundel.
  De bundel bevat 150 coinrapporten. Deze overhead blijft bestaan na de prefixcache
  voor joint_states: die cache lost een andere historiecontrole op.
- DataEngine.load: 600 aanroepen, 19,008 s cumulatief. SQLiteStore.list: 602 calls,
  14,173 s cumulatief; vrijwel al deze lijsten zijn de groeiende datasets-cache.
  Uit de directe cProfile-callerrelatie naar json.loads blijkt dat de opslaglijst
  60.945 JSON-records decodeert. Dat zijn geen 60.945 verschillende datasets.
- De twee werkpakketten report_digest en DataEngine.load overlappen onderling niet
  in deze implementatie en nemen samen ongeveer 74,5% van de gemeten totaaltijd in.
  De list-tijd is onderdeel van load, dus niet nogmaals optellen.
- Indicatorfunctie technical: 450 berekeningen, slechts circa 0,529 s cumulatief
  (ongeveer 1% van totaal). Indicatorwiskunde is hier niet de hoofdoorzaak.

## Waarom dit kwadratisch kan groeien

1. **Dataset-cache:** DataEngine.load gebruikt
   `next((x for x in store.list('datasets') if x['id']==key), None)`.
   SQLiteStore.list haalt alle payloads op en decodeert ze vóór de Pythonzoekactie.
   Bij een groeiend aantal unieke vensters is dat O(k) per zoekactie en O(n²)
   over n stappen. Zelfs een cachehit leest de hele cache. De tabel heeft al een
   primaire index op id; de code benut die index hier niet voor een puntlookup.
2. **Rapportbundel:** _frozen → _manifest → report_digest reconstrueert alle berichten,
   sorteert hun JSON en hasht de volledige bundel. Bij O(n) berichten en O(n)
   portefeuillestappen ontstaat minstens kwadratisch serdewerk, met daarbovenop sorteren.
   De per-stapkosten hangen dus ook af van de totale vooraf gebonden bundelgrootte.
3. **Ledger, ook zonder analyses:** _evaluate maakt een deepcopy van de vorige state.
   Per munt wordt de ledger gekopieerd, waarna EntryAgent dezelfde ledger nogmaals
   kopieert. _save kopieert state en serialiseert ledger_state; _read herstelt de hele
   ledger en _validate hasht opnieuw alle ledger-events. Iedere stap voegt minimaal
   een joint_evaluated-event toe. De prefixcache controleert nieuwe state-records,
   maar vermijdt deze groeiende payloadkopieën en eventcontroles niet.
4. **Rapportselectie:** _evaluate doorloopt self.reports bij next per coin en nogmaals
   voor source_reports. Ook dat is een volledige bundelscan per stap. Dit is een
   code-aantoonbare extra O(n²)-bron; de gemeten dominante serdekosten hebben prioriteit.

Historische arrays worden dus daadwerkelijk herhaald opgebouwd: niet alleen de
32-candle-indicatorvensters, maar vooral datasetlijsten, rapport-JSON, volledige
ledger-events en gekopieerde states. SQLite-auditrijen worden append-only geschreven;
er is in dit pad geen aanwijzing dat de hele aparte audit-tabel wordt herlezen.
Wel wordt de ledger-interne auditketen in elke volledige ledger opnieuw verwerkt.

## Herhaalde analyses en candles

Bij 50 stappen worden 450 technische berekeningen gedaan (9 per stap: 3 coins ×
3 timeframes), maar slechts 201 exacte vensters onderscheiden. 249 aanroepen zijn
herhalingen van exact hetzelfde coin/timeframe/start/eind-venster. Elk venster heeft
32 candles: 14.400 bezoeken aan slechts 480 unieke coin/timeframe/candle-identiteiten;
een candle wordt maximaal 50 maal bezocht. Overlap tussen verschillende rolling
vensters is op zichzelf nodig; identieke vensters opnieuw berekenen is vermijdbaar.

Per stap: één scanner, drie Technical Analysis-, drie Market Regime-, drie
Multi-Timeframe-, drie News/Sentiment- en drie gecombineerde rapportagenten: 16
analyse-agentuitvoeringen. Daarnaast drie Decision en drie Entry. Bij de gemeten
workload is geen positie open en draait Exit niet. Geen gesimuleerde trades.
Daardoor worden hier geen conclusies over de prestatiekosten van een actieve
Exit/Risk/fillketen getrokken. De lege replay heeft nul indicatorberekeningen en
nul analyse-agentuitvoeringen, maar nog steeds Decision/Entry en ledgeropslag.

run_research maakt per 15m-stap een nieuwe AnalysisContext en berekent alle drie
frames opnieuw. Een 1h-venster blijft normaal vier stappen gelijk, een 4h-venster
zestien. De gecachete candles voorkomen geen herberekening van technical. De scanner
wordt eveneens elke 15 minuten opnieuw uitgevoerd op het laatst afgesloten 1h-venster.

## Concreet voorstel, nog niet geïmplementeerd

1. **Eerste kleine ingreep:** voeg SQLiteStore.get(table,id) toe en gebruik die in
   DataEngine.load. Haal alleen de gevraagde payload via de bestaande primaire index
   op. Behoud alle bron-, candle-, UTC-, volledigheids- en as_of-validaties.
2. **Rapportbinding:** ontwerp een versiegebonden, diep onveranderlijke gevalideerde
   bundel met eenmalig berekende inhoudshash. Gebruik een index op (coin,as_of) voor
   selectie. Herhash bij een echte wijziging of gewijzigde bronversie; schakel
   mutatiedetectie niet simpelweg uit. Message is frozen, maar zijn nested dicts zijn
   nu nog mutable; alleen een hash memoizen zou de huidige controles verzwakken.
3. **Ledger-hotpath:** een gecontroleerde actuele ledgerstaat, append-only events en
   periodieke checkpoints met incrementele ketenverificatie. Geef agents een kleine
   onveranderlijke portefeuillesnapshot in plaats van twee volledige historiekopieën.
   Behoud duurzame deduplicatie, Decimal, transacties, rollback en herstartbewijs.
4. **Pas daarna indicatorcache:** sleutel op coin, timeframe, gesloten grens, exacte
   vensterinhoud/bronversie, lookback en parameterhash. Geen hele analyseberichten
   hergebruiken met een nieuwe timestamp/TTL. De huidige EMA/Wilder-seeding over
   precies 32 candles moet gelijk blijven; een onbeperkt doorlopende EMA verandert
   de strategie en is geen toegestane performance-optimalisatie.

Aan te passen modules bij een volgende expliciete implementatieopdracht:
crypto/storage.py (puntlookup/eventopslag), crypto/data.py (cachelookup),
crypto/protocol.py (bundelbinding), crypto/joint_portfolio.py en
crypto/readiness_runner.py (manifest, selectie, state-hotpath),
crypto/research_execution.py en eventueel crypto/trade_agents.py (ledger-snapshots),
crypto/analysis.py (versiegebonden technische featurecache). Niet al deze wijzigingen
hoeven tegelijk; eerst de kleine aantoonbare lookupverbetering isoleren.

## Tests die functionele gelijkheid moeten bewijzen

- Exact gelijke berichten, signalen, beslissingen, fills, kosten, afwijzingen en
  Decimal-equity vóór/na, inclusief actieve exits, pauzes en muntwissels.
- Cachehit/miss, gewijzigde bronversie, indicatorparameters, inhoud en tijdzone;
  toekomstige/extreme candles mogen eerdere uitkomsten niet beïnvloeden.
- Afgesloten 1h/4h-grenzen, gaps, duplicaten en onvolledige candles blijven fail-closed.
- Mutaties in nested berichten, oude events, andere databaseverbindingen, rollback,
  rowid-hergebruik en heropening moeten dezelfde integriteitsafwijzing geven.
- Deterministische 50/100/200-prefixen, dezelfde query-/berekeningstellingen,
  checkpoint-herstart en economische inhoud; performancegrenzen los van correctness.
- Aantonen dat een dataset-cachehit één record decodeert en geen hele tabel, en dat
  onveranderde rapportbundels niet per stap volledig worden geserialiseerd.

Alleen de diagnostische runs en tel-/schema-invarianten zijn in deze opdracht
noodzakelijk. Geen volledige testsuite opnieuw uitgevoerd bij ongewijzigde logica.

## Directe hoofdoorzaak van de oorspronkelijke lege replay

De lege 200-stappenreplay kost 58,120 s. `copy.deepcopy` neemt daarvan
35,577 s cumulatief in (circa 61,2%). EntryAgent.__init__ kost 14,181 s,
grotendeels onderdeel van die kopieerkosten; _validate kost 5,766 s.
Hier draaien geen indicatoren, scanner of analyseagenten: die kunnen de
oorspronkelijke lege jaarprobe dus niet verklaren. De primaire oorzaak daarvan
is het per stap veelvuldig kopiëren en controleren van een groeiende volledige
ledger. De state-prefixcache heeft dit niet weggenomen. Voor een latere volledige
analyseketen komen de afzonderlijke bundelhash- en dataset-cacheproblemen erbij.

Het aantal events groeit van 2 bij stap 1 naar 201 bij stap 200; de
statepayload groeit van 2.119 naar 71.068 tekens in de JSON-meetrepresentatie.
Totale functieaanroepen groeien bij viermaal zoveel stappen ongeveer twaalfvoudig,
van 1,55 naar 18,69 miljoen. De volledige statehistorie wordt dankzij de prefixcache
niet steeds gehasht, maar de huidige ledger bevat nog altijd de hele eventhistorie.

## Voltooide schaalmetingen

| Workload | Stappen | Totale s | s/stap | Functieaanroepen incl. recursie | SQLite execute-calls | Indicatorberekeningen |
|---|---:|---:|---:|---:|---:|---:|
|chain_50|50|54.217|1.0843|5689024|19382|450|
|empty_50|50|13.186|0.2637|1550657|3666|0|
|empty_100|100|26.188|0.2619|5180329|7270|0|
|empty_200|200|58.120|0.2906|18686976|14474|0|

Alle door cProfile gemeten functies, eigen/cumulatieve tijden en calls staan
in de bijbehorende JSON en .prof. Het setupdeel en enkele meet-snapshots zijn
inbegrepen. De beperkte 50/100/200-totaaltijden alleen bewijzen geen exacte
kwadratische exponent: per stap gemiddeld 0,264 / 0,262 / 0,291 s bij de lege
replay. Maar de code, eventgroei en functieaanroepen tonen de herhaling van
groeiende arrays wel aan. Hostbelasting en profileroverhead blijven onzekerheden.

| Workload | Gemiddelde eerste 10 stappen s | Gemiddelde laatste 10 stappen s |
|---|---:|---:|
|chain_50: analysis|0.2160|0.7655|
|chain_50: replay|0.4289|0.7423|
|empty_50: replay|0.1246|0.2452|
|empty_100: replay|0.1672|0.2469|
|empty_200: replay|0.0709|0.6136|

Binnen de 200-stappenlege replay stijgt de stapkostenmeting van circa 0,071
naar 0,614 s voor de eerste/laatste tien stappen. Dit is sterke empirische
ondersteuning voor groeiende hotpathkosten, zonder extrapolatie naar een jaar.

## Begrensde uitgebreide metingen

De chain-aanroep voor 100 stappen leverde binnen de 300-secondenbegrenzing
geen volledig resultaatbestand op; er is geen volledige totaaltijd/doorvoer voor
100 chain-stappen beschikbaar. Dat wordt niet als nul ingevuld. De 200-chain-run
is eveneens afgebroken op de grens van 300 seconden inclusief processtart.
Zijn afzonderlijk opgeslagen SIGTERM-profiel bevat 294,171 s na het begin van
de instrumentatie, nog in analyse-opbouw: 119 stappen voltooid en stap 120 deels
uitgevoerd. Geen portfolio-replay voor die 200-chain-run gestart. DataEngine.load
kostte cumulatief 254,735 s, SQLiteStore.list daarbinnen 210,631 s. Dat ondersteunt
het afzonderlijke cacheprobleem, niet een gemeten totale 200-chain-replaytijd.
De gedeeltelijke functieaanroepen/cumulatieve tijden staan in chain_200.partial.prof.
Een langere run is niet nodig om deze oorzaken te identificeren en is niet gestart.

## Tien duurste applicatiefuncties: chain_50

| Functie | Calls | Eigen s | Cumulatief s |
|---|---:|---:|---:|
|run_research|50|0.273971|26.969655|
|FixtureJointRunner.run|50|0.003470|26.348620|
|JointPortfolio._read|203|0.017790|23.030881|
|JointPortfolio._frozen|203|0.020640|22.593773|
|FixtureJointRunner._manifest|204|0.004683|22.518408|
|JointPortfolio._manifest|204|1.185010|22.510049|
|report_digest|208|0.282722|21.402954|
|DataEngine.load|600|1.456858|19.008196|
|AnalysisContext.__init__|150|0.143145|16.575720|
|SQLiteStore.list|602|1.393432|14.173207|
## Tien duurste applicatiefuncties: empty_50

| Functie | Calls | Eigen s | Cumulatief s |
|---|---:|---:|---:|
|FixtureJointRunner.run|50|0.080812|11.737964|
|JointPortfolio.evaluate|50|0.045542|10.023568|
|JointPortfolio._evaluate|50|0.111860|9.978026|
|Orchestrator.execute|50|0.102012|3.582092|
|JointPortfolio._read|203|0.045227|2.222628|
|EntryAgent.__init__|150|0.001842|1.810946|
|DecisionAgent.run|150|0.051020|1.344223|
|fingerprint|359|0.023641|1.279493|
|JointPortfolio._frozen|203|0.034869|1.105748|
|JointPortfolio._save|51|0.015969|1.016405|
## Tien duurste applicatiefuncties: empty_100

| Functie | Calls | Eigen s | Cumulatief s |
|---|---:|---:|---:|
|FixtureJointRunner.run|100|0.018725|25.513685|
|JointPortfolio.evaluate|100|0.142556|22.809370|
|JointPortfolio._evaluate|100|0.263940|22.666814|
|JointPortfolio._read|404|0.266024|5.448377|
|Orchestrator.execute|100|0.203536|4.393419|
|JointPortfolio._save|101|0.031254|4.360014|
|EntryAgent.__init__|300|0.030752|3.702087|
|digest|27612|0.350173|3.221881|
|JointPortfolio._validate|505|0.485590|2.773138|
|canonical|29019|0.178168|2.599263|
## Tien duurste applicatiefuncties: empty_200

| Functie | Calls | Eigen s | Cumulatief s |
|---|---:|---:|---:|
|FixtureJointRunner.run|200|0.080696|57.791620|
|JointPortfolio.evaluate|200|0.265703|52.856336|
|JointPortfolio._evaluate|200|0.491676|52.590633|
|EntryAgent.__init__|600|0.035281|14.180568|
|JointPortfolio._read|805|0.245234|9.052608|
|Orchestrator.execute|200|0.696295|7.830920|
|JointPortfolio._save|201|0.038019|6.841195|
|digest|105263|0.551200|6.407071|
|JointPortfolio._validate|1006|0.810707|5.766397|
|canonical|108071|0.347012|5.759766|

De volledige top tien inclusief standaardbibliotheek/asyncio-omhulsels staat
als top10_all in summary.json; zulke ouderfuncties omvatten vrijwel de hele run.

## Diagnostische controles

Telinvarianten gecontroleerd: maximaal 200 stappen, 9 technische berekeningen
en 16 analyse-agentuitvoeringen per voltooide chain-stap, nul daarvan in empty,
steeds drie Decision- en drie Entry-uitvoeringen per replaystap. Alle datasets
zijn synthetisch; databases waren in-memory. Er zijn geen wijzigingen in crypto/,
tests/, strategieën, parameters of onderzoeksregistraties aangebracht. Alleen
diagnostische artefacten en dit rapport zijn toegevoegd. Geen nieuwe commit.

## Query-aantal versus hoeveelheid werk

De lege replay doet circa 73,3 / 72,7 / 72,4 Connection.execute-aanroepen per stap
bij 50 / 100 / 200 stappen, inclusief setup en meet-snapshots. Het probleem is dus
niet primair een kwadratisch groeiend query-aantal: de omvang van de gekopieerde,
gelezen en geschreven payloads groeit. Dit onderscheid is essentieel bij het
ontwerpen van een oplossing; alleen transacties batchen of SQL-calls verminderen
neemt het herhaalde in-memory deep-copywerk niet weg.
