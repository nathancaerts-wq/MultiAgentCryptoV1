# Onderzoeksprotocol fase 4 — phase4-v1

## Scope en preregistratie

Dit protocol legt uitsluitend onderzoeksinterfaces en selecties vast. De huidige
execution-engine heeft geen fills, portefeuille-ledger, saldoreservering, intrabar-
volgorde, stopuitvoering of slippage-simulatie. Daarom wordt geen backtest gestart.
Geen meetwaarde wordt als nul ingevuld wanneer deze niet berekend is: alle
prestatievelden blijven null en evidence is insufficient_evidence.

Een ResearchPlan legt vóór inzage vast: alfabetisch gesorteerde EUR-watchlist,
bron en dataset-SHA-256, SHA-256 van de exacte berichtenbundel per deelperiode,
indicatorparameters, hypothesen, vensters, selectiecriterium, kosten, slippage,
risico, horizon en uitgangskapitaal. Plan-ID is de hash van de volledige inhoud.
Wijzigingen maken een nieuw plan; opgeslagen plannen worden niet overschreven.
De berichtenhash verifieert de daadwerkelijke ingestuurde inhoud. De dataset-hash
identificeert het onderliggende corpus maar vervangt geen externe data-audit.
Het hashen van een bundel is geen beoordeling van uitkomsten; geen validatie-
of testresultaten mogen vooraf worden bekeken om het plan te kiezen.

## Vaste hypothesen en benchmarks

Geen zoekgrid, willekeurige sampling of automatische parameteroptimalisatie.
De volgende drie hypotheses zijn vooraf beschreven in crypto.protocol.HYPOTHESES:

1. regime_momentum: bullish 1h-regime, positieve 1h-momentum, RSI tussen 40 en 70.
2. aligned_trend: bullish 1h-regime en EMA-richting omhoog op 15m, 1h en 4h.
3. sideways_recovery: sideways 1h-regime, 1h-RSI onder 40, positieve 15m-momentum.

Een eligible-waarde is uitsluitend een onderzoeksselectie, geen transactie of
voorspelling. De toekomstige toetsbare uitkomsthypothese is positieve netto-
verwachtingswaarde na vooraf vastgelegde kosten en verbetering tegenover benchmarks.
Een mogelijke uitkomst wordt hier niet berekend.

Voor toekomstige simulatie geldt vooraf: long Spot, geen leverage/short; instap
niet vóór de volgende candle-open, initiële stopafstand 2 ATR op beslismoment,
maximale horizon 4 uur. Fills, gaps, intrabar-stopvolgorde, beursfilters, liquiditeit
en portefeuilleconcurrentie moeten eerst expliciet geïmplementeerd en gevalideerd
worden. Deze ontbrekende voorwaarden blokkeren prestatiemeting.

Benchmarks: buy-and-hold (eenmalig bij eerste uitvoerbare open van de periode,
waardering/afsluiting op periode-einde) en ema_trend (1h-EMA-fast boven slow buiten
de vaste sideways-grens). Voor trend gelden dezelfde toekomstige uitvoerings- en
risicoregels als voor hypotheses. Buy-and-hold heeft een andere exposure; een latere
vergelijking moet zowel ruwe als risico/exposureverschillen tonen, niet wegpoetsen.
De interfaces beschrijven beide benchmarks; er is nog geen uitgevoerde vergelijking.

## Tijd en onafhankelijkheid

Ontwikkeling, validatie en onafhankelijke test zijn chronologische halfopen
UTC-intervallen met minimaal vier uur embargo. Een signaal plus volledige 4h-
uitkomsthorizon moet binnen zijn deelperiode vallen. Indicator-warm-up mag alleen
oudere candles gebruiken. QuantResearcher controleert beslismoment, bericht-TTL,
parameters, volledige dekking, timeframegrenzen, bronvermelding en consistentie
van regime/technical/multi-timeframe-componenten. Fase-3-berichten worden hergebruikt;
geen kenmerken worden uit toekomstige uitkomsten afgeleid.

Walk-forward-vensters liggen uitsluitend in de ontwikkelperiode: standaard zeven
dagen training, vier uur embargo en twee dagen evaluatie, vervolgens doorschuiven.
Venstergroottes zijn deel van de preregistratie. Bij te weinig dekking is de foldlijst
leeg. Dit is een gevalideerde vensterplanning, geen uitgevoerde walk-forward-backtest.

Inzage wordt vóór berekening duurzaam geregistreerd en over herstarts bewaard.
De testset is na eerste inzage niet meer onaangeraakt, ook bij latere validatiefouten.
Overlap wordt op marktparen en perioden gecontroleerd, niet alleen op datasetnamen.
Een nieuw plan kan reeds bekeken validatie/testperioden niet als nieuw registreren.
Herhaalde inzage blijft mogelijk, maar wordt expliciet als eerder blootgesteld
behandeld. Gebruik mark_external_view voor al elders bekeken perioden. De software
kan handmatige inzage buiten de database niet automatisch detecteren; dit vereist
onderzoeksdiscipline. Een lokale gebruiker kan de database wijzigen: dit is geen
beveiligd onafhankelijk preregistratieregister.

## Kosten, risico en geplande metingen

Elke vergelijkbare experimentstart gebruikt €200. Gepland risico per trade maximaal
0,5% (= aanvankelijk €1). De geïsoleerde planned_size-rekeninterface begrenst ook
notional op 50% equity en neemt twee zijden kosten/slippage mee. Dit is geen
executieautorisatie en garandeert geen maximale gerealiseerde verliezen bij gaps.
Bestaande harde risicogrenzen worden nergens aangepast.

Standaard fee en slippage elk 0,1% per zijde. Kostenrekening:
netto = q × exit × (1-slippage) × (1-fee) − q × entry × (1+slippage) × (1+fee).
Gevoeligheid: verdubbel vooraf de kosten en verwijder de drie grootste netto-
winnaars. Deze scenario's worden vooraf benoemd; resultaten blijven onbekend.

Per hypothese én benchmark, coin en periode zijn velden voorzien voor trades,
nettoresultaat, winrate, gemiddelde winst/verlies, expectancy, profit factor,
maximale drawdown, exposure en beide gevoeligheidsanalyses. Zonder gevalideerde
fills en equitycurve zijn al deze velden null, ook trade-aantal (niet nul trades).

Minimaal 30 trades is slechts een noodzakelijke ondergrens, geen bewijs van
betrouwbaarheid. Autocorrelatie, overlapping, regimes en coin-correlatie verminderen
het effectieve aantal onafhankelijke waarnemingen. Voor latere inferentie zijn
bijvoorbeeld tijdsblok-bootstrap en onzekerheidsintervallen nodig.

De geplande hypothesefamilie telt hypotheses × coins; nominale familie-alpha is
0,05 met vastgelegde Bonferroni-grens. Dit wordt uitsluitend als gepland criterium
opgeslagen: geen p-waarden of significantie berekend. Extra plannen, folds,
benchmarks en selectie-effecten vereisen een expliciet uitgebreid analyseplan en
correctie vóór enige claim. Het aantal geregistreerde plannen wordt gerapporteerd.
Selectiecriterium: netto-expectancy, bij gelijkheid lagere drawdown; toepassing
blijft geblokkeerd zolang prestatiemeting ontbreekt. Geen automatische promotie.

## Aanvulling fase 5 — gecontroleerde beslisworkflow

De eerdere beschrijving van ontbrekende fills is de historische fase-4-status;
PHASE4B_REPORT.md documenteert de later gebouwde simulator. Fase 5 voegt een
 afzonderlijke technische onderzoeksworkflow toe, zonder de bovenstaande hypothesen
of bestaande meetresultaten te veranderen. PHASE5_REPORT.md legt DecisionPolicy
phase5-v1, strengere veiligheidsfilters en expliciete offline uitvoering vast.

Standaardhypothese aligned_trend, stop 2 ATR, horizon 4 uur, kosten en maximaal
0,5% gepland risico staan vast vóór evaluatie. Geen winsttarget voor deze hypotheses.
Eén andere bestaande hypothese kan alleen vooraf worden gekozen en moet al in het
ResearchPlan staan. Filters, rapportbundel en uitvoeringscandles zijn eveneens gebonden.
Een bevroren beleid kan niet voor hetzelfde plan/coin worden vervangen.

Fase 5 staat uitsluitend kleine technische ontwikkeltests toe, maximaal 192
uitvoeringscandles per coin. Validatie en onafhankelijke test zijn niet beschikbaar
in deze interface. Het toetsen van striktere veiligheidsvoorwaarden is geen nieuwe
statistische validatie van de oorspronkelijke hypotheses. Er is geen zoeklus,
strategiepromotie of claim van positieve verwachtingswaarde.
