"""Read-only source integrity, never decompresses labels or queries historical rows."""
import hashlib
import json
from pathlib import Path
import resource
import signal
import subprocess
import time
from scripts.phase6e_protocol import validate_proposal, verify_registration, BASE

ROOT = Path('experiments/phase6e')
DB = Path('/workspace/development_2024.sqlite3')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify():
    resource.setrlimit(resource.RLIMIT_AS, (1024**3,)*2)
    def timeout(*_):
        raise TimeoutError('300 second integrity budget')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(300)
    started = time.perf_counter()
    before = json.loads((ROOT/'baseline_integrity.json').read_text())
    registration = json.loads((ROOT/'registration.json').read_text())
    plan = json.loads((ROOT/'protocol_proposal.json').read_text())
    validate_proposal(plan)
    verify_registration(plan, registration, sha('PHASE6E_ANALYSIS_PROTOCOL_PROPOSAL.md'))
    for p, expected in registration['proposal_files'].items():
        if sha(p) != expected:
            raise ValueError(f'Changed proposal source: {p}')
    for p, expected in before['files'].items():
        if sha(p) != expected:
            raise ValueError(f'Changed original artifact: {p}')
    old = json.loads(Path('experiments/phase6d/registration.json').read_text())
    if sha(old['manifest']) != old['sha256']:
        raise ValueError('Old manifest mismatch')
    manifest = json.loads(Path(old['manifest']).read_text())
    for p, expected in manifest['files'].items():
        if sha(p) != expected:
            raise ValueError(f'Old source mismatch: {p}')
    original = set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE], text=True).splitlines())
    changed = set(subprocess.check_output(['git','diff','--name-only',BASE], text=True).splitlines())
    if (changed & original) - {'PROGRESS.md', 'NEXT_STEPS.md'}:
        raise ValueError('Existing protected file modified')
    digest = sha(DB)
    if digest != before['database_sha256'] or digest != manifest['database_sha256']:
        raise ValueError('Original financial/audit database changed')
    result = dict(status='proposal_integrity_verified_comparisons_blocked',
        base_commit=BASE, registration_sha256=sha(ROOT/'registration.json'),
        database_sha256=digest, database_bytes=DB.stat().st_size,
        original_artifacts_unchanged=len(before['files']),
        original_code_unchanged=True, old_manifest_verified=True,
        historical_comparisons_run=0, new_price_labels=0, new_orders=0,
        validation_accessed=False, independent_test_opened=False,
        elapsed_seconds=time.perf_counter()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limits=dict(seconds=300, address_space_bytes=1024**3))
    with (ROOT/'integrity.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    signal.alarm(0)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
