# Fase 6B — gerichte ledger-, rapport- en cacheoptimalisatie

27 oktober 2026. Basiscommit c680510057bef3f2cdc320c27c3075eadf4826e9.
De bestaande lokale oorzaakanalyse en meetbestanden zijn behouden. Er zijn geen
historische rendementsbacktests, externe orders, API-sleutels of onafhankelijke
testdata gebruikt. Geen strategie-, indicator-, risico- of onderzoeksperioden gewijzigd.

## Resultaat

De gemeten kopieer-, bundelhash- en dataset-lookupkosten zijn verminderd. Alle
financiële gelijkheids- en veiligheidstests slagen. Bij 1.000 synthetische stappen
kost de lege replay 33,740 s tegenover 123,162 s met de checkpointcode in dezelfde
huidige omgeving. De analyseketen voltooit 1.000 stappen in 76,711 s.

**Geen synthetische jaarprobe gestart.** De stapkosten groeien nog door volledige
ledger-serialisatie en eventvalidatie. De kleinere metingen geven nog onvoldoende
bewijs voor betrouwbare jaarverwerking binnen het bestaande 45-secondencriterium.
Dat criterium is niet verhoogd. Het niet vrijgeven van een jaarprobe is hier een
voorafgaande veiligheidsbeslissing, geen verborgen mislukte jaaruitvoering.

## Referenties vóór wijziging

scripts/ledger_fix_reference.py is vóór de runtimewijzigingen uitgevoerd. De
volledige referentie is opgeslagen in experiments/ledger_optimization/reference_before.json.
Scenario's: normale entry/exit, muntwissel en opeenvolgende transacties/stop,
noodstop, herhaalde signalen/uitvoering, reconstructie, fout na gedeeltelijke
transactieverwerking en orderfilterafwijzing zonder transactie.

Na wijziging zijn alle joint_states, joint_batches, joint_settlements, results én
persistente auditregels exact vergeleken: gelijk. Alleen de audit-wallclock is in
beide runs op dezelfde vaste waarde gezet; er zijn geen financiële velden afgerond
of weggefilterd. Dit vergelijkt voorstellen, BUY/HOLD/exitberichten, quantities,
fillprijzen, kosten/slippage, statehashes, portefeuilles en afwijzingen.

Aanvullend zijn de bestaande dagverlies-, drawdown- en verliesreeksfixtures uitgevoerd
tegen een geïsoleerde git-archive van de oorspronkelijke checkpointcode en tegen
de nieuwe code. Ook hun volledige economische inhoud/audit is gelijk. De oude code
is uit de vastgelegde commit gehaald, niet achteraf gereconstrueerd uit aannames.
Deze fixture-orderfilters zijn synthetische testinstellingen, geen gewijzigde
productieregels of historisch geverifieerde Binance-filters.

## Aangepaste modules en veiligheid

### Ledger en transacties

- crypto/sim_execution.py: analysis_view maakt een kleine, geïsoleerde kopie van
  financiële toestand en configuratie. De oorspronkelijke events/trades/curve/ids
  worden niet aan agents gekopieerd. Het viewtype kan geen buy/sell/process_bar
  uitvoeren. Hypothetische observe-events blijven lokaal en worden niet opgeslagen.
- crypto/trade_agents.py: Entry en Exit gebruiken deze beperkte analyseview.
  Alle gebruikte financiële velden, size-, price-, stop- en risicoberekeningen zijn
  dezelfde. De echte ledger en haar volledige auditgeschiedenis blijven behouden.
- crypto/research_execution.py: alleen de tijdelijke risicopreview gebruikt de
  analyseview. De verliesreeks wordt nog uit de echte tradehistorie beoordeeld.
  De echte fillsimulatie wordt niet vervangen door een analyseview.
- crypto/joint_portfolio.py: statevelden worden gericht/shallow gekopieerd in plaats
  van de oude volledige ledgerpayload meermaals te deep-copyen. _save vervangt de
  ledgerpayload door een nieuwe ledger_state-serialisatie. De lokale Risk-view wisselt
  alleen de instrumentregels; zij deelt uitsluitend gelezen historie.

De architectuur leest een nieuwe lokale ledger uit SQLite vóór werkelijke uitvoering.
BEGIN IMMEDIATE, revisievergelijking, fills, settlement, state, reserveringsvrijgave
 en persistente audit blijven binnen dezelfde bestaande transactie. Er is geen
extra globale mutable execution-ledger ingevoerd. Een fout rolt de database terug;
de lokale onvoltooide ledger wordt weggegooid. De prefixcache bevat raw strings,
geen alias naar die veranderde lokale ledger. Dit is gecontroleerd met storingen
bij settlement én stateopslag en met heropening/reconstructie.

De volledige persistente historie is behouden. Alleen de niet-persistente,
hypothetische audit binnen een analysepreview wordt niet uit de echte historie
gekopieerd. Zij was ook vóór deze wijziging geen onderdeel van de uitvoeringsaudit.
Exacte persistente auditgelijkheid is afzonderlijk bewezen.

### Rapportbundel

crypto/tracked_payload.py voegt versiehoudende JSON-containers toe voor geneste
rapportdata. Normale dict-/listmutaties verhogen de bundelversie, inclusief slices,
update, setdefault, append/extend, sort, reverse en in-place operators. Nieuwe
containers worden recursief aan dezelfde versie gekoppeld. Diepe agentkopieën
zijn gewone onafhankelijke data en kunnen de originele versie niet beïnvloeden.

JointPortfolio._report_digest hergebruikt een hash uitsluitend zolang dezelfde
bundel en versie gelden. Bij vervanging of geneste mutatie wordt opnieuw gehasht
en blijft de bestaande manifestvergelijking gelden. Voor onbekende mutable
objecttypen (bijvoorbeeld sets) wordt caching uitgeschakeld: iedere controle
berekent de inhoud opnieuw. Er is geen aanname dat een bestand ongewijzigd is.

De containers vormen geen sandbox tegen code die bewust via dict.__setitem__,
object.__setattr__ of andere interne omwegen de normale mutatie-API omzeilt.
Zoals de bestaande Python-/SQLite-architectuur is dit bescherming tegen normale
mutaties en inconsistenties, niet tegen een beheerder die code en controles wijzigt.
Een verdere externe trust boundary zou een apart immutable berichtcontract vereisen.

### Dataset-cache

crypto/storage.py voegt get(table,key) toe met de bestaande tabelwhitelist en een
geparametriseerde query via de primaire id-index. crypto/data.py gebruikt die
puntlookup. Per hit wordt één actuele SQLite-payload gedecodeerd; er is geen nieuwe
in-memory datasetcache die buiten de database kan verouderen. Candle-/UTC-/duur-/
volledigheids-/as_of-controles lopen door. Gewijzigde database-inhoud wordt opnieuw
gelezen en gevalideerd. Bronfileverversing volgt de bestaande importidentiteit;
er is geen nieuwe impliciete refresh/revisie van eerder geïmporteerde data toegevoegd.

## Metingen en vergelijkbaarheid

De bestaande oorspronkelijke meting bevatte 58,120 s voor 200 lege stappen en
35,577 s cumulatief deepcopy. In deze omgeving is naast de nieuwe code ook de
checkpointversie opnieuw gemeten. Dat voorkomt dat de sterk gewijzigde hostbelasting
als volledig optimalisatie-effect wordt gepresenteerd. Een git-archive van de
checkpointcode draaide geïsoleerd met dezelfde meet-harness en interpreter.

Alle cijfers hieronder zijn cProfile-metingen, inclusief fase-initialisatie en
beperkte diagnostische snapshots. De harde limiet per aanroep was 180 seconden,
maximaal 1.000 stappen, geen jaar. Fases voor analyse en replay zijn afzonderlijk
opgeslagen. RSS is de gemeten procespiek in KiB; deze is geen incrementele allocatie.
Runs zijn niet op exclusieve hardware gedaan; observaties zijn geen statistische
snelheidsgarantie. Alle ruwe profielen, tijden en callcounts blijven bewaard.

| Workload | Stappen | Checkpoint s | Nieuw s | Checkpoint piek KiB | Nieuw piek KiB |
|---|---:|---:|---:|---:|---:|
|empty|50|0.612|0.344|38432|38772|
|empty|100|1.881|0.834|41364|41404|
|empty|200|5.846|2.643|49868|49964|
|empty|1000|123.162|33.740|256108|252936|
|chain|50|9.174|2.342|58324|60652|
|chain|100|niet opnieuw gemeten|5.154|niet opnieuw gemeten|85484|
|chain|200|niet opnieuw gemeten|10.103|niet opnieuw gemeten|142864|
|chain|1000|niet opnieuw gemeten|76.711|niet opnieuw gemeten|689816|

Empty = geen analyserapporten; chain = analyse-opbouw plus replay. Er is geen
extra oude chain-100/200/1000-run gedaan: de oorspronkelijke begrensde diagnose
was daar al onvolledig. De nieuwe chain-runs zijn wel allemaal voltooid. De
synthetische gemeten chain heeft geen volledige toelatingshistorie voor uitvoerbare
entries; zij meet geen actieve tradingketen over 1.000 stappen. Actieve fills,
stops en risicopauzes zijn via de afzonderlijke exacte referenties getest.

| Nieuwe replay | Stappen | Gem. eerste 10 s | Gem. laatste 10 s |
|---|---:|---:|---:|
|empty|50|0.00559|0.00737|
|empty|100|0.00589|0.01072|
|empty|200|0.00584|0.02325|
|empty|1000|0.00666|0.05490|
|chain|50|0.01202|0.01405|
|chain|100|0.01235|0.01687|
|chain|200|0.01174|0.02176|
|chain|1000|0.01352|0.06727|

De kosten per stap zijn verminderd, maar niet stabiel: bij 1.000 stappen groeit de
lege replay van circa 0,0067 naar 0,0549 s en de chain-replay van circa 0,0135 naar
0,0673 s voor de eerste/laatste tien stappen. Geheugen blijft groeien doordat de
bestaande stateopslag de volledige ledgerhistorie per revisie bevat. Die indeling
is voor deze ingreep bewust niet vervangen door een nieuw opslagformaat.

## Resterende bottlenecks en jaarprobe

- Volledige ledger_state-JSON en actuele ledger-eventvalidatie blijven O(n)-werk
  per stap en kunnen dus nog O(n²) totaalkosten opleveren.
- De bestaande SQLite-statehistorie bewaart complete payloads per revisie.
  Een genormaliseerd append-only event-/tradearchief met gecontroleerde checkpoints
  is nog niet gebouwd. Auditverificatie is niet uitgezet om sneller te lijken.
- FixtureJointRunner._manifest serialiseert aangeleverde history nog opnieuw.
  De performancecases leveren geen volledige zeven-dagenhistory aan. Schaalbaarheid
  van een volledig gevuld historisch universum wordt daarom niet geclaimd.
- Alle rapporten worden vooraf gebonden; deze ingreep verandert dat niet in streaming.
- De 1.000-stappenketen kost 76,711 s en laat groeiende stapkosten zien. Daarom zijn
  de kleinere tests nog onvoldoende basis voor een jaarprobe. **Niet uitgevoerd**.
  Geen verhoging van de bestaande 45-secondenjaarvoorwaarde en geen historische vrijgave.

## Tests en oplevering

**340 tests geslaagd, 0 mislukt**: alle 324 bestaande plus zestien gerichte tests.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. De golden tests voeren de
actuele code opnieuw uit en vergelijken tegen de volledige referentie vóór wijziging,
inclusief persistente audit; zij vergelijken niet alleen twee opgeslagen labels.

Nieuwe dekking: kleine geïsoleerde analyseviews zonder fillbevoegdheid, nested
mutatieversies, cachefallback voor onbekende mutables, eenpunt-datasetlookup,
actualisatie bij databasewijziging, mid-transaction rollback en herstart,
volledige scenario-/risicopauzegelijkheid. Bestaande tests behouden de lange
synthetische invoer, gaps, chronologie, negatieve cash, auditcorruptie en risicolimieten.

Er is geen essentiële financiële of correctheidscontrole mislukt in de definitieve
suite. De conditionele jaarprobe is op grond van de metingen niet vrijgegeven;
resterende schaalbaarheidsbeperkingen zijn geen geslaagde jaarcontrole. checks.json
legt de referentiegelijkheid en bestandshashes vast als beschrijfbare snapshot,
zonder claim van onveranderlijke opslag. PROGRESS.md en NEXT_STEPS.md zijn bijgewerkt.
