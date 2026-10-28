"""No historical rows: proposal binding and causal boundaries on synthetic context."""
from copy import deepcopy
from datetime import timedelta, timezone
from pathlib import Path
import json
import pytest
from scripts.phase6e_protocol import (
    FIRST, LAST, FRAMES, SOURCE, canonical_digest, validate_proposal,
    verify_registration, require_historical_authorization, validate_feature_context,
)


def plan():
    return json.loads(Path('experiments/phase6e/protocol_proposal.json').read_text())


def frames(t=FIRST):
    result = {}
    for tf, seconds in FRAMES.items():
        end = t - timedelta(seconds=int(t.timestamp()) % seconds)
        result[tf] = dict(end=end.isoformat(), previous_end=(end-timedelta(seconds=seconds)).isoformat(),
            count=32, rsi='50', previous_rsi='49', ema_fast='100', ema_slow='99', atr='1', close='100')
    return result


def test_registration_is_reproducible_and_bound_to_document():
    p = plan()
    assert validate_proposal(p) == canonical_digest(dict(reversed(list(p.items()))))
    r = dict(protocol_sha256=validate_proposal(p), analysis_document_sha256='a'*64,
        source_manifest=SOURCE, status='proposal_only_no_comparisons')
    assert verify_registration(p, r, 'a'*64)
    with pytest.raises(ValueError): verify_registration(p, r, 'b'*64)
    r['protocol_sha256'] = '0'*64
    with pytest.raises(ValueError): verify_registration(p, r, 'a'*64)


@pytest.mark.parametrize('mutation', ['missing', 'universe', 'horizon', 'cost', 'family', 'permission'])
def test_missing_or_changed_registration_fails_closed(mutation):
    p = plan()
    if mutation == 'missing': del p['source_manifest']
    if mutation == 'universe': p['coins'].append('XRPEUR')
    if mutation == 'horizon': p['horizon_seconds'] = 3600
    if mutation == 'cost': p['costs']['fee'] = '0'
    if mutation == 'family': p['contrast_family'] = 1
    if mutation == 'permission': p['historical_comparisons_authorized'] = True
    with pytest.raises(ValueError): validate_proposal(p)


def test_proposal_never_authorizes_outcome_comparisons():
    with pytest.raises(PermissionError): require_historical_authorization(plan())


@pytest.mark.parametrize('at', [FIRST, LAST])
def test_exact_boundaries_are_valid(at):
    assert validate_feature_context('BTCEUR', at, frames(at))


@pytest.mark.parametrize('at', [FIRST-timedelta(minutes=15), LAST+timedelta(minutes=15),
    FIRST.replace(year=2025), FIRST.replace(year=2026), FIRST.replace(tzinfo=None),
    FIRST.astimezone(timezone(timedelta(hours=1))), FIRST+timedelta(seconds=1)])
def test_time_scope_and_timezone_fail_closed(at):
    with pytest.raises(ValueError): validate_feature_context('BTCEUR', at, frames())


@pytest.mark.parametrize('case', ['missing_frame', 'future', 'previous_future', 'missing_value', 'nonfinite', 'count'])
def test_missing_and_future_features_rejected_without_label_access(case):
    f = frames()
    if case == 'missing_frame': del f['4h']
    if case == 'future': f['4h']['end'] = (FIRST+timedelta(hours=4)).isoformat()
    if case == 'previous_future': f['1h']['previous_end'] = FIRST.isoformat()
    if case == 'missing_value': del f['1h']['rsi']
    if case == 'nonfinite': f['1h']['atr'] = 'NaN'
    if case == 'count': f['1h']['count'] = 31
    with pytest.raises((ValueError, KeyError)): validate_feature_context('BTCEUR', FIRST, f)


def test_context_check_preserves_input_and_repeats_exactly():
    f = frames(); original = deepcopy(f)
    for _ in range(3): assert validate_feature_context('SOLEUR', FIRST, f)
    assert f == original
