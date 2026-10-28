"""Explicit 2024-only development authorization; existing simulation is unchanged."""
from datetime import timedelta
from .january_pilot import COINS, START, ENTRY, filters
from .readiness import dt
from .streaming import StreamingStore, StreamingFixtureRunner
from .joint_portfolio import JointPolicy
from .trade_agents import DecisionPolicy
from .sim_execution import FillCosts
from .data import validate_series, utc

END = dt('2025-01-01')
LAST_ENTRY = END - timedelta(hours=4, minutes=15)
SOURCES = {f'https://data.binance.vision/data/spot/monthly/klines/{s}/{tf}/{s}-{tf}-2024-{m:02d}.zip'
           for s in COINS for tf in ('15m', '1h', '4h') for m in range(1, 13)}
COSTS = {
    'baseline': FillCosts(),
    'slippage_stress': FillCosts(slippage='.002'),
    'double_costs': FillCosts(fee='.002', spread='.002', slippage='.002'),
}


def policy(scenario):
    return JointPolicy(decision=DecisionPolicy(costs=COSTS[scenario]))


def source(scenario, benchmark):
    if scenario not in COSTS or benchmark not in ('aligned_trend', 'ema_trend'):
        raise ValueError('Unregistered study')
    return f'assumption:development-2024-v1:{benchmark}:{scenario}'


class DevelopmentStore(StreamingStore):
    def _accept_source(self, value):
        return value in SOURCES

    def add_candles(self, kind, rows):
        def checked():
            for c in rows:
                if (c.symbol not in COINS or not START <= c.opened < c.closed <= END
                    or c.interval not in ('15m', '1h', '4h')):
                    raise ValueError('Outside development 2024')
                expected = f'https://data.binance.vision/data/spot/monthly/klines/{c.symbol}/{c.interval}/{c.symbol}-{c.interval}-{c.opened:%Y-%m}.zip'
                if c.source != expected:
                    raise ValueError('Archive provenance does not match candle')
                yield c
        return super().add_candles(kind, checked())

    async def prepare_research(self, engine, at, coins):
        utc(at)
        if tuple(coins) != COINS or not ENTRY <= at <= LAST_ENTRY:
            raise ValueError('Outside development analysis window')
        return await super().prepare_research(engine, at, coins)

    def add_reports(self, reports):
        def checked():
            for r in reports:
                if r.coin not in COINS or not ENTRY <= r.timestamp <= LAST_ENTRY:
                    raise ValueError('Outside development reports')
                yield r
        return super().add_reports(checked())


class DevelopmentData:
    def __init__(self, store):
        self.store = store

    def fetch(self, symbol, tf, start, end):
        utc(start); utc(end)
        if symbol not in COINS or not START <= start < end <= END:
            raise ValueError('Outside development data')
        return validate_series(list(self.store.candles('history', symbol, tf, start, end)),
                               symbol, tf, start, end, end)


class DevelopmentRunner(StreamingFixtureRunner):
    def _accept_plan(self):
        return (type(self.store) is DevelopmentStore
                and self.plan.coins == COINS
                and self.plan.development.start == START and self.plan.development.end == END
                and self.plan.hypotheses == ('aligned_trend',)
                and self.rules == filters()
                and any(self.plan.source == source(s, self.benchmark) and self.policy == policy(s)
                        for s in COSTS))

    def _manifest(self):
        return super()._manifest() | {'technical_fixture_only': False,
            'historical_development': 'development-2024-v1', 'entries_from': ENTRY.isoformat(),
            'hypothetical_filters': True}

    async def evaluate(self, at):
        utc(at)
        if not ENTRY <= at <= END:
            raise ValueError('Outside development execution window')
        return await super().evaluate(at)
