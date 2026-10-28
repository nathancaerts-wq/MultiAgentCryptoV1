# Voortgang — fase 1

## Voltooid

- Python-package met 13 expliciete componentcontracten en afhankelijkheden.
- Centrale asynchrone orchestrator: registratie, DAG-validatie, timeouts,
  pauzeren/hervatten, persistente event-deduplicatie en auditregistratie.
- Pydantic-berichten met UTC, TTL, status en foutvalidatie.
- SQLite-opslag voor alle gevraagde domeinen en transactionele ordervoorstellen.
- Deterministische risicolimieten, noodstop, saldo- en orderfiltercontroles.
- Geïsoleerde onderzoekskandidaten, periodehergebruikcontrole en inactieve goedkeuring.
- Publieke Binance metadata-adapter, EUR-universumselectie en alleen-lezen API.
- Windows-installatie-instructies, dependencyversies en cloud-opstartinstructies.

## Validatie

44 tests geslaagd met Python 3.12 op Linux. Getest: registratie, communicatie,
berichtschema, taakvolgorde/cycli, agentfouten/timeouts, pauzeren/hervatten,
verlopen/toekomstige signalen, dubbele events na databaseheropening,
transactierollback, veiligheidsgrenzen, dubbele ordervoorstellen,
onderzoeksisolatie, Binance fixtureparser, scanner en alle API-endpoints.
Een gevonden herregistratiefout na een herstart is hersteld.
`pip check` meldt geen dependencyconflicten. Installatie is opnieuw uitgevoerd.
De echte HTTP-server is gestart; /health en /portfolio geven de verwachte waarden.

## Beperkingen en openstaande punten

- Publieke Binance-integratie niet live geverifieerd: netwerkproxy geeft 403.
  api.binance.com is toegevoegd aan de concept-omgevingsconfiguratie; toepassen en
  opnieuw controleren is nodig vóór gebruik van echte marktdata.
- Windows 11 is gedocumenteerd maar niet op deze Linux-machine getest.
- Eén externe Starlette/AnyIO-deprecationwaarschuwing; geen testfouten.
- Geen strategieën, LLM-integratie, historische backtestberekening, fills,
  saldoreservering, positiewaardering of grafisch dashboard. Dit zijn volgende fases.
- SQLite gebruikt generieke JSON-records. Getypeerde migraties, grotere datasets,
  concurrente workers en procesisolatie zijn vervolgwerk.
- Goedkeuring is een lokaal Python-contract, zonder geauthenticeerde reviewerworkflow.
- Marktmetadata ondersteunt de basisfilters; volledige Binance-filterdekking moet
  worden uitgebreid voor uitvoeringssimulaties. Geen claim van handelsgereedheid.

Fase 1 vormt een testbare basis voor fase 2. De genoemde integratiebeperkingen
moeten daar expliciet worden afgehandeld. Alleen virtuele voorstellen; geen transacties.

## Fase 2

Marktdata-engine, UTC-OHLCV-validatie, onveranderlijke importcache, volledige
4h-aggregatie, deterministische multi-coin ranking, lokale CLI en alleen-lezen
scanner/data-quality API toegevoegd. Alle 67 tests slagen (44 bestaande + 23 nieuwe).
Geen risico- of handelscode aangepast. Netwerk: api.binance.com geeft HTTP 451;
beide vision-hosts staan niet in de beschikbare allowlist en zijn niet getest.
Actuele EUR-instrumenten en echte historische datasets blijven onbevestigd.
Zie PHASE2_REPORT.md voor volledige oplevering en beperkingen.

## Fase 2B

Officiële dagelijkse Binance Spot ZIP/CSV-adapter toegevoegd met verplichte SHA-256,
exacte ms/us-conversie volgens het gedocumenteerde datumformaat, volledige dagvalidatie
en expliciete officiële 1h/4h-vergelijking. Integreert met Candle en bestaande caching;
datasetrecords bewaren archiefprovenance, checksum en validatiestatus.

96 tests slagen: alle 67 bestaande plus 29 nieuwe archieftests. Echte integratie:
7 kleine archieven via HTTP 200, 276 geldige candles, alle checksums gelijk;
BTCEUR en ETHEUR 1h/4h komen exact overeen. Geen orders aangemaakt.
Beperkingen: uitsluitend dagelijkse expliciete batches van maximaal zeven archieven,
geen automatische verversing van gewijzigde bronbestanden; Windows niet uitgevoerd.
Zie PHASE2B_REPORT.md. Fase 3 niet gestart.

## Fase 3

Vier gespecialiseerde onderzoeksagenten toegevoegd: market regime, technical
analysis, multi-timeframe en news/sentiment. Geïntegreerd met scanner, DAG,
Message-validatie, audit, SQLite en alleen-lezen API. Deterministische EMA/RSI/ATR,
momentum en prijsstructuur; parameters en candleprovenance worden vastgelegd.
Geen betrouwbare nieuwsfeed: expliciet unknown, geen verzonnen sentiment.
Historische replay ververst geen signaal; ontbrekende data/conflicten blijven zichtbaar.

124 tests geslaagd, 0 mislukt (96 bestaande + 28 nieuwe). Zes echte publieke GETs
HTTP 200, 192 candles, twee historische coinrapporten; alle indicatorframes compleet,
regime uncertain, timeframes conflict, rapporten incomplete door ontbrekend nieuws.
Lokale CLI en API eveneens getest. Eén bestaande dependencywaarschuwing.
Beperkingen: geen point-in-time bronversies/publicatielatentie of betrouwbare nieuwsfeed,
Windows niet uitgevoerd, single-process SQLite. Zie PHASE3_REPORT.md.
Geen transacties of parameteroptimalisatie. Fase 4 niet gestart.

## Fase 4

QuantResearcher, ResearchPlan en OfflineResearchOptimizer toegevoegd met vaste
hypotheses, preregistratie, chronologische splits/embargo, walk-forward-planning,
bundelhashcontrole en duurzame registratie van bekeken testperioden.
Kosten- en risicorekeninterfaces: €200 en maximaal 0,5% gepland risico per trade.
Bestaande productiestrategieën, agents en harde grenzen worden niet gewijzigd.

154 tests geslaagd, 0 mislukt (124 bestaande + 30 nieuwe). Geen gevalideerde
fillsimulator aanwezig: prestaties, benchmarks en gevoeligheidsuitkomsten blijven
expliciet niet berekend, met onvoldoende bewijs. Geen winstclaims of transacties.
Zie RESEARCH_PROTOCOL.md en PHASE4_REPORT.md. Fase 5 is niet gestart.

## Fase 4B

Onderbroken ontwikkeling hervat en behouden vanaf da81022303a8300ded72519567114701ff0482a1.
Offline fillsimulator, single-position EUR-ledger en preregistreerde backtestrunner
met kosten, orderfilters, stops/gaps, risico- en verliespauzes, audit-hashketen,
benchmark- en gevoeligheidsscenario's. Onderzoeksopslag en API blijven gescheiden
van papertrading. Bestaande agenten en harde grenzen zijn ongewijzigd.

191 tests geslaagd, 0 mislukt (154 bestaande + 37 nieuwe). De bestaande kleine
BTC/EUR-integratietest is gecontroleerd en opgeslagen in experiments/phase4b_smoke.json;
geen nieuwe historische backtest uitgevoerd bij hervatten. Historische orderfilters
zijn aannames; alle uitkomsten blijven onvoldoende bewijs. De onafhankelijke test
is niet vrijgegeven. Zie PHASE4B_REPORT.md voor alle uitvoeringsaannames en beperkingen.
Fase 5 niet gestart.

## Fase 5

Decision, Entry en Exit geïntegreerd via bestaande analyses, Message, orchestrator,
Risk Engine en een afzonderlijke offline Execution-adapter. Bevroren beslisbeleid,
transparante HOLD/conflicten, 0,5% gepland risico inclusief kosten, bestaande
verlieslimieten, conservatieve exits, verliesreekspauze, persistente deduplicatie
 en ledgerherstel. Geen automatische paper-orders of strategiepromotie.

251 tests geslaagd, 0 mislukt (191 bestaande + 60 nieuwe). Kleine lokale integratie
met zes officiële Binance-archieven en 252 candles; alle checksums geldig. BTC/EUR
 en ETH/EUR geven HOLD wegens onvoldoende warm-up. Volledige entry/exit/fillketen
met synthetische fixtures getest. Onafhankelijke test blijft gesloten; geen nieuwe
uitgebreide backtests. Zie PHASE5_REPORT.md en experiments/phase5_smoke.json.
Fase 5 afgerond; geen volgende fase gestart.

## Fase 6A

Nieuwe gezamenlijke portefeuillemode met één €200-balans voor de hele EUR-watchlist.
Cash, bezit, fees, P&L en verliespauzes blijven gedeeld bij muntwissels. Centrale
Risk Engine, één positieplaats, atomische reserveringen, reproduceerbare ranking
met zichtbare UTC-rotatie bij ties, expliciete offline fills en duurzame deduplicatie.
Bestaande simulator, bots en risicoconfiguraties zijn behouden.

287 tests geslaagd, 0 mislukt: alle 251 bestaande plus 36 nieuwe. Twee verbindingen,
rollback, muntwissels, heropening, gedeelde verliesbescherming en de volledige
portefeuille-reproduceerbaarheid zijn getest met kleine fixtures. Geen nieuwe
historische downloads, parameteroptimalisatie of onafhankelijke testinzage.
Zie PHASE6A_REPORT.md. Fase 6A afgerond; geen volgende fase gestart.

## Fase 6B — preregistratiecontrole afgerond, evaluatie geblokkeerd

Vanaf b1c6049ff36e34b3c1fd6adec4cf5f490a6dd289 zijn bestaande plannen,
configuraties, experimentartefacten en toegankelijke projectdatabase-metadata
gecontroleerd. Twee oude smoke-testplannen zijn teruggevonden; geen volledig
fase-6B-plan voor de gezamenlijke zesmunten-evaluatie of compleet inzageregister.
Exacte nieuwe perioden, historische universumregels, gezamenlijke benchmarks en
meet-/gevoeligheidsconventies ontbreken. De gezamenlijke runner ondersteunt nog
uitsluitend ontwikkeling tot 192 candles per coin.

Conform de expliciete stopvoorwaarde is vóór nieuwe historische resultaten gestopt.
Geen nieuwe Binance-verzoeken of evaluatieruns; onafhankelijke test niet geopend.
Alle prestatievelden blijven niet berekend. 287 bestaande tests geslaagd, 0 mislukt;
een bestaande dependencywaarschuwing. Geen runtime-, strategie- of risicowijzigingen.
Zie PHASE6B_REPORT.md en experiments/phase6b_preregistration_audit.json.
De historische evaluatie is niet voltooid; geen volgende fase gestart.

## Fase 6B — protocolvoorstel, wacht op expliciete goedkeuring

Op 27 oktober 2026 (Europe/Brussels) vanaf
58863994285005fe052d9e87acc52eadedcdfe0d de oude plannen en inzage gecontroleerd.
PHASE6B_PROTOCOL_PROPOSAL.md stelt ontwikkeling 2024, validatie vanaf februari
2025 en een voorlopig gesloten testvenster januari–september 2026 voor. Heel 2025
als validatie conflicteert met het bestaande testslot 15–16 januari 2025 en eerdere
inzage. Oude registraties en PHASE6B_REPORT.md blijven ongewijzigd. De eerder
gecontroleerde tijdelijke projectdatabases zijn nu niet meer aanwezig; externe
onaangeraaktheid blijft onbewezen.

Uitsluitend HEAD-metadata onderzocht voor zes EUR-paren op 15m/1h/4h in alle
maanden van 2024 en 2025: 432 ZIP- en 432 CHECKSUM-objecten, alle HTTP 200,
plus twee voorafgaande succesvolle HEAD-probes. Geen nieuwe koersbestanden,
checksuminhoud, signalen of rendementen bekeken; geen 2026-verzoeken.
Bestandsaanwezigheid bewijst nog geen candlekwaliteit of historische orderfilters.
Bewijs en herhaalbaar begrensd script zijn opgeslagen.

Voorstel specificeert vaste aligned_trend, één €200-ledger, bestaande risicogrenzen,
liquiditeit/datatoelating, cash/marktindex/EMA-benchmarks, uitkomsten en kostenstress.
Nieuwe toelatingsvoorwaarden zijn expliciet voorstellen, niet in handelscode
geïmplementeerd. Historische filterbewijzen en een geteste lange gezamenlijke
validatierunner ontbreken nog. Zonder geldige metadata wordt niet ingestapt.

287 bestaande tests geslaagd, 0 mislukt; één bestaande dependencywaarschuwing.
Geen rendementsbacktests en geen testvrijgave. Stop na dit voorstel en wacht op
expliciete goedkeuring vóór evaluatie; geen automatische vervolgfase.

## Fase 6B — technische voorbereiding

Dagelijkse data-audit, expliciete periode-/testsloten, inhoudsgebonden manifest,
trailing liquiditeit, langere gezamenlijke fixture-runner en benchmarkprimitieven
toegevoegd. De bestaande centrale ledger, Risk Engine en simulator worden hergebruikt.
Historische rendementen zijn niet vrijgegeven. Volledige corpusaudit, bewezen
historische filters en de historische validatieregisseur blijven blokkeringen.
Officiële documentatieverzoeken faalden met proxy 502; geen reconstructie geclaimd.
Zie PHASE6B_READINESS_REPORT.md voor exact gerealiseerde onderdelen en beperkingen.

Definitieve verificatie: 310 tests geslaagd, 0 mislukt; één bestaande dependencywaarschuwing.

## Fase 6B — resterende blokkeringen onderzocht

Volledige zesmunten-data-audit uitgevoerd met officiële maandchecksums, dagelijkse
validatie, timeframevergelijking, schijfcache en downloadbudget. XRP/ADA/LINK hebben
strikte timeframe-afwijkingen; exacte dagrapporten zijn bewaard. Historische filters
blijven onbewezen; een hypothetisch model is alleen voorgesteld, niet geactiveerd.
Kalenderbinding benchmarks getest. Echte zesmunten-jaarfixture gemeten; candlehash-
cache en tijdindex versnellen verwerking, maar de jaarreplay voltooit niet binnen
45 seconden. Schaalbaarheid blijft open. 317 tests geslaagd, 0 mislukt; één bestaande
waarschuwing. Geen historische rendementen of testvrijgave. Zie PHASE6B_FINAL_READINESS.md.

## Fase 6B — afzonderlijke drie-muntenstudie, gestopt vóór backtest

De gebruiker gaf voorwaardelijke toestemming voor BTC/EUR, ETH/EUR en SOL/EUR.
PHASE6B_THREE_COIN_AMENDMENT.md legt de afzonderlijke hypothetische studie vast.
Bestaand en nieuw manifest gecontroleerd; BTC D/V/warm-up en ETH ontwikkeling opnieuw
uit cache gevalideerd. De synthetische drie-muntenjaarcontrole voltooide niet binnen
45 seconden. Volgens de expliciete stopvoorwaarde is geen historische backtest gestart
en de overige datahercontrole gestopt. 317 tests geslaagd, 0 mislukt; één bestaande
waarschuwing. Jaarreproduceerbaarheid niet bewezen; onafhankelijke test gesloten.
Zie PHASE6B_BACKTEST_REPORT.md. Geen commit/push wegens de niet-geslaagde essentiële
controle; bestaande HEAD b55aa218f66b3facd6d980032fea495f9701bf80 behouden.

## Fase 6B — performanceonderzoek

Vanaf d46f2f9 cProfile- en tracemalloc-metingen met uitsluitend synthetische data.
De herhaalde volledige SQLite-statecontrole is deels geoptimaliseerd met een
gecontroleerde prefixcache, mutatietriggers en portfolio-index. De drie kleine
voor/na-fixtures leveren exact dezelfde economische inhoud en berichten op.
De synthetische jaarcontrole voltooit echter nog niet binnen 45 seconden; omvangrijke
ledgerkopieën en JSON-opslag blijven knelpunten. Geen historische resultaten of
testvrijgave. Zie PHASE6B_PERFORMANCE_REPORT.md en experiments/performance/.

Definitieve suite: 324 tests geslaagd, 0 mislukt; één bestaande waarschuwing.
Geen commit/push omdat de volledige jaarcontrole niet slaagt; wijzigingen lokaal bewaard.

## Fase 6B — targeted performance fix

Gerichte financiële analyseviews vervangen grote agent-ledgerkopieën; gerichte
statevelden blijven binnen bestaande SQLite-transacties. Dataset-cache gebruikt
primaire-key-lookups. Rapporthashes zijn mutation-versiegebonden met fallback voor
onbekende mutable payloads. De originele referenties, inclusief persistente audit,
rollback, herstart en risicopauzes, zijn exact gelijk. Alle 340 tests slagen (324
behouden plus zestien nieuwe), één bestaande waarschuwing.

De 50/100/200/1.000-stappenmetingen zijn voltooid. Lege 1.000-replay: 33,740 s
tegenover 123,162 s met de checkpointcode opnieuw gemeten; chain 1.000: 76,711 s.
Volledige stateserialisatie/eventvalidatie blijft groeien. Geen jaarprobe uitgevoerd,
geen historische backtest of testvrijgave. Zie PHASE6B_LEDGER_OPTIMIZATION_REPORT.md.
De bestaande lokale oorzaakanalyse en artefacten zijn behouden.

## Fase 6B — scalability finalization

Volledige synthetische analyse-opbouw/replay gemeten voor 100/500/1.000 stappen,
met cProfile, eerste/laatste 100 en piek-RSS. 1.000 stappen: 75,814 → 57,100 s.
Begrensde causale feature- en gevalideerde candlecaches, versiegebonden rapportindex
en inhoudsgebonden auditbewijs verminderen herhaald werk. 100-stappenreferentie
inclusief analyses en audit byte-exact gelijk. Alle 353 tests slagen (340 behouden
plus dertien nieuwe); één bestaande waarschuwing.

Geen 2.000-run wegens voorspelde tijd/geheugen boven het diagnostische budget.
Geen jaarprobe of historische backtest. Stateopslag blijft bijna kwadratisch;
modeljaar circa 4 uur bij voldoende middelen, maar circa 214 GB statepayload maakt
dat geen uitvoerbare verwachting voor de huidige in-memoryconfiguratie.
Zie PHASE6B_SCALABILITY_REPORT.md. Onafhankelijke test gesloten.


## Fase 6B — streamingcheckpoint, 28 oktober 2026

Geheugenbegrensde fixture-runner met schijfopslag, compacte checkpoints en
append-only historie toegevoegd. Bestaande agents, risicoregels en Decimal-fills
worden hergebruikt. Exacte vergelijking met de bestaande runner, procescrash,
rollback, pending entry/exit, dubbele fills en risicopauzes getest.

Bestaande definitieve metingen bevestigd: 500 stappen 25,067 s / 59,0 MiB;
1.000 stappen 52,620 s / 60,6 MiB; 2.000 stappen 112,010 s / 64,0 MiB;
5.000 stappen voltooid in 291,499 s / 74,4 MiB. Geen meetproces bij hervatting,
geen nieuwe meting gestart. Alle bronhashes stemmen overeen. 377 tests geslaagd
(353 behouden plus 24 nieuwe), 0 mislukt, één bestaande dependencywaarschuwing.

Het herhaald lezen/hashen van de volledige auditgeschiedenis blijft een CPU-/I/O-
bottleneck. Prestatiefixtures hadden nul trades; lange actieve handelsketens en
jaarcapaciteit zijn niet bewezen. Geen historische backtests, jaarprobe, testvrijgave
of strategie-/risicowijzigingen. Zie PHASE6B_STREAMING_REPORT.md.


## Fase 6B — audit-hashoptimalisatie, 28 oktober 2026

Begrensde 2-MiB-cache van exacte eventbytes vermindert herhaalde SQL-prefixlezingen.
Hashsemantiek, stream-v1-checkpoints, financiële regels en herstelcontroles behouden.
Rollback/savepoint wist de cache; externe commits, tailcontrole en mutatie-epoch
beschermen tegen verouderd hergebruik. Herstart verifieert alles zonder cache.

100/500/1.000 synthetische stappen gemeten met elk drie gesloten virtuele trades.
Alle vergeleken analyses, beslissingen, fills, states en auditregels exact gelijk
tegen de module uit 00271e1. Bij 1.000 stappen: hashfunctie 2,028 → 0,886 s;
totaal 89,977 → 91,382 s. Geen aantoonbare totale versnelling geclaimd.
385 tests geslaagd (377 behouden plus acht nieuwe), 0 mislukt, één bestaande
waarschuwing. Geen 5.000-run, jaarprobe, historische rendementen of testvrijgave.
Zie PHASE6B_AUDIT_OPTIMIZATION_REPORT.md voor beperkingen en metingen.


## Fase 6B — historische januari-ontwikkelpilot, 28 oktober 2026

Expliciet geautoriseerde aparte pilot over januari 2024, BTC/EUR, ETH/EUR en SOL/EUR.
Negen volledige officiële archieven opnieuw op checksum, UTC/OHLCV, dekking en
15m/1h/4h-consistentie gecontroleerd; 11.718 broncandles geldig. Warm-up 1–7 januari,
entries vanaf 8 januari. Bestaande aligned_trend en baseline/hypothetische filters.

Pilot volledig afgerond: 2.305 evaluatiegrenzen, 78,706 s, 70,1875 MiB piek-RSS.
127 BUY-kandidaten, zeven entryreserveringen waarvan vier fillafwijzingen, drie
gesloten verliestrades. Netto −€2,96793681; eindwaarde €197,03206319, vlak. Gezamenlijke
verliesreekspauze behouden. Audit, zes unieke fills, cash/fees en checkpointherstel
geverifieerd; 389 tests geslaagd, 0 mislukt. Drie trades zijn onvoldoende bewijs.

Zie PHASE6B_JANUARY_PILOT_REPORT.md en experiments/january_pilot/. Checkpointdatabase
/workspace/january_pilot.sqlite3 behouden, niet in Git. Geen validatie, onafhankelijke
test, jaarprobe, benchmarks/stressruns, optimalisatie of echte orders. Stop na pilot.

## Fase 6B — ontwikkeljaar 2024 volledig afgerond

Alleen BTC/EUR, ETH/EUR en SOL/EUR, 2024; warm-up 1–7 januari. Alle 108 officiële
archieven/138.348 broncandles opnieuw geldig. De bestaande voorbereiding is bij
hervatting hergebruikt; geen duplicaatproces of financiële herstart vanaf nul.
Januari-checkpoint ongewijzigd geverifieerd; afzonderlijke jaarreplay wegens de
verzegelde maandgrenzen. Jaarprefix januari exact gelijk: €197,03206319 en drie trades.

Alle zes geregistreerde replays volledig voltooid, januari t/m december: drie
aligned_trend-kostenscenario’s en drie EMA-benchmarkscenario’s. Ieder 34.465
chronologische evaluatiegrenzen; één €200-portefeuille per vergelijkingsscenario,
geen reset per maand/coin. Baseline: 1.953 kandidaten, zeven entryreserveringen,
vier fillafwijzingen, drie gesloten verliestrades; netto −€2,96793681 en eindkapitaal
€197,03206319. Verliesreekspauze vanaf 11 januari blijft het hele jaar actief.
Slippage-stress €197,03119966; dubbele kosten €197,03035790. EMA-baseline €200,58224413,
EMA-slippage €199,17805569, EMA-dubbel €199,50530416; elk vijf trades. Onvoldoende bewijs.
Cashbenchmark €200. Driemunten-buy-and-hold niet uitgevoerd: bestaande functie
vereist zes coins; geen vervangende regels geïntroduceerd.

Alle replays binnen 1.800 s en 1,5 GiB adresruimte; voorbereiding 694,180 s /
177,113 MiB piek-RSS. Definitieve read-only verificatie: zes audit-/checkpointketens,
unieke fills, kas/fees/netto, risicolimieten, chronologie, alle maanden/coinbijdragen,
SQLite integrity ok, nul paperorders. Database /workspace/development_2024.sqlite3
15.057.117.184 bytes; inhoudshash en eindcheckpoints in verification.json.
402 tests geslaagd, 0 mislukt, één bestaande dependencywaarschuwing. Bestaande
389 tests en strategie-/risicomodules behouden. Geen validatie/test, optimalisatie
of echte orders. Zie PHASE6B_DEVELOPMENT_2024_REPORT.md en experiments/development_2024/.
Stop na ontwikkeling 2024; geen automatische vervolgfase.

## Fase 6C — diagnostiek voltooid, nieuwe uitkomstlabels geblokkeerd

Vanaf 86596f90: verliesreeks 1/2/3 gereconstrueerd, alle volgende checkpoints blijven
gepauzeerd volgens het expliciete protocol. Geen automatische reset bestaat; geen
verwerkingsfout in de drie verliezen gevonden. Sizing op cash versus controle op
min(200,cash) is apart als aandachtspunt beschreven, zonder logica te wijzigen.
Offline analyzer classificeert per baseline alle 103.395 opgeslagen coinbeoordelingen,
ook HOLD. aligned_trend: 3 uitgevoerd, 4 bij fill geweigerd, 1.946 geblokkeerde
kandidaten, 101.442 overige momenten. EMA: 5/2/39.765/63.623.
420 tests geslaagd (402 behouden + 18). Oude datasetdatabase en alle ontwikkel-
resultaten byte-identiek. Diagnose 64,870 s / 44,660 MiB binnen 300 s / 1 GiB.
Nieuwe historische stijgings-/dalings-/netto-/alternatieve-coinlabels niet berekend:
meetregistratie ontbreekt; expliciete gebruikersstopregel toegepast. Voorstel
PHASE6C_MEASUREMENT_PROPOSAL.md wacht op bevestiging. Geen backtest, wijziging van
strategie/risico, validatie- of testinzage. Zie PHASE6C_DIAGNOSTICS_REPORT.md.

## Fase 6D — vooraf geregistreerde vieruursprijsdiagnose

Expliciete gebruikersgoedkeuring verwerkt in protocol en content-addressed manifest,
naar main gepusht in 0ba9995 vóór historische labels. Alleen 2024, drie EUR-paren;
0,001 coin vaste prijsunit, bestaande FillCosts en tick. Alle 103.344 vensters
volledig; 101.391 oorspronkelijke HOLDs: 52.483 positief, 48.829 negatief, 79 neutraal;
30.721 netto positief na vaste kosten. UTC4h-steekproef 6.459 coinvensters; per coin
niet-overlappend, tussen coins afhankelijk. Geen optelling van hypothetische P&L.
793 expliciete pauzeafwijzingen: 384 later positief, 409 negatief, 247 netto positieve
units; geen uitvoerbare gemiste winsten. Score-audit bevestigt 60.924 momenten met
een andere hogere bekende score, zonder toekomstige winnaarselectie.
Bestaande zeven orderketens hergebruikt (drie fills/vier weigeringen), geen nieuwe
HOLD-ordersimulatie, risicogoedkeuring of portefeuillebacktest. Prijslabels zijn
geen tradetoestemming. Oude database/resultaten/audits en risicoregels ongewijzigd.
432 tests geslaagd (420 behouden + 12), één bestaande waarschuwing. Hoofdrun
75,503 s, 72,887 MiB RSS, binnen 600 s/1 GiB. Zie PHASE6D_MISSED_OPPORTUNITIES_REPORT.md
en experiments/phase6d/. Validatie en onafhankelijke test gesloten; stop na fase 6D.

## Fase 6E — protocolvoorstel; nieuwe patroonvergelijkingen geblokkeerd

Basis 2a7efeda. Bestaande registratie dekt nieuwe RSI-/volume-/timeframefeatures,
pauzegroepen, EMA-selectiecontrasten en multipliciteitscorrectie niet. Expliciete
gebruikersstopregel toegepast vóór nieuwe historische uitkomstvergelijkingen.
PHASE6E_ANALYSIS_PROTOCOL_PROPOSAL.md legt het afzonderlijke ontwerp vast:
27 causale features, 332 contrasten, gezamenlijke UTC4h-tijdsblokken, bootstrap/Holm,
vaste ontbrekendheids- en minimumdekkingsregels. Voorstel, niet geactiveerd.
PHASE6E_PATTERN_RESEARCH_REPORT.md herhaalt alleen eerder gepubliceerde cijfers;
PHASE6E_HYPOTHESES.md bevat vijf toetsbare voorstellen zonder optimalisatie.
103.344 bestaande labels brongebonden, niet opnieuw berekend/gegroepeerd.
Geen nieuwe pauze-/EMA-patroonuitkomsten, backtest of optimizerpromotie.
456 tests geslaagd, 0 mislukt (432 behouden +24), één bestaande waarschuwing.
Oude resultaten, auditdatabase en risicoregels behouden; integriteitsbewijs onder
experiments/phase6e/. 2025/2026 gesloten. Wacht op expliciete protocolgoedkeuring.
