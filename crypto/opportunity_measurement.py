"""Phase 6D descriptive price labels, with a causal feature/output boundary."""
from datetime import timedelta
from decimal import Decimal as D
from .data import Candle, utc, validate_series
from .january_pilot import COINS, ENTRY
from .development_2024 import END, LAST_ENTRY
from .sim_execution import FillCosts
from .indicators import IndicatorConfig
from .analysis import boundary

Q=D('.001'); TICK=D('.01'); COSTS=FillCosts()

def known_features(report, coin, at, previous):
    utc(at)
    if (report.coin!=coin or report.timestamp!=at or previous.symbol!=coin or previous.closed!=at
        or previous.interval!='15m' or report.data['parameters']!=IndicatorConfig().model_dump(mode='json')):
        raise ValueError('Invalid known-at feature context')
    for tf in ('15m','1h','4h'):
        f=report.data['frames'][tf]
        from datetime import datetime
        end=datetime.fromisoformat(f['end']);utc(end)
        if f['status']!='complete' or f['count']!=32 or end!=boundary(at,tf):
            raise ValueError('Missing or future feature frame')
    f=report.data['frames']['1h']
    out={'regime':report.result['components']['regime']['frames']['1h']['classification'],
         'direction':f['direction']}
    for key in ('rsi','momentum','atr'):
        value=D(f[key])
        if not value.is_finite():raise ValueError('Nonfinite feature')
        out[key]=value/previous.close if key=='atr' else value
    return out


def measure(rows, coin, at):
    utc(at)
    if coin not in COINS or not ENTRY<=at<=LAST_ENTRY:raise ValueError('Outside approved label universe')
    candles=[Candle.model_validate(c.model_dump()) for c in rows]
    end=at+timedelta(hours=4)
    if end>END:raise ValueError('Outside development')
    validate_series(candles,coin,'15m',at,end,end)
    a,b=candles[0].open,candles[-1].close
    buy,sell=COSTS.price(a,'buy',TICK),COSTS.price(b,'sell',TICK)
    fee=COSTS.charge(Q,buy)+COSTS.charge(Q,sell)
    gross=b/a-1;net=Q*(sell-buy)-fee
    return dict(gross=gross,label='positive' if gross>0 else 'negative' if gross<0 else 'neutral',
        hypothetical_net=net,net_positive=net>0,minimum=min(c.low for c in candles)/a-1,
        fees=fee,entry_open=a,valuation_close=b,
        nonoverlap=int(at.timestamp())%14400==0,executable=False)
