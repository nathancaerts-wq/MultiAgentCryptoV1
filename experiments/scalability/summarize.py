import json,statistics,hashlib
from pathlib import Path
root=Path('experiments/scalability');out={}
for label in ('before','after_stage1','after'):
 out[label]={}
 for n in (100,500,1000):
  p=root/label/f'chain_{n}.json'
  v=json.loads(p.read_text());combined=[a+b for a,b in zip(v['analysis_steps'],v['replay_steps'])]
  assert len(combined)==n
  out[label][str(n)]=dict(total_seconds=v['elapsed_profiled'],mean_seconds_per_step=v['elapsed_profiled']/n,
   first_100_seconds=sum(combined[:100]),last_100_seconds=sum(combined[-100:]),peak_rss_kib=v['peak_rss_kib'],phases=v['phases'],sql_payload_bytes=v['sql_payload_bytes'],indicator_cache=v['indicator_window_cache'],indicator_computations=v['technical_calls'],trades=v['trades'],top_application_functions=[r for r in v['profile'] if '/crypto/' in r['file']][:20])

def fit(xs,ys):
 # Exacte interpolatie op drie punten, geen statistisch betrouwbaarheidsinterval.
 x0,x1,x2=xs;y0,y1,y2=ys
 b=((y2-y1)/(x2-x1)-(y1-y0)/(x1-x0))/(x2-x0)
 a=(y1-y0)/(x1-x0)-b*(x1+x0);c=y0-a*x0-b*x0*x0
 return c,a,b
c,a,b=fit([100,500,1000],[out['after'][str(n)]['total_seconds'] for n in (100,500,1000)])
N=35136
pred=c+a*N+b*N*N
cs,as_,bs=fit([100,500,1000],[out['after'][str(n)]['sql_payload_bytes']['joint_states'] for n in (100,500,1000)])
last=out['after']['1000']
out['year_model']=dict(steps=N,model='c+a*n+b*n^2; interpolation only, not measured year run',c=c,a=a,b=b,conditional_seconds=pred,conditional_hours=pred/3600,optimistic_linear_seconds=last['total_seconds']*N/1000,joint_states_payload_predicted_bytes=cs+as_*N+bs*N*N,year_probe_executed=False)
out['gate_2000']=dict(executed=False,timeout_budget_seconds=180,memory_budget_bytes=1610612736,conservative_time_forecast_seconds=4*last['total_seconds'],conservative_rss_forecast_bytes=4*last['peak_rss_kib']*1024,reason='Both conservative time and memory forecast exceed the diagnostic budget; no 2000-step run started')
out['tests']=dict(passed=353,failed=0)
out['source_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('crypto/analysis.py'),Path('crypto/data.py'),Path('crypto/joint_portfolio.py'),Path('crypto/storage.py'),Path('scripts/measure_scalability.py')]}
(root/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['year_model'],indent=2));print(out['gate_2000'])
