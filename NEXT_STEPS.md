# Vervolg na de fase-6B-preregistratiecontrole

De historische fase-6B-evaluatie is geblokkeerd conform de expliciete stopvoorwaarde.
Lees PHASE6B_REPORT.md en experiments/phase6b_preregistration_audit.json. Start geen
nieuwe evaluatie zolang de hieronder genoemde afspraken niet vooraf zijn vastgelegd.
Behoud alle 287 tests en alle bestaande bots, resultaten en risicogrenzen.

1. Consolideer het echte onderzoeks-/inzageregister, inclusief eerdere warm-updata.
   De oude smoke-testdatabases zijn niet duurzaam bewaard; ontbrekende registratie
   is geen bewijs van onaangeraakte historische gegevens. Fixtures blijven apart.
2. Leg exacte UTC-ontwikkel-/validatieperioden, embargo en beschermde testvensters
   vast. De twee bekende plannen reserveren 2025-01-15 → 2025-01-16 UTC als
   onafhankelijke test. Open of herlabel die periode niet zonder expliciete toestemming.
3. Leg de primaire bestaande hypothese en eventuele afzonderlijke secundaire
   studies vast, plus historische toelatings-/uitsluitingsregels voor de zes paren.
   Selecteer geen coins of vensters met kennis van latere rendementen/datadekking.
4. Definieer gezamenlijke benchmarks, allocatie, periode-eindebehandeling,
   kostenstress en exact omschreven gevoeligheid voor uitzonderlijke winnaars/verliezers.
   Onderscheid marktrendement van de risicoconforme handelsportefeuille.
5. Bouw en test zo nodig een gezamenlijke evaluatierunner die deze afspraken kan
   uitvoeren; de huidige mode accepteert geen validatie en maximaal 192 candles.
   Omzeil dit niet door splits te hernoemen of losse €200-portefeuilles op te tellen.
6. Bevries het complete plan en registreer data-/rapporthashes en inzage vóór
   uitvoering. Houd binnen een run één gedeelde ledger en alle verliespauzes intact.
7. Voer pas daarna de vooraf beschreven evaluatie uit. Rapporteer ontbrekende data,
   te weinig trades en onzekerheid; geen optimalisatie of winstclaims zonder bewijs.

Geen echte orders, API-sleutels, automatische paperbot of volgende fase gestart.
