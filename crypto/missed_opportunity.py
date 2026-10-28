"""Read-only decision diagnostics. Historical forward labels await a new protocol."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal as D
from .data import Candle, utc, validate_series
from .sim_execution import FillCosts

COINS = ('BTCEUR', 'ETHEUR', 'SOLEUR')
START = datetime.fromisoformat('2024-01-01T00:00:00+00:00')
END = datetime.fromisoformat('2025-01-01T00:00:00+00:00')


def classify_batch(batch, settlement=None):
    """One record per (portfolio, UTC boundary, coin); no future-price input."""
    at = datetime.fromisoformat(batch['at']); utc(at)
    if not START <= at <= END: raise ValueError('Only development 2024 boundaries')
    if settlement and settlement['portfolio'] != batch['portfolio']:
        raise ValueError('Settlement portfolio mismatch')
    if settlement and settlement['batch'] != batch['id']:
        raise ValueError('Settlement batch mismatch')
    seen = set(); result = []
    for c in batch['candidates']:
        coin = c['symbol']
        if coin not in COINS or coin in seen: raise ValueError('Invalid/duplicate coin')
        seen.add(coin)
        decision = c.get('decision'); action = decision['result']['action'] if decision else None
        if decision and (decision['coin'] != coin or datetime.fromisoformat(decision['timestamp']) != at):
            raise ValueError('Decision time/coin mismatch')
        if c['selected']:
            if settlement and settlement.get('side') == 'buy':
                if settlement['coin'] != coin: raise ValueError('Settlement coin mismatch')
                category = 'executed_entry' if settlement['success'] else 'approved_execution_rejected'
            elif settlement and settlement.get('kind') == 'expiry':
                category = 'approved_execution_rejected'
            elif settlement:
                raise ValueError('Selected entry has incompatible settlement')
            else: category = 'selected_unresolved'
        elif action == 'BUY_CANDIDATE' or c.get('eligible'):
            category = 'blocked_candidate'
        else: category = 'not_selected_no_buy'
        score = D(c['score']) if c.get('score') is not None else None
        if score is not None and not score.is_finite(): raise ValueError('Invalid score')
        higher = sorted(x['symbol'] for x in batch['candidates']
                        if x['symbol'] != coin and score is not None and x.get('score') is not None
                        and D(x['score']) > score)
        result.append(dict(key=(batch['portfolio'], at.isoformat(), coin), coin=coin, at=at.isoformat(),
            category=category, action=action, reason=c['reason'], agent_reason=c.get('agent_reason'),
            risk_approved=c.get('risk_approved'), selected=c['selected'],
            execution_reason=settlement['reason'] if c['selected'] and settlement else None,
            higher_known_score_coins=higher, retrospective_label=None,
            historical_executability='not_established'))
    return result


def trailing_losses(trades):
    """Independent diagnostic reconstruction of the existing persisted suffix."""
    streak = 0; previous = None
    for t in trades:
        at = datetime.fromisoformat(t['exited_at']); utc(at)
        if not START <= at <= END or previous and at < previous: raise ValueError('Trade chronology')
        previous = at
        net = D(t['net'])
        if not net.is_finite(): raise ValueError('Invalid P&L')
        streak = streak + 1 if net < 0 else 0
    return streak


@dataclass(frozen=True)
class FixtureLabelSpec:
    """Proposed measurement only; not approved for historical forward outcomes."""
    hours: int = 4
    def __post_init__(self):
        if self.hours != 4: raise ValueError('Only proposed four-hour window')


def fixture_outcome(rows, coin, at, quantity, tick=D('.01'), costs=None, spec=FixtureLabelSpec()):
    """Synthetic mark-to-horizon labels; no order, stop simulation or portfolio claim.

    Uses the existing adverse FillCosts arithmetic. A close mark is a hypothetical
    liquidation valuation, not an executable same-close order. No historical gate.
    """
    utc(at); end = at + timedelta(hours=spec.hours)
    if coin not in COINS or not START <= at < end <= END: raise ValueError('Window outside 2024')
    candles = [Candle.model_validate(c.model_dump()) for c in rows]
    if any(not c.source.startswith('fixture:') for c in candles):
        raise ValueError('Historical forward results blocked: protocol choices pending')
    validate_series(candles, coin, '15m', at, end, end)
    q = D(quantity); tick = D(tick)
    if not q.is_finite() or q <= 0 or not tick.is_finite() or tick <= 0: raise ValueError('Invalid size/tick')
    costs = costs or FillCosts()
    opened, closed = candles[0].open, candles[-1].close
    entry, exit = costs.price(opened, 'buy', tick), costs.price(closed, 'sell', tick)
    fees = costs.charge(q, entry) + costs.charge(q, exit)
    gross = closed / opened - 1
    return dict(label='later_rise' if gross > 0 else 'later_fall' if gross < 0 else 'flat',
        gross_return=gross, hypothetical_net=q*(exit-entry)-fees, fees=fees,
        minimum_from_entry=min(c.low for c in candles)/opened-1,
        executable=False, hypothetical_only=True, overlapping_windows_not_independent=True)
