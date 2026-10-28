# Fase 6E — onderzoeksbasis gecontroleerd, nieuwe vergelijkingen geblokkeerd

Basis: `2a7efedaefd755bcc7ae190102fd0fba015e1725`, bij aanvang schone branch `work`;
GitHub main wees naar dezelfde commit. Geen lopende onderzoeksrun aangetroffen.
**Geen nieuwe historische patroonvergelijkingen uitgevoerd.** De expliciete
stopvoorwaarde van de opdracht is toegepast: de bestaande preregistratie dekt de
gevraagde uitbreiding niet. Dit rapport rond de voorbereiding af, niet de empirische
fase 6E. 2025-validatie en de onafhankelijke 2026-test blijven gesloten.

## Onderzoeksbasis en ontbrekende preregistratie

PHASE6D_MISSED_OPPORTUNITIES_REPORT.md, experiments/phase6d/protocol.json,
de registratie, het bronmanifest, de verificatie, RESEARCH_PROTOCOL.md en de
bestaande 6B/6C-rapporten zijn gecontroleerd. Het oorspronkelijke fase-6D-protocol
registreert regime/richting en enkele gemiddelden, maar geen RSI-verandering,
volume, nieuwe featuregroepen, afhankelijke onzekerheidsberekening of uitgebreide
familie van toetsen. Het oorspronkelijke algemene protocol zegt bovendien:
'Extra plannen, folds, benchmarks en selectie-effecten vereisen een expliciet
uitgebreid analyseplan en correctie vóór enige claim.'

De gebruikersopdracht zegt: 'Als de bestaande preregistratie onvoldoende is om
nieuwe kenmerken, groepen of vergelijkingen verantwoord te onderzoeken, stel eerst
een afzonderlijk analyseprotocol op en stop vóór de nieuwe uitkomstvergelijkingen.'
Daarom is PHASE6E_ANALYSIS_PROTOCOL_PROPOSAL.md gemaakt. Het beschrijft 27 causale
kenmerken, 332 vooraf bepaalde contrasten, tijdsblok-bootstrap, Holm-correctie,
vaste ontbrekendheids- en minimumdekkingsregels. Het ontwerp heeft status
**proposal_requires_approval**. Publicatie of een inhoudshash is geen goedkeuring.

Er is geen featureextractie tegen historische labels uitgevoerd, geen nieuwe
HOLD/pauzetabel gemaakt en geen EMA-featurevergelijking berekend. De 103.344 labels
zijn als bronbestand gecontroleerd en gebonden, niet opnieuw gegenereerd of als
nieuwe onafhankelijke steekproef aangemerkt. Het bestaande onderzoekregister is
niet gewijzigd; de nieuwe registratie is uitsluitend een voorstelregistratie.

## Reeds bekende resultaten — uitsluitend bronverwijzing

Onderstaande aantallen zijn overgenomen uit de bestaande rapporten, geen nieuwe
fase-6E-bevindingen. De ruwe labels zijn niet opnieuw gegroepeerd.

| Bestaande 6D-steekproef | Aantal | Bruto positief | Bruto negatief | Neutraal | Netto positief |
|---|---:|---:|---:|---:|---:|
| Alle momenten, overlappend | 103344 | 53454 | 49811 | 79 | 31366 |
| Oorspronkelijke HOLD, overlappend | 101391 | 52483 | 48829 | 79 | 30721 |
| UTC4h, alle coins | 6459 | 3344 | 3110 | 5 | 2013 |
| UTC4h, HOLD | 6307 | 3261 | 3041 | 5 | 1959 |

Bestaande HOLD-aantallen per coin: BTC 34.067, ETH 33.906, SOL 33.418; bestaande
netto-positieve aantallen respectievelijk 8.801, 9.820, 12.100. De vaste 0,001-coinunit
is niet EUR-gelijkgewogen en voldoet niet noodzakelijk aan minimale ordergrootte.
Deze verschillen zijn geen ranking van verhandelbare winst.

Het oude rapport beschrijft voor alle overlappende observaties een gemiddelde
voorafgaande RSI van 50,518223 bij positieve en 51,432080 bij negatieve labels,
en regime-/EMA-richtingstabellen. Geen nieuwe HOLD-, timeframe- of volumepatronen
zijn vastgesteld. Die oude gemiddelden bewijzen geen voorspellende werking;
selectie, coin-correlatie en overlappende horizons beperken de interpretatie.

UTC4h verwijdert overlap binnen een coin, niet gelijktijdige crosscoin-afhankelijkheid
of opeenvolgende regimes. Het nieuwe voorstel resamplet daarom gezamenlijke
UTC-tijdgroepen. Geen overlappende koerswinsten zijn opgeteld tot portefeuillewinst.

## Verliesreekspauze

Volgens de al gecontroleerde 6C/6D-audit is aligned_trend vanaf 11 januari 16:00 UTC
gepauzeerd na drie verliezen. Er zijn 793 expliciete pauze-afwijzingen: in 6D waren
384 daarvan later bruto positief, 409 negatief en 247 netto positief in de vaste
prijsdiagnose. **Dit is niet het aantal HOLD-momenten tijdens de pauze.**

Het gevraagde nieuwe aantal HOLDs tijdens/buiten pauze en hun feature-/labelverschillen
zijn **niet berekend**. Daarvoor definieert het voorstel de ledgerprefix en exacte
beoordelingsvolgorde op t. Een bijna jaarlange pauze en slechts enkele dagen ervoor
zijn bovendien sterk verward met kalenderregime; geen causaal experiment. De vaste
minimumblokregel zal de inferentiële pauzevergelijking waarschijnlijk blokkeren.

Een positief endpoint tijdens pauze had geen Risk-goedkeuring, geen gereserveerd
saldo en geen toegestane orderketen. Intraperiode-stops, kosten en orderfilters
kunnen de uitkomst wijzigen. Geen risicoreset of versoepelingssimulatie uitgevoerd.

## EMA Trend — bestaande resultaten, geen nieuwe featurevergelijking

Bronnen: PHASE6B_DEVELOPMENT_2024_REPORT.md en PHASE6C_DIAGNOSTICS_REPORT.md.
Deze jaartotalen hebben het oorspronkelijke replay-universum; toekomstige
featurevergelijkingen moeten expliciet op het kortere 6D-instapuniversum aansluiten.

| Bestaande baseline | aligned_trend | EMA Trend |
|---|---:|---:|
| BUY-kandidaten | 1953 | 39772 |
| Goedgekeurde entries | 7 | 7 |
| Bij uitvoering geweigerd | 4 | 2 |
| Gesloten virtuele trades | 3 | 5 |
| Netto EUR | -2,96793681 | 0,58224413 |
| Geboekte fees EUR | 0,18502791 | 0,42692417 |
| Tijd met positie, % | 0,11384335 | 0,24191712 |
| Gemiddelde kapitaalblootstelling, % | 0,01739135 | 0,05150601 |
| Begin verliesreekspauze, UTC | 11 januari 16:00 | 9 januari 12:15 |

Beide gebruiken dezelfde oorspronkelijke kosten-/risicoregels. Spread en slippage
zitten in de fillprijzen en zijn niet nogmaals bij de fee opgeteld. De bestaande
EMA-nettowinst steunt op één winnaar; beide bestaande kostenscenario's eindigden
negatief. Drie versus vijf trades is onvoldoende bewijs van superioriteit.

De bestaande selectieregels verschillen: aligned_trend vereist bullish 1h-regime
én up op drie timeframes; EMA gebruikt de bestaande 1h EMA9/21-afstand >0,002.
Deze codefeiten zijn geen nieuw berekende marktkenmerken. Het eerdere 6C-rapport
meldt verschillende risicoblokkeringen, waaronder EMA-sizing boven de toegestane
risicocontrole na winst. Geen sizing- of andere regel aangepast.
Welke concrete regimes/RSI/volumes EMA selecteerde tegenover aligned_trend blijft
onberekend totdat de nieuwe vergelijkingsregistratie is goedgekeurd.

## Voorstellen en volgende stap

PHASE6E_HYPOTHESES.md bevat vijf voorstellen, gerangschikt op onderzoekbaarheid:
scannerscore; RSI-niveau/verandering; EMA-afstanden/timeframes/selectie;
ATR/volume; pauzecontext. Het zijn hypotheses, geen uitkomsten van een nieuwe
zoektocht en geen automatisch gepromoveerde strategieën. De bestaande optimizer
heeft geen kandidaatbacktest of goedkeuring aangemaakt.

Aanbevolen volgende stap: expliciete beoordeling van het afzonderlijke protocol,
met name de 27 features, 332 contrasten, zeven-dagenblokken, Holm-correctie,
minimumdekking en eventvolgorde van de pauze. Pas na goedkeuring een technisch
gevalideerde extractie en een nieuw uitvoeringsmanifest registreren, vóór nieuwe
uitkomstvergelijkingen. Een wijziging van deze keuzes krijgt een nieuwe versie.
Het voorstel opent geen 2025/2026-periode en autoriseert geen ordersimulatie.

## Integriteit, tests en middelen

De 15.057.117.184-byte ontwikkeldatabase is volledig gehasht, zonder SQL-selectie
van nieuwe uitkomsten. De hash komt overeen met de bestaande auditregistratie:
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa`.
Oude fase-6D-manifestbindingen en financiële/resultaat-/checkpointartefacten zijn
gecontroleerd. Geen bestaande bron-, strategie-, Risk Engine- of executiemodule
gewijzigd. Alleen nieuwe voorstel-/controlebestanden en de voortgangsdocumenten.

scripts/phase6e_protocol.py bevat alleen voorstelbinding en een synthetisch te
testen tijd-/featurecontextcontract; geen historische reader, statistiekengine,
backtestrunner of activatiepad. Zelfs een geldig voorstel geeft PermissionError
voor historische uitvoering. Een JSON-vlag op true zetten maakt het voorstel ongeldig.
De contextcheck is geen volledige implementatie van de voorgestelde featureextractie.

Verificatie-uitkomst, volledige bronhashes en gemeten middelen staan in
experiments/phase6e/integrity.json. Voor- en nacontrole elk begrensd op 300 seconden
met 1 GiB adresruimte. Tests begrensd op 300 seconden en 1 GiB adresruimte.
De latere statistische analyse is niet uitgevoerd en heeft geen gemeten capaciteit.

Volledige suite: **456 geslaagd, nul mislukt** in 16,06 s; alle 432 bestaande tests
behouden plus 24 deterministische tests voor registratiebinding/reproduceerbaarheid,
ontbrekende definities, verboden permissiewijziging, UTC/grensdata, ontbrekende en
toekomstige featurecontext. Eén bestaande Starlette/AnyIO-deprecationwaarschuwing.
Nieuwe tests gebruiken uitsluitend synthetische context, geen historische labels.
De bestaande suite gebruikt haar eerder bekende fixtures; geen nieuwe historische
validatie-/testanalyse. Geen financiële resultaten of auditlogs gewijzigd.

De voorbereiding is afgerond; de **empirische fase 6E blijft geblokkeerd** tot
expliciete goedkeuring van het nieuwe analyseprotocol. Niet-berekende tellingen,
patronen en intervallen worden niet als nul of als geslaagd resultaat gepresenteerd.
