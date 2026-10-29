# Fase 6G — Protocol A: verliesreekspauze met herstel na 24 uur

Protocol-ID: `phase6g-recovery24h-v1`. Status: **ONTWERP, NIET ACTIEF**.
Basiscommit: `fed7ec29f13d0fe3742f811399a19a19ab5ac4c8`.
Alleen onderzoeksvoorbereiding is toegestaan; implementatie, varianttests en
historische evaluatie vereisen afzonderlijke expliciete goedkeuring.
Gemeenschappelijke dataset, kosten, metingen en stopvoorwaarden staan in
`PHASE6G_EXPERIMENT_PLAN.md` en zijn onderdeel van dit ontwerp.

## Vraag, wijziging en ongewijzigde referentie

Vraag: hoe veranderen nettoresultaat, kosten, blootstelling en risicoblokkeringen
als uitsluitend de permanente verliesreekspauze wordt vervangen door een vaste
24u-pauze met een nieuwe verliesreeksperiode? Geen voorafgaande winstclaim.
Universum: uitsluitend BTC/EUR, ETH/EUR, SOL/EUR; ontwikkeling uitsluitend 2024.
Dat jaar is reeds onderzocht en kan geen onafhankelijke bevestiging leveren.

De bestaande baseline telt in `ResearchExecutionEngine._reason` achterwaarts
negatieve gesloten netto-trades totdat een resultaat >= 0 voorkomt. Drie verliezen
geven een entryveto zonder automatische eindtijd. Deze code blijft ongewijzigd.

**Expliciet verschil met fase 6F R1:** dit nieuwe ontwerp staat herhaalde cycli van
maximaal drie nieuwe verliestrades en een volgende 24u-pauze toe. Het gebruikt niet
het eerdere één-proefrecht met definitieve sluiting bij een mislukte proef. Dat oude
voorstel blijft behouden. De huidige opdracht staat het ontwerpen van deze
verandering toe, niet het activeren ervan. Geen budgethalvering (R3), marktbevestiging
(R2), ATR-filter of andere extra strategievoorwaarde in experiment A.

## Verliesdefinitie en klok

Een verlies is een definitief gesloten trade met `net < Decimal('0')`, na de
bestaande entry-/exitfees, spread, slippage en afronding. Een fill, voorstel,
boekhoudkundige revisie, ongerealiseerd verlies of dubbele close is geen extra
trade. `net > 0` onderbreekt de reeks. `net == 0` onderbreekt haar eveneens, zoals
in de baseline; nul wordt niet als winst in de winrate geteld.

`t0` is de historische UTC-afrekentimestamp van de derde verliestrade, gekoppeld
aan de unieke definitieve close en de auditvolgorde waarin zij wordt geboekt.
Het is niet de wall-clocktijd waarop een replay draait en ook geen verondersteld
intrabar-stopmoment. `pause_until = t0 + 86400 seconden`. Er is geen zomer-/wintertijd.
Een laat binnengekomen, eerder gedateerde financiële gebeurtenis vereist stoppen
wegens inconsistentie; niet de pauze terugdateren en oude beslissingen herschrijven.

Signalen die in de bestaande batch vóór afrekening liggen, mogen deze afrekening
niet alvast kennen. De eerste daaropvolgende beslissing ziet de pauze. Een eerder
geregistreerde entry mag bij uitvoering na de trigger niet passeren: dezelfde
actuele pauzecontrole is verplicht bij toestemming én uitvoering. Geen nieuwe
instap in dezelfde exitbatch, geen bewaren van oude signalen tot na de pauze.

## Voorgestelde persistente toestand

Naast de ongewijzigde volledige ledger/auditketen: protocol-ID, portefeuillesleutel,
`epoch` (initieel 0), `epoch_anchor` (auditpositie), `loss_count` (0..3),
`pause_started_at`, `pause_until`, verwerkte definitieve close-ID's/auditcursor,
en de laatste volledig gecommitteerde beslisgrens. Eén toestand voor alle drie
coins, nooit een eigen teller per munt. De bestaande pending orders, reservaties,
positie, cash, peak, dagstatus en noodstop worden in dezelfde checkpointcontext
bewaard. De ruwe levenslange verliesreeks blijft apart reconstrueerbaar.

| Gebeurtenis | Voorwaarde | Nieuwe hersteltoestand |
|---|---|---|
| Initialisatie | Nieuw, afzonderlijk toegestaan experiment | epoch=0, loss_count=0; één €200-startledger |
| Unieke definitieve close, netto < 0 | Niet in actieve pauze | loss_count += 1; bij 3 atomair t0 en pause_until vastleggen |
| Unieke definitieve close, netto >= 0 | Niet in actieve pauze | loss_count=0; geen cash/peak/dagreset |
| Beslismoment t < pause_until | Pauze actief | Nieuwe entries geweigerd, teller=3 behouden |
| Eerste chronologische 15m-beslisgrens t >= pause_until | Consistente ledger, flat, geen pending/reservatie | Eén `cooldown_expired`-event; epoch += 1; anchor naar vorige laatste definitieve close; loss_count=0; actieve timer sluiten |
| Eerste nieuwe negatieve trade na hervatting | Nieuwe epoch | loss_count=1; daarna 2 en 3 bij twee volgende negatieve closes |
| Nieuwe derde negatieve close | Nieuwe epoch | Nieuwe t0, nieuwe volle 24u-pauze |
| Dubbele verwerking/restart | Close-ID of expiry-event al gecommitteerd | Geen nieuwe telling, reset of event |

Het resetmoment is dus de eerste verwerkte beslisgrens op of na expiry, niet de
volgende winst en niet het begin van een nieuw bestand of kalenderjaar. De vorige
drie verliezen liggen vóór de nieuwe anchor en tellen niet opnieuw als nieuwe
verliesreeks. Zij blijven volledig deel van gerealiseerd verlies, cash, drawdown,
dagverlies en de auditgeschiedenis. Geen fictieve winsttrade of verwijderde trade.

Als t0 geen kwartiergrens zou zijn, is het eerste mogelijke resetmoment
`ceil((t0 + 86400s)/900s)*900s`, met correcte UTC-epoch. De duur is nooit korter
als gevolg van afronding. Ontbrekende marktdata geeft geen instap; de klokovergang
mag bij een valide ledger wel éénmaal worden geregistreerd, waarna markt-/risicoveto's
blijven gelden. Onvolledige ledger, onverwachte positie of pending order bij expiry:
stop en onderzoek, geen destructieve schoonmaak of automatische reset.

Een synthetisch voorbeeld van de specificatie (niet uitgevoerd): derde close op
D om 10:00 geeft blokkering tot D+1 10:00; op die grens kan epoch 1 met teller 0
beginnen. Eén nieuwe negatieve close geeft 1, een volgende netto nul geeft 0.
Een herstart of afwijzing zonder fill verandert deze teller niet.

## Voorrang van alle overige beveiligingen

- Eén gezamenlijke portefeuille, oorspronkelijk €200. Nooit opnieuw storten of
  €200 per coin/maand/herstelcyclus creëren; geen leverage/futures/shorts.
- Hoogstens één positie. Maximaal 0,5% gepland risico, inclusief de bestaande
  kostencontrole en budget `0,005 × min(€200, beschikbare cash)`. Alle strengere
  cash-/equitycontroles blijven gelden. Maximaal 50% blootstelling bij entry.
- Dagverlies 3%, drawdown 10%, noodstop, marktdata-/liquiditeits-/filtercontroles,
  tijdigheid, cashreserveringen, deduplicatie en conservatieve fills blijven gelijk.
- Expiry raakt uitsluitend de verliesreeksteller. Dagverliesbaseline en peak blijven
  staan; alleen de bestaande UTC-dagovergang kan de dagverliespauze beëindigen.
  Drawdownpauze en noodstop worden niet automatisch opgeheven.
- Safety-exits mogen doorgaan volgens bestaande regels; een timer mag een
  risicoverlagende exit nooit blokkeren. Geen entry zonder een verse aligned_trend-
  kandidaat en alle overige goedkeuringen op het historische beslismoment.
- Tickafronding, 2 ATR-stop, horizon 4 uur en geen winsttarget blijven gelijk.
  Gaps kunnen gerealiseerd verlies boven 0,5% brengen; het is gepland risico.

Dit is een vooraf ontworpen andere semantiek van precies één veto. Een toekomstige
geïsoleerde onderzoeksimplementatie moet de centrale controle op die semantiek
baseren; een agent mag niet na afwijzing alsnog uitvoeren. De baseline mag nooit
met een gesnoeide ledger of vervalste Risk-goedkeuring worden aangeroepen.

## Risico's, extra veiligheidsvoorwaarden en nog te bewijzen werking

Een dag wachten levert geen marktherstelbewijs. Meerdere nieuwe cycli kunnen
verliezen en kosten opstapelen, ook verdeeld over UTC-dagen waardoor de daggrens
niet wordt geraakt. De bestaande drawdownbeveiliging blijft daarom cumulatief en
gelatcht. Deze variant specificeert geen extra gekozen maximumaantal cycli of
kleiner risicobudget; dat zou een andere, apart goed te keuren variant zijn.

Verplicht voor eventuele implementatie: atomische registratie van close, teller,
timer en audit; één reset per epoch; persistente IDs; fail-closed bij onbekende
reeksstatus; bij replay dezelfde gebeurtenisvolgorde; opnieuw risicocontrole bij
fill; geen oude pending entry over een pauze meenemen. Het begin van een nieuwe
cyclus moet zichtbaar zijn in checkpoints én in de afwijsrapportage.

Vóór historische toestemming zijn synthetische tests nodig voor: drie verliezen
over verschillende coins; winst en exact netto nul; expiry−15m/expiry/expiry+15m;
UTC-daggrens; duplicate close; afwijzing zonder trade; crash vóór/na atomische
close/reset; gap en stop; behoud van drawdown/noodstop; lege of beschadigde state;
maand-/batchwissels; drie nieuwe verliezen na reset; baseline-equivalentie als
geen pauze optreedt. Deze varianttests zijn in fase 6G niet uitgevoerd.
