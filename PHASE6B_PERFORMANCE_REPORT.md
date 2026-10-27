# Fase 6B — technische performance-optimalisatie

Basis d46f2f9d09be873e7df5f44ee62bae560fbe9587; uitsluitend synthetische gegevens.
Geen historische backtests, nieuwe marktdata, transacties buiten fixtures of
onafhankelijke testtoegang. De 45-secondenvoorwaarde is niet verhoogd.

## Metingen en grenzen

scripts/profile_replay.py gebruikt cProfile, perf_counter, een tijdsbegroting van
30 seconden per profiel en resource.ru_maxrss. Dit is een profielbudget, geen
vervanging van de bestaande 45-secondenjaarcontrole. 1.000, 10.000 en 35.136
candles per munt, telkens BTC/EUR, ETH/EUR en SOL/EUR. Alle functies blijven in de
ruwe .prof-bestanden; JSON bevat cumulatieve en eigen functietijden. Cumulatieve
tijden overlappen en mogen niet als afzonderlijke kosten worden opgeteld.

De capaciteitsscreening bevat geen volledige analyserapporten en blijft daardoor
een ondergrens. Niet uitgevoerde componenten zijn niet als gratis/verwerkt aangemerkt.
De afzonderlijke scripts/performance_equivalence.py voert wél de analyse-, agent-,
Risk-, fill- en ledgerketen uit met bestaande deterministische fixtures. Profielen
van deze drie scenario's staan in components_before/after.json. Zij meten geen
volledige analyseketen voor 10.000 of een jaar candles; dat blijft onbewezen.

De gedeelde cloudomgeving had wisselende CPU-belasting; enkele profielen en tests
liepen gelijktijdig. Daarom geen gecontroleerde speedupclaim of lineaire extrapolatie
uit deze wandtijden. Instrumentatie kost zelf tijd. De signal-tijdslimiet wordt in
Python afgehandeld en kan enige afhandelings-/profielschrijftijd overschrijden.

## Aantoonbaar knelpunt en wijziging

Bij de 1.000-candlebaseline kostte _read cumulatief circa 17,69 seconden binnen
het 30-secondenprofiel. De volledige joint_states-historie werd bij iedere read,
vergelijking en snapshot opnieuw opgehaald, gedecodeerd en gehasht. Naarmate de
historie groeit veroorzaakt dit herhaald werk boven op groeiende ledgerkopieën.

Alleen dit gemeten knelpunt is aangepast:

- Expressie-index op het portfolio-ID in joint_states.
- Incrementele verificatie van nieuwe records boven een reeds geverifieerde prefix.
- SQLite-epochtriggers bij UPDATE, DELETE en inserts vóór bestaande rowids dwingen
  een volledige hercontrole af. Dit geldt ook voor andere verbindingen.
- De opgeslagen anchorpayload wordt steeds met de database vergeleken; rollback,
  verdwenen anchors of hergebruikte rowids kunnen niet stilzwijgend een oude prefix
  geldig maken. Bij heropening is er geen prefix en vindt volledige controle plaats.
- Financiële reconciliatie, huidige ledger-auditketen, risicocontroles en manifest-
  vergelijking worden nog uitgevoerd. Decimal-precisie en alle regels blijven gelijk.

De cache bevat uitsluitend reeds gevalideerde opslaghistorie, geen indicatoren of
marktfeatures. Daardoor wordt geen toekomstige candle ontsloten. Een nieuwe test
vond tijdens ontwikkeling dat een negatieve rowid bij volledige fallback werd
overgeslagen. Dit is gecorrigeerd: volledige fallback gebruikt geen rowid-ondergrens.
De bijbehorende regressietest moet slagen. Dit is geen beveiliging tegen een beheerder
die code/triggers en database gezamenlijk wijzigt.

## Functionele gelijkheid

Voor en na zijn drie identieke fixtureworkflows doorlopen: normale entry/exit,
muntwissel en noodstop. Vergelijking van alle inhoud van results, joint_batches,
joint_settlements en joint_states is exact gelijk (equivalence.json). Dit omvat
beslissingen, afwijzingen, kosten, fills, audit-hashes en portefeuillewaarderingen.
Wallclock-auditregels en viewed_at-exposurevelden zijn niet in die gelijkheidsclaim
opgenomen; zij zijn per uitvoering verschillend. Geen afgeronde floatvergelijking
van financiële cijfers: vergelijking van de volledige JSON/Decimalrepresentatie.

Nieuwe tests vergelijken bovendien geoptimaliseerde uitvoering met uitgeschakelde
prefixcache en controleren updates, deletes, inserts vóór de prefix, rollback,
andere verbindingen, lange invoer en vervanging van candlebundels. De 317 bestaande
tests behouden dekking voor gaps, toekomstinformatie en risicobeveiligingen.

## Jaarcontrole en resterende beperkingen

De bestaande echte drie-muntenjaarprobe is opnieuw uitgevoerd, met dezelfde
45-seconden-/1,5-GB-begrenzing. Uitkomst: **niet voltooid**. Laatste checkpoint:
201 verwerkte tijdstappen (603 coin-candles), circa 32,81 seconden, piek-RSS tot
checkpoint 429.196 KiB. Na 45 seconden is de subprocess gestopt. Voortgang en
geheugenpiek ná het laatste checkpoint zijn onbekend. Geen 35.136 stappen voltooid;
geen complete jaarsom trades of sluitende eindjaarledger beschikbaar. De beoogde
invoer was 105.408 coin-candles. Zonder rapporten ontstaan geen koopvoorstellen;
dat is geen bewijs van een echte full-agent-jaarsimulatie met nul transacties.
De oorspronkelijke checkpointproef stond op building_candles, zonder verwerkte
batches. Hostbelasting en checkpointgranulariteit verhinderen een eerlijke numerieke
snelheidsverhouding met die oorspronkelijke timeout.

Het probleem is gedeeltelijk verminderd, **niet opgelost**. Volledige ledgers,
curves en events worden nog gekopieerd, geserialiseerd en per revisie opgeslagen;
Entry/Exit-agentkopieën groeien mee. Een incrementele verificatieprefix verwijdert
die kosten niet. Een veilige wijziging van de ledger-/eventopslag met herstart- en
integriteitsbewijs is nodig voor de volgende stap. Er wordt niet beweerd dat een
iets langere runtime de jaarcontrole betrouwbaar zou laten slagen.

Geen indicatorcache toegevoegd zonder voldoende profielbewijs; de indicatorformules,
scanner, agentregels, kosten, onderzoeksperioden, risicolimieten en historische
uitvoeringsblokkades zijn behouden. De bestaande manifesten zijn historische
hashsnapshots; gewijzigde code heeft voor een eventuele toekomstige uitvoering
een nieuw manifest nodig. Er is in deze opdracht geen historische vrijgave.

## Begrensde cProfile-uitkomsten

| Variant | Candles/munt | Status | Stappen | Wandtijd s | Piek-RSS KiB | Laatste fase |
|---|---:|---|---:|---:|---:|---|
|before|1000|timeout|48|30.24|41776|replay|
|before|10000|timeout|27|30.24|142092|replay|
|before|35136|timeout|0|30.25|330068|initialization|
|after|1000|timeout|127|30.20|46152|replay|
|after|10000|timeout|0|30.11|60296|data_input|
|after|35136|timeout|0|30.33|257008|initialization|

Data-invoertijden per afgeronde fase en topfuncties staan in de afzonderlijke JSONs.
De tragere after-invoer bij grotere corpora toont waarom deze metingen niet als
een vaste algemene speedup mogen worden gepresenteerd.

## Componentprofielen van de volledige kleine fixtureketen

| Component / bestand | Voor cumulatief s | Na cumulatief s |
|---|---:|---:|
|Indicatoren|0.122333|0.049097|
|Coin Scanner|0.400158|0.173543|
|Market Regime|0.043344|0.011038|
|Technical Analysis|0.060678|0.013048|
|Multi-Timeframe|0.034866|0.031538|
|Orchestrator|8.387765|6.844238|
|Decision|1.101483|1.445596|
|Entry|1.136137|1.120521|
|Exit|0.278703|0.116246|
|Risk Engine|0.006691|0.011225|
|Fillsimulator buy|0.001178|0.034118|
|Fillsimulator sell|0.008569|0.014099|
|Ledger snapshot|0.116764|0.101032|
|SQLite put|1.538992|0.000000|

Alle functietijden en callcounts blijven beschikbaar voor controle; timings zijn
fixturemetingen, geen jaarmetingen. Allocations_input.json bevat een afzonderlijke
tracemalloc-snapshot voor 3.000 synthetische candles, inclusief allocatielocaties.
Dit is geen geheugenprofiel van de volledige replay.

## Eindverificatie en Git

Definitieve volledige suite: **324 geslaagd, 0 mislukt** (317 bestaande plus zeven
nieuwe), één bestaande Starlette/AnyIO-deprecationwaarschuwing. De eerder gevonden
negatieve-rowid-fout is hersteld en de volledige suite is daarna opnieuw uitgevoerd.
Er zijn geen resterende functionele testfouten.

Niet alle aangevraagde prestatiecontroles slagen: volledige jaarafloop en
jaarreproduceerbaarheid met complete analyses blijven onbewezen. Daarom geen commit
of push onder de voorwaarde “als alle controles slagen”. Alle code, rapporten en
meetgegevens blijven lokaal bewaard; HEAD blijft d46f2f9d09be873e7df5f44ee62bae560fbe9587.
Geen historische backtest, externe order, parameterwijziging of volgende fase gestart.
