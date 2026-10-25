# Concrete instructies voor fase 2

1. Lees ARCHITECTURE.md en voer de bestaande tests uit voordat je uitbreidt.
2. Laat publieke HTTPS-toegang tot api.binance.com toe en herhaal exchangeInfo.
   De eerste poging in de cloud gaf een proxy-403; gebruik geen verzonnen actuele paren.
3. Sla EUR spot-symbolen en alle toepasselijke Binance-filters inclusief versie,
   bron en ophaaltijd op. Breid filterondersteuning uit vóór enige simulatie van fills.
4. Bouw een uitsluitend lezende downloader voor candles, orderboek en 24u-volume,
   met rate limiting, retries, caching en expliciete datakwaliteitsstatus.
5. Maak canonieke dataset-IDs/hashes, UTC-validatie en checks voor ontbrekende,
   dubbele en toekomstige candles. Documenteer halfopen tijdsintervallen.
6. Integreer scannerselectie met opgeslagen metadata en verse marktmetingen.
7. Test met opgenomen kleine fixtures; behandel een echte publieke GET als aparte
   optionele integratietest. Gebruik geen account, API-sleutel of orderendpoint.
8. Voer Linux-tests én Windows 11-installatie/starttests uit. Werk voortgang bij.

Bouw in fase 2 geen strategieactivatie, live-tradingpad of grafisch dashboard.
