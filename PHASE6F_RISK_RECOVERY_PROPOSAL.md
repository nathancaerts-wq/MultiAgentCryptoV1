# Fase 6F — voorstel voor gecontroleerd herstel na verliesreekspauze

Status: **niet geïmplementeerd, niet geactiveerd, niet getest als variant**.
Basis: commit `4f3e9a2675cca3ce6015609145380f3c161d4cc9`.
De opdracht autoriseert uitsluitend onderzoeksvoorbereiding. Dit document is geen
amendering van de actieve Risk Engine en verleent geen orderautorisatie.

## Bestaande werking en bewijs

`ResearchExecutionEngine._reason` telt achterwaarts werkelijk gesloten trades
met nettoresultaat < 0; een resultaat >= 0 onderbreekt de reeks. Bij drie verliezen
volgt een entryveto. Dit is geen timer die bij een nieuwe dag, coin, maand of
procesherstart verdwijnt. De ledger/auditgeschiedenis blijft de bron van waarheid.
Zonder nieuwe trade kan geen niet-verlies ontstaan dat de reeks onderbreekt.
`DecisionPolicy.max_consecutive_losses` blijft 3. De dagverliespauze heeft een
eigen UTC-dagovergang; drawdownpauze blijft gelatcht. Noodstop is afzonderlijk.

De bestaande 2024-run had drie verliestrades. Het derde verlies werd op 11 januari
16:00 UTC geboekt ná de beslissing op dat tijdstip. De oorspronkelijke beslissing
kende de pauze voor het eerst om 16:15 UTC. Fase 6E telt op UTC4h 6.240 HOLDs
tijdens en slechts 67 buiten de pauze; alle acht pauzecontrasten hebben onvoldoende
steun. Dit toont geen oorzakelijk effect of voordeel van herstel. De 793 expliciete
pauze-afwijzingen zijn een andere populatie dan alle HOLDs tijdens pauze.
Bronnen: fase-6E-eindrapport/v4-JSON, `crypto/research_execution.py`,
`crypto/sim_execution.py`, `crypto/joint_portfolio.py`, `crypto/trade_agents.py`.

## Gemeenschappelijke voorwaarden voor alle drie ontwerpen

Een toekomstige, apart goedgekeurde onderzoeksvariant zou een expliciete
hersteltoestand moeten toevoegen; de bestaande code kan dit nu niet zonder
beleidswijziging. Een agent mag het veto nooit omzeilen met een ander event-ID,
een nieuwe portefeuille of een kortere handelsgeschiedenis.

- Eén gezamenlijke portefeuille, oorspronkelijk €200; geen aanvulling of reset.
- Hoogstens één open positie. Geen herstel met open positie, pending order,
  reservering, inconsistent saldo of onvolledige auditketen.
- Risicobudget hoogstens 0,005 × min(€200, beschikbare cash), inclusief geplande
  stopkosten; daarnaast alle bestaande equity-/cashcontroles. Exposure maximaal
  50%. Geen leverage. Gaps kunnen gerealiseerd verlies boven gepland risico brengen.
- Dagverliesgrens 3%, drawdowngrens 10%, noodstop, cash, filters, bronkwaliteit,
  liquiditeit en alle overige bestaande veto's blijven doorslaggevend.
- Herstel wist nooit peak, day_start, verliezen, kosten, IDs of auditgebeurtenissen.
  Alleen de reeds bestaande UTC-dagovergang mag de dagverliesstatus veranderen.
  Geen automatische reset van drawdown of noodstop.
- `t0` is de geregistreerde afrekening van het derde negatieve nettoresultaat.
  De nieuwe pauzestatus mag pas worden gebruikt ná die afrekening volgens de
  bestaande eventvolgorde. Geen hernieuwde entry in dezelfde exitbatch.
- Een herstelrecht is hoogstens één proef-entry. Het is geen order en geen
  versoepeling voor alle gelijktijdige kandidaten. Een verse kandidaat en een
  volledige Risk-/Execution-hercontrole blijven verplicht.
- Voorstel voor proefafhandeling: alleen een gesloten trade met netto > 0 mag
  terugkeer naar normaal onderzoek toestaan. Netto <= 0, een afgebroken proef of
  een uitvoeringsafwijzing sluit dit hersteltraject; daarna is afzonderlijke
  menselijke onderzoeksgoedkeuring nodig. Geen automatische herhaalpogingen.
  Geen kandidaat betekent blijven wachten; een niet vervulde risicocontrole
  produceert geen proeforder. Registratie van het eerste goedgekeurde entryvoorstel
  verbruikt het ene proefrecht atomair, ook als uitvoering daarna wordt geweigerd.
- Bij ontbrekende data: wachten, geen synthetische winst of reset. Herstart bewaart
  t0, herstelstatus, verbruikt proefrecht, coin, reservatie en auditverwijzingen.

Dit ontwerp introduceert bij latere implementatie een expliciet geautoriseerde
uitzondering op het verliesreeksveto voor één proef. Dat is een inhoudelijke
risicoregelwijziging en vereist afzonderlijke toestemming. Het is geen bestaande
mogelijkheid of technische reparatie. De ruwe verlieshistorie blijft intact. Ook netto nul onderbreekt in de bestaande
code de ruwe reeks; het voorgestelde herstelbeleid blijft in dat geval toch
gesloten. Alleen netto > 0 geeft volgens dit ontwerp terugkeer naar normaal onderzoek.

## R1 — vaste afkoeling, één gecontroleerde proef

**Trigger:** bestaande derde verliesafrekening. **Gereed:** eerste 15m-beslismoment
t >= t0 + 24 uur, ná verwerking van de pauze, met alle gemeenschappelijke controles.
De 24 uur is een vooraf voorgestelde volledige UTC-dagduur, niet uit 2024-rendement
gekozen. Wachten zelf is geen bewijs van marktherstel.

**Selectie/reset:** neem de eerstvolgende geldige aligned_trend-kandidaat volgens
de bestaande scannerscore en UTC-tiebreak. Proef met bestaande maxima 0,5%/50%;
na netto > 0 normaal, anders gesloten voor automatische hervatting. Een latere
nieuwe reeks van drie verliezen na geslaagd herstel vormt een nieuwe episode.
Geen terugwerkende kracht naar oude signalen tijdens de afkoeling.

**Risico:** dezelfde slechte markt kan voortduren; de eerste proef kan opnieuw
verliezen of door een gap meer verliezen dan gepland. Een timer biedt geen
risicobewijs. De grens van één proef voorkomt een onbeperkte reeks timer-retries.

**Data/techniek:** ledgerafrekeningen, originele UTC-klok, volledige actuele
analyseframes, cash/peak/dagstatus, fills en orderfilters. Vereist persistente,
atomische proefrechten; een procesklok of reset van een teller is onvoldoende.

**Onafhankelijke test na toestemming:** synthetisch t0+24h−15m, exact +24h,
week-/maandgrens, crash vóór/na toestemming, uitvoeringsafwijzing, netto nul,
alle gelijktijdige veto's. Daarna uitsluitend een apart geregistreerde evaluatie
op expliciet vrijgegeven, werkelijk niet gebruikte gegevens; meerdere onafhankelijke
pauze-episodes vereist. De oude 2024-pauze alleen is onvoldoende.

## R2 — bevestiging door twee afgesloten marktobservaties

**Trigger:** dezelfde derde verliesafrekening. **Gereed:** op twee opeenvolgende
UTC4h-grenzen heeft dezelfde coin een volledig valide aligned_trend-analyse:
1h-regime bullish en EMA-richting up op 15m, 1h en 4h. Beide bijbehorende 4h-candles
moeten geheel ná t0 beginnen (open >= t0); hun sluitingen liggen exact vier uur
uiteen. Een datagat, ongeldige bron of niet voldane voorwaarde verbreekt de reeks.
Geen bevestiging door een toekomstig candle of door een andere coin.

**Selectie/reset:** uitsluitend op de tweede of volgende kwalificerende UTC4h-grens
kan een verse kandidaat van die coin meedoen. Bij meerdere coins geldt dezelfde
bestaande rangschikking. Het recht vervalt na dat beslismoment als er geen geldig
voorstel is; volgende grens vereist opnieuw twee geldige opeenvolgende observaties.
Eén proef met maxima 0,5%/50%, daarna dezelfde proefafhandeling als R1. Er is geen
extra 24u-timer. Twee observaties is een eenvoudige voorgestelde bevestigingsregel,
geen empirisch geselecteerde optimale wachttijd.

**Risico:** prijsherstel kan te laat of vals zijn; gecorreleerde coins en dezelfde
EMA-berekeningen leveren geen onafhankelijke bevestigingen. Bevestiging selecteert
bovendien dezelfde marktvoorwaarden als de strategie; causaliteit is niet aangetoond.

**Data/techniek:** causale 15m/1h/4h-frames, twee brongebonden snapshots per coin,
persistente kwalificatiestatus en alle gemeenschappelijke ledgerdata. Geen uitlijning
op de toevallig eerste candle van een batch. Indicatoren blijven exact ongewijzigd.

**Onafhankelijke test na toestemming:** synthetische grens om 03:45/04:00,
t0 midden in een 4h-candle, veranderende coin, onderbroken reeks, negatieve/ontbrekende
snapshot, dubbele grens en crash. Daarna een nieuwe toegestane periode met voldoende
verschillende regimes en pauze-episodes; geen selectie van het beste aantal frames.

## R3 — afkoeling met kleinere proefblootstelling

**Trigger/gereed:** exact dezelfde 24u- en chronologieregel als R1.
**Proefbudget:** maximaal 0,25% × min(€200, beschikbare cash), maximaal 25% exposure;
daarbovenop alle bestaande strengere controles. Dit zijn voorgestelde halveringen
van de huidige maxima, geen uit resultaten afgeleide waarden. Kosten en afronding
moeten volledig in dat kleinere budget passen. Onder minnotional: afwijzen, niet
opschalen. Stop blijft 2 ATR, horizon 4 uur; geen verdere financiële regel verandert.

**Selectie/reset:** één aligned_trend-proef met bestaande rangschikking. Alleen
netto > 0 geeft terugkeer naar de bestaande 0,5%/50%-maxima; anders gesloten.
Dit is geen bewijs dat één winsttrade herstel aantoont: het is een vooraf gekozen,
controleerbare toelatingsregel. De omvang stijgt nooit boven de bestaande limieten.

**Risico:** procentueel kleinere blootstelling garandeert geen klein gapverlies;
fees en minimumordergrootte kunnen alle proeforders onmogelijk maken. Succes van
één proef blijft toeval. Geen versoepeling van filters om toch een trade te verkrijgen.

**Data/techniek:** dezelfde gegevens als R1 plus Decimal-sizing onder het kleinere
budget en dubbele controle bij voorstel én uitvoering. Het huidige bevroren beleid
kan niet midden in een run worden vervangen: toekomstige implementatie moet een
vooraf geregistreerde hersteltoestand ondersteunen zonder configuratie-mutatie.

**Onafhankelijke test na toestemming:** alle R1-tests plus handmatig controleerbare
kosten/minnotional/afrondingsgrenzen, cash onder €200, prijs-gap, exposure en exact
één proef; vergelijk later R3 met R1 om de budgetbijdrage te isoleren. Geen keuze
van budget of terugkeerregel op basis van geobserveerde winst.

## Keuze die nog goedkeuring vereist

Aanbevolen volgorde voor eventueel technisch vervolg: eerst R1 als eenvoudige
referentie voor toestandsovergangen, daarna R3 als conservatiever budgetvoorstel;
R2 heeft meer data- en afhankelijkheidsproblemen. Er is geen rendementrangschikking.
Kies vóór implementatie één mechanisme, inclusief de proefafhandeling, of wijs alle
voorstellen af. Ook toestemming voor synthetische varianttests en iedere latere
historische counterfactual-run moet afzonderlijk worden gegeven. Nu blijft de
huidige onbeperkte verliesreekspauze volledig van kracht.
