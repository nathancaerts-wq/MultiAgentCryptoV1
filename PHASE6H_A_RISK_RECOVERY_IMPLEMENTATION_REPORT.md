# Fase 6H-A — geïsoleerde offline risicohervatting

Basiscommit: `baa1cb77d87be9b1f2569dcc6e15e2d4af00a512`.
Leidend protocol: `PHASE6G_RISK_RECOVERY_PROTOCOL.md`, phase6g-recovery24h-v1.
De gebruikersopdracht geeft toestemming voor technische implementatie en
synthetische tests. Historische uitvoering en fase 6H-B zijn niet vrijgegeven.

## Architectuur en isolatie

Nieuwe module `crypto/recovery_research.py`; de bestaande modules zijn byte-identiek.
`RecoveryResearchPortfolio` is een afzonderlijke subclass van de gezamenlijke
`JointPortfolio`. De variant staat standaard uit (`enabled=False`). Ingeschakeld
gebruikt zij de naamruimte `offline-recovery:<planhash>` en bindt zij protocol-ID
plus fixture-only-scope in het bevroren manifest. Daardoor worden de baseline-
portefeuille, resultaten, reserveringen en checkpoints niet hergebruikt als variant.
Geen registratie in een bot, scheduler, live- of paperroute.

De ingeschakelde constructor accepteert uitsluitend synthetische plannen,
synthetische candles en analysebronnen, de drie munten BTC/EUR, ETH/EUR en SOL/EUR,
ontwikkeling binnen 2024, aligned_trend en de vaste drie-verliezengrens. Geen
historische adapter, historische runneruitbreiding of ATR-kostenfilter toegevoegd.
Het blijft een kleine gezamenlijke fixture-runner, met de bestaande maximaal
192 aaneengesloten uitvoeringscandles per coin. Geen jaarcapaciteitsclaim.

`_RecoveryReview` bevat de bestaande offline voorstelcontrole met precies één
vervangen blok: het levenslange verliesreeksveto wordt vervangen door de opgeslagen
afkoelingsstatus en versheidsgrens van de nieuwe epoch. Alle overige financiële
controles en de daadwerkelijke aanroep van de bestaande centrale Risk Engine zijn
behouden. Een regressietest vergelijkt de methode vóór en na dit blok exact met
de baseline; een latere wijziging daarvan vereist bewuste herbeoordeling. Deze
kopie is een onderhoudsverplichting, geen automatische overname van toekomstige
baselinewijzigingen. De actieve Risk Engine is niet aangepast.

Beoordeling én uitvoering gebruiken dezelfde nieuwe gate via de bestaande
`_risk_reason`-route. Nog vóór die beoordeling verbiedt de variant een entry in
dezelfde batch als een definitieve exit. Oude signalen van vóór de hervattingsgrens
blijven geweigerd. De bestaande orchestrator, gevalideerde berichten, centrale
reserveringen, fillsimulator, SQLite-opslag en ledger blijven de uitvoering verzorgen.

## Exacte toestand en eventvolgorde

`advance` is een pure transitie over uitsluitend definitieve gesloten ledger-trades:

- Netto < 0 verhoogt de gezamenlijke teller; netto >= 0 zet hem op nul, conform
  protocol en baseline. Netto nul is dus een reeksbreuk, geen winstclaim.
- De derde negatieve close legt atomair `pause_started_at` op haar definitieve
  afrekentijd vast en `pause_until` exact 86.400 seconden later. Het is UTC,
  geen wall-clocktijd van de test en geen geschat intrabar-stopmoment.
- Gedurende de pauze kan geen entry de controle passeren. Een extra definitieve
  trade tijdens deze flat-pauze is inconsistent en stopt verwerking.
- Op de eerste chronologische 15m-beslisgrens op of na expiry registreert de
  variant één `cooldown_expired`. Voorwaarde: valide ledger, flat, geen pending
  order/reservering. Een positie of pending order wordt niet stilzwijgend gewist.
- De epoch stijgt met één; `epoch_anchor` verwijst naar de definitieve tradeprefix
  tot dat moment; teller wordt nul. Dit is een cursor in de geaudite definitieve
  tradegeschiedenis, gebonden aan prefixhash en de bestaande checkpoint-/auditketen.
- De eerste nieuwe negatieve close telt als één. Drie nieuwe verliezen geven
  opnieuw 24 uur pauze. De oude verliezen blijven volledig in trades, fees,
  gerealiseerd resultaat, cash, drawdown en auditgeschiedenis staan.
- Prefixhash, aantal verwerkte closes en unieke exit-ID's maken herhaalde
  verwerking idempotent. Gewijzigde/verwijderde prefix, dubbele close in de
  financiële geschiedenis of teruggedateerde close wordt geweigerd.

De herstelstatus zit in `joint_states`, onder dezelfde statehash en vorige-hash-
verwijzing als de volledige ledger. `_validate` controleert prefix, aantal,
epoch-anchor, teller versus de werkelijke suffix en de 24u-timer. Dag-/drawdown-
flags, noodstop, cash, posities, pending en audit blijven in het bestaande checkpoint.
Ontbrekende of inconsistente herstelstatus geeft geen nieuwe instap.

## Atomiciteit, crashes en hervatting

Een fill, definitieve close, gewijzigde verliesreeksteller, timer en checkpoint
worden binnen de bestaande SQLite `BEGIN IMMEDIATE`-transactie opgeslagen. Bij
fouten wordt ook de reeds ingevoegde checkpointregel teruggedraaid. Na heropening
van het bestand wordt de gevalideerde toestand gereconstrueerd; geen geheugen-
teller geldt als alternatieve waarheid en geen nieuw startkapitaal.

Expiry is zelf een afzonderlijke geldige, atomische klokovergang vóór de volgende
beslisbatch. Als de latere batch mislukt, blijft deze volledige expiry-overgang
hervatbaar. Mislukt de expiry-opslag zelf, dan blijven timer en oude epoch intact.
Bij opnieuw aanbieden van dezelfde grens ontstaat geen tweede expiry-event.
De bestaande settlement-deduplicatie voorkomt dubbele fills na een crash.

## Alle andere beveiligingen behouden

Eén oorspronkelijke €200-portefeuille; één positie; maximaal 0,5% gepland risico
inclusief kosten met de bestaande min(200,cash)-grens; maximaal 50% exposure;
3% dagverlies, 10% drawdown en noodstop. Geen leverage of shorts. Cash, filters,
liquiditeit, signal freshness, stopafstand 2 ATR, horizon 4 uur, conservatieve
kosten/gaps en safety-exits blijven zoals in de bestaande uitvoering.
Expiry wijzigt geen enkele andere risicostatus. Een dagelijkse reset kan alleen
plaatsvinden door de reeds bestaande UTC-dagovergang in de ledger.

## Deterministische controles

De tests staan in `tests/test_recovery_research.py`. Alle gegevens zijn synthetisch.
Ze controleren:

- precies drie verliezen, geen trigger na één/twee, gedeelde teller over drie coins;
- expiry−15m, exact expiry en expiry+15m, inclusief een afrekening buiten de kwartiergrens;
- oude trades/cash/kosten/risicoflags behouden, nieuwe teller en tweede verliescyclus;
- winst en netto nul tussen verliezen, herhaalde events en gewijzigde tradeprefix;
- maand-/coinwisseling en herstart tijdens of precies na expiry, ook via echte
  sluiting en heropening van een tijdelijke SQLite-database;
- dagverlies, drawdown en noodstop blijven actief, inclusief werkelijke veto's
  door de offline review na expiry;
- pending/reservering bij expiry geeft een fout en bewaart de oude pauze;
- fouten na checkpointinvoer bij close, expiry en echte execution rollen terug;
- echte agent-entry, simulator-stop-exit, verliesregistratie en dubbele settlement;
- verstreken tijd alleen geeft geen autorisatie vóór de checkpointovergang;
- hercontrole bij uitvoeringsreferentie, ongeldige stop na gap en oude voorstellen;
- uitgeschakeld: exact gelijke beslissingen, reserveringen, fills, Decimal-kosten,
  ledgerstates, portefeuillewaarde en ledger-audit-events tegenover JointPortfolio;
  na drie verliezen blijft ook de permanente baselinepauze aanwezig;
- uitsluitend synthetische bron/toegestane datum en regressiecontrole van alle
  ongewijzigde reviewcontroles buiten het verliesreeksblok.

Eerste testruns vonden onjuiste fixtureaannames: een beoogde kleine winst werd na
kosten verlies, een kunstmatige pending ontbrak een vereist veld, en een directe
review gebruikte filters van een andere coin. De fixtures zijn gecorrigeerd;
geen financiële baselinecode of risicogrens is hiervoor aangepast.
Definitieve aantallen en volledige suite-uitvoer staan in `experiments/phase6h_a/`.
Tests draaien onder 180 s wall-clock en 1,5 GiB adresruimte; bronintegriteit wordt
streamend gecontroleerd onder 180 s en 1 GiB. Geen jaarprobe of nieuwe historische
uitkomsten. De kleine synthetische tests zijn geen rendements- of capaciteitstest.

## Beperkingen en vereisten voor fase 6H-B

Een dag wachten bewijst geen marktherstel. Herhaalde cycli kunnen nieuwe verliezen
opleveren; de bestaande cumulatieve drawdown en noodstop blijven essentieel.
Gepland risico begrenst geen gerealiseerd gapverlies. De nieuwe state is versie-
gebonden; bestaande baselinecheckpoints worden niet omgezet naar herstelcheckpoints.

Voor 6H-B is afzonderlijke toestemming vereist, inclusief een nieuwe registratie
van implementatie-, configuratie-, input- en datasetseals, historische fixture-guard-
uitbreiding in een aparte onderzoeksadapter, alle overige datakwaliteitscontroles,
exacte A-versus-baseline-vergelijking en begrensde uitvoeringsbudgetten. Niet deze
synthetische constructor omzeilen. Een toekomstige streaming-adapter moet de
herstelstate met dezelfde atomiciteit en auditsemantiek bewaren en opnieuw getest
worden. 2024 is reeds bekeken ontwikkeling en geen onafhankelijke bevestiging.
Validatie 2025 en onafhankelijke test 2026 blijven gesloten. Geen automatische
promotie naar actieve bot of andere strategie.

## Definitieve verificatie en oplevering

**527 tests geslaagd, 0 mislukt**: alle 497 bestaande tests behouden, 30 nieuwe
deterministische tests. Volledige suite 19,88 s, één bestaande Starlette/AnyIO-
waarschuwing. Gerichte tussenrun 27/27; na aanscherping van de constructorguard
voor exact drie coins zijn drie scope-tests toegevoegd en is de volledige suite
opnieuw uitgevoerd. Geen test van historische prestaties.

Alle **384 bestaande gevolgde bestanden** zijn byte-identiek aan de basiscommit.
De volledige financiële/auditdatabase heeft vóór en na controle dezelfde SHA-256
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`; WAL leeg.
Afsluitcontrole 12,24 s en circa 12,20 MiB piek-RSS. Dit is een bytescontrole van
oud bewijs; de nieuwe simulaties gebruikten uitsluitend tijdelijke fixturedatabases.
Bronbestanden, protocollen, financiële resultaten en oude checkpoints zijn behouden.
De registratie bindt de nieuwe module, tests, rapport en controlebewijzen met hashes
en documenteert de toestemming voor alleen deze technische fase. De oude
6G-documenten en hun historische statusvelden zijn niet overschreven.

Er is geen variant in de bot geactiveerd; geen nieuwe historische vergelijking,
marktdata-download, externe transactie of paper-order uitgevoerd. Validatie 2025
en onafhankelijke test 2026 blijven gesloten. Stop na commit/push; fase 6H-B
vereist afzonderlijke expliciete toestemming.
