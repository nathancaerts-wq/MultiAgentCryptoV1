# Fase 6H-B — metadata-preflight geblokkeerd, geen backtest uitgevoerd

Basiscommit: `c4edd8c50bafa2c01efde5cdce932a3e0b944e42`.
**Status: niet uitgevoerd.** Dit is een preflight-/blokkeringsrapport; geen
voltooide adapter, nieuwe financiële jaarproef of historische vergelijking.

## Scope van de opdracht en toegepaste stopregel

De gebruiker autoriseert uitsluitend aligned_trend met permanente pauze versus
24u-herstel op bestaande BTC/EUR-, ETH/EUR- en SOL/EUR-ontwikkeling 2024. Geen
ATR-kostenstrategie, extra variant, downloads, validatie 2025 of test 2026.
Dezelfde opdracht schrijft expliciet voor:

> Stop onmiddellijk bij een financiële inconsistentie of ontbrekende historische metadata.

De huidige broncode en bestaande registraties bewijzen exacte historische
Binance-orderfilters niet. `crypto/january_pilot.py::filters()` levert voor ieder
paar `status='assumed'` met de notitie `Hypothetical; historical Binance filters
unproven`. `known_at`, `valid_from` en `valid_until` zijn alle null. De drie munten
hebben dus wel een volledig hypothetisch filterobject, maar geen bewezen
historische filtergeldigheid voor de onderzoeksperiode.

| Paar | Filterstatus | known_at | valid_from / valid_until | Historisch bewezen |
|---|---|---|---|---|
| BTC/EUR | assumed | ontbreekt | ontbreken | nee |
| ETH/EUR | assumed | ontbreekt | ontbreken | nee |
| SOL/EUR | assumed | ontbreekt | ontbreken | nee |

De eerdere jaarbaseline en het fase-6G-plan stonden expliciet hypothetische filters
toe. De nieuwe stopregel vereist hier een keuze: betekent ontbrekende historische
metadata ook deze reeds gedocumenteerde onbewezen orderfilters, of mogen de oude
hypothetische aannames expliciet blijven gelden? Er is niet stilzwijgend gekozen
voor een uitzondering. Uitvoering is vóór adapterbouw/replay gestopt; de bestaande
synthetische variant blijft intact. Geen actuele filters als historische feiten
gebruikt en geen nieuwe metadata gedownload.

De aanwezige aannames zijn tick €0,01; min_qty/step en marktorder-minimum/stap
0,00001; max_qty en marktordermaximum 1.000.000; minimum notional €10. Deze
waarden zijn alleen bronbewijs voor het bestaande hypothetische model, niet
nieuwe of historisch geverifieerde beursvoorwaarden. Het volledige bestaande
object staat in het preflightmanifest. Geen parameter is gewijzigd.

## Registratie en integriteit

Git-status was schoon, HEAD was de opgegeven commit. Fase-6G-documenten en het
fase-6H-A-rapport zijn gelezen; hun oude statusvelden worden niet overschreven.
De huidige goedkeuring is geregistreerd met haar datum-/coin-/variantgrenzen en
de metadata-stopvoorwaarde. Het inhoudsgebonden preflightmanifest onder
`experiments/phase6h_b/manifest_<sha256>.json` bindt de bestaande gevolgde bestanden,
configuratiebronnen, filterobjecten, databasehash en reeds opgeslagen baseline.
`registration.json` geeft de exacte manifestnaam en SHA-256. De uitvoeringstoestand
is `blocked_before_adapter_and_replay` en `execution_permitted=false`.

Het manifestbestand is read-only en inhoudsgebonden. Dit is geen extern
onveranderlijke WORM-opslag en geen claim dat een volledig uitvoeringsmanifest
voor een nog niet gebouwde adapter bestaat. Na een eventuele expliciete keuze
zijn definitieve adaptercode, inputseals en aanvullende deterministische tests
nog verplicht vóór historische uitvoering.

De volledige oorspronkelijke financiële/auditdatabase is uitsluitend streamend
als bytes gelezen, niet geopend voor nieuwe SQL-analyse of replay:
`/workspace/development_2024.sqlite3`, verwachte SHA-256
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.
Exacte verificatie-uitkomst, aantal oude bestanden, tijd en geheugen staan in
`preflight.json`. De bestaande checkpointketen is niet aangepast. Dit herhaalt een
integriteitscontrole, niet een nieuwe inhoudelijke herberekening van de baseline.

## Variant A — uitsluitend reeds opgeslagen baseline

Overgenomen uit `experiments/development_2024/aligned_trend_baseline.json`.
Geen nieuwe baseline-run en geen nieuwe berekening van ontbrekende metrics.

| Maat | Bestaande opgeslagen waarde |
|---|---:|
| Oorspronkelijk kapitaal | €200 |
| Eindkapitaal | €197,03206319 |
| Nettoresultaat | −€2,96793681 |
| Netto portefeuillerendement | −1,483968405% |
| Gesloten trades / fills | 3 / 6 |
| Winstpercentage | 0% |
| Geboekte fees | €0,18502791 |
| Maximale drawdown op close-grid | 1,483968405% |
| Aanvullende conservatieve candle-drawdown | 1,509320075% |
| BUY-kandidaatsignalen | 1.953 |
| Goedgekeurde entries | 7 |
| Geweigerde BUY-voorstellen | 1.946 |
| Geweigerde uitvoeringen | 4 |
| Verliesreekspauze | Eén, vervolgens permanent binnen de oude run |
| Expliciete verliesreekspauze-afwijzingen | 793 coinbeoordelingen |

Alle vier uitvoeringsweigeringen hebben de opgeslagen reden:
`ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging`.
De drie trades betroffen twee ETH/EUR- en één SOL/EUR-trade; BTC/EUR had geen fill.
Het opgeslagen baseline-eindcheckpoint is flat, zonder pending of reserveringen.

De fees hierboven zijn geen optelling van alle economische frictie: spread,
slippage en tickafronding zijn al in de gesimuleerde prijzen verwerkt. De oude
trade-records bewaren die componenten afzonderlijk; er is nu geen nieuwe som
berekend. Er zijn ook positie-/liquiditeitsafwijzingen in de opgeslagen baseline;
geen nieuwe dagverlies-/drawdowntrigger of onbekende blokkering is als nul ingevuld.
Zie de oorspronkelijke redenverdeling voor de volledige oude diagnostiek.

De derde verliesafrekening is geregistreerd op 11 januari 2024 16:00 UTC.
Het eerste oorspronkelijke beslismoment dat deze afrekening kende was 16:15 UTC,
zoals fase 6E v4 documenteert. Een 24u-afkoelingstotaal voor de permanente baseline
is niet van toepassing; de bestaande permanente pauzeduur is niet opnieuw
berekend. Geen nieuwe metric wordt op basis van een onjuiste tijdsvolgorde ingevuld.

## Variant B — niet uitgevoerd

Alle financiële uitkomstvelden, kandidaat-/goedkeurings-/fillaantallen,
uitvoeringsweigeringen, risicotriggeraantallen en afkoelingsduur zijn **null /
niet berekend**, niet nul. Er is geen nieuwe portefeuille, historische fill of
recovery-checkpoint aangemaakt. Er is dus geen A-versus-B-resultaat of uitspraak
over het effect van 24 uur wachten.

De historische adapter en zijn nieuwe integratietests zijn niet gebouwd omdat
de essentiële metadata-gate vóór die werkzaamheden faalde. De bestaande fase-6H-A-
variant en haar 30 synthetische tests blijven ongewijzigd beschikbaar. Er is geen
synthetische broncontrole omzeild en geen oude database als schrijfdoel gebruikt.

## Tests, limieten en veilige afsluiting

Alle **527 bestaande automatische tests slagen**, 0 mislukt, één bestaande
Starlette/AnyIO-deprecationwaarschuwing; 17,78 s. Uitvoer: `tests.txt`.
Geen nieuwe interface geïmplementeerd en daarom geen nieuwe spiegeltests toegevoegd.
De suite gebruikt bestaande bekende fixtures; dit is geen nieuwe historische
validatieanalyse. Alle bestaande bronbestanden en testbestanden blijven behouden.

Tests: harde limiet 180 s en 1,5 GiB adresruimte. Preflight/hashcontrole: 180 s en
1 GiB, streamend in blokken van 1 MiB. De eerder voorziene replaylimieten blijven
1.800 s, 1,5 GiB adresruimte, RSS-stop 1.288.490.188 bytes, 2 GiB vrije schijf,
netwerkbudget nul; er is geen replay gestart en geen budget verruimd.

De bron-/bytecontroles en suite slagen, maar de vereiste historische metadata-
controle niet. Daarom wordt dit rapport niet als voltooide vergelijking beschouwd.
Conform 'commit en push uitsluitend na geslaagde controles' blijven deze nieuwe
preflight-/rapportbestanden lokaal behouden: **geen nieuwe commit of push**.
De bot, actieve Risk Engine, strategieën, risico's en oorspronkelijke auditdatabase
zijn ongewijzigd. Geen echte of automatische paper-orders.

## Benodigde beslissing en beperkingen voor hervatting

Voor hervatting is expliciete toestemming nodig om óók in fase 6H-B exact het
bestaande hypothetische filtermodel te gebruiken, ondanks onbewezen historische
filtermetadata. Het resultaat zou dan uitsluitend hypothetische orderuitvoering
beschrijven. Als de stopregel bewezen historische filters vereist, blijft de
vergelijking geblokkeerd totdat betrouwbare tijdgebonden filtermetadata beschikbaar
is; deze opdracht staat geen nieuwe downloads toe.

Na die keuze zijn de geïsoleerde historische/streaming-adapter, financiële
fixturegelijkheid, checkpoint/crashtests, inputseal en volledige pre-execution-
registratie nog te realiseren. De baseline mag alleen worden hergebruikt na
compatibiliteitscontrole van de nieuwe meetdefinities. Geen ATR-experiment of
andere variant toevoegen. 2024 is reeds onderzocht en geen onafhankelijke
validatie; drie baselinetrades zijn onvoldoende statistisch bewijs. Validatie
2025 en onafhankelijke test 2026 blijven gesloten.
