# Fase 2B — officiële Binance-archiefadapter

Gebouwd op fase-2-commit d2881af. Uitgevoerd op 26 oktober 2026.

## Gerealiseerd

`crypto.archive.ArchiveDataAdapter` implementeert de bestaande
`fetch(symbol, interval, start, end) -> list[Candle]`-interface. Ze haalt uitsluitend
publieke dagelijkse Spot-klines op vanaf data.binance.vision. EUR-paren zijn
configureerbaar; ondersteunde intervallen zijn 15m, 1h en 4h. Geen nieuwe libraries.

Per expliciete aanvraag worden maximaal zeven dagarchieven opgehaald. Ook voor een
subdagbereik wordt het volledige dagarchief gecontroleerd. Geen maandarchieven,
meerjarige downloads, achtergrondtaken, hostfallback of locatie-omzeiling.
De download is begrensd op 2 MB en 20 seconden per bestand; TLS-verificatie blijft
actief. HTTP-fouten stoppen de import en worden via de Data Engine geregistreerd.

De adapter haalt de officiële `.CHECKSUM` op en controleert bestandsnaam en SHA-256
**voordat** ZIP/CSV wordt verwerkt. Alleen één CSV met de verwachte naam en een
begrensde uitgepakte grootte wordt geaccepteerd. Bestanden worden niet uitgepakt
naar het bestandssysteem. ZIP-CRC wordt eveneens door de ZIP-reader gecontroleerd.

## Exacte tijden en datakwaliteit

Volgens de officiële bronformaatdocumentatie gebruikt Binance Spot vanaf
2025-01-01 microseconden; oudere Spot-archieven gebruiken milliseconden:
https://github.com/binance/binance-public-data#spot

De eenheid wordt door de archiefdatum bepaald, niet door een gok op basis van de
getalgrootte. Integerrekenwerk converteert naar expliciete UTC-datetimes, zonder
floatafronding. Inclusieve Binance-close-tijden worden exact naar het bestaande
exclusieve Candle-einde omgezet. Verkeerde of gemengde eenheden worden afgewezen.

Validatie omvat 12 CSV-velden, candleduur en UTC-uitlijning, positieve geldige
OHLC-prijzen, eindige niet-negatieve volumes, takervolumegrenzen, volledigheid,
volgorde, duplicaten en afgesloten candles. Een gat wordt niet geïnterpoleerd.
Ook een subdagaanvraag kan een onvolledig dagbestand niet verbergen.

`verify_4h(engine, symbol, start, end, as_of)` vergelijkt de officiële 4h-candles
exact met vier volledige 1h-candles, inclusief open/high/low/close, basisvolume,
quotevolume en tijdsgrenzen. Succes en mismatch worden geaudit; mismatch werpt een
fout op. Dit is een expliciete controle, geen impliciete extra download bij iedere
fetch. Individuele datasets blijven afzonderlijk gevalideerde bronrecords.

## Opslag en caching

De bestaande Data Engine bewaart normaliseerde candles zoals voorheen. Een optioneel
`archive_manifest` in het datasetrecord bevat bron-URL, checksum-URL, geverifieerde
SHA-256, archiefperiode, tijdseenheid, bronformaatreferentie en validatiestatus.
Bestaande adapters en oude cache-records blijven werken.

De Data Engine voorkomt herhaalde imports van dezelfde aanvraag en dezelfde
candles. Een geheugen-cache voorkomt herhaalde downloads van hetzelfde gevalideerde
archief bij overlappende aanvragen in één adapterinstantie. De database-cache blijft
over herstarts bestaan. Onjuiste archieven worden niet gecachet of geïmporteerd.
Herhaalde requests gebruiken een onveranderlijke momentopname; er is geen stille
vervanging wanneer Binance later archiefcorrecties publiceert. Een expliciet beleid
voor bronupdates en cacheverversing blijft vervolgwerk. Checksummetadata beschrijft
de oorspronkelijke download; een cache-hit downloadt geen nieuwe checksum.

## Echte integratiecontrole

Alle zeven ZIP-bestanden en alle zeven officiële checksum-bestanden gaven HTTP 200:

| Dataset | Interval | Candles | Eenheid | Checksum |
|---|---|---:|---|---|
| BTCEUR 2025-01-10 | 15m | 96 | us | SHA-256 gelijk |
| BTCEUR 2025-01-10 | 1h | 24 | us | SHA-256 gelijk |
| BTCEUR 2025-01-10 | 4h | 6 | us | SHA-256 gelijk |
| ETHEUR 2025-01-10 | 15m | 96 | us | SHA-256 gelijk |
| ETHEUR 2025-01-10 | 1h | 24 | us | SHA-256 gelijk |
| ETHEUR 2025-01-10 | 4h | 6 | us | SHA-256 gelijk |
| BTCEUR 2024-12-31 | 1h | 24 | ms | SHA-256 gelijk |

Voor beide EUR-paren komen alle zes officiële 4h-candles exact overeen met de
1h-aggregaties. De live Data Engine importeerde 7 datasets en 276 candles in een
tijdelijke database. Er zijn nul orders aangemaakt. De ongewijzigde kleine officiële
archieven en checksum-bestanden zijn opgenomen als reproduceerbare lokale fixtures.

## Tests en grenzen

Alle **96 tests geslaagd**: de 67 bestaande tests en 29 nieuwe archieftests.
Nieuwe tests omvatten beide echte fixtureparen, alle intervallen, ms/us-grens,
verkeerde/gemengde eenheden, corrupte ZIP, ZIP-inhoud, verkeerde checksum en
bestandsnaam, ongeldige OHLCV, ontbrekende/duplicaat/omgekeerde candles,
onafgesloten archieven, downloadlimieten, cache na herstart, overlappende imports,
geen gedeeltelijke database-import en correcte/afwijkende 4h-aggregatie.
Offline tests hebben geen netwerk nodig. De echte netwerkcontrole is aanvullend
uitgevoerd; geen internetafhankelijke test maakt deel uit van de standaardsuite.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing blijft bestaan.

Deze steekproeven bewijzen geen actuele verhandelbaarheid of dekking van alle
historische perioden. Windows is nog niet daadwerkelijk getest. De bestaande
single-process SQLite-beperkingen blijven gelden. Risicogrenzen, strategieën,
tradinginstellingen en overige bots zijn niet gewijzigd. Geen transacties, sleutels
of parameteroptimalisatie. Fase 3 is niet gestart.
