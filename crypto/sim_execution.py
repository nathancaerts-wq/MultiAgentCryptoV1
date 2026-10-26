"""Conservatieve OFFLINE uitvoering. Geen beursverbinding of paper-orderopslag."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
import hashlib
import json
from math import lcm
from typing import Literal
from pydantic import AwareDatetime, Field, model_validator
from .models import Model, Limits
from .data import utc

D = Decimal
MONEY = D('.00000001')


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def rounded(value, step, upward=False):
    return (value / step).to_integral_value(rounding=ROUND_CEILING if upward else ROUND_FLOOR) * step


class FillCosts(Model):
    fee: Decimal = Field(default=D('.001'), ge=0, le=D('.2'))
    spread: Decimal = Field(default=D('.001'), ge=0, le=D('.2'))
    slippage: Decimal = Field(default=D('.001'), ge=0, le=D('.2'))

    def price(self, raw, side, tick):
        impact = self.spread/2+self.slippage
        return rounded(raw*(1+impact if side=='buy' else 1-impact), tick, side=='buy')

    def impact(self, quantity, raw, price):
        spread=quantity*raw*self.spread/2
        slippage=quantity*raw*self.slippage
        return {'spread':spread,'slippage':slippage,
                'adverse_tick_rounding':quantity*abs(price-raw)-spread-slippage}

    def charge(self, quantity, price):
        return rounded(quantity*price*self.fee, MONEY, True)


class SpotFilters(Model):
    symbol: str = Field(pattern=r'^[A-Z0-9]+EUR$')
    source: str = Field(min_length=1)
    status: Literal['assumed', 'validated']
    note: str = Field(min_length=1)
    known_at: AwareDatetime | None = None
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    tick: Decimal = Field(gt=0)
    min_price: Decimal = Field(default=D(0), ge=0)
    max_price: Decimal | None = Field(default=None, gt=0)
    min_qty: Decimal = Field(ge=0)
    max_qty: Decimal = Field(gt=0)
    step: Decimal = Field(gt=0)
    market_min_qty: Decimal = Field(default=D(0), ge=0)
    market_max_qty: Decimal | None = Field(default=None, gt=0)
    market_step: Decimal = Field(default=D(0), ge=0)
    min_notional: Decimal = Field(default=D(0), ge=0)
    min_notional_market: bool = True
    notional_min: Decimal = Field(default=D(0), ge=0)
    notional_max: Decimal | None = Field(default=None, gt=0)
    notional_apply_min_market: bool = True
    notional_apply_max_market: bool = True
    avg_price_mins: int = Field(default=0, ge=0)

    @model_validator(mode='after')
    def consistent(self):
        if self.min_qty>self.max_qty or (self.market_max_qty is not None and self.market_min_qty>self.market_max_qty):
            raise ValueError('Ongeldige hoeveelheidsgrenzen')
        if self.max_price is not None and self.min_price>self.max_price: raise ValueError('Ongeldige prijsgrenzen')
        if self.notional_max is not None and self.notional_min>self.notional_max: raise ValueError('Ongeldige notionalgrenzen')
        for t in (self.known_at,self.valid_from,self.valid_until):
            if t is not None: utc(t)
        if self.status=='validated':
            from urllib.parse import urlsplit
            if urlsplit(self.source).hostname not in ('api.binance.com','data-api.binance.vision'):
                raise ValueError('Officiële Binance metadata-host vereist')
            if None in (self.known_at,self.valid_from,self.valid_until): raise ValueError('Historische geldigheid vereist')
            if self.valid_from>=self.valid_until: raise ValueError('Ongeldige metadataperiode')
            if not self.source.startswith('https://'): raise ValueError('Officiële metadata-bron vereist')
        return self

    @property
    def quantity_step(self):
        if self.market_step==0: return self.step
        scale=10**max(-self.step.as_tuple().exponent,-self.market_step.as_tuple().exponent,0)
        return D(lcm(int(self.step*scale),int(self.market_step*scale)))/scale

    def check(self, quantity, price, at):
        if self.status=='validated' and not (self.known_at<=at and self.valid_from<=at<self.valid_until): return 'historische_metadata_niet_geldig'
        if self.avg_price_mins: return 'historische_gemiddelde_notionalprijs_ontbreekt'
        if quantity<=0 or not self.min_qty<=quantity<=self.max_qty or quantity%self.step: return 'LOT_SIZE'
        if quantity<self.market_min_qty or (self.market_max_qty is not None and quantity>self.market_max_qty) or (self.market_step and quantity%self.market_step): return 'MARKET_LOT_SIZE'
        if price<=0 or price%self.tick or price<self.min_price or (self.max_price is not None and price>self.max_price): return 'PRICE_FILTER'
        notional=quantity*price
        if self.min_notional_market and notional<self.min_notional: return 'MIN_NOTIONAL'
        if self.notional_apply_min_market and notional<self.notional_min: return 'NOTIONAL_MIN'
        if self.notional_apply_max_market and self.notional_max is not None and notional>self.notional_max: return 'NOTIONAL_MAX'
        return None


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: Decimal
    average_price: Decimal
    entry_fee: Decimal
    raw_entry: Decimal
    stop: Decimal
    target: Decimal | None
    entered_at: datetime
    deadline: datetime
    order_id: str


class OfflineLedger:
    """Eén open positie per experiment; exacte kas- en kostenbasisreconciliatie."""
    def __init__(self, costs, rules, risk=D('.005')):
        if not D(0)<risk<=D('.005'): raise ValueError('Maximaal 0,5% gepland risico')
        self.costs,self.rules,self.risk=costs,rules,risk
        self.cash=D(200); self.realized=D(0); self.fees=D(0)
        self.position=None; self.ids=set(); self.events=[]; self.trades=[]
        self.peak=D(200); self.day_start=D(200); self.day=None
        self.day_paused=False; self.drawdown_paused=False
        self.max_drawdown=D(0); self.curve=[]; self.last_equity=D(200)
        self.limits=Limits()

    def snapshot(self, mark):
        p=self.position
        basis=p.quantity*p.average_price+p.entry_fee if p else D(0)
        value=p.quantity*mark if p else D(0)
        liquidation=(p.quantity*self.costs.price(mark,'sell',self.rules.tick)-self.costs.charge(p.quantity,self.costs.price(mark,'sell',self.rules.tick))) if p else D(0)
        return {'mark':mark,'cash':self.cash,'holdings':{p.symbol:p.quantity} if p else {},'cost_basis':basis,
                'average_price':p.average_price if p else None,'fees':self.fees,'realized':self.realized,
                'unrealized':value-basis,'equity':self.cash+value,'liquidation_equity':self.cash+liquidation}

    def audit(self, action, at, **details):
        record={'sequence':len(self.events),'action':action,'at':at.isoformat(),'details':details,
                'previous':self.events[-1]['hash'] if self.events else '0'*64}
        record['hash']=digest(record); self.events.append(record)

    def reject(self, order_id, at, reason):
        self.audit('rejected',at,order_id=order_id,reason=reason)
        return False

    def reconcile(self):
        basis=self.position.quantity*self.position.average_price+self.position.entry_fee if self.position else D(0)
        if self.cash<0 or self.cash+basis != D(200)+self.realized:
            raise ArithmeticError('Ledger-reconciliatie mislukt')

    def observe(self, at, mark):
        utc(at)
        if not mark.is_finite() or mark<=0: raise ValueError('Ongeldige marktprijs')
        equity=self.snapshot(mark)['liquidation_equity']
        if self.day!=at.date():
            self.day=at.date(); self.day_start=self.last_equity; self.day_paused=False
            self.audit('risk_day_started',at,day=str(self.day),baseline=self.day_start)
        old_day_pause,old_drawdown_pause=self.day_paused,self.drawdown_paused
        self.peak=max(self.peak,equity)
        dd=(self.peak-equity)/self.peak
        self.max_drawdown=max(self.max_drawdown,dd)
        if dd>=self.limits.drawdown: self.drawdown_paused=True
        if self.day_start-equity>=self.day_start*self.limits.daily_loss: self.day_paused=True
        if self.day_paused and not old_day_pause: self.audit('daily_loss_pause',at,equity=equity,baseline=self.day_start)
        if self.drawdown_paused and not old_drawdown_pause: self.audit('drawdown_pause',at,equity=equity,peak=self.peak)
        self.last_equity=equity
        return equity

    def size(self, reference, distance):
        stop=rounded(reference-distance,self.rules.tick)
        if stop<=0: return D(0),stop
        buy=self.costs.price(reference,'buy',self.rules.tick)
        sell=self.costs.price(stop,'sell',self.rules.tick)
        unit_loss=buy*(1+self.costs.fee)-sell*(1-self.costs.fee)
        # Fee-afronding naar boven wordt vooraf gereserveerd.
        budget=max(D(0),self.cash*self.risk-2*MONEY)
        qty=min(budget/unit_loss,self.cash*self.limits.exposure/(buy*(1+self.costs.fee)))
        return rounded(qty,self.rules.quantity_step),stop

    def buy(self, order_id, at, raw, quantity, stop, deadline, target=None):
        utc(at); utc(deadline)
        self.reconcile()
        if order_id in self.ids: return self.reject(order_id,at,'duplicate_order')
        self.ids.add(order_id)
        if self.position: return self.reject(order_id,at,'positie_bestaat_correlatie_niet_gemodelleerd')
        if not all(x.is_finite() for x in (quantity,raw,stop)) or raw<=0 or (target is not None and not target.is_finite()): return self.reject(order_id,at,'niet_eindig_of_ongeldige_prijs')
        self.observe(at,raw)
        if self.drawdown_paused: return self.reject(order_id,at,'max_drawdown_pause')
        if self.day_paused: return self.reject(order_id,at,'daily_loss_pause')
        price=self.costs.price(raw,'buy',self.rules.tick)
        reason=self.rules.check(quantity,price,at)
        if reason: return self.reject(order_id,at,reason)
        if not 0<stop<min(raw,price) or stop%self.rules.tick or stop<self.rules.min_price or deadline<=at or (target is not None and (target<=price or target%self.rules.tick or (self.rules.max_price is not None and target>self.rules.max_price))):
            return self.reject(order_id,at,'ongeldige_stop_target_of_horizon')
        fee=self.costs.charge(quantity,price); debit=quantity*price+fee
        if debit>self.cash: return self.reject(order_id,at,'onvoldoende_saldo_inclusief_kosten')
        if quantity*price>self.cash*self.limits.exposure: return self.reject(order_id,at,'exposure_limit')
        stop_price=self.costs.price(stop,'sell',self.rules.tick)
        risk=debit-(quantity*stop_price-self.costs.charge(quantity,stop_price))
        if risk>self.cash*self.risk: return self.reject(order_id,at,'planned_risk_limit')
        self.cash-=debit; self.fees+=fee
        self.position=Position(self.rules.symbol,quantity,price,fee,raw,stop,target,at,deadline,order_id)
        self.reconcile()
        self.audit('buy',at,order_id=order_id,raw=raw,price=price,quantity=quantity,fee=fee,planned_risk=risk,
                   costs=self.costs.model_dump(mode='json'),impact=self.costs.impact(quantity,raw,price),metadata=self.rules.model_dump(mode='json'),snapshot=self.snapshot(price))
        return True

    def sell(self, order_id, at, raw, reason, ambiguous=False):
        utc(at)
        self.reconcile()
        if order_id in self.ids: return self.reject(order_id,at,'duplicate_order')
        self.ids.add(order_id)
        p=self.position
        if p is None: return self.reject(order_id,at,'geen_positie')
        if at<p.entered_at: return self.reject(order_id,at,'verkoop_voor_aankoop')
        if not raw.is_finite() or raw<=0: return self.reject(order_id,at,'ongeldige_verkoopprijs')
        price=self.costs.price(raw,'sell',self.rules.tick)
        failure=self.rules.check(p.quantity,price,at)
        if failure: return self.reject(order_id,at,'exit_'+failure)
        fee=self.costs.charge(p.quantity,price); proceeds=p.quantity*price-fee
        net=proceeds-p.quantity*p.average_price-p.entry_fee
        self.cash+=proceeds; self.fees+=fee; self.realized+=net; self.position=None
        trade={'entry_id':p.order_id,'exit_id':order_id,'quantity':p.quantity,'entry':p.average_price,'exit':price,
               'entered_at':p.entered_at.isoformat(),'exited_at':at.isoformat(),'fees':p.entry_fee+fee,'net':net,
               'reason':reason,'ambiguous':ambiguous,'entry_raw':p.raw_entry,'exit_raw':raw,
               'entry_impact':self.costs.impact(p.quantity,p.raw_entry,p.average_price),
               'exit_impact':self.costs.impact(p.quantity,raw,price),
               'cost_assumptions':self.costs.model_dump(mode='json')}
        self.trades.append(trade); self.reconcile()
        self.audit('sell',at,**trade,raw=raw,costs=self.costs.model_dump(mode='json'),snapshot=self.snapshot(price))
        self.observe(at,price)
        return True

    def process_bar(self, bar, serial):
        """OHLC-bar is volledig bekend bij offline verwerking; geen instapselectie hier."""
        p=self.position
        if not p: return
        if bar.opened>=p.deadline:
            self.sell(f'exit:{serial}',bar.opened,bar.open,'horizon'); return
        event_at=bar.closed-timedelta(microseconds=1)
        stop=bar.low<=p.stop; target=p.target is not None and bar.high>=p.target
        if stop:
            self.sell(f'exit:{serial}',event_at,min(bar.open,p.stop),'stop_gap' if bar.open<p.stop else 'stop',target)
        elif target:
            self.sell(f'exit:{serial}',event_at,p.target,'target')
        else:
            self.observe(event_at,bar.low)
            if self.drawdown_paused or self.day_paused:
                self.sell(f'exit:{serial}',event_at,bar.low,'portfolio_limit_worst_bar_price',True)
