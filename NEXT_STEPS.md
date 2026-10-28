# Vervolg na streamingcheckpoint fase 6B

Lees PHASE6B_STREAMING_REPORT.md. Alle 377 tests slagen. De opgeslagen 5.000-
stappenmeting is voltooid: 291,499 seconden en 74,4 MiB piek-RSS. Jaarcapaciteit
is niet bewezen; de oorspronkelijke 45-secondenjaarvoorwaarde is niet geslaagd.

1. Onderzoek uitsluitend na een nieuwe opdracht hoe het herhaald lezen van de
   volledige auditgeschiedenis voor statehashes verminderd kan worden met behoud
   van exacte audit-/statehashgelijkheid en veilige reconstructie.
2. Behoud de 24 streamingtests en alle 353 bestaande tests: financiële gelijkheid,
   crashherstel, deduplicatie, pending orders, risicopauzes en causaliteit.
3. Begroot een eventuele langere actieve synthetische test vooraf. De huidige
   prestatieruns hadden nul trades; hun geheugen- en tijdcijfers bewijzen geen
   jaarcapaciteit of onbeperkte actieve workload. Geen automatische jaarprobe.
4. Gebruik echte schijfopslag voor database én SQLite-tempbestanden. /tmp is hier
   tmpfs. Consumeer stream(times) zonder alle snapshots zelf op te sparen.
5. Historische uitvoering/migratie en API-ondersteuning voor het nieuwe compacte
   stateformaat zijn afzonderlijke vervolgstappen, zonder automatische activering.
6. Onafhankelijke testperiode gesloten houden. Geen historische rendementsbacktest,
   strategiepromotie, parameteroptimalisatie of volgende fase automatisch starten.

Stop na het veiligstellen van dit checkpoint.
