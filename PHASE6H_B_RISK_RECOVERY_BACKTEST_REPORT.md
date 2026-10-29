# Fase 6H-B — onvolledige diagnostische run, geverifieerd checkpoint

**Geen voltooide financiële jaarvergelijking.** De eenmalige replay stopte op de
vooraf vastgelegde 1.800-secondenlimiet. Januari t/m november zijn volledig verwerkt;
december is verwerkt tot de beslisgrens **11 december 2024 19:45 UTC**. De volgende
nog niet verwerkte grens is 11 december 20:00 UTC. Er ontbreken 1.937 van de
34.465 geplande replay-grenzen. Er is niet automatisch hervat of opnieuw gestart.

## Toestemming, preregistratie en metadata

De gebruiker gaf na de eerdere metadata-stop expliciet toestemming om exact de
bestaande hypothetische historische orderfilters te gebruiken. De oude blokkering
blijft behouden in BLOCKED_METADATA_REPORT.md en de oude manifest-/registratieversie.
De filters blijven `assumed`, zonder bewezen historische known_at/validiteitsperiode.
Geen actuele filters als historische feiten gebruikt en geen nieuwe downloads.

Uitsluitend BTC/EUR, ETH/EUR, SOL/EUR en ontwikkeling [2024-01-01,2025-01-01) UTC.
Warm-up 1–7 januari, entries vanaf 8 januari 00:00, laatste toegestane entry
31 december 19:45. De eindgrens is uitsluitend de waardering van 2024-candles;
validatie 2025 en onafhankelijke test 2026 blijven gesloten. Dit reeds onderzochte
ontwikkeljaar kan geen onafhankelijke bevestiging leveren. Geen ATR-kostenfilter,
extra kostenvariant, optimalisatie, echte of automatische paper-orders.

De registratie is vóór financiële uitvoering op main gezet: e288d61 en c20fafc.
Geldig uitvoeringsmanifest: `16aeac432cb79b0d1a87aa027acef6c20cdf815da6455f27ece7a576c87534b4`.
Dit read-only, inhoudsgebonden manifest bindt code-, bron-, configuratiehashes,
inputseal, expliciete goedkeuring en budget. Git maakt eerdere versies controleerbaar;
geen claim van externe, onveranderlijke WORM-opslag.

## Geïsoleerde historische adapter

Nieuwe module crypto/historical_recovery.py, uitsluitend aangeroepen door
scripts/phase6h_b_replay.py. Eigen database:
`/workspace/phase6h_b_recovery.sqlite3`. De oude database is alleen via een
uri=True read-only/query-only verbinding gelezen. Raw input wordt in begrensde
blokken van 256 rijen gekopieerd. De volledige gekopieerde inputseal komt exact
overeen met de gevalideerde baseline; er zijn geen nieuwe historische analyses
of prijslabels aangemaakt. V1 van de voorbereiding stopte vóór kopiëren/financiën
op een SQLite-URI-ATTACH-fout. De lege database, fout en oude manifestversie zijn
bewaard. De geteste V2-leesroute is opnieuw geregistreerd vóór de replay.

De adapter hergebruikt streamingrunner, rapporten, ledger, fillsimulator en centrale
Risk Engine. Alleen het verliesreeksveto wordt vervangen door dezelfde offline
review en timer/epochsemantiek als fase 6H-A. De bestaande historische toelatings-
en liquiditeitsgate is exact overgenomen en door een regressietest gebonden.
De actieve bot, Risk Engine, strategieën en oorspronkelijke auditdatabase zijn
niet aangepast. Eén oorspronkelijk €200-portfolio, één positie, maximaal 0,5%
gepland risico en 50% exposure; dagverlies 3%, drawdown 10% en noodstop behouden.

Baselinefilters ongewijzigd: tick €0,01, minimum/stap 0,00001, maximum 1.000.000,
minimum notional €10; marktorderfilters eveneens conform het geregistreerde oude
object. Fee 0,1% per zijde, spread volledig 0,1%, slippage 0,1% per zijde.
Decimal, nadelige tickafronding en feeafronding omhoog op 1e-8 EUR behouden.
Stop 2 oorspronkelijke 1h-ATR, horizon 4 uur, geen target, entry open N+1,
conservatieve gap-/stopuitvoering. Geen gunstige intrabarvolgorde verondersteld.

## Variant A — bestaande baseline, niet opnieuw uitgevoerd

| Maat | Opgeslagen volledige 2024-baseline |
|---|---:|
| Startkapitaal | €200 |
| Eindkapitaal | €197,03206319 |
| Nettoresultaat | −€2,96793681 |
| Netto portefeuillerendement | −1,483968405% |
| Gesloten trades / fills | 3 / 6 |
| Winstpercentage | 0% |
| Geboekte fees | €0,18502791 |
| Close-grid-drawdown | 1,483968405% |
| BUY-kandidaatsignalen | 1.953 |
| Goedgekeurde entries | 7 |
| Geblokkeerde BUY-voorstellen | 1.946 |
| Uitvoeringsweigeringen | 4 |
| Verliesreekspauze | Eén, permanent binnen de oude run |

Bron: experiments/development_2024/aligned_trend_baseline.json. Alleen bestaande
gegevens hergebruikt, geen baseline-replay. Voor de eerste hervatting zijn de eerste
drie trade-records van B financieel exact vergeleken met A, met uitzondering van
plan-afhankelijke order-ID's. Dezelfde cash €197,03206319 op 11 januari 16:00;
de beslissing op die grens lag nog vóór de derde afrekening. Bewijs in
baseline_prefix_check.json. Het eerste volgende beslismoment kende de pauze.

## Variant B — uitsluitend diagnostische stand tot het checkpoint

Deze stand heeft een andere einddatum dan de jaarlijkse baseline. Geen definitief
jaarverschil, jaarwinstpercentage of winstclaim wordt berekend. Alle jaarlijkse
vergelijkingsvelden blijven niet berekend totdat de resterende verwerking én
resultaatcontroles volledig zijn afgerond.

| Diagnose | Stand op 11 december 19:45 UTC |
|---|---:|
| Gecommitteerde replay-grenzen | 32528 |
| Gesloten trades | 85 |
| Cash / portefeuillewaarde, flat | €179,92423059 |
| Gerealiseerd resultaat tot checkpoint | €-20,07576941 |
| Geboekte fees tot checkpoint | €6,99473531 |
| BUY-kandidaatsignalen | 1890 |
| Geselecteerde/goedgekeurde entries | 161 |
| Geblokkeerde BUY-voorstellen | 1729 |
| Geweigerde uitvoeringen | 76 |
| Geactiveerde/afgeronde 24u-pauzes | 12 / 12 |
| Volledige 24u-intervallen tot checkpoint | 288 uur |
| Open positie / pending / reservering | geen / geen / nul |
| Drawdownpauze / dagverliespauze / noodstop | actief / niet actief / niet actief |

161 entrytoestemmingen resulteerden in 85 uitgevoerde entries en 76 geweigerde
uitvoeringen. De 85 entries zijn inmiddels gesloten. Alle 76 weigeringen hadden
de bestaande reden 'ongunstige open overschrijdt gereserveerde cash; geen
automatische verhoging'. Een kandidaat of toestemming is dus geen uitgevoerde trade.
Fees zijn niet alle economische frictie: spread, slippage en afronding zitten al
in de fills. Er wordt geen frictiesom opnieuw van het resultaat afgetrokken.

De drawdownbeveiliging is eenmaal geactiveerd. De geobserveerde conservatieve
ledger-drawdown is 10,037884705%; gerealiseerde marktschade kan de grens op de
triggerende candle overschrijden. De 10%-limiet is niet verhoogd. Het checkpoint
behoudt `drawdown_paused=true`; expiry heeft dit niet gewist. Er is geen reset
naar €200, geen risicopromotie en geen aanpassing van de 24 uur geweest.
De huidige epoch is 12; de teller sinds de laatste expiry is 2. Oude verliezen
blijven volledig geboekt. Alle 12 expiry-overgangen zijn onafhankelijk gecontroleerd
op behoud van cash, fees, positie, dagstatus, peak, drawdown en noodstop.

Redenverdelingen van coinbeoordelingen staan in partial_diagnostics.json, afzonderlijk
van BUY-voorstellen. Onder meer: 58 verliesreekspauze-afwijzingen en 87 drawdownpauze-
afwijzingen; niet-BUY-HOLDs en positie-/liquiditeitsafwijzingen zijn aparte categorieën.
Dit zijn diagnostische aantallen binnen de verwerkte periode, geen vermeden trades.

## Tijd, geheugen, onderbreking en herstel

Voorbereiding: 43.699 s, 54.965 MiB piek-RSS.
Replay: 1800.093 s, gestopt door de vaste 1.800s-alarmgrens. Het laatst
waargenomen procespiekgeheugen was 88.324 KiB (circa 86,25 MiB); dit is een
observatie kort vóór de stop, geen gegarandeerd exact eindpiekgetal. Limieten:
1,5 GiB adresruimte, RSS-stop 1.288.490.188 bytes, 2 GiB vrije schijf, nul netwerk.
Geen limiet verruimd. De voorgelegd aanvullende 300s-toestemming is nog niet
ontvangen en is niet gebruikt.

De poging voor 20:00 werd onderbroken tijdens statehashopslag; de transactie is
volledig teruggedraaid. Laatste checkpoint: revision 32786, kind
`evaluated`, hash `27dd947b3d573efa715edb726a09490d713e68535cb60b2d82f123047a0d82f2`.
Pending is null. Voor deze concrete toestand is de volgende te verwerken grens
11 december 20:00. Geen dubbele fill of gedeeltelijke transactie achtergebleven.
Een toekomstige hervatting moet input-/code-/beleidshashes opnieuw controleren en
vanaf dit checkpoint doorgaan, nooit opnieuw vanaf nul. Bij een ander checkpoint-
kind, bijvoorbeeld expiry vóór beslisbatch, moet eerst de nog onvoltooide batch
op dezelfde grens worden afgehandeld; niet blind een kwartier overslaan.

## Tests en controlebewijs

Alle **534 tests geslaagd**: 527 bestaande behouden en zeven nieuwe synthetische
adapter-/integratietests, 0 mislukt, één bestaande Starlette/AnyIO-waarschuwing,
18,84 s. Tests onder 180 s/1,5 GiB. Geen herhaling van de financiële jaarproef.

De onafhankelijke afsluitcontrole verifieert 32787 checkpoints,
85 unieke gesloten trades, de volledige auditketen en twaalf expiry-overgangen.
Cash = €200 + gerealiseerd resultaat, fees = som tradefees, geen positie/pending,
geen dubbele entry-/exit-ID. Na herstel van een formatteringsfout in de controle-
uitvoer is de volledige verificatie herhaald. Dat was geen financiële replay.
Verificatie: 63.971 s, 46.656 MiB piek-RSS,
onder 180 s en 1,5 GiB. Bron- en artifactbewijs onder experiments/phase6h_b/.

Alle **392 oorspronkelijk gevolgde bestanden** blijven byte-identiek aan c4edd8c.
De volledige oorspronkelijke financiële/auditdatabase heeft nog steeds SHA-256
`fa2290c6352550186da5dd4750ad35077b4d9cf2cd2684322368eb96b28aadfa` en lege WAL. Nieuwe resultaten/checkpoints staan
uitsluitend in de aparte onderzoeksdatabase; geen oude resultaten overschreven.

## Conclusie en resterende voorwaarden

De adapter en financiële checkpointconsistentie zijn getest; de geautoriseerde
jaarvergelijking is **niet afgerond wegens de tijdslimiet**. De diagnostische stand
wordt veiliggesteld als checkpoint, niet als definitieve jaarprestatie. De volledige
nieuwe SQLite-database blijft in de workspace en wordt wegens omvang niet in Git
opgenomen; Git bewaart code, manifesten, verificatie en de checkpointidentificatie. Volledige
A-versus-B-resultaten, eindkapitaal, winstpercentage, close-grid-drawdown en totale
kostenvergelijking blijven open totdat de resterende 1.937 grenzen en eindcontroles
zijn uitgevoerd onder een expliciet goedgekeurd aanvullend budget.

Dit is hypothetisch onderzoek met onbewezen orderfilters en een OHLCV-fillsimulatie,
geen werkelijk haalbaar rendement. 2024 is reeds bekeken, drie oorspronkelijke
baselinetrades en afhankelijke coins leveren geen onafhankelijke winstvalidatie.
Geen parameteroptimalisatie, ATR-filter, extra kostenscenario of strategiepromotie.
Validatie 2025 en onafhankelijke test 2026 blijven gesloten. Stop bij dit checkpoint
en wacht op de nog openstaande expliciete hervattoestemming.
