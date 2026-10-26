# Fase 4B — offline fillsimulator, ledger en runner

Afgerond op 26 oktober 2026, voortbouwend op
`da81022303a8300ded72519567114701ff0482a1`.
De onderbroken werkzaamheden zijn hervat op branch `work`, met dezelfde HEAD en
alle bestaande wijzigingen intact. GitHub main stond bij controle nog op die
basiscommit. De simulator, ledger, runner, tests en historische testuitkomst waren
al aanwezig; zij zijn behouden. Er is bij hervatten geen nieuwe backtest gestart.

## Onderdelen en integratie

- `crypto.sim_execution`: FillCosts, SpotFilters en OfflineLedger.
- `crypto.backtest`: SimulationProtocol, prestatiemeting en BacktestRunner.
- De runner gebruikt het bestaande ResearchPlan, QuantResearcher en de inspectie-
  workflow van OfflineResearchOptimizer. Bestaande hypotheses worden niet aangepast.
- Uitvoeringsregels en candlehashes worden vooraf geregistreerd in
  simulation_protocols. Per plan kan niet achteraf een ander uitvoeringsprotocol
  worden opgeslagen. Resultaten gaan naar backtest_runs, volledig gescheiden van
  papertrading-orders en -posities.
- Alleen-lezen API: `/backtests` en `/simulation-protocols`.
- `scripts/phase4b_smoke.py` is de handmatig aan te roepen kleine integratietest;
  deze wordt niet automatisch uitgevoerd door de applicatie of pytest.

## Uitvoeringsaannames

1. Alleen long Spot, volledige gesimuleerde marktorders, geen short, leverage,
   deeluitvoering, orderboek, wachtrij of gekalibreerde marktimpact.
2. De runner accepteert historische volledige 15m- of 1h-uitvoeringscandles en
   valideert het volledige preregistreerde UTC-bereik. Officiële bronnen en
   synthetische fixtures worden expliciet onderscheiden. URL/provenancecontrole
   vervangt geen onafhankelijke authenticiteitsaudit van aangeleverde data.
3. Een gesloten-candlesignaal kan pas op een volgende candle-open worden uitgevoerd.
   De ordergrootte en stop gebruiken de vorige afgesloten uitvoeringsprijs en de
   reeds bekende ATR (stopafstand 2 ATR). Geen high/low/close van de instapcandle
   wordt gebruikt voor instapselectie of voorafgaande omvang. Ontbreekt een vorige
   prijs binnen het uitvoeringsbereik, dan wordt de eerste order afgewezen.
4. Koopprijs = open × (1 + halve spread + slippage), naar boven op tick afgerond.
   Verkoopprijs = referentie × (1 − halve spread − slippage), naar beneden afgerond.
   Standaard fee 0,1% per zijde, volledige spread 0,1% en slippage 0,1% per zijde.
   Daardoor kan de gemodelleerde prijs buiten OHLC liggen: dit is een ongunstige
   kostenaanname, geen waargenomen intrabarprijs. Fees worden in EUR afgerekend,
   naar boven op 0,00000001 EUR afgerond; geen BNB-korting.
5. Openingsgap door een stop: verkoop vanaf min(open, stop), daarna kosten en
   ongunstige afronding. Zonder openingsgap is de stop de prijsreferentie; onbekende
   intrabarsprongen worden niet gereconstrueerd. Wanneer stop én target geraakt
   worden, wint de stop en wordt de trade ambigu gemarkeerd. Een target krijgt
   geen gunstige gapverbetering. De huidige hypotheses activeren geen winsttarget;
   de primitive is wel getest.
6. Intrabarregistratietijden gebruiken het candle-einde minus één microseconde als
   boekhoudconventie. Dit is geen claim dat de fill precies toen plaatsvond.
7. Horizonexit op de eerste open vanaf de vooraf bepaalde deadline (vier uur).
   Resterende posities worden aan het einde van de periode tegen de laatste close
   met verkoopkosten afgewikkeld. Dit is een vooraf geplande terminale liquidatie,
   geen instapsignaal dat dezelfde candle-close benut.
8. Bij een portefeuillelimiet binnen een bar wordt de laagste barprijs gebruikt
   voor een pessimistische gedwongen exit. Exposure telt een geraakte bar volledig.
   Drawdown volgt de gemodelleerde liquidatiewaarderingen; het exacte intrabarpad
   en de intrabar equitypiek zijn onbekend.

## Filters, risico en ledger

PRICE_FILTER (tick en grenzen), LOT_SIZE, MARKET_LOT_SIZE, MIN_NOTIONAL en NOTIONAL
zijn configureerbaar. Gecombineerde quantity-steps gebruiken een gemeenschappelijke
veelvoudstap. Omvang wordt naar beneden afgerond. Niet-passende orders worden met
exacte reden afgewezen, zonder de kas te wijzigen. Filters met vereiste historische
gemiddelde notionalprijzen worden afgewezen als die prijzen niet beschikbaar zijn.
Tickcontrole op de gemodelleerde marktfill is een extra conservatieve simulatierestrictie.

Metadata moet expliciet `assumed` of `validated` zijn. Voor validated zijn officiële
Binance-bron, bekendheidstijd en historische geldigheidsperiode vereist. De
betrouwbaarheid van aangeleverde metadata blijft een verantwoordelijkheid van de
importeur. Er is geen reconstructie van historische beursfilters toegevoegd.
De historische integratietest gebruikt daarom zichtbare aannames, geen claim dat
alle fills destijds op Binance daadwerkelijk toegestaan waren.

Ieder coin/hypothese-experiment begint met €200 en maximaal één open positie.
Verschillende experimenten worden niet als één gedeelde multi-coinportefeuille
opgeteld. Daardoor is er geen gelijktijdig cross-coin-correlatierisico in één ledger;
extra posities worden geweigerd. Maximaal 0,5% gepland risico inclusief beide zijden
kosten en maximaal 50% exposure. Gaps kunnen het gerealiseerde verlies vergroten;
het geplande risico is geen verliesgarantie. Risico en cash worden op de werkelijke
simulatieprijs opnieuw gecontroleerd; een ongunstige instapgap kan tot weigering leiden.

Bestaande Limits blijven intact: 3% dagverlies en 10% drawdown. Dagverlies pauzeert
nieuwe instappen tot de volgende UTC-dag; drawdown pauzeert de rest van het experiment.
Overnachtelijke openingsgaps tellen mee vanaf de vorige waardering. Verkooporders
blijven toegestaan tijdens pauzes. De simulatierunner verandert geen productiegrenzen.

De ledger registreert cash, bezit, gemiddelde prijs, kostenbasis, fees, gerealiseerde
P&L, ongerealiseerde P&L, bruto equity en geschatte liquidatie-equity. Na elke fill
moet cash + resterende kostenbasis gelijk zijn aan €200 + gerealiseerde P&L.
Order-ID's voorkomen dubbele fills. Het auditspoor bevat begin/eindbalans,
risico-overgangen, weigeringen, fills, kostencomponenten en een SHA-256-hashketen.
Een geweigerde exit verwijdert de positie niet. Zo'n resultaat blijft incomplete;
het volledige nettoresultaat wordt dan null, niet fictief gerealiseerd.

## Testperioden en metingen

De bestaande chronologische splits, embargo, rapporthashes en uitkomsthorizon
blijven van kracht. De onafhankelijke test wordt door BacktestRunner geweigerd
zolang het vooraf geregistreerde SimulationProtocol geen expliciete autorisatie
bevat. Inzage wordt via de optimizer geregistreerd vóór simulatie-uitkomsten.
Herhaling gebruikt dezelfde run-ID en retourneert de opgeslagen uitkomst met
replay=true; dat is geen nieuw onafhankelijk bewijs.

De historische smoke-test heeft independent_test_authorization=null. Het bestaande
artefact meldt independent_test_opened=false; de protocol- en resultaat-ID zijn bij
hervatten opnieuw gecontroleerd. De tijdelijke testdatabase was door de vorige
uitvoering opgeruimd, dus is geen nieuwe database-inzage geclaimd. De gate en
blootstellingsregistratie zijn tevens met synthetische unit-tests gecontroleerd.
Die expliciet geautoriseerde fixturetest opent geen echte historische holdout.

Per coin, hypothese en periode worden trades, netto P&L, winrate, gemiddelde
winst/verlies, expectancy, profit factor, drawdown en exposure berekend. Zonder
trades blijven ratio's null; profit factor zonder verliezen is ongedefinieerd.
Verdubbelde fee/spread/slippage wordt als afzonderlijk scenario gesimuleerd met
opnieuw begrensde ordergroottes; daardoor hoeft het absolute verlies niet monotoon
te stijgen. Het scenario is geen vaste-omvang-kostencounterfactual. Verwijderen van
de drie grootste winnaars is een rekenkundige gevoeligheidscheck, geen heruitgevoerde
portefeuille met veranderde kaspaden.

De vooraf gedefinieerde EMA-benchmark gebruikt dezelfde uitvoeringsregels.
Buy-and-hold zonder stop blijft expliciet not_simulated omdat het niet onder de
0,5%-gepland-risicoregel past. Er is geen stilzwijgend andere benchmark gemaakt.
Minimaal 30 trades is alleen een ondergrens: ook daarboven wordt aanvullende
onafhankelijke statistische validatie vereist. Bootstrap, p-waarden en winstbewijs
zijn niet toegevoegd.

## Bestaande historische integratietest

De vorige sessie voerde na fixturetests een kleine ontwikkelingstest uit op BTC/EUR
van 2025-01-10 00:00 tot 2025-01-11 00:00 UTC: 24 officiële 1h-uitvoeringscandles,
twee analyses op 12:00 en 16:00 met historische 15m/1h/4h-prefixen. Het officiële
archief is vóór verwerking via SHA-256 gecontroleerd:
`a034d2f10ece1ffa26d185d837fed7297d36249f77c5e3a42d377872a9f287b6`.

De teruggevonden uitkomst is ongewijzigd opgeslagen in
`experiments/phase4b_smoke.json`, inclusief plan, kosten, aangenomen filters,
candlehashes, checksumprovenance en testvergrendeling.

| Onderzoek | Gesloten trades | Netto EUR |
|---|---:|---:|
| regime_momentum | 1 | -0,99958495 |
| aligned_trend | 0 | 0 |
| sideways_recovery | 0 | 0 |
| EMA-benchmark | 2 | -0,51164873 |

Dit zijn afzonderlijke €200-experimenten. Alle uitkomsten zijn insufficient_evidence.
Nul papertrading-orders; geen echte transacties. Bij hervatten is deze test niet
opnieuw gedraaid en is geen nieuwe uitgebreide backtest gestart.

## Verificatie en beperkingen

Alle **191 tests geslaagd, 0 mislukt**: de 154 bestaande en 37 nieuwe tests.
De eerdere tussentelling van 183 was al uitgebreid vóór de onderbreking.
Getest: kosten/slippage, negatieve input, afronding, alle ondersteunde filters,
historische metadata, stops, gaps, ambiguïteit, volgende-candle-uitvoering,
onafhankelijkheid van toekomstige extremen, volgorde/duplicaten/ontbrekende data,
ledgerreconciliatie, dubbelorders, cash, risico, pauzes en dagovergangen,
incomplete exits, preregistratie, holdout-gate en expliciete fixtureautorisatie,
herstart/replay, onderzoeksisolatie en alleen-lezen API.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing; geen testfouten.

Beperkingen: OHLCV zonder werkelijk intrabarpad, onbekende historische filters,
aangenomen liquiditeit en volledige fills, vaste niet-gekalibreerde kosten,
geen orderboek/latentie/deeluitvoering, afzonderlijke single-position-experimenten,
geen multi-assetportefeuille, geen point-in-time broncorrectie/publicatielatentie,
geen volwaardige buy-and-hold-vergelijking of statistisch winstbewijs.
Windows is niet uitgevoerd. Onderzoeksruns worden afgerond opgeslagen, niet
halverwege crashbestendig hervat; audit-hashes vormen geen extern beveiligd register.
Bestaande agenten, strategieën, risico- en executioncode zijn behouden. Fase 5 is
niet gestart.
