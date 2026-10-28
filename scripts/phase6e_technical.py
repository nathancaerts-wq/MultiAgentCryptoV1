"""Technical research primitives; no historical reader, order path or activation."""
import math
import random
from array import array
from datetime import timedelta
from decimal import Decimal as D, getcontext
from crypto.data import Candle, validate_series, SECONDS
from crypto.analysis import boundary
from crypto.indicators import technical, IndicatorConfig
from scripts.phase6e_protocol import COINS, FIRST, LAST, utc


def extract_features(coin, at, candles, recorded, scores, *, score_at):
    at = utc(at)
    if getcontext().prec != 28 or utc(score_at) != at:
        raise ValueError('Decimal precision or scanner snapshot mismatch')
    if coin not in COINS or not FIRST <= at <= LAST or at.microsecond or int(at.timestamp()) % 900:
        raise ValueError('Outside decision grid')
    if set(candles) != set(SECONDS) or set(recorded) != set(SECONDS):
        raise ValueError('Missing timeframe')
    out = {}; up = 0
    for tf, seconds in SECONDS.items():
        end = boundary(at, tf)
        rows = [Candle.model_validate(c.model_dump()) for c in candles[tf]]
        validate_series(rows, coin, tf, end-timedelta(seconds=33*seconds), end, at)
        if rows[0].opened < FIRST.replace(day=1):
            raise ValueError('Warmup outside 2024')
        current = technical(rows[1:], IndicatorConfig())
        previous = technical(rows[:-1], IndicatorConfig())
        saved = recorded[tf]
        if utc(saved['end']) != end or saved['count'] != 32:
            raise ValueError('Wrong recorded window')
        for key in ('rsi','ema_fast','ema_slow','ema_gap','atr','direction'):
            if current[key] != saved[key]:
                raise ValueError('Recorded indicator reproduction mismatch: '+key)
        close = rows[-1].close
        volume_mean = sum(c.volume for c in rows[-21:-1])/20
        vals = dict(rsi=D(current['rsi']), delta_rsi=D(current['rsi'])-D(previous['rsi']),
            ema_gap=D(current['ema_gap']), trend_strength=abs(D(current['ema_gap'])),
            close_ema=close/D(current['ema_slow'])-1, relative_atr=D(current['atr'])/close,
            volume_ratio=rows[-1].volume/volume_mean if volume_mean else None,
            volume_change=rows[-1].volume/rows[-2].volume-1 if rows[-2].volume else None)
        out.update({tf+':'+k:v for k,v in vals.items()})
        up += current['direction']=='up'
    if set(scores) != set(COINS):
        raise ValueError('Incomplete contemporaneous scanner universe')
    normalized = {c:D(v) if v is not None else None for c,v in scores.items()}
    if any(v is not None and not v.is_finite() for v in normalized.values()):
        raise ValueError('Nonfinite score')
    own = normalized[coin]
    out.update(scanner_score=own, scanner_rank=None if any(v is None for v in normalized.values()) else
        D(1+sum(v>own for v in normalized.values())), up_count=D(up))
    return out


def holm(pvalues):
    """None participates as 1; retains None in visible output."""
    p = [1.0 if v is None else float(v) for v in pvalues]
    if any(not math.isfinite(v) or not 0<=v<=1 for v in p):
        raise ValueError('Invalid p')
    order = sorted(range(len(p)), key=lambda i:(p[i],i)); result=[None]*len(p); running=0
    for rank, i in enumerate(order):
        running=max(running,min(1.0,(len(p)-rank)*p[i]))
        if pvalues[i] is not None: result[i]=running
    return result


def nearest(values, probability):
    if not values or not 0<=probability<=1: raise ValueError('Invalid quantile')
    return sorted(values)[max(0,math.ceil(probability*len(values))-1)]


def centered_p(theta, replicates):
    if not replicates or not math.isfinite(theta) or any(not math.isfinite(v) for v in replicates):
        raise ValueError('Invalid bootstrap estimates')
    return (1+sum(abs(v-theta)>=abs(theta) for v in replicates))/(len(replicates)+1)


def bootstrap_starts(n, repetitions=9999, block=42, seed=606):
    if n<block or repetitions<1 or block<1: raise ValueError('Invalid bootstrap dimensions')
    rng=random.Random(seed)
    return [array('I',(rng.randrange(n) for _ in range(math.ceil(n/block)))) for _ in range(repetitions)]


def aggregate_groups(times, left, right):
    """Each time contains all three coins; None = absent/feature missing.

    Returns sums/counts; same observation may be present in both groups (D).
    Missingness eligibility is checked separately before aggregation by the caller.
    """
    if len(times)!=len(left) or len(times)!=len(right) or not times:
        raise ValueError('Invalid time groups')
    start=utc(times[0]); result=[]; blocks=[set(),set()]; groups=[0,0]
    if int(start.timestamp())%14400 or start<FIRST or utc(times[-1])>LAST:
        raise ValueError('Not the approved UTC4h grid')
    for i,(t,a,b) in enumerate(zip(times,left,right)):
        if utc(t)!=start+timedelta(hours=4*i) or len(a)!=3 or len(b)!=3:
            raise ValueError('Overlap, gap or ungrouped coins')
        sums=[]
        for side, vals in enumerate((a,b)):
            vs=[float(v) for v in vals if v is not None]
            if any(not math.isfinite(v) for v in vs): raise ValueError('Nonfinite feature')
            if vs:
                blocks[side].add(int((t-FIRST).total_seconds())//604800); groups[side]+=1
            sums.extend((sum(vs),len(vs)))
        result.append(tuple(sums))
    eligible=all(len(b)>=20 for b in blocks) and all(n>=30 for n in groups)
    return result,eligible


def block_bootstrap(aggregates, starts, eligible=True, block=42):
    """Circular blocks of sufficient statistics: preserves paired group/coin weights."""
    if not eligible: return dict(status='insufficient_groups',p=None,interval=None)
    n=len(aggregates)
    if n<block or not starts or any(len(s)!=math.ceil(n/block) for s in starts):
        raise ValueError('Invalid starts')
    if any(i<0 or i>=n for s in starts for i in s): raise ValueError('Invalid start index')
    if any(len(r)!=4 or any(not math.isfinite(v) for v in r) or r[1]<0 or r[3]<0 for r in aggregates):
        raise ValueError('Invalid aggregates')
    total=[sum(r[j] for r in aggregates) for j in range(4)]
    if not total[1] or not total[3]:return dict(status='empty_group',p=None,interval=None)
    theta=total[0]/total[1]-total[2]/total[3]
    # Prefix tables give exactly the same sampled sums as expanding coin rows.
    prefix=[]
    for j in range(4):
        acc=array('d',[0.0])
        for r in aggregates*2: acc.append(acc[-1]+r[j])
        prefix.append(acc)
    full=[[p[i+block]-p[i] for i in range(n)] for p in prefix]
    rest=n%block
    tail=[[p[i+rest]-p[i] for i in range(n)] for p in prefix] if rest else full
    reps=array('d')
    for indices in starts:
        sums=[sum(table[i] for i in indices[:-1])+last[indices[-1]] for table,last in zip(full,tail)]
        if not sums[1] or not sums[3]: return dict(status='empty_replicate',p=None,interval=None)
        reps.append(sums[0]/sums[1]-sums[2]/sums[3])
    if min(reps)==max(reps):return dict(status='zero_variation',p=None,interval=None)
    return dict(status='computed',theta=theta,p=centered_p(theta,reps),
        interval=[nearest(reps,.025),nearest(reps,.975)],replicates=len(reps))


def feature_names():
    names=[tf+':'+key for tf in SECONDS for key in ('rsi','delta_rsi','ema_gap','trend_strength',
        'close_ema','relative_atr','volume_ratio','volume_change')]
    return names+['scanner_score','scanner_rank','up_count']


def contrast_family():
    strata=('pooled',)+COINS
    names=[(family,stratum,feature) for family in ('A','B','D') for stratum in strata for feature in feature_names()]
    return names+[('C',stratum,label) for stratum in strata for label in ('gross_positive','net_positive')]


def missing_eligible(missing, selected, pooled_scores_complete=True):
    if selected<0 or missing<0 or missing>selected:raise ValueError('Invalid missing count')
    return bool(selected and missing*100<=selected and pooled_scores_complete)
