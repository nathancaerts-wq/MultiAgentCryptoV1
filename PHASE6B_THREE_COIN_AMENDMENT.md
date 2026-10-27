# Fase 6B — afzonderlijke hypothetische drie-muntenstudie

Datum 27 oktober 2026. Basis b55aa218f66b3facd6d980032fea495f9701bf80.
Versie phase6b-three-coin-v1. Vooraf vastgelegd vóór enige nieuwe rendementsevaluatie.
De laatste gebruikersopdracht geeft voorwaardelijke toestemming: uitsluitend uitvoeren
als alle essentiële technische controles slagen. Een mislukte controle betekent stoppen.
De oorspronkelijke zesmuntenstrategie en haar registraties worden niet vervangen.

## Universum en selectie

Uitsluitend BTCEUR, ETHEUR, SOLEUR, alfabetisch. Geselecteerd op de eerder vastgelegde
volledige datakwaliteit, niet op rendementsuitkomsten. Selectie op achteraf bekende
corpuskwaliteit is zelf selectie met kennis van de toekomst. Daarom een afzonderlijk
hypothetisch onderzoek, geen reconstructie van een destijds prospectief gekozen universum.
Geen conclusies over de oorspronkelijke zesmuntenstrategie of alle EUR-markten.

## Perioden en voorwaarden

Halfopen UTC: ontwikkeling [2024-01-01 00:00,2025-01-01 00:00), validatie
[2025-02-01 00:00,2025-12-31 20:00). Ontwikkelwarm-up [2024-01-01,2024-01-08),
geen instap. Validatiewarm-up [2025-01-25,2025-02-01), uitsluitend kenmerken.
Januari 2025 blijft quarantaine met deze warm-upuitzondering. Het oude testslot
[2025-01-15,2025-01-16) blijft geheel gesloten. Embargo [2025-12-31 20:00,2026-01-01).
Geen marktdata vanaf 2026-01-01 lezen, ook niet voor rapporthashes of benchmarkwaardering.
Een datumgrens in een manifest is geen toegang tot de achterliggende marktdata.

De validatieperiode is door eerdere historische kwaliteitsinzage en onvolledig extern
inzageregister niet noodzakelijk volledig onafhankelijk. Voor iedere deelperiode en
elk vooraf vastgelegd scenario eenmaal €200 totaal; nooit €200 per coin. Geen
herkapitalisatie, cash- of pauzereset binnen een run.

## Hypothetische filters (aannames, geen historische Binance-feiten)

Voor alle drie coins gelijk: PRICE_FILTER tick €0,01, min_price 0, max_price niet
opgelegd; LOT_SIZE min_qty/step 0,00001 coin, max_qty 1.000.000 coin;
MARKET_LOT_SIZE dezelfde grenzen/stap; MIN_NOTIONAL €10 ook voor marktorders;
NOTIONAL min €10, geen aanvullende maximale notional; avg_price_mins=0.
status=assumed, bron assumption:phase6b-three-coin-v1. known_at/valid_from/valid_until
blijven leeg: er wordt geen historische verificatie gesuggereerd. Andere niet-
gereconstrueerde Binance-filters worden niet als getoetst gepresenteerd.

Tick/stap/minimumnotional volgen het eerder voorgestelde hypothetische model.
Minimum €10 blokkeert kleine orders; ongunstige tickafronding voorkomt voordelige
fictieve afronding. De ruime maximale quantity is slechts een expliciete modelgrens;
€200 cash, 50% exposure en 0,5% risico begrenzen feitelijke voorstellen veel strenger.
Deze aannames zijn niet gegarandeerd conservatiever dan alle echte historische
filters en bewijzen geen historische orderuitvoerbaarheid. Verkoopfilters kunnen
kleine restposities blokkeren; een onvoltooide run blijft onvolledig.
Geen aanpassing na inzage. Deze documentatie activeert geen nieuwe orderroute.

## Strategie, risico, tijd en kosten

Alleen aligned_trend; alle bestaande analyse-, Decision-, Entry-, Exit-, Risk-,
fill- en ledgerregels blijven gelden. EMA9/21, RSI14, ATR14, momentum10, structuur5,
sideways0,002, 32 gesloten candles per timeframe. Stop 2 ATR, horizon 4h, geen target.
Volgende-candle-open; geen informatie uit toekomstige high/low/close bij instap.
Laatste entry uiterlijk einde−4h15m. Eén positie; geen entry in een exitbatch.
Risico maximaal 0,5% van min(€200,cash) inclusief kosten; entry-exposure maximaal
50%; dagverlies3%, drawdown10%, verliesreeks3 en noodstop blijven gelden.
Trailing toelating: zeven volledige dagen, €100.000 quotevolume/24h en
€10.000/laatste15m. Exacte timeframeconsistentie blijft vereist.

Scannerformule/gewichten gelijk; rang dalend. Tie-rotatie volgt de bestaande
formule met deze drie coins: floor(UTC_epoch/900) modulo 3. Relatieve scores en
prioriteiten verschillen daardoor van de zesmuntenstudie; dat is onderdeel van
de expliciete universumamendering, geen parameteroptimalisatie.

| Scenario | Fee per zijde | Volledige spread | Slippage per zijde |
|---|---:|---:|---:|
| Baseline | 0,1% | 0,1% | 0,1% |
| Slippage-stress | 0,1% | 0,1% | 0,2% |
| Alles dubbel | 0,2% | 0,2% | 0,2% |

Dit vervangt voor deze studie de eerdere suggestie uitsluitend 0,2% te gebruiken,
conform de huidige gebruikersopdracht. Positiegrootte en risicopauzes worden per
scenario opnieuw berekend; nooit het beste scenario kiezen. Daarnaast de vooraf
vastgelegde afzonderlijke rekenkundige verwijdering van maximaal drie grootste
netto-winnaars/verliezers; geen hersimulatie of claim van haalbaar tegenfeitelijk rendement.

## Benchmarks en metingen

Cash €200 zonder rente. Buy-and-hold als analytische marktindex van deze drie coins,
ieder €200/3, restcash behouden; eenmalige instap op 2024-01-08 respectievelijk
2025-02-01. Ongeschikte component blijft cash, geen vervanging/herweging. Dezelfde
kosten, fractionele indexprecisie en terminale waardering als het oorspronkelijke
voorstel; index heeft mogelijk 100% exposure en drie componenten zonder stop.
Dit is de expliciete drie-muntenaanpassing op de oude zesdelige index, geen wijziging
aan de oorspronkelijke indexfunctie. EMA-benchmark: dezelfde drie coins, 1h-gap
EMA9/EMA21−1>0,002; hoogste gap eerst, dezelfde tie-rotatie, risico/entry/exitregels.

Primair netto portefeuillerendement na kosten; alle maten, per-coinbijdragen,
periode-uitkomsten, afwijzingen en onzekerheid volgens §8 van het oorspronkelijke
voorstel. Alle benchmark- en stressresultaten rapporteren. Minder dan 30 trades:
onvoldoende bewijs. Ook meer trades bewijzen geen statistische superioriteit.

## Vooraf vastgelegde technische toegangspoort

Volledige bronkwaliteit en hashes moeten overeenkomen; volledig synthetisch jaar
moet aflopen, twee volledige uitvoeringen/herstart moeten dezelfde economische
ledger/uitkomsten geven. De gehele agentketen, risicopauzes, toekomstinformatie-
afscherming en gesloten testtoegang moeten worden gecontroleerd. Een begrensde
jaarproef zonder rapporten is slechts een noodzakelijke ondergrens, geen voldoende
bewijs voor deze complete keten. Gebruik voor de eerste capaciteitsscreening dezelfde
45 seconden/1,5 GB als het bestaande meetprotocol. Timeout, incomplete replay of
fout is een mislukte controle; geen verlenging gekozen op rendementen.

Pas als alle controles slagen: één ontwikkelstudie met de vaste scenario's/benchmarks.
Daarna validatie uitsluitend bij volledige gegevens, reconciliërende cash/posities/
fees, nul dubbele fills, geldige chronologie en volledige audit. Een lage of negatieve
winst is geen reden om validatie over te slaan; technische inconsistentie wel.
Geen parameterwijziging tussen D en V. Voor inzage duurzaam stage, dataversies,
configuratiehash en autorisatiereferentie registreren. Geen automatische strategiepromotie.
