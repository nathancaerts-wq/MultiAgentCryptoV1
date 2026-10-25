# Vervolg na fase 3

Fase 3 is afgerond. Begin fase 4 alleen na expliciet verzoek.

1. Behoud alle 124 tests en de officiële checksum-fixtures. Lees PHASE3_REPORT.md.
2. Voor eventueel later backtesting: definieer point-in-time datasetversies,
   candlepublicatielatentie, indicator-warm-up, kosten en onafhankelijke evaluatie.
   Historische onderzoeksrapporten zijn nog geen backtests of handelsadviezen.
3. Stel pas na broncontrole een betrouwbare NewsAdapter beschikbaar. Publicatie,
   werkelijke beschikbaarheid en verval zijn verplicht; unknown blijft het veilige
   resultaat zonder bruikbare bron. Gebruik geen betaalde API zonder toestemming.
4. Onderzoek procesisolatie voor blokkerende workloads en een expliciet
   archiefcorrectie/cacheverversingsbeleid. Voer Windows 11-installatie/starttests uit.
5. Bewaak dat incomplete data, conflicten en historische timestamps ook in latere
   consumenten zichtbaar blijven. usable is berichtgeldigheid, geen handelsautorisatie.

Geen automatische strategieactivatie, optimalisatie, transacties of dashboard.
Bestaande risicogrenzen en overige tradingbots blijven behouden.
