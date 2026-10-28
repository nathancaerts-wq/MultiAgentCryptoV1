"""Proposal-only registration and causal-context checks. No outcome reader or runner."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

BASE = '2a7efedaefd755bcc7ae190102fd0fba015e1725'
SOURCE = '933be8ac13e01a7dd4e4a749291306e2f026a87bf92431f17a3163f83a98e779'
COINS = ('BTCEUR', 'ETHEUR', 'SOLEUR')
FIRST = datetime(2024, 1, 8, tzinfo=timezone.utc)
LAST = datetime(2024, 12, 31, 19, 45, tzinfo=timezone.utc)
FRAMES = {'15m': 900, '1h': 3600, '4h': 14400}


def utc(value):
    t = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(t, datetime) or t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError('Explicit UTC required')
    return t


def canonical_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_proposal(plan):
    """Exact fixed design; a proposal can never act as historical permission."""
    expected = dict(version='phase6e-proposal-v1', status='proposal_requires_approval',
        base_commit=BASE, source_manifest=SOURCE, coins=list(COINS),
        first_decision=FIRST.isoformat(), last_decision=LAST.isoformat(),
        horizon_seconds=14400, quantity='0.001', tick='0.01',
        costs={'fee': '0.001', 'spread': '0.001', 'slippage': '0.001'},
        feature_count=27, contrast_family=332, bootstrap_replicates=9999,
        block_timegroups=42, seed=606, multiplicity='Holm', alpha='0.05',
        prior_viewed=True, historical_comparisons_authorized=False,
        validation_authorized=False, independent_test_authorized=False)
    if canonical_digest(plan) != canonical_digest(expected):
        raise ValueError('Missing, changed or unapproved protocol definitions')
    return canonical_digest(plan)


def verify_registration(plan, registration, document_hash):
    if registration.get('protocol_sha256') != validate_proposal(plan):
        raise ValueError('Protocol hash mismatch')
    if (registration.get('analysis_document_sha256') != document_hash
            or registration.get('status') != 'proposal_only_no_comparisons'
            or registration.get('source_manifest') != SOURCE):
        raise ValueError('Missing or mismatched proposal binding')
    return True


def require_historical_authorization(plan):
    validate_proposal(plan)
    raise PermissionError('Proposal only: separate approval and execution manifest required')


def validate_feature_context(coin, at, frames):
    """Fixture-testable future extraction contract; no feature or label calculation."""
    t = utc(at)
    if coin not in COINS or not FIRST <= t <= LAST or t.microsecond or int(t.timestamp()) % 900:
        raise ValueError('Outside registered decision grid')
    if set(frames) != set(FRAMES):
        raise ValueError('Missing timeframe')
    for tf, seconds in FRAMES.items():
        frame = frames[tf]
        end = t - timedelta(seconds=int(t.timestamp()) % seconds)
        if (utc(frame['end']) != end or frame['count'] != 32
                or utc(frame['previous_end']) != end - timedelta(seconds=seconds)):
            raise ValueError('Incomplete, unaligned or future feature context')
        for key in ('rsi', 'previous_rsi', 'ema_fast', 'ema_slow', 'atr', 'close'):
            value = Decimal(frame[key])
            if not value.is_finite():
                raise ValueError('Nonfinite feature')
            if key in ('ema_fast', 'ema_slow', 'close') and value <= 0:
                raise ValueError('Nonpositive price')
            if key in ('rsi', 'previous_rsi') and not 0 <= value <= 100:
                raise ValueError('Invalid RSI')
            if key == 'atr' and value < 0:
                raise ValueError('Negative ATR')
    return True
