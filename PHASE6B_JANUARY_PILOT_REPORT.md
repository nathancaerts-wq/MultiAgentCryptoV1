# Fase 6B — eerste historische ontwikkelpilot januari 2024

28 oktober 2026. Basis 301f7db61e7d6b4eff93848cbf12da94e966f2d1.
Expliciete gebruikersautorisatie voor deze begrensde hypothetische pilot. Dit is
geen bewijs van daadwerkelijke historische Binance-orderuitvoerbaarheid.

## Vooraf vastgelegd

`experiments/january_pilot/protocol.json` is vóór enige rendementsevaluatie geschreven.
Alleen BTC/EUR, ETH/EUR, SOL/EUR en [2024-01-01, 2024-02-01) UTC. 1–7 januari
uitsluitend warm-up; eerste mogelijke entry 8 januari 00:00 UTC. Laatste mogelijke
entry 31 januari 19:45 UTC conform de bestaande 4h15m-eindmarge. Evaluatie/exits tot
1 februari 00:00 gebruiken uitsluitend de voorafgaande januari-candle.

Alleen de primaire aligned_trend-strategie en het baselinekostenscenario. Deze
opdracht is een afzonderlijke maandpilot, geen vrijgave van de eerdere volledige
ontwikkel-/validatiestudie. Geen benchmarks, stressruns, validatie of onafhankelijke
test uitgevoerd. Eerdere jaarcapaciteitsvoorwaarden worden niet als geslaagd gemeld.

Eén gezamenlijke €200-portefeuille, maximaal één positie, maximaal 0,5% gepland risico
inclusief kosten en maximaal 50% entry-exposure. EMA9/21, RSI14, ATR14, momentum10,
structuur5, sideways0,002, precies 32 afgesloten candles per timeframe. Stop 2 ATR,
horizon 4 uur; dagverlies3%, drawdown10%, verliesreeks3 en noodstop behouden. Geen
parameteroptimalisatie. Onbekend nieuws blijft onbekend.

Baseline: fee 0,1% per zijde, volledige spread 0,1%, slippage 0,1% per zijde.
Hypothetische filters uit PHASE6B_THREE_COIN_AMENDMENT.md: tick €0,01; min_qty en
lotstap 0,00001; max_qty 1.000.000; dezelfde marktordergrenzen; minimum notional €10,
avg_price_mins=0. status=assumed, bron assumption:phase6b-three-coin-v1. Geen actuele
filters als historische feiten gebruikt. Werkelijke OHLCV komt uit Binance;
fillprijzen, spread/slippage en orderfilters zijn simulatie/aannames.

## Datakwaliteit

De eerder opgeslagen kwaliteitsrapporten melden 31 geldige januaridagen per paar.
Alle negen benodigde maandarchieven zijn opnieuw volledig uit de bestaande cache
gelezen. Officiële eerder gedownloade CHECKSUM-bestanden zijn opnieuw tegen de
volledige ZIP-inhoud gecontroleerd vóór CSV-verwerking. Geen nieuwe netwerkdownload;
geen claim dat de huidige serverversie opnieuw is opgevraagd.

Per coin 2.976 kwartiercandles, 744 uurcandles en 186 vieruurcandles: in totaal
11.718 unieke broncandles. Alle UTC-/eenheids-/volledigheids-/volgorde-/OHLCV-controles
slagen, inclusief ontbrekende en dubbele candles. 15m→1h en 1h→4h komen exact overeen.
De bestaande decoder controleert alle twaalf klinevelden; 2024 gebruikt milliseconden.
Dagelijkse interne checksums zijn afgeleid en worden niet als officiële checksums
gepresenteerd. De originele officiële maandhashes staan in quality.json en manifest.

Dit bewijst historische candledekking en transactiedata van de EUR-paren, geen exacte
listingdatum, beursstatus of historische orderfilters. De bestaande toelating gebruikt
uitsluitend zeven voorafgaande dagen en eerdere quotevolumes. Selectie van deze drie
coins is achteraf op datakwaliteit gebaseerd; survivorship-/selectiebias blijft.
Archieven kunnen achteraf gereviseerd zijn; point-in-time bronversies zijn onbekend.
Geen data uit validatie of onafhankelijke test gebruikt.

## Uitvoering en herstel

De standaard streamingroute blijft uitsluitend voor fixtures. Een aparte
`JanuaryStore`/`JanuaryRunner` accepteert uitsluitend de negen exacte januari-URL's,
de drie coins, de vaste maandgrenzen, het bestaande beleid en de vaste filters.
Officiële data is niet als fixture hernoemd. De onderliggende beslis-, risico-,
fill-, ledger-, hash- en checkpointmethoden worden hergebruikt. De bronselectiehooks
zijn de enige wijzigingen aan de algemene streamingmodule.

Analysevoorbereiding loopt tot de laatste mogelijke entry. In de terminale 4h15m
worden geen nieuwe entryrapporten gemaakt; Exit Agent blijft iedere afgesloten bar
beoordelen. Cash, posities en pauzes lopen door. Geen geforceerde eindliquidatie
tegen een verzonnen prijs. Een resterende positie/reservering maakt de run onvolledig.

Vooraf budget: 600 seconden, harde 1,5 GiB address space, vroeg stoppen boven 1,2 GiB
RSS. Onderbouwing: circa 2.305 evaluatiegrenzen tegenover de eerdere actieve
1.000-stappenmeting van 91,4 s en lege 5.000-stappenmeting van 291,5 s. Dit is een
pilotbudget, geen wijziging van het oude 45-secondenjaarcriterium. SQLite en tijdelijke
sorteerbestanden op /workspace; niet op tmpfs. Bij onderbreking blijft de database
bewaard en rapporteert het script uitsluitend diagnostiek. Bestaande databases en
resultaten worden geweigerd bij starten; geen automatische herstart vanaf nul.

Voor de eerste beslissing legt manifest.json alle invoer-/rapporthashes, het
ResearchPlan, beleid, filters, protocol en codehashes vast. Bestanden zijn snapshots,
geen externe onveranderlijke registratie. Checkpoints staan in
`/workspace/january_pilot.sqlite3`; de grote database wordt niet in Git opgenomen.

## Resultaat — volledig afgerond

2.288 analysetijdstippen en 2.305 evaluatiegrenzen verwerkt. Het uitvoeringsvenster
bevat 6.912 unieke 15m-candles voor de drie coins; daarnaast is de volledige
januari-invoer/warm-up van 11.718 broncandles gevalideerd. Geen onderbreking/herstart.
Uitvoering inclusief voorbereiding en eindcontrole: **78,706 s**. Piek-RSS:
**70,1875 MiB** (71.872 KiB), ruim binnen het vooraf vastgelegde budget.

| Maatstaf | Uitkomst |
|---|---:|
| BUY_CANDIDATE-signalen | 127 |
| Goedgekeurde entryreserveringen | 7 |
| Afgewezen BUY-kandidaten | 120 |
| Entryreserveringen afgewezen bij fill-hercontrole | 4 |
| Succesvolle virtuele aankopen | 3 |
| Goedgekeurde en uitgevoerde exits | 3 |
| Afgesloten virtuele trades | 3 |
| Winrate | 0% |
| Nettoresultaat na alle gemodelleerde kosten | −€2,96793681 |
| Netto portefeuillerendement | −1,483968405% |
| Gemiddelde winst | Niet van toepassing: geen winnaars |
| Gemiddeld verlies | −€0,98931227 |
| Verwachtingswaarde in deze steekproef per trade | −€0,98931227 |
| Maximale conservatieve drawdown | 1,509320075% |
| Expliciete fees totaal | €0,18502791 |
| Eindwaarde / beschikbare cash | €197,03206319 |
| Open posities / reserveringen op einde | 0 / 0 |

Spread en slippage zitten al in de fillprijzen en zijn niet dubbel als fee afgetrokken.
Vier entryreserveringen (drie BTC, één ETH) zijn bij uitvoering geweigerd doordat de
ongunstige volgende open meer cash vereiste dan gereserveerd. Geen automatische
verhoging of alternatieve muntkeuze. Na drie verliestrades greep de bestaande
gezamenlijke verliesreekspauze in en bleef die behouden.

| Coin | Gesloten trades | Netto EUR |
|---|---:|---:|
| BTC/EUR | 0 | 0 |
| ETH/EUR | 2 | −1,98449225 |
| SOL/EUR | 1 | −0,98344456 |

Afwijzingen/HOLD in alle 6.915 coinbeoordelingen: 5.544 onvolledig vergelijkings-
universum/geen nieuwe instap; 1.189 uitsluitend BUY_CANDIDATE wordt beoordeeld;
120 centrale positielimiet; 49 verliesreekspauze; 6 liquiditeit_15m. Dit zijn
**6.908 niet-geselecteerde coinbeoordelingen**, niet 6.908 afgewezen orders.
Ontbrekende/conflicterende essentiële analysevoorwaarden leiden conform bestaande
regels tot HOLD, ook bij volledig aanwezige broncandles. De terminale periode heeft
bewust geen nieuwe entryrapporten. Alle redenen en afzonderlijke fillafwijzingen
staan in result.json en verification.json.

De checkpointketen is volledig gecontroleerd en opnieuw gereconstrueerd. Aanvullende
read-only verificatie: SQLite integrity_check=ok; één portefeuille; niet-negatieve
cash in alle 2.316 states; zes unieke fills; drie verklaarde trades; fees en netto
reconciliëren exact; geen open positie/reservering op einde; geen paper-orders.
Laatste revisie 2315. Databasegrootte 611.958.784 bytes; SHA-256 en laatste state-/
checkpointhash staan in verification.json. De codehashes uit het uitvoeringsmanifest
komen overeen. Er is geen rendementshersimulatie uitgevoerd voor deze controle.

**389 automatische tests geslaagd, 0 mislukt**: alle 385 behouden plus vier
pilotgrens-/bron-/aannametests. Eén bestaande Starlette/AnyIO-waarschuwing.
Slechts drie trades: onvoldoende statistisch bewijs; dit negatieve pilotresultaat
bewijst geen structurele positieve of negatieve verwachtingswaarde.


## Beperkingen

Eén ontwikkelmaand en een beperkte, achteraf geselecteerde watchlist geven geen
statistisch bewijs voor winstgevendheid. OHLCV bepaalt geen exacte intrabarroute,
orderboekdiepte, latency, gedeeltelijke fills of werkelijke uitvoerbaarheid. De
simulator gebruikt ongunstige impact/afronding en bestaande stop-/gapregels.
Drawdown omvat de bestaande conservatieve liquidatiewaardering en waargenomen
bar-lows; het is geen gereconstrueerde tickcurve. Geen toekomstige candles bij
instapselectie; alleen de volgende open wordt voor de gesimuleerde fill gebruikt.

Geen echte transacties, API-sleutels, paperbot, strategie-/parameterwijzigingen of
verhoging van risicogrenzen. Onafhankelijke test blijft gesloten. Stop na deze pilot.
