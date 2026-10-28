import csv,json,collections,hashlib
from pathlib import Path
root=Path('experiments/phase6e_descriptive');r=json.loads((root/'result.json').read_text())
reg=json.loads((root/'registration_v4.json').read_text());perf=json.loads((root/'performance.json').read_text())
def num(v):return '—' if v is None else f'{v:.6g}'
def key(s):return r['samples'][s]['contrasts']
def counttab(t):return '| Groep | N | Bruto + | Bruto − | Neutraal | Netto + |\n|---|---:|---:|---:|---:|---:|\n'+''.join(f'|{name}|{v.get("n",0)}|{v.get("positive",0)}|{v.get("negative",0)}|{v.get("neutral",0)}|{v.get("net_positive",0)}|\n' for name,v in t)
with (root/'contrast_summary.csv').open('x',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['sample','family','stratum','feature','status','difference_mean','p','p_holm','confidence_interval']+[side+'_'+field for side in ('left','right') for field in ('n','selected','missing','timegroups','blocks','status','mean','median','p10','p90','min','max')])
 for sample in ('utc4h','overlapping'):
  for k,v in key(sample).items():
   w.writerow([sample,*k.split(':'),v['status'],v['difference_mean'],'','','']+[v[side][field] for side in ('left','right') for field in ('n','selected','missing','timegroups','blocks','status','mean','median','p10','p90','min','max')])

def contrast_rows(keys,sample='utc4h'):
 lines=['| Contrast (links − rechts) | Stratum | n links/rechts | Verschil gemiddelde | Mediaan links/rechts | p10–p90 links/rechts | Status |','|---|---|---:|---:|---:|---|---|']
 for family,feature in keys:
  for stratum in ('pooled','BTCEUR','ETHEUR','SOLEUR'):
   v=key(sample).get(f'{family}:{stratum}:{feature}')
   if v is None:continue
   a,b=v['left'],v['right'];rng=lambda z:f'{num(z["p10"])}–{num(z["p90"])}'
   lines.append(f'|{family}: {feature}|{stratum}|{a["n"]}/{b["n"]}|{num(v["difference_mean"])}|{num(a["median"])}/{num(b["median"])}|{rng(a)}/{rng(b)}|{v["status"]}|')
 return '\n'.join(lines)+'\n'

s=r['samples'];t4=s['utc4h']['tables'];to=s['overlapping']['tables']
statuses={x:dict(collections.Counter(v['status'] for v in key(x).values())) for x in s}
missing={x:sum(v[z]['missing'] for v in key(x).values() for z in ('left','right')) for x in s}
coins=[(c,v) for c,v in t4['coin'].items()]
regimes=[(x,v) for x,v in sorted(t4['regime'].items())]
text=f'''# Fase 6E — beschrijvende patroonanalyse 2024

Alleen de vooraf geregistreerde BTC/EUR-, ETH/EUR- en SOL/EUR-gegevens uit 2024.
Dit is een exploratieve beschrijving van **reeds bekeken** 2024-data. De vijf
hypotheses en 332 contrasten staan vooraf vast; er is geen nieuwe drempel, coin of
winnaar achteraf gekozen. De studie heeft geen p-waarden, Holm-verwerpingen,
inferentiële intervallen, causale claims of nieuwe handelsautorisatie.

## Registratie en integriteit

De expliciete gebruikersgoedkeuring is vóór uitkomstverwerking geregistreerd in
manifest `{reg['sha256']}`. De inhoudsgebonden manifestbestanden bevatten de
oude databasehash, fase-6D-labels, officiële gecachete januariarchieven,
indicatorcode, oorspronkelijke protocolversie, vijf hypotheses, goedgekeurde
beschrijvende amendering en de vaste 332 contrasten. De oorspronkelijke documenten
zijn niet overschreven. Het bestaande ontwikkelregister kende 2024 al als bekeken.
De eerste registratie stopte vóór uitkomstverwerking bij een tuple/JSON-controle.
Een tweede run werd wegens oplopend geheugen onderbroken. De derde leverde een
diagnostisch artefact met een pauzegrens één beslismoment te vroeg. Alle oude
registraties en diagnostische bytes zijn bewaard. De vierde versie is opnieuw
vóór haar resultaten op main gezet.

De oorspronkelijke datasetcache bevatte slechts 32 candles per timeframe. Voor
ΔRSI is de ene extra oudere 2024-candle per coin en timeframe gelezen uit hetzelfde
reeds officieel SHA-256-gecontroleerde maandarchief. Geen netwerkdownload of
andere periode. De werkelijke prijslabels zijn niet opnieuw berekend: exact de
bestaande 103.344 fase-6D-rijen zijn verbonden met kenmerken die op hun
beslismoment bekend konden zijn. De oude indicatoruitkomsten zijn per venster
exact gereproduceerd voordat de nieuwe beschrijving werd opgeslagen.

## Omvang en kostencontext

De vaste primaire vergelijking is de UTC4h-grid; de overlappende kwartiermomenten
staan afzonderlijk. Per coin raken de 4h-vensters elkaar alleen op hun grenzen;
gelijktijdige coins en opeenvolgende regimes blijven afhankelijk. De netto-labels
gebruiken de reeds vastgelegde vaste 0,001-coinprijsdiagnose met 0,1% fee per zijde,
0,1% volledige spread en 0,1% slippage per zijde. Het zijn geen uitvoerbare orders
of EUR-gelijkgewogen portefeuillewinsten.

### UTC4h (primair)

{counttab([('Alle coinmomenten',t4['all']),('Oorspronkelijke HOLD',t4['hold']),('HOLD tijdens pauze',t4['pause_hold']),('HOLD buiten pauze',t4['nonpause_hold'])])}

### Overlappende 15m-momenten (afzonderlijk)

{counttab([('Alle coinmomenten',to['all']),('Oorspronkelijke HOLD',to['hold']),('HOLD tijdens pauze',to['pause_hold']),('HOLD buiten pauze',to['nonpause_hold'])])}

Per coin, uitsluitend HOLD op UTC4h:

{counttab(coins)}

## Vooraf vastgelegde hypothesen

Alle tabellen hieronder gebruiken de UTC4h-grid. `A` vergelijkt bruto positieve
versus bruto negatieve HOLDs; `B` netto positieve versus netto niet-positieve HOLDs;
`C` vergelijkt pauze versus daarbuiten; `D` EMA versus aligned_trend BUY-kandidaten.
Een verschil is uitsluitend het verschil van de twee getoonde groepsgemiddelden.
Mediaan en p10–p90 zijn empirische spreidingsmaten, geen betrouwbaarheidsinterval.
De volledige uitwerking van alle 332 contrasten, voor beide steekproeven en met
n, ontbrekendheid, minimum/maximum en status per groep, staat in
`experiments/phase6e_descriptive/contrast_summary.csv` en `result.json`.

### 1. Oorspronkelijke scannerscore en rang

{contrast_rows([('A','scanner_score'),('B','scanner_score'),('B','scanner_rank')])}

Een hogere score is slechts informatie die destijds beschikbaar was; geen
Risk-goedkeuring of aanwijzing dat een andere munt uitvoerbaar winstgevender was.

### 2. RSI-niveau en verandering

{contrast_rows([('A','1h:rsi'),('A','1h:delta_rsi'),('B','1h:delta_rsi')])}

ΔRSI gebruikt een volledig eerder 32-candlevenster. Een verschil hier is geen
nieuwe RSI-grens of voorspellingsbewijs; ook 15m en 4h staan in de volledige tabel.

### 3. EMA-afstanden en selectie

{contrast_rows([('B','1h:ema_gap'),('B','up_count'),('D','1h:ema_gap'),('D','up_count')])}

Bestaande kandidaat-aantallen in dit exacte instapuniversum, UTC4h:
{dict(t4['ema_candidates'])} voor EMA; {dict(t4['aligned_candidates'])} voor
aligned_trend. Overlappend: {dict(to['ema_candidates'])} en
{dict(to['aligned_candidates'])}. Beide selecties gebruiken hetzelfde
beslismoment; `D` beschrijft hun kenmerken. Oorspronkelijke aparte jaarruns
hadden respectievelijk vijf en drie virtuele trades en verschillende blootstelling
aan de markt; hun rendement is hier niet opnieuw getest. Sommige momenten kunnen
in beide kandidaatsets zitten. Er is geen nieuwe EMA-run uitgevoerd.

### 4. Volatiliteit en volume

{contrast_rows([('B','1h:relative_atr'),('B','1h:volume_ratio'),('B','1h:volume_change')])}

Deze kenmerken zijn beschrijvend. Een nulvolumedeler wordt als ontbrekend geteld;
geen volumefilter of stopafstand is aangepast. 15m en 4h staan in de volledige tabel.

### 5. Verliesreekspauze

{contrast_rows([('C','gross_positive'),('C','net_positive')])}

De pauzestatus is afgeleid uit de onveranderde oorspronkelijke ledgerprefix vanaf
het eerste oorspronkelijke beslismoment na de derde verliesexit: 11 januari 2024
om 16:15 UTC. Om 16:00 werd het signaal nog vóór de stopafrekening beoordeeld
met twee gesloten verliezen en een open positie.
De oude 793 expliciete pauze-afwijzingen zijn **niet** hetzelfde als alle HOLDs
tijdens de pauze. De pauze verdeelt dit jaar sterk naar kalenderperiode en
marktomgeving. Een positief prijslabel tijdens een veto was geen toegestane trade.
`insufficient_support` betekent geen robuuste basis voor zelfs een latere
inferentiële vergelijking; de ruwe beschrijving blijft transparant zichtbaar.

## Marktregimes op de primaire grid

Oorspronkelijk 1h-regime bij HOLD, zonder nieuwe regimegrenzen:

{counttab(regimes)}

Regimes zijn ook op het beslismoment bekend. Bruto/netto aandelen verschillen
mogelijk omdat kosten kleine stijgingen uitfilteren. Deze tabellen zeggen niets
over een causaal effect van regime of pauze.

## Ontbrekende gegevens en steun

| Steekproef | Vaste contrasten | Statusverdeling | Ontbrekende featurelidmaatschappen* |
|---|---:|---|---:|
| UTC4h | 332 | {statuses['utc4h']} | {missing['utc4h']} |
| Overlappend | 332 | {statuses['overlapping']} | {missing['overlapping']} |

* Een ontbrekende feature kan in meer dan één vooraf vastgelegd contrast vallen;
dit is geen aantal unieke missende candles. Beide groepen tonen afzonderlijk
`selected`, `missing`, `n`, aantal tijdgroepen en zevendaagse kalenderblokken.
Essentiële ontbrekende bronnen, duplicaten en indicatorafwijkingen zouden de run
hebben gestopt. Groepen met minder dan twintig kalenderblokken, dertig tijdgroepen
of meer dan 1% ontbrekendheid krijgen expliciet onvoldoende steun. Een lege groep
heeft geen ingevuld gemiddelde of verschil. Er is nergens een ontbrekende waarde
op nul gezet of met een later candle aangevuld.

## Grenzen van de conclusies en vervolg

Deze patronen zijn op een eerder bekeken ontwikkeljaar beschreven. Grote aantallen
kwartierlabels zijn overlappend en drie coins bewegen samen. De UTC4h-grid verwijdert
binnen-coin-overlap, maar maakt de tijdgroepen niet onafhankelijk. Dit rapport trekt
geen significantie-, effectiviteits-, voorspellings- of winstconclusie. De 332
beschrijvingen zijn niet gerangschikt op het grootste verschil. Geen parameterzoektocht,
strategiepromotie, automatische paperorders, risk-reset of backtest uitgevoerd.

Maximaal drie prioritaire vervolgonderzoeken, naar bronkwaliteit en toetsbaarheid:

1. Controleer of oorspronkelijke scannerherkomst en rang in een nieuwe,
   afzonderlijk geregistreerde dataset volledig en tijdig reproduceerbaar zijn.
2. Onderzoek onder een nieuw protocol welke volume-/ATR-metingen stabiel blijven
   buiten deze eerdere 2024-inzage, met expliciete datagaten- en coinafhankelijkheid.
3. Beoordeel eerst de eventvolgorde en voldoende niet-gepauzeerde vergelijkingsduur
   voordat een afzonderlijke pauzevraag wordt overwogen; geen versoepeling nu.

Validatie 2025 en onafhankelijke test 2026 blijven gesloten. De code voor strategie,
indicatoren, uitvoering en risico is byte-identiek gebleven; alle oude financiële
resultaten en auditlogs blijven behouden. De run gebruikte een limiet van 600 s,
1 GiB adresruimte en een vroege stop bij 768 MiB. Uitvoeringstijd
{perf['elapsed']:.3f} s, piek-RSS {perf['peak_rss_kib']/1024:.3f} MiB.
Volledige onafhankelijke artifact-/broncontrole staat in
`experiments/phase6e_descriptive/verification.json`.
'''
Path('PHASE6E_DESCRIPTIVE_PATTERN_REPORT.md').write_text(text)
print('rendered',len(text),'statuses',statuses,'missing',missing)
