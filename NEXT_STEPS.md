# Vervolg na het fase-6B-protocolvoorstel

Lees PHASE6B_PROTOCOL_PROPOSAL.md. Dit is een **voorstel**, geen geregistreerd of
vrijgegeven uitvoeringsplan. Wacht op expliciete goedkeuring voordat historische
rendementsbacktests starten. Het oude onafhankelijke testslot 15–16 januari 2025
blijft gesloten; het kandidaat-testvenster januari–september 2026 eveneens.
Goedkeuring van ontwikkeling/validatie opent geen onafhankelijke test.

1. Laat de keuzes uit §11 expliciet bevestigen: exacte perioden/warm-up,
   januari-quarantaine, vaste zes munten en aligned_trend, voorgestelde
   liquiditeitsregels en strikte historische filters, benchmarkdefinities,
   netto portefeuillerendement als primaire maat en beschrijvende statistiek.
2. Vul het externe inzageregister aan. De eerdere tijdelijke databases zijn nu
   afwezig; de oude audit en smoke-artefacten blijven bewaard. Claim niet dat
   2026 onaangeraakt is alleen omdat lokaal geen inzage teruggevonden is.
3. Pas na akkoord: bouw/test de benodigde gescheiden onderzoeksmanifesten en
   lange gezamenlijke replay met fixtures. Huidige interfaces zijn beperkt tot
   ontwikkeling en 192 candles per coin. Geen checks omzeilen, oude registraties
   overschrijven of per-coinportefeuilles optellen. Houd alle 287 tests intact.
4. Voer vervolgens uitsluitend de goedgekeurde D/V-data-audit uit, zonder
   rendementsselectie. De HEAD-inventaris bewijst alleen archiefaanwezigheid;
   inhoudelijke checksums, candles, historische filters en beschikbaarheid op
   het beslismoment moeten nog worden gevalideerd. Januari-2025-warm-up alleen
   via de expliciete dagelijkse archieven 25–31 januari, niet via de hele maand.
5. Bind code, parameters, datasets, echte hashes, uitsluitingen, toestemming en
   bekeken bereiken aan een onveranderlijk manifest vóór resultaatberekening.
   Ontbrekende filters leiden tot afwijzing; geen automatische aannamesarm.
6. Start pas na expliciete evaluatietoestemming en geslaagde technische controles
   de vastgelegde D/V-evaluaties. Rapporteer alle scenario's, pauzes, afwijzingen,
   kleine steekproeven en onvolledige runs. Geen parameteroptimalisatie.
7. Houd de onafhankelijke test apart vergrendeld tot afzonderlijke expliciete
   toestemming. Geen automatische strategiepromotie of volgende fase.

Geen echte transacties, API-sleutels, automatische paperbot, wijzigingen aan
andere bots of verhoogde risicogrenzen. In deze oplevering is geen rendementsbacktest
uitgevoerd. Metadata: experiments/phase6b_coverage_metadata_20261027.json;
broncontrole: experiments/phase6b_proposal_sources_20261027.json.
