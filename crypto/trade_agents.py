"""Vaste fase-5-onderzoeksregels. Agents produceren berichten, nooit orders."""
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal as D
from typing import Literal
from uuid import NAMESPACE_URL, uuid5
import json
from pydantic import Field
from .analysis import boundary, FRAMES
from .data import Candle, utc
from .models import Model, Message, now
from .news import NewsItem
from .quant import QuantResearcher
from .sim_execution import FillCosts, digest, canonical


class DecisionPolicy(Model):
    version: Literal['phase5-v1'] = 'phase5-v1'
    # Geen nieuwe hypothese of achteraf geselecteerde "beste" variant.
    hypothesis: Literal['regime_momentum', 'aligned_trend', 'sideways_recovery'] = 'aligned_trend'
    unknown_sentiment: Literal['neutral_unknown'] = 'neutral_unknown'
    planned_risk: D = Field(default=D('.005'), gt=0, le=D('.005'))
    stop_atr: Literal[2] = 2
    horizon_hours: Literal[4] = 4
    # De drie bestaande hypotheses hebben geen target; exit primitive ondersteunt het wel.
    target: None = None
    max_consecutive_losses: int = Field(default=3, ge=1, le=3)
    costs: FillCosts = Field(default_factory=FillCosts)

    @property
    def fingerprint(self): return digest(self.model_dump(mode='json'))


def message(kind, symbol, at, policy, result, inputs=(), **data):
    utc(at)
    payload = dict(policy=policy.fingerprint, dependencies=[str(m.event_id) for m in inputs], **data)
    result = json.loads(canonical(result))
    identity = digest(dict(kind=kind, coin=symbol, at=at, data=payload, result=result))
    return Message(agent_id=kind+':'+symbol, event_id=uuid5(NAMESPACE_URL, identity),
                   coin=symbol, timestamp=at, timeframe='15m/1h/4h', data=payload,
                   result=result, rationale='Vast onderzoeksbeleid; geen uitvoerbare order of winstkans', ttl_seconds=60)


class DecisionAgent:
    def __init__(self, plan, policy, symbol, at, report=None, position=None):
        utc(at)
        self.plan, self.policy, self.symbol, self.at = plan, policy, symbol, at
        self.report = report.model_copy(deep=True) if report else None
        self.position = deepcopy(position)
        self.id = 'decision:'+symbol

    async def run(self, inputs):
        missing, conflicts, contributors = [], [], {}
        result = dict(action='HOLD', missing=missing, conflicts=conflicts, contributions=contributors,
                      hypothesis=self.policy.hypothesis, sentiment='unknown', research_only=True)
        report = self.report
        try:
            if self.at > now() or boundary(self.at, '15m') != self.at:
                raise ValueError('Beslissing vereist een afgesloten 15m-candlegrens')
            if self.symbol not in self.plan.coins or self.policy.hypothesis not in self.plan.hypotheses:
                raise ValueError('Coin of hypothese buiten vast protocol')
            if not self.plan.development.contains(self.at) or self.at+timedelta(hours=4)>self.plan.development.end:
                raise ValueError('Uitsluitend ontwikkeling; validatie en onafhankelijke test gesloten')
            if report is None: raise ValueError('Onderzoeksanalyses ontbreken')
            if report.timestamp!=self.at: raise ValueError('Verouderd of verkeerd uitgelijnd rapporttijdstip')
            if report.coin != self.symbol: raise ValueError('Verkeerde coin')
            result['analysis_validation'] = 'failed'
            components = report.result.get('components', {})
            for name in ('scanner', 'regime', 'technical', 'multi_timeframe', 'sentiment'):
                if name not in components: missing.append(name)
                else: contributors[name] = components[name]
            if missing: raise ValueError('Essentiële analysecomponent ontbreekt')
            for tf, f in report.data.get('frames', {}).items():
                if f.get('status')!='complete': missing.append(tf+': onvolledige indicatorgegevens')
            selection = QuantResearcher(self.plan).evaluate(report, self.at)
            result['analysis_validation'] = 'validated'
            frames = selection['features']
            for tf, f in frames.items():
                conflicts.extend(f'{tf}: {c}' for c in f.get('conflicts', []))
                if f.get('missing'): missing.extend(f['missing'])
                for field in ('atr', 'rsi', 'momentum', 'ema_gap', 'ema_fast', 'ema_slow'):
                    value = D(f[field])
                    if not value.is_finite(): raise ValueError('Niet-eindige indicator')
                if D(f['atr']) <= 0 or not 0 <= D(f['rsi']) <= 100:
                    raise ValueError('Ongeldige ATR/RSI')
            scan = components['scanner']
            ranked = [r for r in scan['ranking'] if r['symbol']==self.symbol]
            if len(ranked)!=1 or any(r['symbol']==self.symbol for r in scan['rejections']):
                raise ValueError('Coin ontbreekt in geldige scannerselectie')
            row = ranked[0]
            if datetime.fromisoformat(row['data_end']) != boundary(self.at, '1h') or not row['sources']:
                raise ValueError('Verouderde scanner of bron ontbreekt')
            if not D(row['score']).is_finite() or not 0<=D(row['score'])<=100:
                raise ValueError('Ongeldige scannerscore')
            mtf = components['multi_timeframe']
            if mtf['agreement'] != 'agreement' or len(set(mtf['directions'].values())) != 1:
                conflicts.append('Timeframes spreken elkaar tegen of zijn onvolledig')
            if mtf['ends'] != {tf: frames[tf]['end'] for tf in FRAMES}:
                raise ValueError('Verkeerde timeframe-uitlijning')
            sentiment = components['sentiment']
            # De huidige adapter kent uitsluitend unknown; tekst/scores worden nooit positief bewijs.
            if sentiment['sentiment'] != 'unknown':
                raise ValueError('Onbekende, niet gevalideerde sentimentclassificatie')
            seen = set()
            for raw in sentiment['items']:
                item = NewsItem.model_validate(raw)
                if item.symbol != self.symbol or not item.available<=self.at<item.expires or item.id in seen:
                    raise ValueError('Toekomstig, verlopen of dubbel nieuwsitem')
                seen.add(item.id)
            if sentiment.get('rejections'): missing.append('Nieuwsadapter heeft ongeldige data afgewezen')
            if not sentiment['items']: result['uncertainties'] = ['geen betrouwbare nieuwsdata; neutraal/onbekend, geen positieve bijdrage']
            conflicts.extend(report.result.get('conflicts', []))
            missing.extend(x for x in report.result.get('missing', []) if x != 'geen betrouwbare nieuwsdata')
            result['eligible'] = selection['hypotheses'][self.policy.hypothesis]['eligible']
            result['atr'] = frames['1h']['atr']
            regime = components['regime']['classification']
            if regime == 'uncertain': missing.append('Onzeker marktregime')
            if not missing and not conflicts:
                if self.position and self.position.symbol==self.symbol and regime=='bearish':
                    result['action'] = 'EXIT_REVIEW'
                elif not self.position and result['eligible']:
                    result['action'] = 'BUY_CANDIDATE'
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            missing.append(str(exc))
        result['missing'] = sorted(set(missing)); result['conflicts'] = sorted(set(conflicts))
        return message('decision', self.symbol, self.at, self.policy, result,
                       (report,) if report else (), plan=self.plan.fingerprint)


class EntryAgent:
    def __init__(self, policy, symbol, at, ledger, reference):
        self.policy, self.symbol, self.at = policy, symbol, at
        self.ledger, self.reference = deepcopy(ledger), reference
        self.id = 'entry:'+symbol

    async def run(self, inputs):
        result = dict(action='REJECTED', reason='BUY_CANDIDATE ontbreekt', research_only=True)
        try:
            if len(inputs)!=1: raise ValueError('Eén beslissing vereist')
            decision = inputs[0]
            if decision.agent_id!='decision:'+self.symbol or decision.coin!=self.symbol or not decision.usable(self.at) or decision.timestamp!=self.at or decision.data['policy']!=self.policy.fingerprint:
                raise ValueError('Verkeerde, toekomstige of verlopen beslissing')
            if decision.result['action']!='BUY_CANDIDATE': raise ValueError('Uitsluitend BUY_CANDIDATE wordt beoordeeld')
            if self.ledger.position: raise ValueError('Bestaande positie; geen tweede exposure')
            bar = Candle.model_validate(self.reference.model_dump() if isinstance(self.reference,Candle) else self.reference)
            if bar.symbol!=self.symbol or bar.interval!='15m' or bar.closed!=self.at:
                raise ValueError('Laatste afgesloten 15m-candle ontbreekt')
            qty, stop = self.ledger.size(bar.close, D(decision.result['atr'])*self.policy.stop_atr)
            price = self.policy.costs.price(bar.close, 'buy', self.ledger.rules.tick)
            reason = self.ledger.rules.check(qty, price, self.at)
            if reason: raise ValueError(reason)
            if stop<=0 or stop>=bar.close or stop%self.ledger.rules.tick: raise ValueError('Ongeldige stop')
            fee = self.policy.costs.charge(qty, price)
            sell = self.policy.costs.price(stop, 'sell', self.ledger.rules.tick)
            stop_failure = self.ledger.rules.check(qty, sell, self.at)
            if stop_failure: raise ValueError('stop_exit_'+stop_failure)
            risk = qty*(price-sell)+fee+self.policy.costs.charge(qty, sell)
            if qty*price+fee>self.ledger.cash: raise ValueError('onvoldoende saldo inclusief kosten')
            if risk>min(D(200), self.ledger.cash)*self.policy.planned_risk: raise ValueError('gepland risico boven 0,5%')
            result.update(action='ENTRY_CANDIDATE', reason='Vaste hypothese; volgende candle-open, onder voorbehoud van Risk Engine',
                          quantity=qty, reference=bar.close, price=price, stop=stop, target=None,
                          deadline=(self.at+timedelta(hours=4)).isoformat(), earliest_execution=self.at.isoformat(),
                          planned_risk=risk, fee=fee, costs=self.policy.costs.model_dump(mode='json'),
                          metadata=self.ledger.rules.model_dump(mode='json'))
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            result['reason'] = str(exc)
        return message('entry', self.symbol, self.at, self.policy, result, inputs,
                       reference=self.reference.model_dump(mode='json') if isinstance(self.reference,Candle) else None)


class ExitAgent:
    def __init__(self, policy, symbol, at, ledger, bar=None, emergency=False):
        self.policy, self.symbol, self.at = policy, symbol, at
        self.ledger, self.bar, self.emergency = deepcopy(ledger), bar, emergency
        self.id = 'exit:'+symbol

    async def run(self, inputs):
        result = dict(action='HOLD_POSITION', reason='Geen positie', research_only=True)
        try:
            p = self.ledger.position
            if not p: return message('exit', self.symbol, self.at, self.policy, result, inputs)
            if p.symbol!=self.symbol: raise ValueError('Positie van andere coin')
            bar = Candle.model_validate(self.bar.model_dump() if isinstance(self.bar,Candle) else self.bar)
            if bar.symbol!=self.symbol or bar.interval!='15m' or bar.closed!=self.at or bar.opened<p.entered_at:
                raise ValueError('Ontbrekende, onafgesloten of verkeerd uitgelijnde exitcandle')
            stop, target = bar.low<=p.stop, p.target is not None and bar.high>=p.target
            raw, reason, ambiguous = bar.close, 'Geen exitvoorwaarde geraakt', False
            if self.emergency or self.ledger.day_paused or self.ledger.drawdown_paused:
                raw, reason, ambiguous = bar.low, 'veiligheidsstop: ongunstigste candleprijs', True
            elif bar.opened>=p.deadline:
                raw, reason = bar.open, 'tijdslimiet'
            elif stop:
                raw, reason, ambiguous = min(bar.open,p.stop), 'stop_gap' if bar.open<p.stop else 'stop', target
            elif target:
                raw, reason = p.target, 'winstdoel'
            else:
                # Alleen observeren op een kopie: dagelijkse/drawdownbescherming uit fase 4B.
                self.ledger.observe(bar.closed, bar.low)
                if self.ledger.day_paused or self.ledger.drawdown_paused:
                    raw, reason, ambiguous = bar.low, 'portefeuillelimiet: ongunstigste candleprijs', True
            result.update(reason=reason, position_id=p.order_id)
            if reason!='Geen exitvoorwaarde geraakt':
                result.update(action='EXIT_CANDIDATE', quantity=p.quantity, reference=raw,
                              price=self.policy.costs.price(raw,'sell',self.ledger.rules.tick), ambiguous=bool(ambiguous))
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            result['reason'] = str(exc)
        return message('exit', self.symbol, self.at, self.policy, result, inputs,
                       bar=self.bar.model_dump(mode='json') if isinstance(self.bar,Candle) else None)
