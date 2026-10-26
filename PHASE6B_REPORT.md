# Fase 6B — preregistratiecontrole; historische evaluatie geblokkeerd

Controle uitgevoerd op 26 oktober 2026 vanaf
`b1c6049ff36e34b3c1fd6adec4cf5f490a6dd289`. De werkmap was bij aanvang schoon.

**De gevraagde historische evaluatie is niet uitgevoerd.** De controle vooraf is
wel afgerond. Er ontbreekt een eenduidig, volledig vastgelegd gezamenlijk
onderzoeksplan voor de zesmunten-evaluatie. Daarom is deze expliciete stopvoorwaarde
uit de opdracht toegepast:

> Indien de bestaande preregistratie onvoldoende duidelijk is, stop vóór het
> bekijken van nieuwe historische resultaten en rapporteer wat nog moet worden
> vastgelegd.

Geen nieuwe Binance-verzoeken, downloads, historische evaluatieruns of nieuwe
validatie-uitkomsten zijn bekeken. De onafhankelijke historische test is niet
geopend. Ontbrekende registratie geldt niet als bewijs dat een periode onaangeraakt is.

## Onderzochte bronnen

Gelezen: PHASE6A_REPORT.md, RESEARCH_PROTOCOL.md, PROGRESS.md, NEXT_STEPS.md,
ResearchPlan, JointPolicy, DecisionPolicy, IndicatorConfig, Limits,
OfflineResearchOptimizer, BacktestRunner en de bestaande smoke-testscripts.

`experiments/phase6b_preregistration_audit.json` bewaart de basiscommit, SHA-256 van
de twee eerdere experimentartefacten, planfingerprints, oorspronkelijke plannen,
bron-/periode-/datasetmetadata, opgeslagen checksumrecords en configuratiewaarden.
Dit bestand is een **controleverslag, geen vrijgegeven fase-6B-onderzoeksplan**.

In de repository is geen operationele onderzoeksdatabase gevonden, ook niet tussen
genegeerde databasebestanden. Vier toegankelijke projectdatabases in `/tmp` zijn
met SQLite `mode=ro` gecontroleerd. Daarin ontbreken de latere research_plans,
research_exposures en joint_protocols-tabellen; de oudere periods-tabellen zijn leeg.
Alleen registratie- en importmetadata zijn uitgelezen. Geen nieuwe prijsseries,
indicatoren of rendementen zijn geëvalueerd.

De fase-4B-database was tijdelijk en is volgens het bestaande script/rapport
verwijderd. Fase 5 gebruikte een in-memorydatabase. Hun JSON-artefacten bewaren
plannen, maar vervangen geen volledig duurzaam register van eerdere inzage.
De databases onder `/tmp/pytest-of-agent` zijn testartefacten en vormen geen
historische studiepreregistratie. Ook de CLI-fixture is expliciet synthetisch.

De bestandszoekactie kon `/tmp/codex-daemon-1000` niet lezen; deze niet-projectmap
is niet verder benaderd. Databases buiten deze toegankelijke omgeving of op andere
machines zijn niet onderzocht. Volledigheid van een extern register wordt niet geclaimd.

## Teruggevonden onderzoeksperioden

Halfopen bereiken `[start, eind)`, alle grenzen om 00:00 UTC. Het lezen van deze
registratiemetadata is geen inzage in marktuitkomsten van de onafhankelijke test.

| Artefact | Coins | Ontwikkeling | Validatie | Onafhankelijke test |
|---|---|---|---|---|
| phase4b_smoke.json | BTC/EUR | 2025-01-10 → 2025-01-11 | 2025-01-12 → 2025-01-13 | 2025-01-15 → 2025-01-16 |
| phase5_smoke.json | BTC/EUR, ETH/EUR | 2025-01-10 → 2025-01-12 | 2025-01-13 → 2025-01-14 | 2025-01-15 → 2025-01-16 |

Planfingerprints:

- Fase 4B: `abcdf19dac30fe1423b7aacd1de11313a495373af460923a78cf96e3c28695d4`.
- Fase 5: `af69653d7015072bec3b75c5b4e19a0328d382f48490d1aa7cc81b22177d5a86`.

Beide artefacten melden independent_test_opened=false. Het fase-4B-protocol bevat
geen testautorisatie. Deze gereserveerde testgrenzen blijven beschermd; zij zijn
niet hernoemd tot ontwikkeling of validatie. De verschillende validatievensters
horen bij verschillende oudere plannen en vormen geen vanzelfsprekend nieuw
zesmunten-plan. Zonder compleet inzageregister is hun daadwerkelijke
onaangeraaktheid niet gegarandeerd.

## Bekende datasets en eerdere blootstelling

Deze gegevens waren vóór fase 6B al geïmporteerd of als fixture opgeslagen.
Volledige URL's, dataset-SHA's en zeven archiefchecksums staan in het auditbestand.

| Bestaande bron | Coins/interval | Dekking UTC | Status |
|---|---|---|---|
| Officiële dagelijkse Spot-archieven, lokale ZIP/CHECKSUM en fase-2B-database | BTC/EUR en ETH/EUR; 15m, 1h, 4h | 2025-01-10 → 2025-01-11 | 6 archieven, 252 candles; reeds bekende data |
| Officieel dagelijks Spot-archief | BTC/EUR; 1h | 2024-12-31 → 2025-01-01 | 1 archief, 24 candles; gebruikte ms/us-formaatfixture |
| Publieke Binance-API-importmetadata, fase 3 | BTC/EUR en ETH/EUR; 4h | 2025-01-05 16:00 → 2025-01-11 00:00 | 32 candles per coin; bestaande indicatorhistorie |
| Zelfde fase-3-import | BTC/EUR en ETH/EUR; 1h | 2025-01-09 16:00 → 2025-01-11 00:00 | 32 candles per coin |
| Zelfde fase-3-import | BTC/EUR en ETH/EUR; 15m | 2025-01-10 16:00 → 2025-01-11 00:00 | 32 candles per coin |
| CLI-fixture, fixture:synthetic-v1 | BTC/EUR; 1h | 2026-01-01 → 2026-01-02 | Synthetisch; geen Binance-beschikbaarheidsbewijs |

Het fase-4B-script beschrijft tevens analyses op 2025-01-10 om 12:00 en 16:00 met
32 candles per timeframe. De vroegste aangevraagde 4h-warm-upgrens volgt daaruit
als 2025-01-05 04:00. Dit is afgeleid uit het bestaande script; de tijdelijke database
is niet teruggevonden. Ook eerdere warm-up-inzage moet in het register worden opgenomen.

De bestaande automatische tests valideerden de oude lokale ZIP-bestanden opnieuw
tegen de opgeslagen officiële checksums. Dit is geen nieuwe netwerkcontrole of
bewijs van beschikbaarheid van alle munten in een nog te kiezen periode.

| Gevraagde coin | Vastgesteld | Fase-6B-status |
|---|---|---|
| BTC/EUR | Bovenstaande reeds bekende officiële snapshots aanwezig | Nog niet toegelaten tot een nieuwe evaluatie; periode en geschiktheidsregel ontbreken |
| ETH/EUR | Bovenstaande reeds bekende officiële snapshots aanwezig | Zelfde beperking |
| SOL/EUR | Geen passende lokale officiële dataset in deze inventaris | Niet onderzocht na de stop; niet als historisch onbeschikbaar bestempeld |
| XRP/EUR | Geen passende lokale officiële dataset in deze inventaris | Niet onderzocht na de stop |
| ADA/EUR | Geen passende lokale officiële dataset in deze inventaris | Niet onderzocht na de stop |
| LINK/EUR | Geen passende lokale officiële dataset in deze inventaris | Niet onderzocht na de stop |

Er is geen uitkomstgestuurde coinselectie toegepast. Een hedendaagse listing of een
achteraf volledig archief bewijst niet dat een instrument en zijn informatie op
ieder vroeger beslismoment beschikbaar waren.

## Gecontroleerde bestaande parameters

Dit zijn bestaande waarden, geen nieuw gekozen of geoptimaliseerde fase-6B-parameters.

| Onderdeel | Instelling |
|---|---|
| Gezamenlijke portefeuille | €200; maximaal één open positie |
| Gepland risico | Maximaal 0,5% van min(€200, actuele cash), inclusief kosten |
| Instap-exposure | Maximaal 50% |
| Verliesbescherming | 3% dagverlies, 10% drawdown, pauze na 3 opeenvolgende verliezen, noodstop |
| Actieve standaardhypothese | aligned_trend |
| Overige bestaande hypotheses | regime_momentum, sideways_recovery; niet automatisch gecombineerd of geselecteerd |
| Indicatoren | EMA 9/21, RSI 14, ATR 14, momentum 10, structuur 5, sideways-grens 0,002 |
| Timeframes | 15m, 1h, 4h; afgesloten UTC-candles |
| Instap en exit | Volgende candle-open, stop 2 ATR, horizon 4 uur, geen target |
| Kosten | Fee 0,1% per zijde, volledige spread 0,1%, slippage 0,1% per zijde |
| Precisie | Decimal, ongunstige tickafronding, fee naar boven afgerond |
| Selectie | Scannerscore dalend, UTC-rotatie bij gelijke scores |
| Sentiment | Unknown is neutraal/onbekend; geen positief nieuws |
| Bewijsgrens | Minimaal 30 trades is een ondergrens, geen bewijs van superioriteit |

De algemene bestaande harde trade-risicogrens van Limits blijft 1%; de
onderzoeksworkflow gebruikt de strengere 0,5%. Geen grens is verhoogd.

## Vóór hervatting vastleggen

1. **Compleet inzageregister.** Herstel eerdere echte plannen, bekeken perioden en
   warm-upbereiken; houd synthetische fixtures apart. Onbekende herkomst blijft onzeker.
2. **Exacte perioden en splits.** UTC-begin/eind voor ontwikkeling, validatie,
   warm-up, embargo en beschermde testvensters van alle zes paren. Geen keuze op
   bekeken rendementen en geen herlabeling van bestaande holdouts.
3. **Onderzoeksfamilie.** aligned_trend is de huidige standaard. Leg vast of alleen
   deze gezamenlijke strategie wordt getoetst of ook afzonderlijk gelabelde secundaire
   studies. Geen achteraf gekozen combinatie of beste hypothese.
4. **Historisch universum.** Regels voor listing/delisting, historische filters,
   publicatietijd, ontbrekende candles en nieuwe paren, uitsluitend met toen bekende
   informatie. De huidige mode vereist uniforme dekking en één scanneruniversum.
   Hele perioden achteraf uitsluiten vanwege latere datagaten kan selectiebias geven;
   daarvoor ontbreekt een fase-6B-regel.
5. **Gezamenlijke benchmarks.** Allocatie, prioriteit, in-/uitstappen, periodegrenzen,
   exposure en kosten. De bestaande EMA-benchmark werkt per coin geïsoleerd;
   buy-and-hold zonder stop wordt wegens de risicogrens niet gesimuleerd. Een eventuele
   marktrendementreeks moet apart worden gelabeld. Tel geen losse €200-ledgers op.
6. **Uitvoering en metingen.** Lookback/warm-up, beschikbaarheidslatentie, open posities
   bij periode-einde, houdduur, tijdsexposure, drawdown en overgang tussen splits.
   Eén doorlopende ledger binnen een run; geen kas- of pauzereset per downloadbatch.
7. **Gevoeligheden.** De oudere workflow kent verdubbelde kosten met opnieuw berekende
   ordergroottes en rekenkundig verwijderen van maximaal drie grootste winnaars.
   Leg de gezamenlijke scenario's en een exact criterium voor uitzonderlijke
   verliezers vooraf vast. Onderscheid rekenkundige verwijdering van hersimulatie;
   kies geen aantal op grond van resultaten.
8. **Geteste gezamenlijke evaluatierunner.** JointPortfolio en DecisionAgent weigeren
   validatie en meer dan 192 candles per coin. De oude BacktestRunner gebruikt
   geïsoleerde ledgers en is geen vervanging. Test de benodigde uitbreiding en
   gezamenlijke metrics/benchmarks met fixtures vóór nieuwe uitkomsten. Omzeil de
   blokkade niet door onderzoeksdelen te hernoemen of het testslot te verwijderen.

De ontbrekende afspraken zijn niet als een al volledig geregistreerd plan
gepresenteerd. Bestaande parameters en bots zijn niet veranderd om toch prestaties
te kunnen tonen.

## Prestaties en benchmarks

**NB = niet berekend; evaluatie niet gestart.** NB betekent niet nul trades,
nul rendement of aangetoonde afwezigheid van signalen.

| Gevraagde maatstaf | Gezamenlijke fase-6B-strategie |
|---|---|
| Aantal trades | NB |
| Winrate | NB |
| Gemiddelde winst / gemiddeld verlies | NB / NB |
| Nettoresultaat EUR / procent | NB / NB |
| Verwachtingswaarde per trade | NB |
| Profit factor | NB |
| Maximale drawdown | NB |
| Gemiddelde houdduur | NB |
| Blootstelling aan de markt | NB |
| Resultaten per BTC, ETH, SOL, XRP, ADA, LINK | Alle NB |
| Afgewezen historische signalen en redenen | NB; auditblokkades zijn geen handelssignaalafwijzingen |
| Hogere handelskosten | NB |
| Uitzonderlijke winnaars / verliezers | NB / NB |

| Vergelijking | Status |
|---|---|
| EMA-trendbenchmark | Niet uitgevoerd; gezamenlijke allocatie en periode ontbreken |
| Buy-and-hold als handelsbenchmark | Niet uitgevoerd; onbegrensde variant voldoet niet aan gepland-risicoregel |
| Marktrendement | Niet berekend; instrumentweging en venster niet vastgelegd |
| Statistische superioriteit | Geen conclusie mogelijk |

Oude fase-4B-uitkomsten zijn niet opnieuw berekend of als gezamenlijke fase-6B-
prestaties gepresenteerd. Er zijn geen winstclaims.

## Verificatie en opleveringsstatus

`.venv/bin/python -m pytest -q`: **287 tests geslaagd, 0 mislukt**.
Eén bestaande Starlette/AnyIO-deprecationwaarschuwing. Tests voor de gedeelde balans,
reserveringen, reproduceerbaarheid, toekomstige informatie, risico en testvergrendeling
zijn behouden. Enkele tests openen expliciet synthetische fixture-testperioden;
dat is geen toegang tot de echte historische holdout. Bekende lokale archieffixtures
zijn opnieuw gecontroleerd, zonder nieuwe fase-6B-resultaten te onderzoeken.

Geen runtimewijzigingen of nieuwe tests waren nodig voor deze metadata-/documentatie-
controle. Strategieën, simulators, risicolimieten en oudere resultaten blijven intact.
PROGRESS.md en NEXT_STEPS.md beschrijven de blokkade. De omgeving viel tijdelijk
weg na de succesvolle tests; bij herstel waren basiscommit en auditbestand behouden.
De documentatie is vervolgens opgeslagen.

De controle vooraf is afgerond; **de historische fase-6B-evaluatie blijft geblokkeerd**.
Er is geen volgende fase gestart.
