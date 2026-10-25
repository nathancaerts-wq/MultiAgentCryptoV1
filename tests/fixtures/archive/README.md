# Kleine officiële Spot-fixtures

Deze zeven originele ZIP-archieven en bijbehorende officiële `.CHECKSUM`-bestanden
zijn op 26 oktober 2026 opgehaald via HTTPS vanaf:

`https://data.binance.vision/data/spot/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{date}.zip`

- BTCEUR en ETHEUR: 2025-01-10, elk 15m/1h/4h (microseconden).
- BTCEUR: 2024-12-31, 1h (milliseconden).

De bestanden blijven ongewijzigd. Offline tests verifiëren SHA-256 vóór ZIP/CSV-
verwerking en hebben geen internettoegang nodig. Synthetische corrupties worden
uitsluitend tijdens de tests in geheugen gemaakt, met eigen testchecksums; zij
vervangen nooit de officiële checksum-fixtures.

Bronformaat en tijdseenheden:
https://github.com/binance/binance-public-data#spot
Datasetvoorwaarden: https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md

Dit zijn kleine historische steekproeven, geen volledige historische datasets of
bewijs van actuele instrumentbeschikbaarheid.
