# Vervolg na de gerichte ledgeroptimalisatie

Lees PHASE6B_LEDGER_OPTIMIZATION_REPORT.md. De financiële gelijkheids- en
correctheidstests slagen; 340 tests behouden. De jaarreplay is niet vrijgegeven.

1. Ontwerp een afzonderlijk genormaliseerd append-only audit-/tradearchief met
   gecontroleerde checkpoints, zodat niet iedere revisie de hele ledger kopieert
   en valideert. Behoud alle auditdata, Decimal, rollback en herstartgelijkheid.
2. Meet volledige analyse-/toelatingshistorie en actieve posities met synthetische
   data. De huidige 1.000-stappenperformancecases zijn geen actieve jaarsimulatie.
3. Onderzoek versiegebonden binding van FixtureJointRunner.history en streaming
   van gepreregistreerde rapporten, met dezelfde mutatie-/as_of-beveiligingen.
4. Pas bij stabiele, voldoende snelle kleine runs: een begrensde synthetische
   jaarprobe met herhaalrun. De 45-secondenvoorwaarde niet stilzwijgend verhogen.
5. Historische rendementsevaluatie blijft afhankelijk van alle eerdere essentiële
   controles. De onafhankelijke test blijft gesloten; geen automatische volgende fase.
