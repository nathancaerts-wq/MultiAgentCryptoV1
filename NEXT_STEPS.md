# Vervolg na fase-6B-performanceonderzoek

Lees PHASE6B_PERFORMANCE_REPORT.md. De prefixcache vermindert herhaalde
historieverificatie; de jaarblokkering is nog niet volledig opgelost.

1. Bewaar de lokale wijzigingen en profielartefacten; verander geen onderzoekparameters.
2. Ontwerp een incrementele ledger-/eventopslag, met bewijs voor dezelfde inhoud,
   kosten, risicopauzes, herstart, corruptiedetectie en rollback.
3. Meet daarna sequentieel op gereserveerde resources: 1.000, 10.000 en een jaar
   met volledige synthetische agentrapporten en transacties, plus herhaalrun.
   De bestaande lege-rapporten-screening is slechts een ondergrens.
4. Handhaaf het afzonderlijke 45-secondencriterium; rapporteer overschrijding eerlijk.
5. Historische evaluatie blijft afhankelijk van alle essentiële controles.
   Geen historische backtests in deze performancefase; onafhankelijke test gesloten.
