# Fase 6B — diagnose januari-uitvoering

28 oktober 2026. Basis ab7e5df03f856fa98a02038696e98877d47d6fca.

**Conclusie: technisch correct binnen het vastgelegde hypothetische model.** Alle vier weigeringen zijn correcte veiligheidsafwijzingen op de cashreservering. Entry en Execution gebruiken bewust verschillende prijsreferenties; er is geen technische fout vastgesteld en geen simulatiecode gewijzigd.

## Bewijs en afbakening

De bestaande database is uitsluitend via SQLite mode=ro geopend. De volledige bestandshash komt overeen met experiments/january_pilot/verification.json: `6c1e170a294e1db60ce5b9bafae9c2ee97a4297bca6cacd0a24dc5cee1b33d57`. Alle zeven geselecteerde entryberichten zijn gekoppeld aan hun batch, reserveringscheckpoint, settlement en eventuele buy-/sell-audit. Alleen januari-2024-candles van deze zeven instappen en drie exits zijn inhoudelijk onderzocht. Geen nieuwe backtest, replay, externe aanvraag of ander historisch venster. Decimal-herberekeningen betreffen uitsluitend deze reeds opgeslagen transacties.

## Zeven voorstellen

Alle bedragen in EUR; hoeveelheid in coins. Tijdstippen UTC. Prijs is inclusief de verwachte ongunstige spread/slippage en tickafronding. Fee is apart, naar boven afgerond. Cash is de totale beschikbare cash vóór reservering; er was geen andere positie/reservering.

| Nr | Coin | UTC | Voorstelprijs | Hoeveelheid | Stop-loss | Entryfee verwacht | Cash vóór | Gereserveerd incl. fee |
|---:|---|---|---:|---:|---:|---:|---:|---:|
|1|BTCEUR|2024-01-08 16:30:00+00:00|41210.34|0.00110|40448.12|0.04533138|200|45.37670538|
|2|BTCEUR|2024-01-08 17:15:00+00:00|41297.90|0.00110|40534.96|0.04542769|200|45.47311769|
|3|BTCEUR|2024-01-08 17:30:00+00:00|41467.55|0.00110|40704.36|0.04561431|200|45.65991931|
|4|ETHEUR|2024-01-08 21:00:00+00:00|2137.80|0.01880|2092.00|0.04019064|200|40.23083064|
|5|ETHEUR|2024-01-08 21:30:00+00:00|2141.67|0.01880|2095.87|0.04026340|200|40.30365940|
|6|ETHEUR|2024-01-10 10:15:00+00:00|2216.95|0.01470|2156.89|0.03258917|199.00408541|32.62175417|
|7|SOLEUR|2024-01-11 12:00:00+00:00|95.48|0.22067|91.32|0.02106958|198.01550775|21.09064118|

### Verwachte kosten per voorstel

Baseline per zijde: fee 0,1%, halve spread 0,05% en slippage 0,1%. Onderstaande impact is voor entry op de laatste close; tickkosten zijn het resterende ongunstige afrondingsverschil. Zij zitten al in de voorstelprijs en worden niet nogmaals van cash afgetrokken. Stop-exitfee is de verwachte fee bij de vastgelegde stop na verkoopimpact, geen garantie bij gaps.

| Nr | Verwachte spread EUR | Slippage EUR | Tickimpact EUR | Stop-exitfee verwacht EUR |
|---:|---:|---:|---:|---:|
|1|0.0226317355000000|0.0452634710000000|0.0000077935000000|0.04442619|
|2|0.0226798220000000|0.0453596440000000|0.0000065340000000|0.04452157|
|3|0.0227729920000000|0.0455459840000000|0.0000020240000000|0.04470763|
|4|0.0200651460000000|0.0401302920000000|0.0001525620000000|0.03927057|
|5|0.0201015240000000|0.0402030480000000|0.0000434280000000|0.03934314|
|6|0.0162701070000000|0.0325402140000000|0.0001406790000000|0.03165866|
|7|0.0105182355500000|0.0210364711000000|0.0015457933500000|0.02012070|

### Risk Engine en uitvoering

Alle zeven voorstellen kregen vóór reservering `risk_approved=True` en de reden “centrale Risk Engine akkoord; cash en positieplaats gereserveerd”. Goedkeuring geldt voor het voorstel op de laatste gesloten candle; zij is geen onvoorwaardelijke filltoezegging.

| Nr | Gepland risico voorstel EUR | Volgende raw open | Uitvoeringsprijs* | Entryfee* | Benodigd incl. fee | Boven/onder reservering | Resultaat |
|---:|---:|---:|---:|---:|---:|---:|---|
|1|0.99494757|41174.80000000|41236.57|0.04536023|45.40558723|0.02888185|Geweigerd|
|2|0.99607426|41239.70000000|41301.56|0.04543172|45.47714772|0.00403003|Geweigerd|
|3|0.99699694|41408.18000000|41470.30|0.04561733|45.66294733|0.00302802|Geweigerd|
|4|0.99953321|2136.03000000|2139.24|0.04021772|40.25792972|0.02709908|Geweigerd|
|5|0.99986654|2138.25000000|2141.46|0.04025945|40.29970745|-0.00395195|Fill|
|6|0.99475783|2213.21000000|2216.53|0.03258300|32.61557400|-0.00618017|Fill|
|7|0.99007128|95.30000000|95.45|0.02106296|21.08401446|-0.00662672|Fill|

*Bij weigering zijn uitvoeringsprijs en fee uitsluitend de herberekende, niet uitgevoerde waarden; er is geen fee geboekt en geen crypto gekocht.*

Exacte afwijsreden voor voorstellen 1–4: **“ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging”**. Voorstellen 5–7 hebben succesvolle entry-settlements met reden “Vaste hypothese; volgende candle-open, onder voorbehoud van Risk Engine”.

Entry gebruikt laatste 15m-close; Execution gebruikt uitsluitend de volgende candle-open. Beide gebruiken dezelfde fee/spread/slippage, filters, quantity en stop. Reservering = q × voorgestelde buyprijs + afgeronde fee. Execution rekent dat opnieuw uit en weigert zodra werkelijk benodigd > reservering. Alle vier hadden nog €200 totale cash: dit is dus geen tekort aan totale cash, maar een striktere controle op het vooraf gereserveerde bedrag. Geen hoeveelheid vergroten/verkleinen of vrije cash bijboeken.

| Voorstel | A: veiligheidsafwijzing | B: orderfilteraannames als oorzaak | C: Entry/Execution-verschil | D: technische fout |
|---|---|---|---|---|
|1–4|Ja, exact volgens vastgelegde reserveringsregel|Nee: PRICE/LOT/MARKET_LOT/NOTIONAL-check op nieuwe prijs slaagt|Ja: volgende open hoger dan eerdere close; bewust faseverschil|Niet vastgesteld|
|5–7|Niet afgewezen; nieuwe prijs past binnen reservering|Geen filterafwijzing|Volgende open gunstiger; ongewijzigde hoeveelheid|Niet vastgesteld|

Bij 1–4 wordt de uitvoering al vóór een nieuwe Risk Engine-aanroep tegengehouden (`failure or _risk_reason`). Er is dus geen tweede vastgelegde riskgoedkeuring voor de gewijzigde prijs. Als aanvullende rekenkundige controle (geen alternatief uitvoeringsscenario) wordt het stoprisico op die nieuwe prijs respectievelijk €1,02382942, €1,00010429, €1,00002496 en €1,02663229: alle boven het toenmalige €1-budget. De primaire geregistreerde afwijsreden blijft de reservering.

De aangenomen filters beïnvloeden wel sizing en tick-/feeafronding, maar geen van de vier meldingen is een filterfout. Dit bewijst niet dat de echte historische Binance-filters gelijk waren. De strikte reserveringsregel kan zelfs kleine nadelige koersverschillen blokkeren; dat was vooraf beschreven in PHASE6B_PROTOCOL_PROPOSAL.md en is expliciet getest in test_gap_does_not_spend_unreserved_cash. Het achteraf versoepelen zou een andere uitvoeringsregel zijn.

## Drie verliezen

| Coin | Entry UTC | Exit UTC (registratie) | Hoeveelheid | Entryprijs | Stop | Exitprijs | Fees totaal | Netto EUR | Reden |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
|ETHEUR|2024-01-08T21:30:00+00:00|2024-01-09T00:45:00+00:00|0.01880|2141.46|2095.87|2092.72|0.07960259|-0.99591459|stop|
|ETHEUR|2024-01-10T10:15:00+00:00|2024-01-10T13:00:00+00:00|0.01470|2216.53|2156.89|2153.65|0.06424166|-0.98857766|stop|
|SOLEUR|2024-01-11T12:00:00+00:00|2024-01-11T16:00:00+00:00|0.22067|95.45|91.32|91.18|0.04118366|-0.98344456|stop|

### Definitie en controle van R

1R = het geplande euroverlies naar de initiële stop, inclusief beide fees, spread, slippage en ongunstige afronding. Voor traceerbaarheid staan zowel het oorspronkelijk goedgekeurde voorstelrisico als het werkelijk bij entry geaudite risico hieronder. De gunstigere entry-open verlaagt dat laatste. Verliesomvang in R wordt positief weergegeven; de netto-P/L is negatief. Het 0,5%-budget is een bovengrens, niet automatisch de R-noemer.

| Coin / entry | Voorstel-1R EUR | Werkelijk entry-1R EUR | Risicobudget EUR | Verlies / voorstel-R | Verlies / entry-R |
|---|---:|---:|---:|---:|---:|
|ETHEUR 2024-01-08T21:30:00+00:00|0.99986654|0.99591459|1.000|0.996047523|1|
|ETHEUR 2024-01-10T10:15:00+00:00|0.99475783|0.98857766|0.99502042705|0.993787262|1|
|SOLEUR 2024-01-11T12:00:00+00:00|0.99007128|0.98344456|0.99007753875|0.993306825|1|

Alle drie verliezen zijn exact **1 entry-R**: geen stopgap. Elke exitbar heeft open boven de stop en low op/onder de stop.

| Exit UTC | Bar-open | Bar-low | Raw exit = min(open, stop) |
|---|---:|---:|---:|
|2024-01-09T00:45:00+00:00|2122.96000000|2094.36000000|2095.87|
|2024-01-10T13:00:00+00:00|2173.15000000|2145.50000000|2156.89|
|2024-01-11T16:00:00+00:00|92.65000000|91.09000000|91.32|

Verkoopprijs = floor_tick(raw_exit × 0,9985); aankoopprijs = ceil_tick(raw_open × 1,0015). Fees per zijde naar boven op €0,00000001. Netto = q × (exitprijs − entryprijs) − entryfee − exitfee. Alle drie regels zijn exact herberekend; bedragen sluiten aan op audit en trades. Stop en orderfilterchecks slagen. Geen fees/spread/slippage dubbel geteld.

Geen winsttarget. Alle exitbars openen vóór de deadline en raken de stop. Ook SOL: bar 15:45–16:00 raakt de stop; haar open ligt vóór de 16:00-deadline, zodat dit volgens de bestaande prioriteit een stop is, geen tijdexit. De geregistreerde exittijd is candle-close, geen bewezen intrabar-filltijd. Er is geen trigger voor een eerdere veiligheids- of tijdexit in deze opgeslagen exitbeslissingen.

Som netto = −€2,96793681; fees = €0,18502791; €200 + netto = €197,03206319. Alle posities gesloten, zes unieke fills, geen dubbele uitvoering. De drie negatieve trades tellen gezamenlijk voor de bestaande verliesreekspauze; coinwissel reset die niet.

## Tests en conclusie

120 tests geslaagd, 0 mislukt: tests/test_joint_portfolio.py, tests/test_trade_agents.py en tests/test_streaming.py. Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. Dit zijn synthetische contract-/risico-/kosten-/stop-/hersteltests, geen nieuwe historische rendementsrun. Aanvullend zijn voor deze opgeslagen januari-entries reservering, filters, exposure en Decimal-kosten exact gecontroleerd. Voor de drie posities zijn respectievelijk 13, 11 en 16 reeds opgeslagen januari-bars gecontroleerd: geen eerdere stopdoorbraak vóór de geregistreerde exitbar. De databasebestandshash is onveranderd gebleven.

**Technisch correct** binnen de gepubliceerde aannames. Geen simulatiecodewijziging nodig. A en het bewuste prijsverschil C verklaren de vier weigeringen; B is niet de directe oorzaak en D is niet vastgesteld. Geen alternatieve uitvoering gesimuleerd of filters aangepast. Geen statistische conclusie uit drie trades; geen bewijs van feitelijke historische orderuitvoerbaarheid. Onafhankelijke testperiode gesloten.

Bronnen: experiments/january_pilot/{protocol,manifest,result,verification}.json; de hash-gecontroleerde januari-checkpointdatabase; crypto/trade_agents.py (EntryAgent/ExitAgent), crypto/joint_portfolio.py (_evaluate/_execute), crypto/research_execution.py (risicohercontrole), crypto/sim_execution.py (kosten, filters en ledger). Alleen dit rapport wordt gecommit.
