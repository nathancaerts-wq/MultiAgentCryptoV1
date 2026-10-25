# Vervolg na fase 2

Fase 2 is afgerond met lokale fixtures. Begin fase 3 alleen na expliciet verzoek.

1. Laat, indien gewenst, data-api.binance.vision en data.binance.vision expliciet
   toe in de omgeving. Test officiële publieke endpoints zonder locatiebeperkingen
   te omzeilen; accepteer 451/403 als blokkade, gebruik geen proxy-omweg.
2. Verifieer EUR-instrumenten met officiële metadata en documenteer welke
   historische perioden werkelijk beschikbaar zijn. Bouw een canoniek register.
3. Valideer een kleine echte dataset tegen het bestaande Candle-schema. Een
   archiefadapter vereist checksumverificatie en expliciete timestamp-eenheden.
4. Fase 3: breid de onderzoekscontracten uit voor regime, indicatoren en meerdere
   tijdsframes. Gebruik uitsluitend gegevens beschikbaar op het evaluatietijdstip.
5. Behoud 67 tests en voeg nieuwe controles voor concrete datasets toe. Voer ook
   Windows 11-installatie/starttests uit; dit is nog niet geverifieerd.

Geen strategieactivatie, orderuitvoering, portefeuilletransacties of dashboard
zonder aparte faseopdracht. Harde risicogrenzen blijven behouden.
