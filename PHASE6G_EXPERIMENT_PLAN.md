# Fase 6G — afzonderlijk experimentplan A, B en voorwaardelijk C

Plan-ID: `phase6g-design-v1`. Status: **uitsluitend onderzoeksvoorbereiding**.
Basiscommit: `fed7ec29f13d0fe3742f811399a19a19ab5ac4c8`.
Samen lezen met `PHASE6G_RISK_RECOVERY_PROTOCOL.md` en
`PHASE6G_ATR_COST_PROTOCOL.md`. Geen experiment of variant is nu geautoriseerd
voor implementatie, synthetische varianttests of historische uitvoering.

## 1. Basis, herkomst en omvang van toestemming

HEAD en GitHub main stonden bij aanvang op de opgegeven commit; de werkmap was
schoon. Fase 6F, RESEARCH_PROTOCOL.md en de relevante indicator-, decision-,
ledger-, uitvoerings- en ontwikkelcode zijn gelezen. De drie fase-6F-voorstellen
per richting worden niet herschreven. Alleen herstel na 24 uur en S2 ATR/kosten
worden hier verder gespecificeerd.

Belangrijk verschil: A vervangt het 6F-proefmodel door herhaalbare 24u-cycli met
een expliciete epoch/tellerreset. B behoudt de vaste 6F-S2-kostenproxy en drempel,
met een exacte ratio en rekenvolgorde. Deze nieuwe ontwerpversies zijn geen
stilzwijgende activatie van 6F of wijziging van de actieve Risk Engine.

De fase-6F-registratie en fase-6E-eindartefacthashes worden geverifieerd. De oude
377 gevolgde bestanden krijgen een SHA-256-nulmeting en afsluitvergelijking.
De bestaande financiële/auditdatabase wordt uitsluitend als bytes gehasht:
`/workspace/development_2024.sqlite3`, SHA-256
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.
Een lege WAL en dezelfde hash bevestigen behoud van de bestaande database;
dit is geen nieuwe inhoudelijke audit of historische uitkomstberekening.

Bronbewijs staat in `experiments/phase6g/baseline.json` en `verification.json`.
`registration.json` bindt de drie protocoldocumenten en controlebewijzen met hashes,
verwijst naar de expliciete opdracht voor onderzoeksvoorbereiding en vermeldt
`implementation_authorized=false`, `execution_authorized=false`.
Git/SHA-256 maakt wijzigingen controleerbaar, niet fysiek onmogelijk. Er wordt
geen onveranderlijke externe preregistratie of toestemming voor toekomstige runs
geclaimd. De oude registraties, resultaten en auditlogs blijven byte-identiek.

## 2. Voorgestelde gemeenschappelijke onderzoeksgegevens

Voor eventuele afzonderlijk goedgekeurde historische experimenten, exact:

- BTC/EUR, ETH/EUR, SOL/EUR; geen uitbreiding, nieuwe liquiditeitsdrempel of
  selectie op gerealiseerd rendement. Bestaande historische datakwaliteit/toelating.
- Ontwikkeling [2024-01-01 00:00, 2025-01-01 00:00) UTC. Alleen 2024-candles.
- Warm-up 1–7 januari. Eerste mogelijke beslissing/entry 8 januari 00:00 UTC;
  laatste toegestane entrygrens 31 december 19:45 UTC, volgens de bestaande
  jaarregistratie met vier uur plus één kwartier eindmarge. Geen extra late entry.
- Alleen afgesloten officiële Binance Spot-candles, gevalideerde checksums,
  aaneengesloten 15m/1h/4h en dezelfde causale 32-candle-indicatorvensters.
  Als de benodigde volledige bron ontbreekt: onvolledig en stoppen, geen
  interpolation, synthetisch prijsherstel of opportunistisch schrappen van een coin.
- De waardering op de exclusieve eindgrens gebruikt uitsluitend de laatste
  afgesloten 2024-candle en bestaande eindafhandeling, geen open van 2025.
- Onvolledige bron-/berichtenbundel of onverwachte positie buiten de eindhorizon
  blokkeert een definitief jaarresultaat. Geen nieuw liquidatiebeleid toevoegen.

2024 is al gebruikt voor backtests, beschrijving en ontwerp. Ook een bevroren
herhaling levert daarom uitsluitend exploratief bewijs, geen onafhankelijke
bevestiging. Opsplitsen of hernoemen herstelt de onafhankelijkheid niet. Validatie
2025 en onafhankelijke test 2026 blijven volledig gesloten. De oude suite bevat
bekende technische fixtures met 2025-datums; die herhalen is geen nieuwe studie
van de validatieperiode. Er wordt in deze fase geen marktarchief gedownload.

De bekende fase-6E-CSV-kolomfout blijft gedocumenteerd en ongewijzigd. Geen future
reader mag die export stilzwijgend als correcte input behandelen. Bestaande
provenance-gebonden candles/berichten, niet forwardlabels of die CSV, moeten later
beslissingen aansturen. Geen nieuwe prijslabels of patrooncontrasten in fase 6G.

## 3. Armen en vergelijking zonder vermenging

| Vergelijking | Referentie | Variant | Enige inhoudelijke afwijking |
|---|---|---|---|
| A | B0: bestaande aligned_trend | RA: aligned_trend + protocol A | Verliesreekspauze met 24u-timer/epochreset |
| B | B0: bestaande aligned_trend | AB: aligned_trend + protocol B | ATR/kostenfilter; permanente verliesreekspauze behouden |
| C, later afzonderlijk goedkeuren | B0, RA en AB als vaste referenties | RC: aligned_trend + beide | Beide reeds bevroren wijzigingen, geen nieuwe parameter |

A en B zijn losse onderzoeken; B krijgt nooit de herstelstatus van A. Geen
historische selectie van de beste A/B-parameter en geen conditionele C-activatie
omdat een rendement gunstig lijkt. Voor C moet vooraf een nieuwe toestemming en
registratie bestaan. Later zouden RC−B0, RC−RA en RC−AB afzonderlijk worden
beschreven; een interactie is niet hetzelfde als optellen van de losse winsten.
De primaire vraag per toegestane vergelijking is het verschil in netto
portefeuillerendement tegenover B0; de risico- en kostenmaten hieronder blijven
altijd zichtbaar en worden niet weggeselecteerd.

Iedere arm heeft een afzonderlijke run-ID en geïsoleerde onderzoeksledger met
één oorspronkelijke €200-startbalans voor alle drie coins samen. Dat zijn geen
extra portefeuilles per coin of bij elke hervatting. Er worden geen uitkomsten
van armen bij elkaar opgeteld. Iedere arm heeft daarna zijn eigen chronologisch
ontstane cash, posities en risicoblokkeringen; die mogen door verschillende
trades uiteenlopen. Geen resets naar de toestand van de beter presterende arm.

Dezelfde dataset-/bronbundelhash, kalendergrenzen, indicatorparameters, orderfilter-
aannames, kostenscenario, ranking en uitvoeringsregels zijn verplicht voor ieder
paar. Oude B0-resultaten kunnen later alleen worden hergebruikt als manifest,
terminal cutoff, bronbundel, code en meetdefinities exact aantoonbaar compatibel
zijn. Anders is eerst toestemming voor een nieuwe B0-referentierun vereist; nu
wordt geen baseline opnieuw uitgevoerd of herberekend.

## 4. Bevroren gemeenschappelijke regels

| Onderdeel | Voorgestelde vaste regel voor alle armen |
|---|---|
| Strategie | Bestaande aligned_trend en alle gevalideerde analyse-/conflictveto's |
| Indicatoren | EMA9/21, RSI14, ATR14, bestaande structuur/momentum/sideways; 32-candlevensters |
| Selectie | Bestaande scannerscore dalend en UTC-kwartierrotatie bij gelijke scores |
| Portefeuille | €200 oorspronkelijk, één gezamenlijke positie maximaal, geen leverage |
| Trade-risico | Hoogstens 0,5%, inclusief kosten, met bestaande min(200,cash)-budget en alle strengere controles |
| Exposure | Hoogstens 50% bij entry, volgens bestaande cash-/equitycontrole |
| Beveiliging | Dagverlies 3%, drawdown 10%, noodstop; geen verhoging of reset door variant |
| Stop/exit | 2 × oorspronkelijke 1h-ATR, horizon 4h, geen winsttarget; bestaande conservatieve gap-/stopafhandeling |
| Instap | Open N+1 na gesloten signaalcandle; actuele cashreservering/risico opnieuw controleren |
| Kosten baseline | Fee 0,1% per zijde, volledige spread 0,1%, slippage 0,1% per zijde |
| Afronding | Bestaande Decimal-precisie, nadelige tickafronding, fees omhoog op 1e-8 EUR |
| Filters | Bestaande expliciete hypothetische historische filters; geen actuele filters als historisch bewijs |

De exacte kosten- en filterobjecten moeten vóór toekomstige uitvoering in het
runmanifest staan met alle waarden en hashes; een alleen tekstueel label volstaat
niet. Geen opnieuw gekozen filters om kleine ATR-proeforders uitvoerbaar te maken.
Bestaande historische uitvoerbaarheid is niet bewezen. Sizing, stop en fills
blijven van de nieuwe ATR-kostenproxy gescheiden.

De toekomstige primaire A/B-vergelijkingen gebruiken uitsluitend baselinekosten.
Optionele aanvullende kostenscenario's vereisen expliciete goedkeuring vóór
uitkomsten: bestaande slippage_stress (alleen slippage 0,2%) en double_costs
(fee/spread/slippage alle 0,2%). De filtergrens/c0 blijft baseline. Geen nieuw
kostenscenario op basis van het gevonden rendement, geen automatische extra run.

## 5. Exacte uitkomstmaten vóór enige berekening

Meetinterval voor portefeuille-/tijdmaten: [8 januari 00:00, 1 januari 2025 00:00)
UTC. Warm-up telt niet mee. `E(t)` is de bestaande liquidation_equity op ieder
volledig verwerkt 15m-waarderingsmoment, inclusief cash en netto hypothetische
liquidatiewaarde van eventuele positie volgens dezelfde FillCosts. Geen extra
fee van de werkelijke ledger aftrekken voor deze waardering. Eindpositie behoort
volgens de bestaande horizon flat te zijn; zo niet geen geldig eindresultaat.

| Maat | Definitie en behandeling van lege gevallen |
|---|---|
| Nettoresultaat | E(eind) − 200 EUR; inclusief alle werkelijk geboekte simulatorkosten |
| Netto portefeuillerendement, primair | 100 × (E(eind)/200 − 1); verschil variant−B0 in procentpunten |
| Trades | Aantal uniek definitief gesloten roundtrips; entries, exits, voorstellen en afwijzingen apart tellen |
| Maximale drawdown | 100 × max_t[(max(200, E(u) voor u<=t) − E(t))/max(200, E(u) voor u<=t)]; vaste close-grid |
| Kosten | Som geboekte fees; daarnaast spread-, slippage- en tickcomponenten uit fills, elk eenmaal; niet nogmaals van nettoresultaat aftrekken |
| Risicoblokkeringen | Aantal unieke voorstel/coin/t/stage-afwijzingen per exacte reden; entry- en execution-stage apart, plus unieke UTC-momenten met >=1 blokkering |
| Tijd zonder actieve positie | Duur binnen meetinterval met position=None, en percentage van volledige interval; open op filltijd tot geregistreerde close-tijd; geen intrabarvolgorde verzinnen |
| Reserveringen/pauzes | Pending/reserveringsduur apart (flat is niet automatisch vrij beschikbaar); unieke portefeuilletijd in iedere pauze apart, doorsnedes niet optellen |
| Herstelcycli | Unieke trigger, expiry, eerste latere fill, aantal nieuwe verliezen, volgende trigger; onvoltooide cyclus expliciet aangeven |
| Per coin/per maand | Geboekte trade-netto/fees en unieke aantallen per coin; maandresultaat via dezelfde E-grenzen zonder cashreset; geen drie startkapitalen |

De bestaande Risk Engine kan ook op eerdere uitvoerings-/observatiemomenten
blokkeren; die echte veto's blijven bepalend. Bovenstaande close-grid-drawdown is
een vergelijkbare rapportmaat en vervangt geen risicocontrole. Een bestaande
worst-candle-diagnose kan alleen aanvullend onder een duidelijk ander label worden
getoond, niet stilzwijgend met de primaire maat verwisseld.

Intrabar-stopuitvoering blijft OHLCV-benadering; sluitingstijd is een geregistreerd
tijdstip. Bij nul trades: trades=0, fees conform ledger, flatduur meetbaar, maar
winrate/expectancy/profit factor niet als positieve prestatie invullen. Een
technisch onvolledige run krijgt geen definitief jaarresultaat of verzonnen nul.
Onder 30 trades: onvoldoende bewijs; boven 30 blijft afhankelijkheid een probleem.
Geen p-waarden, significantie, causaliteit, automatische promotie of onafhankelijke
winstclaim op deze opnieuw bekeken ontwikkeling. Alle vooraf gekozen armen en
mislukte/lege uitkomsten moeten zichtbaar blijven.

## 6. Stopvoorwaarden, limieten en hervatting

Economische beveiligingen worden niet met technische stops verward. Dagverlies,
drawdown, noodstop en verliesreekspauze verbieden entries volgens de betreffende
arm. Veilige exits en waardering kunnen chronologisch doorgaan, zodat perioden
met geblokkeerde handel niet uit het rendement verdwijnen. Geen winstdoel voor
de gehele studie of stop zodra een aantrekkelijk resultaat wordt bereikt.

Technisch stoppen bij bron-/manifestmismatch, ontbrekende candle, auditbreuk,
negatieve cash, onverklaarde positie, dubbele fill, niet-causale informatie,
ongeautoriseerde datum/coin of inconsistent herstelstate. Checkpoint bevat laatste
volledig gecommitteerde candle, ledger, pending/reservaties, alle risicostatus,
A-epoch/timer/closecursor indien van toepassing, auditanker en input-/beleidshashes.
Geen gedeeltelijke commit, geen automatische herstart vanaf €200.

Voorstel voor later geautoriseerde limieten, in lijn met bestaande begrensde
jaaronderzoeken: maximaal 1.800 s per voorbereiding en per afzonderlijke replay,
1,5 GiB adresruimte, vroege stop bij 1.288.490.188 bytes RSS (circa 1,2 GiB)
en minimaal 2 GiB vrije schijf. Netwerkbudget 0: uitsluitend gevalideerde cache.
Synthetische technische varianttests: 180 s en 1,5 GiB per proces. Limiet bereikt:
controleerbaar checkpoint/onvolledig rapport, geen automatisch ruimere limiet,
parallelle tweede run of herstart. Een latere toestemming moet ook het aantal
armen/runs omvatten. Deze budgetten zijn geen capaciteitsclaim voor herstelcycli.

Voor de huidige documentfase: suite maximaal 180 s/1,5 GiB; elke streaming
integriteitscontrole maximaal 180 s/1 GiB. Geen jaarprobe, geen historische replay.

## 7. Volgorde en open goedkeuringen

1. Inhoudelijke goedkeuring van de exacte A-epoch-/netto-nulsemantiek en B-proxy/
   ratio/grens, inclusief de expliciete afwijking van 6F's één-proefmodel.
2. Afzonderlijke toestemming voor geïsoleerde implementatie en synthetische
   varianttests. Eerst B (kleine extra filter), daarna A (persistente financiële
   toestandsovergangen). Bewijs baselinebehoud en risicovoorrang vóór historische
   toestemming. Geen uitkomsten gebruiken om de goedgekeurde grenzen aan te passen.
3. Afzonderlijke toestemming en preregistratie voor toekomstige vergelijking B,
   daarna A, op de vastgelegde 2024-bronnen. Deze volgorde kiest technische
   eenvoud, niet historisch rendement. Alle ontbrekende uitvoeringsmanifestvelden
   moeten vóór inzage gevuld en gecontroleerd zijn: definitieve implementatiehash,
   inputs/filters, kosten, arm-ID, bronseal, limieten en toestemming. De huidige
   ontwerpen alleen zijn geen volledig uitvoeringsmanifest.
4. C uitsluitend na nieuwe afzonderlijke goedkeuring, eigen registratie en alle
   technische controles. Geen automatische combinatie, parameterzoektocht of
   promotie. Onafhankelijke bevestiging vraagt later een werkelijk nieuwe,
   expliciet vrijgegeven dataset; dit plan opent noch 2025 noch 2026.

## 8. Huidige controles en oplevering

Alle **497 bestaande tests slagen**, 0 mislukt, 1 bestaande Starlette/AnyIO-
deprecationwaarschuwing, 20,88 s. Bewijs: `experiments/phase6g/tests.txt`.
Geen nieuwe interface of machine-uitvoerbaar protocol geïmplementeerd; geen
nieuwe spiegeltests voor proza toegevoegd. Documentcontrole omvat koppelingen,
exact één A en B, uniforme risico-/kosten-/tijdregels en expliciete activatieverboden.

Nulmeting van oude bestanden/database: 48,11 s, 12,20 MiB piek-RSS; afsluitcontrole
met exacte tijden in `verification.json`. Alle oorspronkelijke bestanden blijven
byte-identiek; nieuwe toevoegingen zijn de drie protocollen en controlebewijs.
Geen nieuwe rendementen, labels, patroonvergelijkingen, orders of risicoresets.
Stop na succesvolle commit/push en wacht op expliciete goedkeuring.
