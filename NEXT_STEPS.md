# Vervolg na technische voorbereiding fase 6B

Het ontwerp is voorlopig aanvaard; historische rendementsevaluatie is niet toegestaan.
Lees PHASE6B_READINESS_REPORT.md en behoud alle oude registraties en testsloten.

1. Voer de data-audit afzonderlijk uit voor de goedgekeurde D/V- en warm-upperioden;
   bewaar per munt/dag de officiële checksums, kwaliteit en ontbrekende data.
   Gebruik geen gesloten testdata. De huidige manifestdatasetvelden zijn nog leeg.
2. Verzamel betrouwbare historische listing-/filterbewijzen. Actuele exchangeInfo
   geldt niet als historische waarheid. Zonder bewijs geen historische instap.
3. Werk de resterende technische blokkeringen uit met fixtures: historische
   stage-regisseur, volledige bronveldconsistentie, benchmarkkalender/toelatingsgates
   en schaalbaarheid. Behoud de aparte fixture- en historische autorisatiepaden.
4. Vul het externe inzageregister aan en bind echte datasetidentificaties, code en
   configuratie aan een gecontroleerd manifest. Hashes detecteren wijzigingen;
   beschrijfbare bestanden zijn niet onveranderlijk.
5. Vraag pas vóór historische rendementsevaluatie de expliciete toestemming die
   nu ontbreekt. De onafhankelijke test vereist afzonderlijke toestemming.

Geen parameteroptimalisatie, risicowijzigingen, echte transacties of paperbot.
