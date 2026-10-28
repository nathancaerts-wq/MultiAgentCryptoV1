# Fase 6B — geheugenbegrensde streamingrunner

Basiscommit: 626b8b511aa373f5721a6e87045f22c5844569c7. De werkmap was schoon bij
start. Alleen synthetische fixtures gebruikt. Geen historische rendementen,
jaarprobe, echte transacties, API-sleutels of onafhankelijke testdata.

## Uitkomst

Er is een afzonderlijke `StreamingFixtureRunner` binnen de bestaande gezamenlijke
onderzoeksarchitectuur. De bestaande Decision/Entry/Exit-methoden, deterministische
ranking, Risk Engine, fillsimulator en Decimal-rekenregels worden hergebruikt.
De oorspronkelijke runner en productieconfiguraties zijn niet gewijzigd.

De volledige analyseketen wordt per tijdstip voorbereid en op schijf opgeslagen;
de replay leest uitsluitend het actuele rapport en de benodigde candles. De ledger
bewaart historie één keer, met compacte checkpoints. Een portefeuille wordt tussen
blokken of herstarts niet opnieuw op €200 gezet.

## Oorspronkelijke geheugengroei

De vorige runner hield alle uitvoeringscandles, rapportobjecten, rapportindexen en
bundelkopieën vast. De meet-harness gebruikte bovendien SQLite `:memory:` voor alle
marktdata, analyses, orchestratorresultaten en audits. Iedere ledgerrevisie bevatte
opnieuw de volledige event-/trade-/orderhistorie. Alleen `joint_states` groeide van
44,3 MB bij 500 naar 175,3 MB bij 1.000 stappen. Dit was kwadratische opslaggroei.

Indicatorberekeningen zelf gebruiken al 32 afgesloten candles per timeframe en
begrensde caches. Orchestrators leven per tijdstip; hun berichten hoeven na opslag
niet voor de rest van de simulatie in RAM te blijven.

## Nieuwe opslag en verwerking

`crypto/streaming.py` voegt drie onderdelen toe:

- `StreamingStore`: bestandsgebonden SQLite met WAL, synchronous=FULL, 8 MiB
  paginacache, mmap uit en tijdelijke sorteerbestanden op schijf. De gebruiker
  kiest een echte schijflocatie; `:memory:` wordt geweigerd.
- `StreamingFixtureRunner`: gezamenlijke chronologische replay met dezelfde
  financiële methoden als `FixtureJointRunner`. `stream(times)` geeft één snapshot
  tegelijk terug. `run(times)` accepteert maximaal 100 stappen, zodat die
  compatibiliteitsroute niet ongemerkt alle snapshots in een lijst verzamelt.
- `DiskList`/`DiskIds`: onveranderbare opgeslagen historie plus een klein lokaal
  buffer voor de huidige transactie. Membership van order-ID's gaat via een index;
  audit- en tradehistorie worden met cursors gelezen, zonder volledige lijsten.

De workflow heeft twee doorgangen, zodat het bestaande protocol de volledige
rapporthash vóór de eerste beslissing kan blijven vastleggen:

1. Voeg fixturecandles in kleine blokken toe. `prepare_research(engine, at, coins)`
   voert de bestaande analyseketen uit en slaat één tijdstip atomair op, inclusief
   datasetimports, agentresultaten, audit en rapporten. Geneste transacties worden
   savepoints. Een fout laat geen half voorbereid tijdstip achter. Hervat de
   voorbereiding bij het eerstvolgende nog niet opgeslagen tijdstip; duplicaten
   worden expliciet geweigerd.
2. `seal()` berekent de volledige daadwerkelijke inhoudshash en dezelfde bestaande
   gesorteerde rapportbundelhash. SQLite-triggers weigeren daarna inserts, updates
   en deletes van input. Bij heropening wordt de hele invoer opnieuw met cursors
   gehasht. Het manifest bindt configuratie, filters, plan, bars en inputhash.
3. Bouw de runner met hetzelfde plan, beleid en filters. Consumeer `stream(times)`
   zonder de snapshots zelf in een onbegrensde lijst te bewaren.

In RAM blijven de financiële scalars, maximaal één positie, één reservering en
kleine actuele rapporten. Bestaande candle-/featurecaches blijven maximaal 128
entries. De toelatingscontrole leest uitsluitend de voorafgaande zeven dagen:
maximaal 672 kwartiercandles en 168 uurcandles per beoordeelde coin. Geen doorlopende
EMA of gewijzigde warm-upformule is ingevoerd. De nieuwe opslag gebruikt een apart
versienummer `stream-v1`; bestaande onderzoeksdatabases worden niet gemigreerd of
overschreven. Historische bronnen en gesloten perioden blijven geweigerd.

## Checkpoints, integriteit en hervatting

Een checkpoint bevat cash, gerealiseerd resultaat, kosten, volledige open positie,
waardering, actieve instrumentregels, pending order/reservering, laatst verwerkt
tijdstip, dagbaseline, peak equity, drawdown, alle pauzevlaggen en centrale noodstop.
Het verwijst met precieze prefixlengten naar events, trades, curve en order-ID's.
De verliesreeks wordt zoals voorheen uit de persistente trades beoordeeld.

Iedere checkpoint bevat zowel de **oude logische statehash** als een extra hashketen
voor de compacte fysieke opslag. Een streaming JSON-hasher gebruikt exact dezelfde
canonicalisatie als de oude runner, zonder de histories in RAM te materialiseren.
Daardoor blijven ook de bestaande `joint_*`-auditdetails en statehashes gelijk.
Het opslagmanifest verschilt expliciet wegens het nieuwe formaat; dit is geen
andere strategie of gewijzigde orderbeslissing.

Historie is append-only met aaneengesloten indices. Nieuwe events worden vóór
opslag op hun bestaande hashketen gecontroleerd. Bij heropening worden de volledige
eventketen, compacte checkpointketen, prefixlengten en laatste logische statehash
gecontroleerd. Normale reads controleren checkpointinhoud en financiële
reconciliatie; zij vertrouwen uitsluitend de eerder geverifieerde, door triggers
tegen mutatie beschermde prefix. Een beheerder die code/triggers en alle hashes
herschrijft valt, net als eerder, buiten deze lokale integriteitsgrens.

De bestaande BEGIN IMMEDIATE-transactie bevat reservering, hercontrole, fill,
settlement, historie, checkpoint en audit. Concurrent gewijzigde revisies worden
via de bestaande `_compare` geweigerd. Eén sequentiële aanroeper per verbinding;
geen nieuw parallel-schrijfcontract. Bij fout/crash rolt de hele transactie terug.
Herhaal na herstart het laatste tijdstip: een pending reservering wordt afgehandeld;
een reeds uitgevoerde batch/fill wordt herkend en niet opnieuw uitgevoerd. Ga daarna
met kwartierstappen verder. Er is geen cash-, positie- of risicopauzereset per blok.

## Functionele gelijkheid en hersteltests

Oude en nieuwe runner zijn vergeleken op volledige logische states, gevalideerde
berichten, kandidaatselectie, afwijsredenen, fills/settlements, kosten, cash,
portefeuillewaarde en persistente audit. Er worden geen financiële velden afgerond
of weggefilterd. Alleen audit- en import-wallclocks zijn in beide testvarianten op
dezelfde vaste waarde gezet.

De fixtures omvatten geen trades, een aankoop, stop-loss, drie opeenvolgende
verliestrades, verliesreekspauze, dagverlies, drawdown, noodstop, dubbele batches en
fills, open positie/pending entry/pending exit op blokgrenzen, datagaten en herstart.
Een afzonderlijke vergelijking voert de volledige scanner-/analyseketen uit en
vergelijkt ook analyses, regimes, datasetinhoud en scanneroutput exact.

Een subprocess wordt daadwerkelijk met `os._exit(77)` beëindigd nadat fill,
historie en checkpoint binnen de transactie zijn geschreven maar vóór commit.
Heropening vindt de vorige reservering terug, geen gedeeltelijke fill; opnieuw
uitvoeren geeft precies één fill. Een tweede foutinjectie controleert rollback
zonder procesherstart. Gewijzigde input en corrupte oude checkpoints worden
geweigerd. Een 150-stappenfixture controleert compacte stategrootte, één opgeslagen
event per gebeurtenis en reconstructie zonder geheugenhistorie.

## Meetopzet en resultaten

De definitieve metingen staan in `experiments/streaming/`; de harness is
`scripts/measure_streaming.py`. Drie synthetische coins, dezelfde candleformule en
analyse-/strategieparameters als eerder, cProfile en `resource.ru_maxrss`. GC-
objecttellingen meten Candle-/Message-objecten en algemene Python-objectgroei.
Deze telling omvat niet alle native SQLite-allocaties; RSS omvat die wel. RSS is
procesgeheugen, geen totale machine-RAM-meting of geheugengarantie voor alle workloads.

Harde subprocesslimiet: 1,5 GiB address space. Vroegtijdige stop boven 1,2 GiB RSS.
500/1.000/2.000 stappen krijgen maximaal 180 seconden. Een eventuele 5.000-run
heeft vooraf expliciet 360 seconden; dit is geen verhoging of geslaagde invulling
van het bestaande 45-secondenjaarcriterium. De grote prestatiefixtures hebben
geen volledige toelatingshistorie en daardoor nul trades. Actieve posities en
pauzes zijn via de afzonderlijke exacte fixtures getest; de prestatiecijfers
bewijzen niet de snelheid van duizenden actieve transacties.

De eerste verkennende metingen gebruikten `/tmp`. Dit bleek tmpfs: databasebestanden
gebruikten machine-RAM buiten de proces-RSS. Die cijfers zijn daarom **uitgesloten**
van de definitieve vergelijking; de eerste 5.000-run is expliciet afgebroken.
Ze blijven herkenbaar bewaard in `excluded_tmpfs/`, niet als geslaagde schijfproeven.
De definitieve database én SQLite-sorteerbestanden staan op `/workspace` (overlay,
geen tmpfs). Kernelbestandscache is terugvorderbaar en valt buiten proces-RSS.
De tussenmeting `before_preparation_batch/` toont de extra fsync-kosten vóór de
atomische opslag van één analysetijdstip; ook die is niet de definitieve variant.

| Stappen | Totaal s | Gemiddeld s/stap | Eerste 100 replay s | Laatste 100 replay s | Piek-RSS MiB |
|---:|---:|---:|---:|---:|---:|
|500|25.067|0.05013|2.047|2.050|59.0|
|1000|52.620|0.05262|2.064|2.268|60.6|
|2000|112.010|0.05601|2.019|2.407|64.0|
|5000|291.499|0.05830|1.920|3.178|74.4|

Alle vier definitieve metingen hebben status `complete`, reconciliatie geslaagd,
één gezamenlijke portefeuille en nul trades. De broncodehashes van runner en
meet-harness stemmen nog exact overeen met alle vier meetbestanden. De 5.000-run
was bij hervatting al afgerond; er is geen nieuwe prestatiemeting gestart.

Ter vergelijking: de vorige schaalbaarheidsfase mat 500 stappen in 25,630 s bij
328,2 MiB en 1.000 stappen in 57,100 s bij 685,2 MiB. Dit zijn eerdere metingen,
geen gelijktijdige herhaalmetingen op een exclusieve host. De nieuwe route gebruikt
schijfopslag en duurzame commits; de oude gebruikte een in-memorydatabase.

Bij 5.000 stappen blijven 4.096 Candle-objecten in de bestaande begrensde caches;
na voltooiing zijn er nul blijvend vastgehouden Message-objecten. Het totale aantal
GC-zichtbare objecten eindigt rond 40.900 voor alle meetlengten. Tijdens de async/
profilerfase groeit die telling tijdelijk (tot circa 101.000 bij de laatste
replaysample); dit is geen bewijs dat iedere native allocatie strikt constant is.
De gemeten RSS neemt van 59,0 MiB bij 500 naar 74,4 MiB bij 5.000 toe. Een harde
geheugengarantie voor willekeurige actieve workloads of een volledig jaar is hiermee
niet aangetoond.

Compacte checkpoints en afzonderlijke historie vervangen de herhaalde complete
ledgerpayloads. De eerste/laatste 100 replaystappen bij 5.000 groeien nog van
1,920 naar 3,178 seconden: het herhaald lezen van de volledige auditgeschiedenis
voor logische statehashes blijft de expliciete resterende bottleneck.

## Verificatie bij hervatting — 28 oktober 2026

Geen meetproces aangetroffen. Alle bestaande wijzigingen en meetresultaten bewaard,
inclusief uitgesloten tmpfs-verkenningen en tussentijdse meetvarianten. Geen nieuwe
jaarprobe of historische rendementsevaluatie uitgevoerd. Functionele verificatie:
**377 tests geslaagd, 0 mislukt** (353 bestaande plus 24 nieuwe), één bestaande
Starlette/AnyIO-deprecationwaarschuwing. Exacte financiële gelijkheid, crashherstel,
deduplicatie, risicopauzes, audit en gezamenlijke portefeuille zijn opnieuw getest.
Jaarcapaciteit en het oorspronkelijke 45-secondenjaarcriterium blijven onbewezen.


## Resterende beperkingen

Het RAM en de ledgeropslag zijn begrensd respectievelijk lineair in de gemeten
scenario's, maar de uitvoering is niet overal lineair: behoud van de oude logische
statehash vereist opnieuw lezen/hashen van de eventprefix bij iedere nieuwe state.
Trade-/kostenreconciliatie en waardering lezen trades met cursors. Dat kost geen
onbegrensd RAM, maar kan bij veel trades nog kwadratische totale tijd geven.

Volledige agentberichten, datasets en audits blijven op schijf groeien; er worden
geen gegevens weggegooid. De nieuwe route gebruikt een afzonderlijke technische
opslaginterface; bestaande API-/historische runners worden niet stilzwijgend naar
het nieuwe stateformaat omgezet. Historische migratie/uitvoering, jaarcapaciteit,
stroomuitval op echte hardware en parallelle schrijvers zijn niet door deze
meting bewezen. Een procescrash is wél getest.

Geen jaarprobe of historische rendementsbacktest gestart. Geen vrijgave van de
onafhankelijke testperiode of automatische vervolgfase.
