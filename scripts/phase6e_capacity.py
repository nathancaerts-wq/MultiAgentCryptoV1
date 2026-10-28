"""Synthetic only: full 332-contrast / 9999-draw capacity check, no file inputs."""
import hashlib,json,math,resource,signal,time,sys
from pathlib import Path
from scripts.phase6e_technical import bootstrap_starts,block_bootstrap,contrast_family,holm


def main():
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
    def timeout(*_):raise TimeoutError('600 second synthetic capacity limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
    began=time.perf_counter();n=2153
    starts=bootstrap_starts(n)
    out=[]
    for j,key in enumerate(contrast_family()):
        # Distinct continuous serially dependent series; paired, coin-pooled counts.
        # Each side stands for up to three simultaneous coins, never resampled apart.
        rows=[(sum(math.sin((i+c)/17)+j/332 for c in range(3)),3,
               sum(math.cos((i+c)/23) for c in range(3)),3) for i in range(n)]
        r=block_bootstrap(rows,starts)
        if r['status']!='computed':raise ValueError('Synthetic capacity contrast incomplete')
        out.append(dict(contrast=key,**r))
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>768*1024:raise MemoryError('RSS early limit')
        if (j+1)%40==0:print(j+1,round(time.perf_counter()-began,3),flush=True)
    adjusted=holm([x['p'] for x in out])
    digest=hashlib.sha256(json.dumps([out,adjusted],sort_keys=True).encode()).hexdigest()
    result=dict(status='completed_synthetic_only',contrasts=len(out),replicates_each=9999,
        timegroups=n,coins_per_group=3,seed=606,block=42,
        elapsed_seconds=time.perf_counter()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        output_sha256=digest,source_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('scripts/phase6e_technical.py','scripts/phase6e_capacity.py')},python=sys.version,limits=dict(seconds=600,address_space_bytes=1024**3,rss_bytes=768*1024**2),
        historical_data_read=False,execution_authorized=False)
    with Path('experiments/phase6e_technical/capacity.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    signal.alarm(0);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
