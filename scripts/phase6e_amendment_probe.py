"""Fixed synthetic validation. No historical reader or automatic activation."""
import hashlib,json,math,random,resource,signal,time
from pathlib import Path
from scripts.phase6e_hac import ratio_hac
from scripts.phase6e_technical import bootstrap_starts,block_bootstrap,holm,contrast_family
ROOT=Path('experiments/phase6e_amendment')


def sample(case,seed,n=2153):
    rng=random.Random(seed);rho={'ar0':0,'ar05':.5,'ar09':.9,'ar098':.98}.get(case,.5)
    states=[0.0]*4;rows=[]
    level=rng.gauss(0,1)
    for i in range(-2000,n):
        for j in range(4):states[j]=rho*states[j]+math.sqrt(1-rho*rho)*rng.gauss(0,1)
        if i<0:continue
        common=states[0]; y=[common+states[1],.5*common+states[2],.5*common+states[3]]
        if case=='variance_break' and i>=n//2:y=[v*4 for v in y]
        # Unconditional mean remains zero, but a persistent random level violates mixing.
        if case=='random_level_break' and i>=n//2:y[0]+=level
        rows.append((y[0],1,y[1]+y[2],2))
    return rows


def wilson(k,n):
    z=1.959963984540054;p=k/n;d=1+z*z/n
    mid=(p+z*z/(2*n))/d;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [mid-half,mid+half]


def main():
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
    def timeout(*_):raise TimeoutError('300 second synthetic amendment budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300);began=time.perf_counter()
    plan=json.loads((ROOT/'synthetic_plan.json').read_text());starts=bootstrap_starts(plan['n'])
    result={}
    for si,case in enumerate(plan['scenarios']):
        ps=[];bs=[];coverage=0
        for i in range(plan['datasets_each']):
            rows=sample(case,plan['data_seed']+si*1000+i)
            r=ratio_hac(rows);ps.append(r['p']);coverage+=r['interval'][0]<=0<=r['interval'][1]
            if i<plan['paired_original_bootstrap_first']:bs.append(block_bootstrap(rows,starts)['p'])
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>768*1024:raise MemoryError('RSS limit')
        k=sum(p<=.05 for p in ps)
        result[case]=dict(hac_n=len(ps),hac_reject_05=k,hac_wilson_95=wilson(k,len(ps)),
            hac_reject_strict=sum(p<=.05/332 for p in ps),hac_coverage_95=coverage/len(ps),
            original_n=len(bs),original_reject_05=sum(p<=.05 for p in bs),
            original_reject_strict=sum(p<=.05/332 for p in bs),
            hac_screen_pass=wilson(k,len(ps))[1]<=.10)
        print(case,result[case],flush=True)
    t=time.perf_counter()
    def family():
        p=[]
        for i,_ in enumerate(contrast_family()):p.append(ratio_hac(sample('ar05',990000+i))['p'])
        return hashlib.sha256(json.dumps([p,holm(p)],sort_keys=True).encode()).hexdigest()
    digest=family();elapsed=time.perf_counter()-t
    repeat=family()
    if digest!=repeat:raise ValueError('Reproducibility failed')
    out=dict(status='synthetic_complete_not_activated',scenarios=result,
        family_seconds_including_generation=elapsed,family_contrasts=332,family_digest=digest,
        reproducible=True,elapsed_seconds=time.perf_counter()-began,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        plan_sha256=hashlib.sha256((ROOT/'synthetic_plan.json').read_bytes()).hexdigest(),
        source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
          ('scripts/phase6e_hac.py','scripts/phase6e_amendment_probe.py')},historical_data_accessed=False)
    with (ROOT/'synthetic_results.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    signal.alarm(0);print(json.dumps(out),flush=True)
if __name__=='__main__':main()
