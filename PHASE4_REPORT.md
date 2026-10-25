# Fase 4 — Quant Researcher en gecontroleerd offline onderzoek

Gebouwd op ad812b517080f1a66587abbae3d1c235f6e48cf6.

## Besluit over uitvoeringsscope

De bestaande ExecutionEngine registreert uitsluitend virtuele voorstellen. Een
gevalideerde backtest/fillsimulator en portefeuille-ledger ontbreken. Daarom is de
expliciet toegestane tussenstap uitgevoerd: reproduceerbare onderzoeksinterfaces,
preregistratie, onafhankelijke testbewaking en tests. Er zijn geen rendementen,
backtests of winstgevendheidsclaims geproduceerd.

## Gebouwd

- QuantResearcher combineert bestaande regime-, technische en multi-timeframe-
  berichten voor drie vooraf gedefinieerde hypotheses en twee benchmarkselecties.
- ResearchPlan valideert UTC-splits, vier uur embargo, vaste begrensde hypotheses,
  parameters, vensterplanning, kosten, datahashes en maximaal 0,5% gepland risico.
- OfflineResearchOptimizer registreert onveranderlijke plannen, verifieert exacte
  rapportbundels, bewaart blootstelling aan deelperioden vóór verwerking en
  rapporteert hergebruik, afwijzingen, selectie-effecten en onvoldoende bewijs.
- Geplande walk-forward-folds, kostenrekening en risicobudget-interface zijn getest.
- Per coin, hypothese/benchmark en periode bestaat een prestatiecontract met alle
  gevraagde metingen, expliciet null zolang fills en equitycurve ontbreken.
- Twee SQLite-tabellen research_plans en research_exposures zijn toegevoegd.
  Resultaten en audit gebruiken bestaande research_results en audit; de bestaande
  alleen-lezen /research API kan de uitkomsten tonen. Geen nieuwe netwerkbron.

De bestaande ResearchOptimizer uit fase 1 en alle agents/interfaces blijven
behouden. De nieuwe OfflineResearchOptimizer is een afzonderlijke onderzoeks-
workflow zonder approve/activate-methoden. Hij roept geen execution/risk/agent-
configuratiemutaties aan. Zie RESEARCH_PROTOCOL.md voor vooraf vastgelegde regels.

## Statistische en praktische grenzen

De workflow voorkomt bepaalde fouten: selectieparameters veranderen niet stil,
validatie/testdelen overlappen niet, signalen en horizon blijven binnen hun periode,
verouderde/toekomstige of inconsistente analyses worden geweigerd en bekeken test-
perioden worden niet opnieuw als onaangeraakt beschouwd. Dit toont gecontroleerd
procesgedrag, geen bewezen statistische geldigheid van een handelsstrategie.

Ontbrekend: fillsimulator, intrabar/gapbeleid, beursfilters, fees/slippagekalibratie,
positieboekhouding, equitycurve, portefeuille-exposure/correlatie, daadwerkelijke
benchmarkvergelijking, walk-forward-uitkomsten, bootstrap/onzekerheidsintervallen
en correctie over meerdere onderzoeksrondes. Ook historische broncorrecties en
publicatielatentie uit fase 3 blijven beperkingen. Vóór performanceclaims moeten
al deze noodzakelijke onderdelen worden uitgewerkt en gevalideerd.

Het systeem kan externe handmatige inzage niet herkennen. Daarvoor bestaat expliciete
mark_external_view-registratie. SHA-256 bindt rapportbundels aan een plan, maar
verifieert geen echtheid van door derden aangeleverde marktdata. Productiedata en
configuraties worden niet gewijzigd. Windows is niet daadwerkelijk getest.

## Verificatie

154 tests geslaagd, 0 mislukt: alle 124 bestaande plus 30 nieuwe tests.
Getest zijn chronologische splits/embargo, vensterplanning, tijdzones, toekomstige
of verlopen analyses, datagaten/dekkingsfouten, parameterisolatie, berichtinhoud-
hashes, herhaalbaarheid, blijvende testblootstelling na databaseheropening,
hernoemde datasets, externe inzage, uitkomsthorizon, kosten/slippage, 0,5%-risico,
€200-startkapitaal en expliciet onbekende prestatievelden. De integratietest laat
ook zien dat bestaande agentconfiguraties, strategieën, risico-instellingen,
portefeuille, voorstellen en orders ongewijzigd blijven.

De gecontroleerde offline integratie gebruikt reproduceerbare synthetische candles
en bestaande fase-3-analyses; er is geen nieuwe internetdownload nodig. Een positieve
hypothese-selectie in deze fixture is uitsluitend een selectie, geen winst of trade.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing blijft bestaan.

Fase 4 eindigt bij deze onderzoeksinterfaces. Fase 5 is niet gestart.
