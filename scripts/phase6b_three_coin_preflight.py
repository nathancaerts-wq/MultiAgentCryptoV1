"""Hercontrole van toegestane corpusdata uit cache; nooit rendementen of testdata."""
import json
from pathlib import Path
from crypto.readiness import quality_report, manifest, verify_manifest
from scripts.phase6b_full_audit import CachedDownloads, MonthlyAuditAdapter

COINS=('BTCEUR','ETHEUR','SOLEUR')

def main():
 verify_manifest(json.loads(Path('experiments/phase6b_final_manifest.json').read_text()))
 out=Path('experiments/phase6b_three_coin_preflight');out.mkdir(exist_ok=False)
 paths=[Path('PHASE6B_THREE_COIN_AMENDMENT.md'),Path('scripts/phase6b_three_coin_scale_probe.py')]
 paths+=list(Path('crypto').glob('*.py'))
 paths+=[Path('experiments/phase6b_full_quality')/f'{s}_{p}.json' for s in COINS for p in ('development','validation','validation_warmup')]
 m=manifest(paths,{'study':'phase6b-three-coin-v1','coins':COINS,'authorization':'conditional_user_instruction','technical_gate_passed':False},[str(p) for p in paths if 'full_quality' in str(p)])
 (out/'manifest_before_checks.json').write_text(json.dumps(m,indent=2)+'\n')
 cache=CachedDownloads('/workspace/phase6b_archive_cache',max_requests=0)
 summary=[]
 for symbol in COINS:
  for period in ('development','validation','validation_warmup'):
   adapters={tf:MonthlyAuditAdapter(cache) for tf in ('15m','1h','4h')}
   class Routed:
    last_manifest=[]
    def fetch(self,s,tf,a,b):
     rows=adapters[tf].fetch(s,tf,a,b);self.last_manifest=adapters[tf].last_manifest;return rows
   result=quality_report(Routed(),symbol,period)
   original=json.loads((Path('experiments/phase6b_full_quality')/f'{symbol}_{period}.json').read_text())
   same=result==original
   (out/f'{symbol}_{period}.json').write_text(json.dumps(result,indent=2)+'\n')
   row=dict(symbol=symbol,period=period,status=result['status'],identical_to_prior_audit=same,valid_days=sum(r['status']=='valid' for r in result['days']),days=len(result['days']))
   summary.append(row);print(json.dumps(row),flush=True)
 verify_manifest(m)
 (out/'summary.json').write_text(json.dumps(dict(checks=summary,requests=cache.requests,old_manifest_verified=True,new_manifest_verified=True,performance_computed=False),indent=2)+'\n')
if __name__=='__main__':main()
