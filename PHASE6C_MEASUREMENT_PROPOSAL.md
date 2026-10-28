# Fase 6C — ontbrekende meetregistratie, voorstel (niet geactiveerd)

Basis 86596f90d2ab53434912fce5972a660470e32a9b. Dit document geeft geen toestemming
voor nieuwe historische uitkomstlabels of backtests.

De bestaande vieruurshorizon beschrijft strategie-exits. Zij definieert nog niet
hoe een HOLD zonder hoeveelheid/stop een gemiste kans moet worden, hoe overlappende
momenten worden geteld of wat 'andere munt aantrekkelijker' meet. Deze keuzes zijn
niet identiek aan het opnieuw rapporteren van al uitgevoerde trades. Volgens de
expliciete stopregel uit de opdracht worden nieuwe historische uitkomsten niet berekend.

## Voor te keuren definities

- Universum: alle opgeslagen 15m-beslisgrenzen vanaf 8 januari tot de laatste
  instapgrens 31 december 19:45, drie vaste coins, baseline. Warm-up en terminale
  grenzen apart tellen; geen stilzwijgende selectie van alleen BUY-signalen.
- Voorstel: één primair vieruursvenster [t,t+4h), geen zoektocht naar gunstige
  1h/24h-vensters. Entryreferentie = open op t (volgende candle na signaalclose).
  Terminale close is een hypothetische waardering, geen bewezen order op die close.
- Bruto label: eindclose/open−1; positief/negatief/nul zonder winstafgestelde drempel.
  Rapporteer daarnaast negatieve minimum-low/open−1 (MAE vanaf de raw entry);
  dit is geen volgorde-exacte intrabar-drawdown of gegarandeerd verlies.
- Netto unit-markering met bestaande FillCosts: adverse ticks en fees per zijde.
  Eerst expliciet kiezen: vaste hoeveelheid voor een prijsdiagnose, of bestaande
  ex-ante sizing inclusief ATR-stop/cash voor een afzonderlijke ordersimulatie.
  De synthetische implementatie vraagt een expliciete fixturehoeveelheid en
  berekent alleen een markering; geen historisch uitvoerbaarheidslabel.
- Voor stop-/horizon-counterfactuals: bestaande simulator en regels ongewijzigd;
  alleen waar ATR/stop/metadata op t bekend zijn. Ontbrekende stop/sizing niet
  achteraf afleiden uit gunstige toekomstige candles. Geen fictieve portefeuille
  voor elke gemiste candle als gezamenlijke winst optellen.
- Werkelijke toelaatbaarheid = aantoonbare toestemming van de oorspronkelijke
  Risk/Entry/Execution-keten en oorspronkelijke positie/reservering. Een hoger
  toekomstig koersrendement kan een bestaande veto niet opheffen. Ontbrekende
  goedkeuring = niet vastgesteld; een afwijzing = geblokkeerd onder dit model.
- Overlap: primaire labels per coin en t, nooit als onafhankelijke trades tellen;
  rapporteer een secundaire vaste UTC-vieruurssteekproef afzonderlijk. Voor crosscoin-
  vergelijking blijven gelijktijdige coins één afhankelijke tijdgroep. Nog te
  bevestigen of deze conventie of een uitsluitend niet-overlappende analyse primair is.
- Alternatieve coin: hogere score op t is een aparte feitelijke rankingdiagnose,
  geen winstclaim. Een vergelijking op toekomstig nettoresultaat is een nieuwe
  secundaire, overlappende oracle-uitkomst en vraagt eigen preregistratie.
- Pauzeversoepeling: geen activering. Leg eerst exact een variant, resetvoorwaarde,
  vergelijkingsmaat, analyseenheid, kostenfamilie en stopregels vast in een aparte
  studie. Houd €200, 0,5%, exposure-, dagverlies- en drawdowngrenzen intact.

## Besluit vereist

Bevestig horizon/waarderingsregel, hoeveelheid en stop, overlapconventie en betekenis
van een 'betere coin' vóór historische labels. Maak daarna een nieuw manifest met
bron- en configuratiehashes en expliciete goedkeuringsreferentie. 2025/2026 blijven
buiten bereik. Tot dan: categorieën latere stijging/daling en financieel betere
alternatieven = niet berekend, geen nul of veronderstelde gemiste winst.

De Research Optimizer mag deze definities voorstellen. Hij verandert geen
bestaande regels en kiest geen gunstige variant op basis van nieuwe resultaten.
