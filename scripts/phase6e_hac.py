"""Unactivated research candidate. Requires stable weak dependence for inference."""
import math


def ratio_hac(rows, lag=42, eligible=True):
    if not eligible:return {'status':'insufficient_data','p':None,'interval':None}
    n=len(rows)
    if not 0<=lag<n or n<2:raise ValueError('Invalid lag/sample')
    if any(len(r)!=4 or any(not math.isfinite(v) for v in r) or r[1]<0 or r[3]<0 for r in rows):
        raise ValueError('Invalid aggregates')
    totals=[math.fsum(r[j] for r in rows) for j in range(4)]
    if not totals[1] or not totals[3]:return {'status':'empty_group','p':None,'interval':None}
    a,b=totals[0]/totals[1],totals[2]/totals[3]
    ca,cb=totals[1]/n,totals[3]/n
    u=[(r[0]-a*r[1])/ca-(r[2]-b*r[3])/cb for r in rows]
    center=math.fsum(u)/n;u=[x-center for x in u]
    gamma0=math.fsum(x*x for x in u)/n
    lrv=gamma0+2*math.fsum((1-k/(lag+1))*math.fsum(u[t]*u[t-k] for t in range(k,n))/n for k in range(1,lag+1))
    if not math.isfinite(lrv):raise ValueError('Nonfinite variance')
    if lrv<=0:return {'status':'zero_or_invalid_variance','p':None,'interval':None}
    se=math.sqrt(lrv/n);theta=a-b;z=theta/se
    p=math.erfc(abs(z)/math.sqrt(2))
    # Underflow must never be presented as exact p=0.
    return dict(status='asymptotic_only',theta=theta,se=se,z=z,
        p=max(p,math.ulp(0.0)),p_underflow=p==0,lag=lag,
        interval=[theta-1.959963984540054*se,theta+1.959963984540054*se])
