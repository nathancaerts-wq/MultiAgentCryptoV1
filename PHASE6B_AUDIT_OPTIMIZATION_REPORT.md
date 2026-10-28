# Fase 6B — compatibele auditcache

28 oktober 2026. Basis 00271e19a459491d3a68c58c53f49a37defd00b8;
werkmap schoon bij aanvang. Alleen deterministische synthetische technische fixtures.
Geen historische rendementsevaluatie, onafhankelijke testdata of externe orders.

## Hashanalyse

`canonical` gebruikt JSON met gesorteerde sleutels, standaard spaties, ASCII-escaping,
`default=str` voor onder andere Decimal/datetime en weigering van NaN.

- Ieder ledger-event bevat sequence, action, at, details en previous; hash is SHA-256
  van die inhoud zonder hash zelf. Details bevatten onder andere order-ID, prijzen,
  hoeveelheden, kosten, uitvoeringsaannames, metadata en snapshots.
- De logische statehash omvat alle statevelden behalve hash: portefeuille, tijdstip,
  checked_at, instrumentregels, mark, pending/reservering, stopped, revision,
  previous, kind, eventuele batch_hash, volledige ledger en valuation. Ledger bevat
  cash, positie, risico-/dag-/drawdownstaat, fees, trades, events, curve en gesorteerde
  order-ID's. Financiële scalars vóór de eventlijst veranderen per transactie.
  De Python-objecten costs/rules/limits zelf zijn uitgesloten van ledger-JSON;
  configuratie en filters zijn apart via het bevroren manifest gebonden en kosten-/
  metadata-aannames staan ook in uitvoerings-events.
- De fysieke checkpoint bevat dezelfde logische hash, histories als prefixlengten,
  checkpoint_previous en checkpoint_hash. Die laatste hasht de compacte inhoud.
- Plan-, rapport- en inputhashes blijven ongewijzigd; de nieuwe cache is uitsluitend
  voor de eventlijst binnen de logische statehash.

Events zijn append-only, met aaneengesloten indices en bestaande SQL-mutatieguards.
BEGIN IMMEDIATE omvat fill, settlement, histories, checkpoint en audit. Fout of
procescrash rolt de hele transactie terug. Herstart controleert de volledige
invoer, eventketen, checkpointketen, laatste logische hash en prefixlengten.

De bestaande streamingrapporten en tests vergelijken expliciet statehashes,
checkpoint-hashes, agentresultaten en persistente audit. Ook de oudere ledger-golden
fixtures en risicopauzereferenties blijven afhankelijk van hun oorspronkelijke
canonicalisatie. Die contracten zijn niet gewijzigd.

## Oplossing en compatibiliteit

Een oude SHA-256-context kan niet worden voortgezet zodra eerdere financiële bytes
veranderen. Daarom is geen Merkle-hash, digest-van-digests of nieuwe hashsemantiek
ingevoerd. De gekozen oplossing cachet **exact de oorspronkelijke eventbytes** in
chunks van circa 64 KiB, maximaal 2 MiB payload voor één portefeuilleprefix per store.
Ieder hashverzoek verwerkt nog alle oorspronkelijke bytes met SHA-256, maar doet
veel minder SQL-rijlezingen, Python-iteraties en UTF-8-conversies.

`pieces`/`streamed_hash` hebben een optionele eventcache; standaard blijven zij
ongecachet. Alleen `_save` schakelt caching in. `verify_history` blijft ongecachet.
IDs (globaal gesorteerd), trades, curve en financiële velden volgen hun oude pad.

Elke cachehit controleert SQLite data_version, de feitelijke laatste prefixrij en
de prefixlengte. Externe commits, andere portefeuille of een kortere prefix geven
herbouw. Een aanvullende transactionele mutatie-epoch op UPDATE/DELETE van historie
weigert gebruik van een veranderde warme prefix, ook wanneer een beheerder alleen
de oorspronkelijke mutatieguard heeft verwijderd. De gewone guards blijven actief.
Rollback van buitenste transactie én savepoint wist de cache. Een mislukte commit
kan dus geen ongecommitteerde bytes als geldig vervolg achterlaten.

Bij overschrijding van 2 MiB vervalt de cache en volgt het oude streaming-leespad.
Dit begrenst extra RAM; het is geen oplossing voor alle jaarlengten. Er worden geen
hashcontexten of cachebewijzen opgeslagen. De enige schema-aanvulling is een epoch-
tabel met triggers; bestaande records, hashes en stream-v1 blijven compatibel.
Geen migratie van financiële data of afwijkend hashformaat nodig.

Dit blijft de bestaande lokale trust boundary: een beheerder die code, triggers,
epoch en data doelbewust samen herschrijft, of private cachebytes wijzigt, is geen
onvertrouwde externe client. Er wordt geen sterkere beveiligingsclaim gedaan.

## Verificatie

De bestaande 377 tests worden behouden. Nieuwe tests controleren gecachte versus
ongecachete hashes op actieve states, het vermijden van volledige prefixlezingen,
rollback na hashing, begrensde fallback, illegale mutatie van een oud event, externe
commits en koude heropening. Een aanvullende subprocess-test beëindigt het proces
met os._exit tijdens de SQLite INSERT van de settlement-audit. Na herstart blijven
reservering, vorige audits en state intact; expliciete hervatting geeft één fill,
en een herhaalde uitvoering geen tweede fill.

De bestaande fixtures blijven entry/exit, stops, kosten, dubbele signalen/fills,
noodstop, dagverlies-, drawdown- en verliesreekspauzes, open posities en reconstructie
vergelijken. De volledige analyseketen wordt eveneens vergeleken.

## Metingen

`scripts/measure_audit.py` meet 100, 500 en 1.000 stappen, achtereenvolgens vóór en
na. De baseline laadt de originele streamingmodule rechtstreeks uit basiscommit
00271e1. Beide gebruiken dezelfde overige modules, candles, vooraf vastgelegde
indicator-/strategieparameters, kosten, portefeuille en risicogrenzen. cProfile,
RSS, schijfopslag en SQLite-tempbestanden op /workspace; maximaal 180 seconden per
subprocess en 1,5 GiB address space, vroege stop boven 1,2 GiB RSS.

De technische FixtureData levert reproduceerbare venstergebonden analyses; dit is
geen coherent historisch marktcorpus of financiële rendementsproef. Drie coins,
gezamenlijk €200 en drie daadwerkelijke gesloten virtuele verliestrades per run.
Daarna grijpt de bestaande verliesreekspauze in. Dit bewijst geen onbeperkte actieve
handelsketen. Audit/import-wallclocks worden voor beide varianten gelijk vastgezet.

Volledige inhoudshashes vergelijken results, analyses, regimes, scan_runs,
stream_states, stream_history, joint_batches, joint_settlements en audit. Er worden
geen financiële velden of statehashes uit die vergelijking gefilterd.

| Stappen | Voor s | Na s | RSS voor MiB | RSS na MiB | Trades per run |
|---:|---:|---:|---:|---:|---:|
|100|9.631|9.185|72.4|72.3|3|
|500|42.879|44.546|81.6|81.2|3|
|1000|89.977|91.382|82.1|81.7|3|

Alle negen vergeleken tabellen zijn per meetlengte exact gelijk, inclusief
logische statehashes, checkpoint-hashes, auditregels en risicopauzes.
Bij 1.000 stappen daalt streamed_hash van 2,028 naar 0,886 s cumulatief (circa 56%).
De calls naar pieces dalen van 3.578.846 naar 540.590. Event-/trade-history raws
(generatorcalls inclusief yields) dalen van 674.363 naar 164.823; resterende calls
omvatten niet-gecachete trades en de verplichte koude verificatie.

De totale looptijd daalt niet aantoonbaar: 500 en 1.000 stappen zijn licht trager.
Er is geen algemene replayversnelling of statistische prestatieclaim. Hostbelasting,
schijfsynchronisaties en overige analyse-/risicowerk domineren; dit zijn enkelvoudige
metingen op een gedeelde host, geen betrouwbaarheidsintervallen. De cache vermindert
aantoonbaar de specifieke hash-/prefixleeslast, maar biedt geen bewijs voor een
snellere volledige jaarreplay. Geen 5.000-run gestart.

**385 tests geslaagd, 0 mislukt**: alle 377 bestaande plus acht nieuwe.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. Meetbestanden en exacte
inhoudsvergelijking staan in experiments/audit_hash/.


## Resterend

De SHA-256-bewerking van de hele eventlijst blijft noodzakelijk voor compatibiliteit;
de totale hoeveelheid gehashte bytes blijft in beginsel kwadratisch. Boven de
cachelimiet keert de oorspronkelijke leeslast terug; de begrensde cache-opbouw
kan dan bovendien opnieuw worden geprobeerd. Winst boven die limiet is niet bewezen. Toelatingshistorie, berichten,
financiële reconciliatie en schijfsynchronisaties blijven kosten veroorzaken.

Geen nieuwe 5.000-stappenrun of jaarprobe. Jaarcapaciteit en de oorspronkelijke
45-secondenvoorwaarde zijn niet bewezen. Onafhankelijke testperiode gesloten.
Geen strategie-, kosten-, indicator- of risicoparameters gewijzigd; geen andere bots.
