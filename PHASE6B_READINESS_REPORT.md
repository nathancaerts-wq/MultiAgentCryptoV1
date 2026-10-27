# Fase 6B — technische voorbereiding

27 oktober 2026; basis f46cd4f16c2c417ea8ee822f11f7adb31b997a00.
Het ontwerp is voorlopig aanvaard. Historische rendementsevaluatie en onafhankelijke
test blijven niet toegestaan. Er zijn geen nieuwe historische rendementen berekend.

## Gerealiseerd

`crypto/readiness.py` biedt een dagelijkse data-audit voor de vastgelegde volledige
ontwikkel- en validatieperioden en hun afzonderlijke warm-up. De workflow gebruikt
de bestaande archiefadapter, SHA-256 vóór CSV-verwerking, strikte Candle-validatie,
exacte UTC-dekking en OHLCV-vergelijking 15m→1h→4h. Per coin en dag blijven fouten
en succesvolle archiefmanifesten zichtbaar. Een ontbrekend bestand maakt het
periodeverslag onvolledig. Eén dag per fetch houdt aanvragen begrensd. Er wordt geen
signaal of rendement berekend. Deze volledige historische audit is nog niet uitgevoerd;
alleen de workflow is met fixtures getest. Bestaande archieftests controleren de
kleine reeds bekende officiële bestanden opnieuw.

Toegestaan: ontwikkeling [2024-01-01,2025-01-01), ontwikkelwarm-up
[2024-01-01,2024-01-08), validatie [2025-02-01,2025-12-31 20:00),
validatiewarm-up [2025-01-25,2025-02-01), alles UTC. De laatste dagelijkse
validatie-ZIP bevat ook het embargo tot 2026-01-01; die laatste vier uur worden
uitsluitend gedecodeerd en niet aan het evaluatiebereik toegevoegd. Er worden geen
candles uit 2026 gelezen. Januari-2025-warm-up gebruikt dagelijkse bestanden;
het gesloten oude slot [2025-01-15,2025-01-16) wordt vóór aanvragen geweigerd.
Ook het kandidaat-testslot [2026-01-01,2026-10-01) blijft gesloten.

`FixtureJointRunner` hergebruikt JointPortfolio, Risk Engine, fillsimulator,
reserveringen en SQLite-ledger. De standaard oude interface behoudt 192 candles;
de aparte technische fixture-interface accepteert tot 1.000.000 candles per coin.
Alle coins hebben dezelfde chronologie. Eén ledger blijft behouden over aanroepen,
coinwissels en databaseheropening; achterwaartse en overgeslagen replay-batches
worden geweigerd, bestaande settlements worden niet dubbel uitgevoerd.
Een instap vereist zeven dagen trailing historie en de vastgelegde liquiditeit.
De eindgrens reserveert 4h15m. Broncontroles weigeren historische rendementruns
voordat de portefeuille wordt opgeslagen. Dit is geen autorisatiepad voor echte data.

De fixture-runner biedt de bestaande aligned_trend en een afzonderlijke EMA-agent:
EMA9/EMA21−1 >0,002 op afgesloten 1h-data, hoogste gap eerst met bestaande
UTC-ties, dezelfde Entry/Risk/Exit-keten. De monotone scoretransformatie behoudt de
rangorde. Cash en de analytische buy-and-hold-index hebben aparte rekenprimitieven:
€200 totaal, zes gelijke budgetten, eenmalige instap, uitgesloten componenten cash,
geen herweging, kosten en hypothetische terminale verkoop. De index verhoogt geen
limieten van JointPortfolio. Tests gebruiken uitsluitend synthetische prijzen.

## Historische verhandelbaarheid: bewijs en onzekerheid

| Paar | Aangetoond in bestaande bewijsstukken | Niet bewezen |
|---|---|---|
| BTC/EUR | Archiefobjecten 2024/2025; kleine officiële historische candles | Volledige listing-/delistinglijn en historische filters |
| ETH/EUR | Archiefobjecten 2024/2025; kleine officiële historische candles | Volledige listing-/delistinglijn en historische filters |
| SOL/EUR | Archiefobjecten 2024/2025 via HEAD | Listingtijd, volledige candlekwaliteit, historische filters |
| XRP/EUR | Archiefobjecten 2024/2025 via HEAD | Listingtijd, volledige candlekwaliteit, historische filters |
| ADA/EUR | Archiefobjecten 2024/2025 via HEAD | Listingtijd, volledige candlekwaliteit, historische filters |
| LINK/EUR | Archiefobjecten 2024/2025 via HEAD | Listingtijd, volledige candlekwaliteit, historische filters |

Nieuwe pogingen om officiële Binance-public-data- en Spot-API-documentatie op
GitHub te raadplegen faalden beide met proxy HTTP 502. URL's en fouten staan in
experiments/phase6b_metadata_sources.json. Geen alternatieve host gebruikt om een
beperking te omzeilen, geen actuele filters opgehaald of teruggedateerd.
Het beschikbare klineformaat bevat geen historische exchangeInfo-filtergeschiedenis.
Betrouwbare reconstructie is op basis van dit bewijsmateriaal niet mogelijk.
`metadata_evidence` weigert aangenomen, ongeldige of historisch niet geldige filters.
Een bronvermelding/statusvlag alleen bewijst geen authenticiteit: onafhankelijk
brononderzoek en gedateerde filterbestanden blijven nodig.

## Manifest en resterende blokkeringen

experiments/phase6b_readiness_manifest.json bevat configuratiehashes en concrete
identificaties/hashes van de kleine bekende fixtures. Ontwikkel-/validatiecorpora
staan expliciet als niet geaudit, historische rendementstoestemming en testtoestemming
zijn false. verify_manifest detecteert wijzigingen in geregistreerde bestanden.
Dit is een inhoudssnapshot op een beschrijfbaar bestandssysteem, geen claim van
onveranderlijke opslag of beveiliging tegen een beheerder.

De uitgebreide historische backtest is nog niet uitvoeringsgereed:

- Volledige corpusvalidatie en bewezen historische listing-/filtermetadata ontbreken.
- De nieuwe lange runner is uitsluitend voor fixtures; formele historische validatie
  blijft geblokkeerd. Er is geen verborgen omschakeling naar een echte run.
- Langere opslag is nog gebaseerd op de bestaande volledige hashketencontrole en
  JSON-manifesten; de schaalbaarheid voor miljoenen events is niet aangetoond.
- De benchmarkprimitieven vereisen een toekomstige geteste perioderegisseur die
  kalenderinstap, alle kwaliteitspoorten en ontbrekende indexkoersen afdwingt.
  De indexfunctie zelf ontvangt reeds beoordeelde toelating; zij bewijst die niet.
- Timeframevergelijking valideert OHLCV; het bestaande Candle-model bewaart geen
  trade-counts/taker-volumes. Volledige vergelijking daarvan vereist extra bronvelden.
- De fixture-runner toetst liquiditeit; volledige zeven-dagen-timeframeconsistentie
  moet via de data-audit worden bewezen vóór een toekomstige historische run.
- Een compleet extern inzageregister ontbreekt. 2026 is niet bewezen onaangeraakt.
  Het oude januari-2025-slot blijft behouden; het voorstel overschrijft geen oude plannen.
- De nieuwe primaire rendementsmaat en benchmarks blijven onderdeel van het nieuwe
  ontwerp; geen wijziging aan oude expectancy-selecties of onderzoeksresultaten.

Geen parameters geoptimaliseerd. €200, één positie, 0,5% gepland risico, 50% entry-
exposure, 3% dagverlies, 10% drawdown en verliesreeks/noodstop blijven behouden.
Geen echte transacties, paperbot, API-sleutels of wijzigingen aan andere bots.

## Tests

**310 tests geslaagd, 0 mislukt**: 287 bestaande plus 23 nieuwe.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. Tests omvatten perioden,
slots, trailing liquiditeit, toekomstige volumes, datagaten, manifestmutaties,
indexkosten, indexafwijzingen, langere multi-coininvoer, heropening en deduplicatie.
Geen historische rendementsevaluatie; geen onafhankelijke testinzage.
