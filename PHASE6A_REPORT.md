# Fase 6A — gezamenlijke virtuele portefeuille

Afgerond op 26 oktober 2026, voortbouwend op
`f0da92ae7ae8383812aa30a1b4fbd10342f459a6`. De werkmap was bij aanvang schoon.
De gezamenlijke mode is een nieuwe, expliciet gekozen onderzoeksinterface.
Bestaande bots, geïsoleerde experimenten, hypotheses, resultaten, filters en
risicoconfiguraties zijn niet vervangen of stilzwijgend omgezet.

## Eén balans voor de gehele watchlist

`crypto.joint_portfolio.JointPortfolio` beheert één EUR-ledger per bevroren
ResearchPlan, met eenmaal €200 startkapitaal voor alle coins samen. Het
portefeuille-ID is aan het volledige plan gebonden. Heropening herstelt dezelfde
balans; een muntwissel maakt geen nieuwe kas. Een ander onderzoeksplan vormt een
expliciet afzonderlijk experiment en mag niet als doorlopend rendement worden opgeteld.

Dezelfde OfflineLedger blijft verantwoordelijk voor cash, bezit, gemiddelde
kostprijs, kostenbasis, fees, gerealiseerd/on-gerealiseerd resultaat en equity.
Alleen wanneer de portefeuille vlak is kunnen de instrumentfilters voor de
volgende munt worden gewisseld. Kopieën voor agentanalyse bevatten de gedeelde
balans en vormen geen extra gefinancierde rekeningen.

`snapshot()` toont cash, gereserveerde cash, vrij saldo, bezit, gereserveerde
hoeveelheid, kostenbasis, fees, gerealiseerd en ongerealiseerd resultaat,
bruto/liquidatie-equity, exposure en de historische waarderingstijd. Gerealiseerd
resultaat en kosten zijn ook per coin zichtbaar. De controles vereisen onder meer:

- cash + resterende kostenbasis = €200 + gerealiseerd resultaat;
- gerealiseerd resultaat = som van gesloten transactieresultaten;
- fees = kosten van gesloten transacties + instapfee van een open positie;
- cash en reserveringen zijn eindig en niet negatief; gereserveerd saldo ≤ cash;
- positie, filters, bezit en waardering komen overeen; audit-hashketens zijn geldig.

Een onverklaarbare balans, ontbrekende toestand of hashconflict blokkeert verwerking.
Een open positie wordt uitsluitend op bekende historische prijzen gewaardeerd.
Zonder positie wordt geen fictieve marktprijs getoond.

## Centraal risico en reserveringen

JointPolicy legt voor deze nieuwe mode vast: €200 startkapitaal, maximaal één
open positie en het bestaande phase5-v1-beslisbeleid. Deze fase ondersteunt bewust
alleen een limiet van één positie; een hogere instelling wordt geweigerd. Meerdere
EUR-paren kunnen wel kandidaat zijn en achtereenvolgens dezelfde cash gebruiken.
De instellingen van bestaande portefeuillemodes blijven ongewijzigd.

De gedeelde RiskEngine gebruikt maximaal 0,5% gepland risico per trade. Inclusief
kosten geldt maximaal 0,5% van min(€200, actuele cash), aanvankelijk maximaal €1.
De instap-exposure blijft maximaal 50%. Bij een bestaande positie wordt iedere
nieuwe instap geweigerd; er is daardoor geen gelijktijdige cross-coin-exposure
waarvoor een correlatie zou moeten worden verzonnen. Risicoverlagende exits blijven
mogelijk tijdens risicopauzes. Mark-to-market-exposure wordt getoond; er is geen
nieuw automatisch herbalanceerbeleid toegevoegd.

De bestaande 3%-dagverliesgrens, 10%-drawdowngrens, kostencontroles en
verliesreekspauze gelden voor de gezamenlijke transactiereeks. Zij worden niet
gerest wanneer een andere munt wordt gekozen. De standaard verliesreekspauze is
na drie verliestrades; vooraf strengere bestaande instellingen blijven mogelijk.
De centrale `stop()` vergrendelt nieuwe instappen duurzaam, ook voor andere
verbindingen en na heropening. Er is geen automatische vrijgave van deze noodstop.

Een succesvolle selectie reserveert de volledige verwachte aankoop plus fee,
het geplande risico, exposure en de ene beschikbare positieplaats. Cash wordt nog
niet afgeschreven. Zowel selectie als reservering worden atomair opgeslagen met
`BEGIN IMMEDIATE` en vergelijking van de gelezen portefeuillerevisie. Twee agents
of verbindingen kunnen niet dezelfde vrije ruimte afzonderlijk toewijzen.
Bij een gewijzigde revisie moet de volledige batch opnieuw worden beoordeeld.

## Deterministische multi-coinselectie

De bestaande Decision/Entry-agents beoordelen elke coin op dezelfde historische
15m-grens via de orchestrator. Zij krijgen kopieën van de centrale ledger, geen
reserverings- of uitvoeringsbevoegdheid. De centrale beoordelaar houdt per coin
het analysebericht, voorstel, geschiktheid, rang, scannerscore, prioriteit,
risicobeoordeling en afwijsreden bij. Onderliggende agentredenen blijven bewaard.

Vooraf vastgelegde volgorde:

1. Hoogste geldige Coin Scanner-score eerst. Dit is een onderzoeksrang, geen winstkans.
2. Bij gelijke score: cyclische volgorde van de alfabetisch vastgelegde watchlist,
   met startindex `floor(UTC-epochseconden / 900) modulo aantal coins`.
3. Beoordeel kandidaten in die volgorde. Een ongeschikte of door risico afgewezen
   kandidaat wordt overgeslagen; de eerste geldige krijgt de reservering.
4. Overige kandidaten worden expliciet afgewezen wegens gereserveerde cash/positieplaats.

De UTC-rotatie en volledige volgorde staan in iedere batch. Daarmee bepaalt de
invoervolgorde of snelheid van een agent niet de winnaar en wordt niet steeds
stilzwijgend dezelfde alfabetisch eerste munt gekozen. Dit garandeert geen gelijke
handelsfrequentie: daadwerkelijke scores en geschiktheid kunnen verschillen.

De reports moeten naar dezelfde scannergebeurtenis verwijzen. Ontbrekende of
ongeldige essentiële analyses verhinderen een nieuwe instap uit het onvolledige
vergelijkingsuniversum. Een bekende inhoudelijke conflicterende analyse maakt die
coin ongeschikt; de overige volledig onderzochte coins kunnen nog meedoen.
Exitbewaking van bestaand bezit gaat onafhankelijk van nieuwe instapsignalen door.

## Offline uitvoering en tijdvolgorde

`evaluate(at)` maakt alleen berichten, beoordelingen en reserveringen. Alleen
`execute(batch_id)` kan expliciet een historische onderzoeksfill verwerken.
Er worden geen paper-orders, externe orders of API-aanroepen gemaakt.

De uitvoering gebruikt uitsluitend de bestaande fase-4B OfflineLedger.buy/sell en
FillCosts, plus de bestaande fase-5-risicocontroles en Exit Agent. De simulator zelf
is ongewijzigd. Standaard blijven fee 0,1% per zijde, volledige spread 0,1% en
slippage 0,1% per zijde, Decimal-berekening en ongunstige afronding gelden.

Een instapsignaal op close N kan pas op open N+1 worden uitgevoerd. Selectie,
hoeveelheid en stop gebruiken geen high/low/close van N+1. Vóór de fill worden
risico, saldo, filters en de reservering opnieuw gecontroleerd. Een ongunstige open
die meer cash vereist dan gereserveerd leidt tot afwijzing en vrijgave; de reservering
wordt niet automatisch verhoogd. Een gunstigere open laat ongebruikte cash vrij.
Na een afgewezen fill wordt niet achteraf op basis van die nieuwe prijsinformatie
een andere coin uit dezelfde batch gekozen.

Een ongebruikte instapreservering vervalt bij de volgende historische evaluatie.
De oude batch krijgt een definitieve expiry-uitkomst en kan geen vertraagde fill
meer opleveren. Exits reserveren uitsluitend bestaand bezit. Een open exit moet
eerst expliciet worden afgehandeld; iedere volgende afgesloten 15m-candle van
een open positie moet worden gecontroleerd. Candles overslaan wordt geweigerd.

Stop-/targetambiguïteit, stopgaps, horizon en veiligheidsstops volgen fase 5.
Onbekende intrabarvolgorde wordt conservatief behandeld. Een afgewezen exit houdt
de positie intact. Er is geen fictieve terminale liquidatie bij ontbrekende data.

Batch-ID, exacte goedgekeurde inhoud, agentherkomst, state-revisie en unieke
settlementsleutel voorkomen omzeilen en dubbele uitvoering. Fill, ledgerstaat,
audit en vrijgave staan in één transactie. Bij opslagfouten rolt alles terug.
Een herhaalde execute retourneert de oude uitkomst met replay=true, zonder nieuwe
kosten, kasmutatie of verkoop. Alle veiligheidscontroles lopen vóór een nieuwe fill.

## Opslag, API en onderzoeksisolatie

Nieuwe tabellen: joint_protocols, joint_states, joint_batches en joint_settlements.
States bevatten de volledige gedeelde ledger, reservering, waardering, revisie en
hashketen. De bestaande paper- en onderzoeksresultaattabellen blijven gescheiden.
De orchestrator gebruikt het bestaande berichtencontract en de bestaande auditopslag.

Alleen-lezen routes:

- `/joint-portfolios`: laatste opgeslagen gezamenlijke historische waarderingen;
- `/joint-protocols`, `/joint-states`: beleid en administratieve geschiedenis;
- `/joint-candidates`, `/joint-settlements`: rangschikkingen, afwijzingen en afhandeling.

De bestaande `/portfolio` blijft de oude paper-interface. De beide modes worden
niet samengevoegd of opgeteld. API-waarderingen zijn historische snapshots, geen
actuele koersfeed en geen uitvoeringsautorisatie.

Plan, beslisbeleid, filters, rapportbundel en candlehashes worden vóór evaluatie
bevroren. Alleen ontwikkeling is toegestaan, maximaal 192 aaneengesloten
15m-candles per coin, met dezelfde dekking voor de hele watchlist. De onafhankelijke
test en formele validatie hebben geen toegangspad in deze interface. Geen historische
testperiode is vrijgegeven. Bestaande hypotheses en onderzoeksresultaten zijn intact.

## Verificatie

**287 tests geslaagd, 0 mislukt**: alle 251 bestaande tests en 36 nieuwe tests.
Er blijft één bestaande Starlette/AnyIO-deprecationwaarschuwing.

De nieuwe suite controleert gelijktijdige signalen, veranderde invoervolgorde,
scoreprioriteit en gelijke scores, twee databaseverbindingen, centrale reservering,
verval, dubbele/ongeautoriseerde uitvoering, kosten, prijsbewegingen, gaps,
muntwissels zonder herkapitalisatie, verliesreeksen, dagverlies/drawdown, noodstop,
risicoveto, hercontrole, transactionele rollback, ontbrekende gegevens, candlevolgorde,
verkeerde tijdzones, testvergrendeling, ongeldige staat, bevroren batchinhoud,
readonly API en isolatie van bestaande bots/resultaten.

Een volledige kleine fixtureworkflow — BTC-instap, BTC-stop, ETH-instap — is exact
vergeleken met heruitvoering inclusief databaseheropening. Cash, fees, gerealiseerd
resultaat, bezit, batches en alle administratieve states zijn gelijk. Dit test
boekhouding en reproduceerbaarheid, geen winstgevendheid.

Er zijn geen nieuwe historische downloads, uitgebreide backtests of parameter-
zoektochten uitgevoerd. De bestaande lokale archiefcontroles blijven deel van de
251 behouden tests. Tijdens ontwikkeling gevonden opslagproblemen zijn opgelost;
er zijn geen resterende mislukte tests.

## Beperkingen en stopgrens

- Eén gelijktijdige positie is in fase 6A de standaard én de toegestane bovengrens.
  Gelijktijdig meerdere open cryptoposities en correlatiemodellen zijn niet gebouwd.
- OHLC-uitvoering blijft een conservatieve aanname zonder orderboek, latency of
  gedeeltelijke fills. Gaps kunnen gerealiseerde verliezen boven gepland risico brengen.
- Historische filters kunnen alleen als expliciete aannames beschikbaar zijn;
  hashes/bronverwijzingen vervangen geen onafhankelijke authenticiteitscontrole.
- Geen betrouwbare nieuwsfeed of statistisch bewijs van positieve expectancy.
- SQLite-transacties en revisiecontroles beschermen de administratie; dit is geen
  gedistribueerde broker of beveiliging tegen een beheerder die code/database wijzigt.
- Handmatige offline workflow, geen automatische paperbot, live trading of scheduler.
  Windows is niet uitgevoerd; de dependencywaarschuwing blijft bestaan.

Fase 6A eindigt hier. Geen automatische start van een volgende fase.
