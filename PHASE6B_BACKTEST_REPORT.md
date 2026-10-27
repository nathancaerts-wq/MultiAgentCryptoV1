# Fase 6B — drie-muntenonderzoek gestopt vóór historische uitvoering

27 oktober 2026. Basiscommit b55aa218f66b3facd6d980032fea495f9701bf80.
**Geen historische rendementsbacktest gestart.** De gebruikersopdracht verleent
voorwaardelijke toestemming en schrijft voor bij een mislukte essentiële controle
te stoppen. De verplichte synthetische jaarcontrole is niet geslaagd.

## Vooraf vastgelegd

PHASE6B_THREE_COIN_AMENDMENT.md beschrijft een afzonderlijke hypothetische studie
voor BTC/EUR, ETH/EUR en SOL/EUR. Selectie is gebaseerd op de eerdere datakwaliteits-
audit, niet op rendement. Selectie op achteraf bekende corpuskwaliteit blijft een
bias. De zesmuntenstrategie en bestaande registraties zijn ongewijzigd.

Alleen aligned_trend. Eén €200-ledger, één positie, maximaal 0,5% gepland risico,
50% entry-exposure, 3% dagverlies, 10% drawdown, verliesreeks3/noodstop. Periode D:
[2024-01-01,2025-01-01); V: [2025-02-01,2025-12-31 20:00), UTC. Warm-up, oude
januari-quarantaine, testslot en embargo blijven gelden. Data vanaf 2026-01-01
zijn geheel gesloten. Geen parameters geoptimaliseerd.

De amendering specificeert aangenomen prijs-/lot-/notionalfilters. Deze zijn geen
historische Binance-feiten en niet automatisch als bewezen metadata geactiveerd.
Baseline fee/spread/slippage 0,1%; de vooraf vastgelegde stressscenario's blijven
slippage 0,2% en afzonderlijk alle kosten 0,2%. Cash, drieledig gelijkgewogen
buy-and-hold en EMA zijn beschreven; geen benchmarkresultaten berekend.

## Controles en stopreden

De omgeving was aanvankelijk als unavailable gemeld, maar kwam beschikbaar. De
repository stond schoon op de juiste commit. Het bestaande final_manifest en alle
daarin geregistreerde bestandshashes zijn gecontroleerd en geldig. Het afzonderlijke
manifest_before_checks.json bindt amendering, uitvoeringscode en bron-auditrecords
vóór de controles. Ook na het stoppen kloppen de hashes. Dit is een snapshot op
beschrijfbare opslag, geen garantie van onveranderlijkheid. Het manifest verleent
geen onvoorwaardelijke uitvoeringsvrijgave.

| Controle | Resultaat |
|---|---|
| Bestaande audit BTC/ETH/SOL | Elk 366/366 ontwikkeldagen, 334/334 validatiedagen, 7/7 warm-updagen goedgekeurd; bewijsbestanden opnieuw op hash gecontroleerd |
| Nieuwe BTC-corpuscontrole | Alle D/V/warm-up opnieuw uit cache gevalideerd; exact gelijk aan eerder verslag |
| Nieuwe ETH-corpuscontrole | Ontwikkeling volledig opnieuw gevalideerd; overige controle afgebroken na stopvoorwaarde |
| Nieuwe SOL-corpuscontrole | Niet gestart vóór stop; oude audit blijft bewaard, niet als nieuwe controle gepresenteerd |
| Volledig synthetisch jaar | Niet geslaagd: timeout na 45 seconden, completed=false |
| Volledige jaarreproduceerbaarheid | Niet aangetoond; geen tweede volledige jaarreplay |
| Risicopauzes en toekomstinformatie | Bestaande fixturetests geslaagd; niet over een voltooide jaarreplay bewezen |
| Onafhankelijke test | Geen toegang; geen 2026-marktdata gelezen |
| Alle automatische tests | 317 geslaagd, 0 mislukt, één bestaande Starlette/AnyIO-waarschuwing |

De synthetische capaciteitsscreening gebruikte de echte FixtureJointRunner met drie
munten en 35.136 beoogde 15m-candles per munt (366 dagen), bestaande 1,5-GB-limiet
en vooraf vastgelegde 45-secondenlimiet. De laatste opgeslagen checkpointfase was
building_candles en completed_steps=0. Het subprocess is na 45 seconden gestopt;
het werkelijke moment van voortgang tussen checkpoint en afbreken is onbekend.
De geregistreerde 26.060 KiB is RSS bij die vroege checkpoint, **geen** gemeten
uiteindelijke geheugenpiek. Deze run vond tijdens de cache-audit plaats; gedeelde
CPU-belasting beperkt elke prestatievergelijking met eerdere metingen. Timeout
bewijst niet dat voltooien met meer middelen onmogelijk is, maar voldoet niet aan
de afgesproken verplichte controle.

De capaciteitsscreening gebruikt nog geen complete analyseberichten en is dus
slechts een noodzakelijke ondergrens. Zelfs een geslaagde screening zou een volledige
agentketen-/risico-/herstarttest niet vervangen. De bestaande runner weigert echte
historische bronnen; de volledige historische benchmarkregisseur is evenmin bewezen.
Er is geen blokkade omzeild om toch rendementen te tonen.

Na de mislukte screening is de lopende cache-audit gestopt. De afgesloten
BTC- en ETH-ontwikkelverslagen zijn bewaard; het onderbroken ETH-validatieverslag
is niet als compleet opgeslagen. halt_record.json bewaart de status per coin en
periode. Geen netwerkdownloads of externe orders uitgevoerd tijdens deze opdracht.
De gebruikte oude auditartefacten blijven onaangeroerd.

## Gevraagde prestaties

NB betekent niet berekend, niet nul trades of nul rendement. Dit geldt voor beide
perioden en alle drie coins. Er zijn geen historische signalen geëvalueerd; een
technische blokkering is geen afgewezen handelssignaal.

| Maatstaf | Ontwikkeling | Validatie |
|---|---|---|
| Trades / winrate | NB / NB | NB / NB |
| Gemiddelde winst / verlies | NB / NB | NB / NB |
| Nettoresultaat EUR / procent | NB / NB | NB / NB |
| Profit factor / verwachtingswaarde | NB / NB | NB / NB |
| Maximale drawdown / gemiddelde houdduur | NB / NB | NB / NB |
| Resultaten per BTC, ETH, SOL | Alle NB | Alle NB |
| Alle afgewezen historische signalen | NB | NB |
| Cash / buy-and-hold / EMA-vergelijking | NB | NB |
| Kostengevoeligheid / extreme winnaars-verliezers | NB | NB |

Geen conclusie over winstgevendheid of positieve verwachtingswaarde mogelijk.
Validatie is door eerdere historische inzage niet noodzakelijk onafhankelijk.
Hypothetische filters, OHLC-uitvoeringsaannames en selectie op corpuskwaliteit
zouden eventuele latere resultaten verder beperken.

## Opleveringsstatus

Amendering, meetbewijs, manifest, gedeeltelijke hercontrole en rapport staan lokaal;
PROGRESS.md en NEXT_STEPS.md zijn bijgewerkt. Geen strategie-/risico-/agentcode
gewijzigd. Geen nieuwe commit of push: de opdracht stelt dit afhankelijk van
slagen van de controles, en de essentiële jaarcontrole is mislukt. HEAD blijft
b55aa218f66b3facd6d980032fea495f9701bf80. De werkmap bevat bewust de nieuwe
voorbereidings- en rapportbestanden; zij is dus niet schoon. Geen volgende fase gestart.
