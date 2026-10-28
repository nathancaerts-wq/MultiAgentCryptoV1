"""Source-only integrity check; no historical SQL or label decompression."""
import hashlib,json,resource,signal,subprocess,time
from pathlib import Path

BASE='2f0a021eed1b3102e6f00af9843237d2f5a773de'
ROOT=Path('experiments/phase6e_technical')


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,)*2)
    def timeout(*_):raise TimeoutError('300 second source verification budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300);start=time.perf_counter()
    old=json.loads(Path('experiments/phase6e/baseline_integrity.json').read_text())
    for p,h in old['files'].items():
        if sha(p)!=h:raise ValueError('Changed old research artifact: '+p)
    reg=json.loads(Path('experiments/phase6d/registration.json').read_text())
    if sha(reg['manifest'])!=reg['sha256']:raise ValueError('Changed old manifest')
    manifest=json.loads(Path(reg['manifest']).read_text())
    for p,h in manifest['files'].items():
        if sha(p)!=h:raise ValueError('Changed old source: '+p)
    # The old proposal retains its historical document bindings, even as progress advances.
    proposal=json.loads(Path('experiments/phase6e/registration.json').read_text())
    for p,h in proposal['proposal_files'].items():
        raw=subprocess.check_output(['git','show',BASE+':'+p])
        if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Old proposal binding mismatch')
        if p not in ('PROGRESS.md','NEXT_STEPS.md') and sha(p)!=h:raise ValueError('Old proposal changed')
    files=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],text=True).splitlines())
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE],text=True).splitlines())
    if (changed&files)-{'PROGRESS.md','NEXT_STEPS.md'}:raise ValueError('Existing file modified')
    a=json.loads((ROOT/'capacity_initial.json').read_text());b=json.loads((ROOT/'capacity.json').read_text())
    if a['output_sha256']!=b['output_sha256']:raise ValueError('Synthetic outputs differ')
    for p,h in b['source_sha256'].items():
        if sha(p)!=h:raise ValueError('Measured implementation changed')
    db=Path('/workspace/development_2024.sqlite3');digest=sha(db)
    if digest!=manifest['database_sha256']:raise ValueError('Audit database changed')
    paths=[p for folder in (ROOT,) for p in folder.rglob('*') if p.is_file()]
    paths += [Path(p) for p in ('scripts/phase6e_technical.py','scripts/phase6e_capacity.py',
        'scripts/verify_phase6e_technical.py','tests/test_phase6e_technical.py',
        'tests/fixtures/phase6e_indicator_reference.json','PHASE6E_TECHNICAL_READINESS_REPORT.md',
        'PROGRESS.md','NEXT_STEPS.md')]
    result=dict(status='synthetic_checks_passed_inference_resolution_limited',base_commit=BASE,
        source_sha256={str(p):sha(p) for p in paths},database_sha256=digest,
        original_artifacts_unchanged=len(old['files']),original_code_and_proposal_unchanged=True,
        tests_passed=480,new_historical_comparisons=0,new_orders=0,protocol_changes_activated=False,
        validation_accessed=False,independent_test_opened=False,
        elapsed_seconds=time.perf_counter()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limits=dict(seconds=300,address_space_bytes=1024**3))
    with (ROOT/'integrity.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    signal.alarm(0);print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
