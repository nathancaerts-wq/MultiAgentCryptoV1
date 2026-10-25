"""Vooraf vastgelegd offline onderzoeksprotocol; geen simulator of strategiepromotie."""
import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from typing import Literal
from pydantic import AwareDatetime, Field, model_validator
from .data import utc
from .models import Model
from .indicators import IndicatorConfig

HYPOTHESES = {
    'regime_momentum': 'Bullish 1h-regime, positieve 1h-momentum en RSI 40..70.',
    'aligned_trend': 'Bullish 1h-regime en alle 15m/1h/4h EMA-richtingen omhoog.',
    'sideways_recovery': 'Sideways 1h-regime, 1h-RSI <40 en positieve 15m-momentum.',
}
BENCHMARKS = ('buy_and_hold', 'ema_trend')
METRICS = ('trades','net_result','winrate','average_win','average_loss','expectancy',
           'profit_factor','max_drawdown','market_exposure','double_cost_net',
           'net_without_top_3_winners')


class Period(Model):
    start: AwareDatetime
    end: AwareDatetime

    @model_validator(mode='after')
    def valid(self):
        utc(self.start); utc(self.end)
        if self.start >= self.end: raise ValueError('Lege of omgekeerde periode')
        return self

    def contains(self, at): return self.start <= at < self.end

    def overlaps(self, other): return self.start < other.end and other.start < self.end


class ResearchPlan(Model):
    version: Literal['phase4-v1'] = 'phase4-v1'
    coins: tuple[str, ...] = Field(min_length=1, max_length=6)
    dataset_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    source: str = Field(min_length=1)
    report_hashes: tuple[str, str, str]
    development: Period
    validation: Period
    independent_test: Period
    indicators: IndicatorConfig = Field(default_factory=IndicatorConfig)
    hypotheses: tuple[Literal['regime_momentum','aligned_trend','sideways_recovery'], ...] = tuple(HYPOTHESES)
    starting_cash: Literal['200'] = '200'
    planned_risk: Decimal = Field(default=Decimal('.005'), gt=0, le=Decimal('.005'))
    fee: Decimal = Field(default=Decimal('.001'), ge=0, le=Decimal('.1'))
    slippage: Decimal = Field(default=Decimal('.001'), ge=0, le=Decimal('.1'))
    horizon_hours: Literal[4] = 4
    stop_atr: Literal[2] = 2
    walk_train_days: int = Field(default=7, ge=1, le=365)
    walk_validation_days: int = Field(default=2, ge=1, le=90)
    minimum_trades: int = Field(default=30, ge=30)
    family_alpha: Decimal = Field(default=Decimal('.05'), gt=0, le=Decimal('.05'))
    selection: Literal['net_expectancy_after_costs_then_lower_drawdown'] = 'net_expectancy_after_costs_then_lower_drawdown'
    assumptions: tuple[str, ...] = ('next_bar_execution_required', 'no_short_no_leverage', 'historical_revisions_not_reconstructed', 'no_validated_fill_simulator')

    @model_validator(mode='after')
    def valid(self):
        import re
        if tuple(sorted(set(self.coins))) != self.coins or any(not re.fullmatch(r'[A-Z0-9]+EUR',s) for s in self.coins):
            raise ValueError('Unieke alfabetisch gesorteerde EUR-paren vereist')
        if not self.hypotheses or len(set(self.hypotheses))!=len(self.hypotheses): raise ValueError('Vaste unieke hypothesen vereist')
        if any(not re.fullmatch(r'[0-9a-f]{64}',h) for h in self.report_hashes): raise ValueError('Drie geldige rapporthashes vereist')
        embargo=timedelta(hours=self.horizon_hours)
        if self.development.end+embargo > self.validation.start or self.validation.end+embargo > self.independent_test.start:
            raise ValueError('Chronologische scheiding met 4h embargo vereist')
        return self

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.model_dump(mode='json'),sort_keys=True).encode()).hexdigest()

    def walk_forward(self):
        train_days,validation_days=self.walk_train_days,self.walk_validation_days
        result=[]
        start=self.development.start
        # Alleen ontwikkeling: onafhankelijke test en formele validatie blijven buiten folds.
        while start+timedelta(days=train_days+validation_days,hours=4)<=self.development.end:
            train_end=start+timedelta(days=train_days)
            valid_start=train_end+timedelta(hours=4)
            result.append({'train':Period(start=start,end=train_end).model_dump(mode='json'),
                           'validation':Period(start=valid_start,end=valid_start+timedelta(days=validation_days)).model_dump(mode='json')})
            start=valid_start+timedelta(days=validation_days)
        return result


def planned_size(equity, entry, stop, fee, slippage, risk=Decimal('.005')):
    """Rekeninterface, geen order: kosten van beide zijden in gepland risicobudget."""
    equity,entry,stop,fee,slippage,risk=map(lambda x:Decimal(str(x)),(equity,entry,stop,fee,slippage,risk))
    if not all(x.is_finite() for x in (equity,entry,stop,fee,slippage,risk)) or not (equity>0 and entry>stop>0 and fee>=0 and slippage>=0 and 0<risk<=Decimal('.005')):
        raise ValueError('Ongeldige risicoinvoer')
    unit_risk=entry-stop+2*entry*(fee+slippage)
    return min(equity*risk/unit_risk, equity*Decimal('.5')/(entry*(1+fee+slippage)))


def round_trip_net(quantity, entry, exit, fee, slippage):
    """Uitsluitend deterministische kostenrekening voor toekomstige fill-adapters."""
    q,a,b,f,s=map(lambda x:Decimal(str(x)),(quantity,entry,exit,fee,slippage))
    if not all(x.is_finite() for x in (q,a,b,f,s)) or not(q>0 and a>0 and b>0 and 0<=f<1 and 0<=s<1): raise ValueError('Ongeldige kosteninvoer')
    return q*b*(1-s)*(1-f)-q*a*(1+s)*(1+f)


def unavailable_performance():
    return dict(status='not_computed',reason='Gevalideerde fillsimulator en ledger ontbreken',
                evidence='insufficient_evidence',metrics={k:None for k in METRICS})


def report_digest(reports):
    from .models import Message
    normalized=[Message.model_validate(r).model_dump(mode='json') for r in reports]
    encoded=sorted(json.dumps(r,sort_keys=True,allow_nan=False) for r in normalized)
    return hashlib.sha256(json.dumps(encoded).encode()).hexdigest()
