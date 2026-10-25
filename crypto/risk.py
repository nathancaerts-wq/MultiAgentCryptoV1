from decimal import Decimal
from uuid import uuid4
from .models import Limits, Proposal, MarketRules, now


class RiskEngine:
    def __init__(self, hard: Limits, operational: Limits):
        for name in Limits.model_fields:
            if getattr(operational, name) > getattr(hard, name):
                raise ValueError('Operationele limiet overschrijdt bovengrens')
        self.hard, self.limits = hard, operational
        self.stopped = False

    def check(self, proposal, rules, cash, equity, exposure, daily_loss, peak, correlation):
        p = Proposal.model_validate(proposal)
        if self.stopped:
            return 'noodstop'
        if rules is None or correlation is None:
            return 'ontbrekende marktgegevens'
        r = MarketRules.model_validate(rules)
        numbers = [Decimal(str(v)) for v in (cash, equity, exposure, daily_loss, peak, correlation)]
        if any(not n.is_finite() or n < 0 for n in numbers):
            return 'ongeldige portefeuille'
        cash, equity, exposure, daily_loss, peak, correlation = numbers
        if equity <= 0 or peak < equity or correlation > 1:
            return 'ongeldige portefeuille'
        l = self.limits
        for timestamp in (p.timestamp, r.timestamp):
            if not 0 <= (now()-timestamp).total_seconds() < l.max_age:
                return 'verouderde marktgegevens'
        if not r.enabled or r.symbol != p.symbol:
            return 'ongeldig handelspaar'
        cost = p.quantity * p.price
        if not r.min_qty <= p.quantity <= r.max_qty or p.quantity % r.step or p.price % r.tick or p.stop % r.tick:
            return 'Binance precisie/hoeveelheid'
        if cost < r.min_notional or (r.max_notional is not None and cost > r.max_notional):
            return 'Binance notional'
        if cost * Decimal('1.001') > cash:
            return 'onvoldoende saldo inclusief fee'
        if p.quantity * (p.price-p.stop) + cost * Decimal('.002') > equity*l.trade_risk:
            return 'trade risico'
        if exposure+cost > equity*l.exposure:
            return 'exposure'
        if daily_loss >= equity*l.daily_loss:
            return 'dagverlies'
        if peak and (peak-equity)/peak >= l.drawdown:
            return 'drawdown'
        if exposure and correlation >= l.correlation:
            return 'correlatie'
        return None


class PortfolioManager:
    def __init__(self, store):
        self.store = store
        if not store.list('portfolio_history'):
            store.put('portfolio_history', '000000000000', {'cash': '200', 'equity': '200', 'currency': 'EUR'})

    def snapshot(self):
        return self.store.list('portfolio_history')[-1]


class ExecutionEngine:
    """Fase 1: uitsluitend virtuele orderregistratie, geen fills of beursverbinding."""
    def __init__(self, store, risk):
        self.store, self.risk = store, risk

    def propose(self, proposal, rules, **portfolio):
        proposal = Proposal.model_validate(proposal)
        # Status komt later uit één transactionele portefeuille-ledger; geen automatische bot.
        with self.store.transaction():
            self.store.put('proposals', proposal.event_id, proposal.model_dump(mode='json'))
            reason = self.risk.check(proposal, rules, **portfolio)
            self.store.put('risk_decisions', proposal.event_id, {'approved': reason is None, 'reason': reason})
            if reason is None:
                self.store.put('orders', proposal.event_id, {'symbol': proposal.symbol, 'mode': 'paper', 'status': 'proposed', 'quantity': str(proposal.quantity), 'price': str(proposal.price)})
            self.store.audit('risk_decision', reason or 'paper voorstel toegestaan; niet uitgevoerd')
        return reason is None
