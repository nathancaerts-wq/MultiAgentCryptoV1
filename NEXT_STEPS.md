# Vervolg na schaalbaarheidsmetingen fase 6B

Lees PHASE6B_SCALABILITY_REPORT.md. Alle 353 tests slagen, maar jaarcapaciteit is
niet bewezen. Geen automatische historische evaluatie of jaarprobe.

1. Normaliseer of stream de state-/eventhistorie met volledige audit-, rollback-,
   reconstructie- en financiële gelijkheid. De huidige complete payload per revisie
   veroorzaakt bijna kwadratische opslag; jaarprojectie circa 214 GB alleen states.
2. Onderzoek immutable/COW-orchestrator-inputs. Verwijder geen isolatie, controles
   of auditregels op grond van uitsluitend snelheid.
3. Als vervolgstap expliciet gevraagd: maximaal 1.250 synthetische stappen,
   timeout 180 s en harde 1,5-GiB-address-spacegrens, vroegtijdig stoppen rond
   1,2 GiB RSS. Voeg volledige toelatingshistorie en actieve posities toe.
4. Behoud alle golden, causale cache-, corruptie-, mutatie- en risicotests. Geen
   onbeperkt doorlopende EMA in plaats van de vaste 32-candleberekening invoeren.
5. Pas na voldoende bewijs een langere test begroten. De oorspronkelijke
   45-secondenjaarvoorwaarde is niet verhoogd of geslaagd.
6. Historische rendementsevaluatie blijft afhankelijk van alle eerdere gates;
   onafhankelijke test gesloten, geen strategiepromotie of volgende fase automatisch.
