# Vervolg na audit-hashoptimalisatie fase 6B

Lees PHASE6B_AUDIT_OPTIMIZATION_REPORT.md. Alle 385 tests slagen. Hashwaarden en
volledige financiële/auditinhoud blijven gelijk. De hashfunctie is bij 1.000
synthetische stappen sneller, maar de totale replaytijd verbetert niet aantoonbaar.

1. Onderzoek alleen na een nieuwe opdracht de overige analyse-/toelatings-/opslag-
   kosten. Behoud agentisolatie, risicoregels en financiële Decimal-rekenregels.
2. De eventcache is maximaal 2 MiB. Boven die limiet geldt terugval met mogelijk
   herhaalde cache-opbouw; versnelling voor lange histories blijft onbewezen.
3. Behoud ongecachete volledige herstartverificatie, hashcompatibiliteit, mutatie-,
   rollback-, audit-insert-crash-, pending-order- en deduplicatietests.
4. Geen automatische 5.000-run, jaarprobe of historische rendementsbacktest.
   Jaarcapaciteit en het oorspronkelijke 45-secondenjaarcriterium blijven onbewezen.
5. Onafhankelijke testperiode gesloten; geen strategiepromotie, parameteroptimalisatie
   of automatische volgende fase. Stop na deze oplevering.
