# Ontwikkeljaar 2024 — actieve uitvoering

De voorbereiding en baseline zijn volledig voltooid; januari is financieel exact
vergeleken met de pilot. Zie PHASE6B_DEVELOPMENT_2024_REPORT.md en de statusbestanden
in experiments/development_2024/. Baseline eindkapitaal €197,03206319;
slippage-stress eindkapitaal €197,03119966. Geen statistisch bewijs uit drie trades.

1. Controleer actieve processen en /workspace/development_2024_*.log vóór hervatting.
   Er is één sequentiële driver voor de vooraf geregistreerde scenario's; start
   geen tweede run. Bewaar /workspace/development_2024.sqlite3 en de originele
   /workspace/january_pilot.sqlite3. Niet opnieuw vanaf nul starten.
2. Rond alleen de geregistreerde ontwikkelruns af binnen hun oorspronkelijke
   limieten; bij een fout/timeout driver stoppen en checkpoint controleren.
3. Voer daarna scripts/verify_development_2024.py read-only uit, voltooi het
   jaarverslag, controleer tests en push een checkpoint naar GitHub main.
4. BuyHoldIndex ondersteunt nog zes coins; de driemuntenindex is niet betrouwbaar
   uitgevoerd. Geen andere benchmark of filter stilzwijgend substitueren.
5. Geen validatie, onafhankelijke test, optimalisatie, strategie-/risicowijziging
   of echte orders. Stop na de ontwikkelperiode.
