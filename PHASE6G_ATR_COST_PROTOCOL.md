# Fase 6G — Protocol B: ATR tegenover vaste verwachte kostenfractie

Protocol-ID: `phase6g-atr-cost-v1`. Status: **ONTWERP, NIET ACTIEF**.
Basiscommit: `fed7ec29f13d0fe3742f811399a19a19ab5ac4c8`.
Alleen onderzoeksvoorbereiding. Geen nieuwe indicator-, label- of rendementsberekening
op historische gegevens. Zie het gemeenschappelijke `PHASE6G_EXPERIMENT_PLAN.md`.

## Eén hypothese, geen zoekruimte

Een afzonderlijke extra filter op de bestaande aligned_trend BUY_CANDIDATE kan
entries vermijden waarvan de ATR-schaal klein is tegenover vooraf bekende
transactiefrictie. Vraag: verandert daardoor de nettoportefeuille-uitkomst en
blootstelling tegenover exact dezelfde strategie zonder filter? Dit is geen
bewijs dat ATR de verwachte winst of haalbare koersruimte voorspelt.

Dit operationaliseert fase 6F S2 met dezelfde kostenformule en grens. Geen andere
ATR-periode, timeframe, multiplicator, quantiel, RSI-filter of scannerweging wordt
onderzocht. BTC/EUR, ETH/EUR en SOL/EUR vormen het vaste universum. 2024 is eerder
bekeken ontwikkeldata en geen onafhankelijke bevestiging voor deze keuze.

## Exacte indicator en causale tijdsgrens

Gebruik uitsluitend de oorspronkelijke `crypto.indicators.technical`-berekening
met `IndicatorConfig.atr=14`, op precies de laatste 32 aaneengesloten, volledig
afgesloten 1h-candles. Noem die candles C0..C31. Voor i=1..31:

`TR_i = max(high_i - low_i, abs(high_i - close_(i-1)), abs(low_i - close_(i-1)))`.

Seed `A14 = sum(TR_1..TR_14)/14`; daarna voor i=15..31
`A_i = (13*A_(i-1) + TR_i)/14`. De gebruikte ATR is A31.
Geen TR voor C0 zonder eerdere close, geen andere Wilder-seed en geen doorlopende
ATR uit de volledige geschiedenis. Alle berekeningen volgen de bestaande Decimal-
precisie 28 (ROUND_HALF_EVEN), in dezelfde volgorde. De ATR uit het bestaande
bericht moet exact gelijk zijn aan deze brongebonden indicator.

`P` is de close van C31, strikt positief. `t` is het huidige UTC15m-beslismoment.
C31 eindigt op floor(t/3600)*3600; ook 15m- en 4h-analyseframes moeten volledig
zijn en op hun eigen UTC-grens eindigen. Op 10:15 zijn de eindgrenzen 10:15,
10:00, 08:00; op 12:00 kan het zojuist afgesloten 4h-frame tot 12:00 worden gebruikt.
Nooit de onvolledige 1h/4h-candle aanvullen met toekomstinformatie. Instap blijft
open N+1; die open, high, low of close wordt niet vooraf in de filter gebruikt.

## Kosten, verhouding en vaste grens

Parameters als exacte Decimal-strings, gelijk aan baseline FillCosts:

| Parameter | Waarde | Betekenis |
|---|---:|---|
| f | 0.001 | Fee per zijde |
| s | 0.001 | Volledige spread, halve spread per zijde |
| l | 0.001 | Slippage per zijde |
| K | 1 | Vaste grens voor de verhouding |

Bereken exact in deze volgorde:

1. `impact = s/2 + l`.
2. `buy_factor = (1 + impact)*(1 + f)`.
3. `sell_factor = (1 - impact)*(1 - f)`.
4. `c0 = 1 - sell_factor/buy_factor`.
5. `relative_atr = ATR/P`.
6. `ratio = relative_atr/c0`.
7. Toelaatbaar uitsluitend als `ratio > Decimal('1')`. Gelijkheid wijst af.

`c0` is de theoretische roundtrip-verliesfractie ten opzichte van de bruto
instapuitgave inclusief fee, bij dezelfde ruwe koop- en verkoopprijs en zonder
afronding. Het is ongeveer 0,5%; gebruik nooit dat afgeronde percentage in de
beslissing. De vergelijking is dezelfde genormaliseerde schaalvergelijking als
6F S2. De grens 1 betekent één ATR-schaal tegenover één vooraf vastgelegde
roundtrip-frictieschaal en komt niet uit de verdeling of winst van 2024.

**Afgebakende kostenproxy:** c0 omvat fees, spread en slippage aan beide zijden,
maar geen tick- of feeafronding, werkelijke toekomstige exitprijs, marktimpact
boven de vaste slippage of beursfiltereffecten. `relative_atr` deelt door de ruwe
close, terwijl c0 door de theoretische instapuitgave wordt genormaliseerd. Dit is
bewust de bestaande 6F-proxy, geen exacte vereiste break-even-prijsstijging of
quantity-specifieke winstberekening. `P*c0` mag als referentiekostenschaal in EUR
per coin worden gerapporteerd, niet als exacte uitvoeringskosten.

Echte hypothetische uitvoeringskosten blijven door de ongewijzigde FillCosts op
de voorgestelde hoeveelheid bepaald: nadelige tickafronding voor koop/verkoop,
fees naar boven op 1e-8 EUR, geldige hoeveelheidsstappen en cashreservering.
Een ratio > 1 garandeert niet dat die werkelijke kosten worden gedekt. De filter
mag nooit een bestaande sizing-, stop-, minnotional- of Risk-afwijzing vervangen.
Geen vaste 0,001-coinprijsdiagnose behandelen als uitvoerbare positie.

Voor eventuele later expliciet toegestane kostensensitiviteit blijft c0 op de
baselinewaarden hierboven bevroren; alleen het uitvoeringskostenmodel verandert.
Dat is een stresstest van hetzelfde filter. Een nieuwe c0 bij hogere kosten is
een andere hypothese en valt buiten dit protocol.

## Beslispad, vereiste bronnen en ontbrekendheid

De bestaande scanner, regime-, technical-, multi-timeframe- en sentimentvalidatie
blijven verplicht. De basis blijft bullish 1h en up op 15m/1h/4h, inclusief alle
bestaande conflict-/missing-veto's. Onbekend nieuws blijft onbekend.

De filter beoordeelt iedere geldige BUY_CANDIDATE vóór de gezamenlijke rangschikking
en vóór een cashreservering. Alleen geslaagde kandidaten gaan door. Scannerscore
en UTC-tiebreak blijven ongewijzigd; er is geen S3-topscorevoorwaarde. Als de hoogst
scorende coin afvalt, mag de bestaande selectie een andere geslaagde kandidaat
kiezen. Alle coins kunnen tegelijkertijd afvallen: HOLD zonder order.

Vereist op t: 32 valide afgesloten 1h-candles met bronhash, actuele oorspronkelijke
ATR en P, consistente timeframegrenzen/parameters, de overige volledige basisframes,
geldige scanner en een bevroren kostenconfiguratie. Geen actuele orderfilters als
historische feiten; bestaande onbewezen filters blijven expliciete aannames.

- Ontbrekend, oud, onvolledig, inconsistent of niet-eindig kenmerk: HOLD met
  `atr_cost_missing_or_invalid`, geen imputatie, overslaan van gaten of toekomstdata.
- ATR <= 0, P <= 0, c0 <= 0 of ongeldige configuratie: fail-closed, geen deling.
- Geldige ratio <= 1: `atr_cost_ratio_not_above_one`, met ATR, P, c0 en ratio loggen.
- Geldige ratio > 1: uitsluitend doorgang naar de bestaande Entry-/Risk-controles;
  nooit directe orderautorisatie. Een ontbrekende marktbron kan daarnaast volgens
  het experimentplan de volledige run als onvolledig stoppen.

De ontbrekendheidsdiagnose van de baseline blijft bewaard. Log de filterfase
apart zodat een filterafwijzing niet ten onrechte als risicogoedkeuring of
vermeden verlies wordt geteld. Deduplicatie op protocol, coin, t en bronbundel.

## Wat behouden blijft en welke tests later nodig zijn

Eén gezamenlijke oorspronkelijk €200-portefeuille; één positie; maximaal 0,5%
gepland risico en 50% exposure; dagverlies 3%, drawdown 10% en noodstop. De
**bestaande permanente verliesreekspauze blijft in B intact**. Geen Risk Recovery.
De stop blijft 2 ATR op het oorspronkelijke beslismoment, horizon 4 uur, geen
target, conservatieve stops/gaps, kosten, sizing en exits ongewijzigd. Niet breder
stoppen of quantity vergroten om de filter of minimale ordergrootte te halen.

Vóór eventuele historische toestemming: exacte oorspronkelijke ATR-seed en
rolling vensters, 1h-/4h-grenzen, later candle verandert huidige beslissing niet,
ratio onder/exact/boven 1, ontbrekend/NaN/nul, vaste Decimal-volgorde, causale
parameters, onderscheid proxy/werkelijke afronding, simultane coins en reservering,
geen risicobypass, dezelfde baseline-uitkomsten zonder filter. Geen van deze
nieuwe varianttests of historische uitkomstvergelijkingen wordt nu uitgevoerd.
