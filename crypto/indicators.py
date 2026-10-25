"""Deterministische Decimal-indicatoren met expliciete warm-up."""
from decimal import Decimal
from pydantic import Field, model_validator
from .models import Model


class IndicatorConfig(Model):
    fast: int = Field(default=9, ge=2, le=200)
    slow: int = Field(default=21, ge=3, le=300)
    rsi: int = Field(default=14, ge=2, le=200)
    atr: int = Field(default=14, ge=2, le=200)
    momentum: int = Field(default=10, ge=1, le=200)
    structure: int = Field(default=5, ge=2, le=100)
    sideways: Decimal = Field(default=Decimal('.002'), gt=0, le=Decimal('.1'))

    @model_validator(mode='after')
    def ordered(self):
        if self.fast >= self.slow: raise ValueError('fast moet kleiner zijn dan slow')
        return self


def ema(values, period):
    if len(values)<period: raise ValueError('Onvoldoende EMA-data')
    state=sum(values[:period])/period
    alpha=Decimal(2)/Decimal(period+1)
    for value in values[period:]: state=alpha*value+(1-alpha)*state
    return state


def wilder(values, period):
    if len(values)<period: raise ValueError('Onvoldoende Wilder-data')
    state=sum(values[:period])/period
    for value in values[period:]: state=(state*(period-1)+value)/period
    return state


def technical(rows, config):
    needed=max(config.slow,config.rsi+1,config.atr+1,config.momentum+1,config.structure*2)
    if len(rows)<needed: return {'status':'incomplete','missing':[f'minimaal {needed} candles vereist; ontvangen {len(rows)}'],'direction':'unknown'}
    closes=[c.close for c in rows]
    differences=[b-a for a,b in zip(closes,closes[1:])]
    gain=wilder([max(d,Decimal(0)) for d in differences],config.rsi)
    loss=wilder([max(-d,Decimal(0)) for d in differences],config.rsi)
    rsi=Decimal(50) if gain==loss==0 else Decimal(100) if loss==0 else 100-100/(1+gain/loss)
    ranges=[max(c.high-c.low,abs(c.high-p.close),abs(c.low-p.close)) for p,c in zip(rows,rows[1:])]
    fast,slow=ema(closes,config.fast),ema(closes,config.slow)
    momentum=closes[-1]/closes[-1-config.momentum]-1
    n=config.structure
    previous,recent=rows[-2*n:-n],rows[-n:]
    structure='higher_highs_lows' if max(c.high for c in recent)>max(c.high for c in previous) and min(c.low for c in recent)>min(c.low for c in previous) else 'lower_highs_lows' if max(c.high for c in recent)<max(c.high for c in previous) and min(c.low for c in recent)<min(c.low for c in previous) else 'mixed'
    gap=fast/slow-1
    direction='up' if gap>config.sideways else 'down' if gap < -config.sideways else 'flat'
    conflicts=[]
    if direction=='up' and (momentum<0 or rsi>=70): conflicts.append('EMA omhoog maar momentum negatief of RSI >=70')
    if direction=='down' and (momentum>0 or rsi<=30): conflicts.append('EMA omlaag maar momentum positief of RSI <=30')
    return dict(status='complete',direction=direction,ema_fast=str(fast),ema_slow=str(slow),ema_gap=str(gap),rsi=str(rsi),atr=str(wilder(ranges,config.atr)),momentum=str(momentum),structure=structure,conflicts=conflicts,missing=[])


def classify(features,config):
    if features['status']!='complete': return 'uncertain'
    gap,momentum=Decimal(features['ema_gap']),Decimal(features['momentum'])
    if abs(gap)<=config.sideways and abs(momentum)<=config.sideways: return 'sideways'
    if gap>config.sideways and momentum>0 and features['structure']=='higher_highs_lows': return 'bullish'
    if gap < -config.sideways and momentum<0 and features['structure']=='lower_highs_lows': return 'bearish'
    return 'uncertain'
