# Fase 6H-B — goedgekeurde hypothetische vergelijking, registratie vóór uitvoering

De gebruiker heeft na de metadata-stop expliciet exact dezelfde hypothetische
historische filters als de bestaande baseline toegestaan. Historische filter-
geldigheid blijft onbewezen. De eerdere blokkering is volledig behouden in
`experiments/phase6h_b/BLOCKED_METADATA_REPORT.md` en de oude preflightregistratie.

De nieuwe adapter staat uitsluitend in `crypto/historical_recovery.py`, met een
apart uitvoeringsscript en nieuwe database `/workspace/phase6h_b_recovery.sqlite3`.
De oorspronkelijke database wordt uitsluitend read-only als bron gelezen.
Alle 533 tests slagen: 527 bestaande plus zes nieuwe synthetische integratietests.

Het read-only, inhoudsgebonden uitvoeringsmanifest en de nieuwe toestemming staan
in `experiments/phase6h_b/execution_registration.json`. De registratie bindt code,
bron-/configuratiehashes, inputseal en dezelfde aangenomen filters/kosten. Git maakt
de voorafgaande versie controleerbaar; geen extern onveranderlijke WORM-claim.

Uitsluitend 2024, BTC/EUR ETH/EUR SOL/EUR, baselinekosten en aligned_trend met
24u-herstel. De gecontroleerde oude baseline wordt hergebruikt. Nog geen nieuwe
financiële uitkomst berekend op het moment van deze preregistratie. Maximaal
1800 s per voorbereiding/replay, 1,5 GiB adresruimte, vroege RSS-stop 1.288.490.188
bytes, 2 GiB vrije schijf, nul netwerkverzoeken. Checkpoints voorkomen herstart
vanaf nul. Validatie 2025/test 2026 gesloten; ATR-kostenfilter buiten scope.
