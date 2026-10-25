# Vervolg na fase 4

Begin fase 5 uitsluitend na expliciet verzoek. Behoud alle 154 tests.

1. Lees RESEARCH_PROTOCOL.md en PHASE4_REPORT.md. Het huidige systeem levert
   onderzoeksselecties en testplannen, geen betrouwbare backtests.
2. Ontwerp en valideer eerst de ontbrekende fillsimulator en portefeuille-ledger:
   volgende-bar-instap, gaps, intrabarstops, fees/slippage, beursfilters,
   saldoreservering, exposure, correlatie en equitycurve. Behoud harde risicogrenzen.
3. Maak vooraf een plan voor benchmarkvergelijking, onzekerheidsintervallen,
   meervoudig testen, onafhankelijke test en resultaatselectie. Bekijk de testset
   pas na preregistratie; registreer externe inzage expliciet.
4. Bereken prestaties pas met geverifieerde fills en voldoende onafhankelijke data.
   Laat ontbrekende resultaten null; claim geen winstgevendheid op basis van
   fixtureselecties, lage trade-aantallen of een enkele uitzonderlijke winnaar.
5. Behoud €200-startkapitaal en maximaal 0,5% gepland risico. Geen automatische
   promotie, live orders, API-sleutels of wijziging van bestaande productie-instellingen.
6. Voer later Windows 11-validatie en een point-in-time dataversie-audit uit.
