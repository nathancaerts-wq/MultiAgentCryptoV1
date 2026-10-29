# Fase 6F — drie afzonderlijke strategiehypotheses

Status: **uitsluitend ontwerpen; geen implementatie, selectie of activatie**.
Basiscommit `4f3e9a2675cca3ce6015609145380f3c161d4cc9`.
Bron: definitieve fase-6E-v4-JSON en beschrijvend eindrapport. De vijf oorspronkelijke
hypotheses en hun 332 contrasten blijven onaangetast. Deze drie nieuwe voorstellen
vallen buiten die oude registratie en vereisen een nieuw goedgekeurd protocol.

## Wat de bestaande resultaten wel zeggen

Op UTC4h heeft bruto positief versus negatief HOLD een gemiddeld 1h-RSI-verschil
van −1,56359; per coin −1,65758 BTC, −1,16207 ETH, −1,90105 SOL. Het pooled
ΔRSI-verschil is −0,526589. Netto positieve versus niet-positieve HOLDs hebben
1h-relatieve-ATR-verschil +0,00183154 (BTC +0,00129485, ETH +0,00146699,
SOL +0,00113782). Dit zijn bestaande beschrijvingen, geen nieuwe berekeningen.

Voor scannerscore is het netto-contrast pooled −2,83004 maar BTC +0,68442,
ETH +0,387326 en SOL −1,24428. Muntsamenstelling en schaal spelen mee. Er is dus
geen aangetoonde universele voorkeur voor hoge scores. EMA-selectie telt 2.491
UTC4h-kandidaten tegenover 152 aligned_trend-kandidaten, met gemiddeld 0,882778
minder up-timeframes. Meer kandidaten betekent geen betere trades.

De labelgroepen omvatten HOLDs met diverse ontbrekende/conflicterende voorwaarden;
zij zijn niet de populatie van uitvoerbare aligned_trend-entries. Gemiddelde
verschillen onderbouwen geen optimale grens. De richting van onderstaande
hypotheses is toetsbaar, maar ook een nulresultaat of geen kandidaten is mogelijk.

## Gemeenschappelijke exacte beslisbasis

Alle voorstellen zijn **afzonderlijke extra toelatingsfilters** op een verse,
volledig geldige bestaande aligned_trend BUY_CANDIDATE: bullish 1h-regime,
EMA9/EMA21-richting up op alle drie timeframes, consistente analyses en alle
bestaande Decision-/Entry-/Risk-controles. Geen versoepeling naar twee timeframes,
geen behandeling van onbekend nieuws als positief, geen combinatie van S1–S3.
De bestaande scannerscore/UTC-kwartierrotatie beslist tussen toegelaten kandidaten.

`t` is een UTC15m-candlegrens. Per timeframe eindigt het gebruikte laatste
volledige candle op floor(t / timeframe) × timeframe; interval [open, close).
Voorbeeld: op 10:15 zijn laatste eindgrenzen 10:15, 10:00 en 08:00 voor
15m/1h/4h. Op 12:00 mag de zojuist afgesloten 4h-candle tot 12:00 gebruikt worden.
Een signaal na sluiting N kan pas open N+1 gebruiken, nooit diens high/low/close.

Indicatoren blijven RSI14, EMA9/21, ATR14 en de bestaande regime-/structuurregels,
met exact dezelfde 32-candleinitialisatie en Decimal-precisie. Voor ΔRSI zijn 33
volledige candles nodig: huidig RSI op de laatste 32, vorig RSI op de eerste 32;
Δ is huidig minus vorig op hetzelfde timeframe. Geen doorlopende alternatieve
RSI-initialisatie. Ontbrekend, oud, onvolledig, nul/noemer of inconsistent: HOLD,
geen imputatie of later candle. Onafhankelijke historische filters zijn nog niet
bewezen; latere ordertests blijven expliciet hypothetisch.

Alle voorstellen behouden één oorspronkelijk €200-portfolio, één positie,
maximaal 0,5% gepland risico inclusief kosten, 50% exposure, 3% dagverlies,
10% drawdown, verliesreekspauze en noodstop. Stop 2 × oorspronkelijke 1h-ATR,
horizon 4 uur, geen winsttarget, dezelfde conservatieve fills/gaps en cashreservering.
Een nieuw filter verandert nooit de stop, quantity achteraf of exitregels.

Kosten blijven fee 0,1% per zijde, volledige spread 0,1%, slippage 0,1% per zijde.
Eventuele latere vooraf toegestane sensitiviteit gebruikt uitsluitend bestaande
slippage 0,2% en het bestaande alle-kosten-verdubbeld-model. Geen frictieloze
claim op basis van 0,001-coinlabels; uitvoerbare omvang en afrondingen blijven nodig.

## S1 — RSI-terugval binnen volledig bevestigde trend

**Instapvoorwaarde:** gemeenschappelijke basis EN `RSI_1h <= 50` EN `ΔRSI_1h < 0`.
Gelijkheid 50 is toegelaten; Δ=0 niet. Geen extra 15m- of 4h-RSI-grens.
De 50 is het neutrale RSI-midden, nul de grens van daling; geen uit een
2024-kwantiel of geoptimaliseerd rendement gekozen waarden. Een lagere RSI is
geen bewijs van goedkoop of van aankomend herstel.

**Hypothese:** een kortdurende RSI-terugval binnen een nog volledige bullish
EMA-/structuurcontext kan een andere netto-uitkomstverdeling hebben dan de
ongewijzigde basisstrategie. De lagere beschreven RSI/ΔRSI motiveert deze vraag,
maar is geen bewijs voor deze conjunctie. Zij kan zeldzaam of leeg zijn.

**Beschikbaar op t:** oorspronkelijke drie frames, 33 gesloten 1h-candles,
scanner, portefeuille en geldige metadata. Geen latere RSI-omslag eisen of meenemen.
Kosten/risico/uitvoering exact volgens de gemeenschappelijke basis.

**Eerlijke toets:** eerst synthetische logische verenigbaarheid en grenzen; bij
nul matches niet versoepelen. Een latere apart goedgekeurde dataset moet zowel
basis- als S1-kandidaten, alle afwijzingen, trades en pauzes chronologisch bevatten.
Rapporteer per coin en vast kalenderblok, inclusief marktblootstelling. Een lagere
RSI in bekende HOLD-labels is geen onafhankelijk winstbewijs voor deze nieuwe filter.

## S2 — relatieve ATR groter dan de vooraf bekende kostenfractie

**Instapvoorwaarde:** gemeenschappelijke basis EN
`ATR14_1h / close_1h > c0`, waarbij
`c0 = 1 - ((1 - s/2 - l)*(1 - f))/((1 + s/2 + l)*(1 + f))`,
met vast baseline f=0,001, s=0,001, l=0,001. Exacte Decimal-formule, geen afgeronde
drempel. Gelijkheid wordt afgewezen. c0 is de theoretische roundtrip-verliesfractie
bij gelijke ruwe koop/verkoopprijs zonder tick-/feeafronding, circa 0,5%.

Deze grens volgt uit vooraf bekende frictie en wordt niet op uitkomsten geschat.
Ook in een latere kostensensitiviteit blijft de kandidaatgrens op baseline c0 staan;
alleen het toegestane uitvoeringskostenmodel verandert, zodat geen tweede strategie
wordt getest. De echte FillCosts, feeafronding en minnotional blijven apart gelden.

**Hypothese:** prijsomgevingen met ATR groter dan deze frictieschaal kunnen een
andere nettoverdeling hebben dan de basisstrategie. Het positieve bestaande
relatieve-ATR-contrast motiveert het ontwerp; ATR is geen verwachte directionele
winst of voorspelling dat kosten terugverdiend worden. Hoge ATR vergroot ook risico.

**Beschikbaar op t:** huidige gesloten 1h-ATR/close, alle basisframes, vooraf
vastgelegde kosten. Geen toekomstige gerealiseerde volatiliteit, geen nieuw
ATR-venster en geen historische percentielgrens. Sizing/stop blijven ongewijzigd;
bij hogere ATR kan quantity kleiner en onder minnotional worden.

**Eerlijke toets:** synthetisch exacte grens, nulprijs, afronding, grote ATR en
onmogelijke order; later dezelfde vastgelegde kalenderperiode en drie coins voor
basis/S2, met kostensensitiviteit en alle uitsluitingen. De 2024-ATR-samenhang kan
slechts grotere koersuitslagen of coinmix weerspiegelen; geen onafhankelijk bewijs.

## S3 — uitsluitend een geldige kandidaat met de hoogste actuele scannerscore

**Instapvoorwaarde:** gemeenschappelijke basis EN
`score(coin,t) = max(score(BTC,t), score(ETH,t), score(SOL,t))`.
Alle drie oorspronkelijke causale scores op hetzelfde beslismoment moeten geldig
zijn. Ontbreekt één score: HOLD voor alle drie in S3. Geen absolute scoregrens.
Bij gelijke hoogste scores blijven alle gelijk geëindigde kandidaten toelaatbaar;
de bestaande UTC-rotatie lost hun concurrentie op.

**Verschil met bestaande ranking:** de bestaande runner rangschikt geschikte
kandidaten. S3 sluit ook een lager scorende geschikte coin uit als de hoogste
coin zelf géén geldige BUY_CANDIDATE heeft of door risico wordt geweigerd.
Er komt geen terugval naar een lagere score. Het is dus een aanvullend gate,
geen herweging van de scanner of keuze van een toekomstige winnaar.

**Hypothese:** alleen op de gelijktijdige hoogste score handelen verandert
selectie en exposure ten opzichte van de basis. De tegenstrijdige per-coin-
verschillen maken dit vooral een toets op informatiewaarde en selectie-effecten,
niet een verwachting van verbetering. De groep kan structureel BTC bevoordelen.

**Beschikbaar op t:** drie oorspronkelijke score-snapshots, bron-/tijdgrenzen,
basisanalyses en portefeuillestatus. Geen toekomstige rang, rendement of score
uit een later opgeleverd rapport. Kosten en risico blijven exact gelijk.

**Eerlijke toets:** synthetische gelijke scores, ontbrekende coin, hoogste coin
ongeschikt, UTC-rotatie, verschillende scoretimestamp en gelijktijdige reservering.
Later per-coin-kandidaat-/afwijsverdelingen en baselinevergelijking op vooraf
vrijgegeven gegevens; pooled effecten alleen zijn onvoldoende wegens coinmix.
De bestaande 2024-scorecontrasten ondersteunen geen universele positieve richting.

## Nog te kiezen, vóór enige implementatie of evaluatie

Kies expliciet welke hypothese(n) een afzonderlijk technisch experiment mogen
worden. Geen combinatie met R1–R3 in dezelfde eerste evaluatie; anders worden
strategie- en herstelbijdragen onidentificeerbaar. De huidige pauze kan ook bij
een kandidaatstrategie blijvend intreden: rapporteer dat in plaats van resetten.

Nieuwe perioden, datasetidentiteiten, toelatingsregels, bronnen, kostenmodellen,
analysefamilie en bewijscriteria moeten vóór inzage worden geregistreerd. 2024 is
ontwikkel- en ontwerpmateriaal dat al veelvuldig is bekeken. Ook een vaste drempel
gekozen ná die inzage levert geen onafhankelijke bevestiging op. Dertig trades
is hoogstens een ondergrens uit het oude protocol, geen bewijs; gecorreleerde coins,
regimes en tijdafhankelijkheid moeten in een nieuwe statistische opzet passen.
2025 en 2026 worden door dit voorstel niet vrijgegeven. Geen p-waarden of rendement
voor S1–S3 berekend; geen hypothese gerangschikt op historische winst.
