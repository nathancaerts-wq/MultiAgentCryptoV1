# Vervolg na fase 2B

Fase 2B is afgerond. Begin fase 3 uitsluitend na expliciet verzoek.

1. Behoud de 96 tests en de kleine officiële archieffixtures met checksum-bestanden.
2. Gebruik ArchiveDataAdapter voor expliciete dagelijkse historische imports;
   roep verify_4h aan voor controles van officiële 4h-data tegenover 1h-data.
3. Leg bij verdere dataontwikkeling een expliciet broncorrectie/cacheverversingsbeleid
   vast. Bestaande imports zijn onveranderlijke momentopnamen, geen actuele bronspiegel.
4. Verifieer instrumentbeschikbaarheid apart met officiële metadata voordat ooit
   simulaties met actuele handelsregels worden gebouwd. Historische data bewijzen
   geen actuele verhandelbaarheid. Archiveer metadata met bron en tijdstip.
5. Fase 3 kan de bestaande onderzoekscontracten voor regime, indicatoren en meerdere
   tijdsframes uitwerken. Gebruik uitsluitend data beschikbaar op het evaluatietijdstip.
6. Voer Windows 11-installatie- en starttests uit; de huidige validatie is op Linux.

Geen strategieactivatie, orders, parameteroptimalisatie of dashboard zonder aparte
opdracht. Harde risicogrenzen en bestaande tradinginstellingen blijven behouden.
