"""Bounded explicit development replay. No validation/test data, no automatic retry."""
import argparse
import asyncio
from collections import Counter
from datetime import timedelta
from decimal import Decimal as D
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import sqlite3
import time

from crypto.development_2024 import *
from crypto.data import DataEngine
from crypto.protocol import ResearchPlan, Period, report_digest
from crypto.sim_execution import digest, canonical
from scripts.development_quality import audit

OUT = Path('experiments/development_2024')
DB = Path('/workspace/development_2024.sqlite3')
STEP = timedelta(minutes=15)


def write(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, default=str) + '\n'); temp.replace(path)


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def code_hashes():
    paths = sorted(Path('crypto').glob('*.py')) + [Path(p) for p in (
        'scripts/development_2024.py', 'scripts/development_quality.py',
        'scripts/phase6b_full_audit.py', 'experiments/development_2024/protocol.json')]
    return {str(p): file_hash(p) for p in paths}


def pilot_checkpoint():
    from crypto.january_pilot import JanuaryStore, JanuaryRunner
    root = Path('experiments/january_pilot')
    m = json.loads((root / 'manifest.json').read_text())
    old = json.loads((root / 'verification.json').read_text())
    for p, sha in m['files'].items():
        if file_hash(p) != sha: raise ValueError('Pilot code changed: ' + p)
    if file_hash('/workspace/january_pilot.sqlite3') != old['database_sha256']:
        raise ValueError('Pilot database changed')
    store = JanuaryStore('/workspace/january_pilot.sqlite3')
    try:
        r = JanuaryRunner(store=store, plan=ResearchPlan.model_validate(m['plan']),
                          policy=JointPolicy(), filters=filters())
        state, ledger = r._read(); ledger.reconcile(); r.verify_history()
        if r.snapshot() != json.loads((root / 'result.json').read_text())['portfolio']:
            raise ValueError('Pilot reconstruction mismatch')
        if ledger.position or state['pending'] or ledger.cash != D('197.03206319'):
            raise ValueError('Pilot financial mismatch')
        result = dict(validated=True, snapshot=r.snapshot(), state_hash=state['hash'],
                      database_sha256=old['database_sha256'], input_seal=store.verify_inputs(),
                      consecutive_losses=sum(D(t['net']) < 0 for t in ledger.trades),
                      resumable_within_original_plan=True, extensible_to_year=False,
                      reason='January plan/end, input seal, report bundle and terminal cutoff are frozen; no approved migration')
    finally: store.close()
    if file_hash('/workspace/january_pilot.sqlite3') != old['database_sha256']:
        raise ValueError('Pilot file changed during verification')
    write(OUT / 'january_checkpoint.json', result)


def make_plan(manifest, scenario, benchmark):
    return ResearchPlan(coins=COINS, source=source(scenario, benchmark),
        dataset_sha256=digest(manifest['quality']),
        report_hashes=(manifest['input_seal']['reports'], report_digest([]), report_digest([])),
        development=Period(start=START, end=END),
        validation=Period(start=dt('2025-02-01'), end=dt('2025-12-31T20:00')),
        independent_test=Period(start=dt('2026-01-01'), end=dt('2026-10-01')),
        hypotheses=('aligned_trend',), fee=COSTS[scenario].fee, slippage=COSTS[scenario].slippage,
        assumptions=('hypothetical_filters_unproven', 'next_bar_execution',
                     'no_validation_or_test_authorization', 'historical_revisions_not_reconstructed'))


def january_gate(runner):
    state, ledger = runner._read()
    old = json.loads(Path('experiments/january_pilot/verification.json').read_text())
    def financial(t): return {k: v for k, v in t.items() if k not in ('entry_id', 'exit_id')}
    same = [financial(t) for t in ledger.trades] == [financial(t) for t in old['trades']]
    if (state['at'] != dt('2024-02-01').isoformat() or ledger.cash != D('197.03206319')
        or ledger.position or state['pending'] or not same):
        raise ValueError('January comparison failed; stop before February')
    runner.verify_history(); ledger.reconcile()
    return dict(passed=True, at=state['at'], cash=ledger.cash,
                financial_trades_exact=True, ignored_fields=['entry_id', 'exit_id'],
                reason='Different plan identity; full financial trade payload compared',
                state_hash=state['hash'], consecutive_losses=3)


def metrics(runner, name):
    """Read persisted complete run; never generate a proposal or replay a candle."""
    store = runner.store; state, ledger = runner._read(); ledger.reconcile(); runner.verify_history()
    if state['at'] != END.isoformat() or ledger.position or state['pending']:
        raise ValueError('Incomplete terminal portfolio')
    reasons = Counter(); by_coin = {s: Counter() for s in COINS}
    candidates = approved = rejected_buy = 0
    for (raw,) in store.db.execute('SELECT payload FROM joint_batches'):
        b = json.loads(raw)
        if b.get('portfolio') != runner.key: continue
        for c in b['candidates']:
            buy = c['decision']['result']['action'] == 'BUY_CANDIDATE'
            candidates += buy; approved += bool(c['selected']); rejected_buy += buy and not c['selected']
            if not c['selected']:
                reasons[c['reason']] += 1; by_coin[c['symbol'] if 'symbol' in c else c['decision']['coin']][c['reason']] += 1
    # Settlement payload binds the batch, whose id is content-addressed.
    settlement_rejections = Counter(); fills = []
    for e in ledger.events:
        if e['action'] in ('buy', 'sell'): fills.append(e)
    ids = [e['details']['order_id'] if e['action'] == 'buy' else e['details']['exit_id'] for e in fills]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate fills')
    for (raw,) in store.db.execute('SELECT payload FROM joint_settlements'):
        v = json.loads(raw)
        # Resolve via portfolio field, or its batch reference (schema evidence checked in tests).
        if v.get('portfolio') == runner.key and not v['success']: settlement_rejections[v['reason']] += 1
    trades = list(ledger.trades)
    wins = [D(t['net']) for t in trades if D(t['net']) > 0]
    losses = [D(t['net']) for t in trades if D(t['net']) < 0]
    if sum((D(t['net']) for t in trades), D(0)) != ledger.realized:
        raise ValueError('Trade P&L mismatch')
    if sum((D(t['fees']) for t in trades), D(0)) != ledger.fees:
        raise ValueError('Fee mismatch')
    held_seconds = sum((dt(t['exited_at']) - dt(t['entered_at'])).total_seconds() for t in trades)
    def group(ts):
        ns = [D(t['net']) for t in ts]
        return dict(trades=len(ts), net=sum(ns, D(0)), fees=sum((D(t['fees']) for t in ts), D(0)),
                    winrate=D(sum(n > 0 for n in ns))/len(ns) if ns else None)
    # At each boundary use the final committed state after that batch and the preceding close.
    # All source queries are bounded to the authorized year; no state mutations.
    monthly = {}; previous_month_equity = D(200); peak = D(200); dd = D(0)
    cap_sum = D(0); cap_max = D(0); pause_first = None; paused_steps = 0
    def compact_states():
        last = None
        for (raw,) in store.db.execute('SELECT payload FROM stream_states WHERE portfolio=? ORDER BY revision', (runner.key,)):
            s = json.loads(raw)
            if last and s['at'] != last['at']: yield last
            last = s
        if last: yield last
    curve = OUT / (name + '_close_curve.csv.gz')
    with gzip.open(curve, 'wt') as out:
        out.write('utc,cash,liquidation_equity,gross_equity,exposure_fraction\n')
        out.write(f'{START.isoformat()},200,200,200,0\n')
        warm = START + STEP
        while warm < ENTRY:
            out.write(f'{warm.isoformat()},200,200,200,0\n')
            warm += STEP
        for s in compact_states():
            at = dt(s['at']); cash = D(s['ledger']['cash']); pos = s['ledger']['position']
            if at == START: continue
            equity = gross = cash; fraction = D(0)
            if pos:
                c = next(store.candles('bars', pos['symbol'], '15m', at-STEP, at), None)
                if c is None: raise ValueError('Missing close valuation')
                q = D(pos['quantity']); gross += q*c.close
                costs = runner.policy.decision.costs; rules = runner.rules[pos['symbol']]
                price = costs.price(c.close, 'sell', rules.tick)
                equity += q*price - costs.charge(q, price)
                fraction = q*c.close/gross
            peak = max(peak, equity); dd = max(dd, (peak-equity)/peak)
            if at < END: cap_sum += fraction; cap_max = max(cap_max, fraction)
            out.write(f'{at.isoformat()},{cash},{equity},{gross},{fraction}\n')
            if at.day == 1 and at.hour == 0 and at.minute == 0 and at > START:
                month = (at-timedelta(days=1)).strftime('%Y-%m')
                monthly[month] = dict(start_equity=previous_month_equity, end_equity=equity,
                    net=equity-previous_month_equity,
                    **{'trade_summary': group([t for t in trades if t['exited_at'].startswith(month)])})
                previous_month_equity = equity
    # Consecutive loss lock remains derived from the unchanged ledger trade suffix.
    streak = 0
    for t in trades:
        streak = streak+1 if D(t['net']) < 0 else 0
        if streak == 3 and pause_first is None: pause_first = t['exited_at']
    duration = D(str((END-START).total_seconds()))
    return dict(status='complete', candidate_signals=candidates, approved_entries=approved,
        rejected_buy_proposals=rejected_buy, rejected_coin_assessments=dict(reasons),
        rejection_reasons_by_coin={s:dict(c) for s,c in by_coin.items()},
        rejected_executions=dict(settlement_rejections), trades=len(trades), trade_records=trades,
        unique_fills=len(ids), winrate=D(len(wins))/len(trades) if trades else None,
        average_win=sum(wins)/len(wins) if wins else None,
        average_loss=sum(losses)/len(losses) if losses else None,
        net=ledger.realized, net_percent=ledger.realized/D(200)*100,
        expectancy=ledger.realized/len(trades) if trades else None,
        profit_factor=sum(wins,D(0))/abs(sum(losses)) if losses else None,
        fees=ledger.fees, equity=runner.snapshot()['equity'],
        conservative_max_drawdown=ledger.max_drawdown, close_max_drawdown=dd,
        average_hold_seconds=D(str(held_seconds))/len(trades) if trades else None,
        time_exposure=D(str(held_seconds))/duration,
        capital_exposure_mean=cap_sum/(duration/900), capital_exposure_max=cap_max,
        capital_exposure_convention='post-batch holdings marked at preceding 15m close; zero warm-up in denominator',
        per_coin={s:group([t for t in trades if t['symbol']==s]) for s in COINS},
        per_month=monthly, loss_streak_pause_from=pause_first,
        pause_until=END if pause_first and streak>=3 else None,
        outlier_diagnostics=dict(without_top_3_winners=ledger.realized-sum(sorted(wins,reverse=True)[:3],D(0)),
            without_worst_3_losers=ledger.realized-sum(sorted(losses)[:3],D(0)),removed_winners=min(3,len(wins)),removed_losers=min(3,len(losses))),
        state_hash=state['hash'], last_revision=state['revision'], portfolio=runner.snapshot(),
        curve_sha256=file_hash(curve), independent_test_opened=False, validation_accessed=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'replay'])
    parser.add_argument('--scenario', choices=list(COSTS), default='baseline')
    parser.add_argument('--benchmark', choices=['aligned_trend', 'ema_trend'], default='aligned_trend')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    name = args.benchmark + '_' + args.scenario
    protocol = json.loads((OUT/'protocol.json').read_text())
    budget = protocol['budget']; began = time.perf_counter(); store = runner = None; current_phase=args.phase
    resource.setrlimit(resource.RLIMIT_AS,(budget['address_space_bytes'],)*2)
    os.environ['SQLITE_TMPDIR']='/workspace'
    limit=budget['prepare_seconds'] if args.phase=='prepare' else budget['each_replay_seconds']
    def timeout(*_): raise TimeoutError('Pre-registered execution time limit')
    signal.signal(signal.SIGALRM, timeout); signal.signal(signal.SIGTERM, timeout); signal.alarm(limit)
    def check():
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>budget['early_rss_bytes']: raise MemoryError('RSS budget')
        if shutil.disk_usage('/workspace').free<budget['minimum_free_disk_bytes']: raise OSError('Disk safety reserve')
    def progress(*info):
        check()
        print(json.dumps(dict(phase=current_phase, info=info, seconds=round(time.perf_counter()-began,3),rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),default=str),flush=True)
    try:
        if args.phase=='prepare':
            if DB.exists() or (OUT/'manifest.json').exists(): raise ValueError('Existing preparation preserved; no automatic restart')
            pilot_checkpoint();store=DevelopmentStore(DB)
            quality=audit(store,progress);write(OUT/'quality.json',quality)
            engine=DataEngine(store,DevelopmentData(store));current_phase='analysis'
            async def prepare():
                at=ENTRY;count=0
                while at<=LAST_ENTRY:
                    reports=await store.prepare_research(engine,at,COINS)
                    if len(reports)!=3 or any(any(f['status']!='complete' for f in r.data['frames'].values()) for r in reports):
                        raise ValueError('Incomplete analysis')
                    count+=1
                    if count%1000==0:progress(count,at)
                    at+=STEP
            asyncio.run(prepare());current_phase='seal';seal=store.seal()
            manifest=dict(protocol=protocol,quality=quality,input_seal=seal,files=code_hashes(),
                          policy={s:policy(s).model_dump(mode='json') for s in COSTS},
                          filters={s:f.model_dump(mode='json') for s,f in filters().items()},
                          python=__import__('sys').version,decimal= str(__import__('decimal').getcontext()),
                          validation_accessed=False,independent_test_opened=False)
            manifest['plans']={source(s,b):make_plan(manifest,s,b).model_dump(mode='json') for s in COSTS for b in ('aligned_trend','ema_trend')}
            write(OUT/'manifest.json',manifest)
            write(OUT/'preparation.json',dict(status='complete',elapsed=time.perf_counter()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,database_bytes=DB.stat().st_size))
        else:
            manifest=json.loads((OUT/'manifest.json').read_text())
            if manifest['files']!=code_hashes():raise ValueError('Code/configuration changed after seal')
            resultpath=OUT/(name+'.json');access=OUT/(name+'_access.json')
            if access.exists() and not args.resume:raise ValueError('Existing run preserved; explicit resume required')
            if args.resume and resultpath.exists() and json.loads(resultpath.read_text())['status']=='complete':raise ValueError('Completed run cannot restart')
            if name!='aligned_trend_baseline':
                baseline=json.loads((OUT/'aligned_trend_baseline.json').read_text())
                if baseline['status']!='complete':raise ValueError('Baseline not complete')
            if not access.exists():write(access,dict(stage='development',source=source(args.scenario,args.benchmark),
                manifest_sha256=file_hash(OUT/'manifest.json'),started_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                independent_test_opened=False,validation_accessed=False))
            store=DevelopmentStore(DB)
            plan=ResearchPlan.model_validate(manifest['plans'][source(args.scenario,args.benchmark)])
            runner=DevelopmentRunner(store=store,plan=plan,policy=policy(args.scenario),filters=filters(),benchmark=args.benchmark)
            state,_=runner._read();last=dt(state['at'])
            at=ENTRY if last==START else last if state['pending'] else last+STEP
            if last>dt('2024-02-01') and name=='aligned_trend_baseline' and not (OUT/'january_comparison.json').exists():raise ValueError('January gate absent')
            async def replay():
                nonlocal at
                while at<=END:
                    await runner.run((at,))
                    if name=='aligned_trend_baseline' and at==dt('2024-02-01'):
                        write(OUT/'january_comparison.json',january_gate(runner));progress('January exact match')
                    if int((at-ENTRY)/STEP)%1000==0:progress(name,at)
                    at+=STEP
            asyncio.run(replay());current_phase='verification'
            result=metrics(runner,name)
            snapshot=runner.snapshot()
            restored=DevelopmentRunner(store=store,plan=plan,policy=policy(args.scenario),filters=filters(),benchmark=args.benchmark)
            if restored.snapshot()!=snapshot:raise ValueError('Checkpoint reconstruction differs')
            result.update(elapsed=time.perf_counter()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                checkpoint=str(DB),checkpoint_reconstruction_equal=True,processed_boundaries=int((END-ENTRY)/STEP)+1,
                processed_execution_candles=int((END-ENTRY)/STEP)*3)
            write(resultpath,result)
        progress('complete')
    except BaseException as exc:
        signal.alarm(0)
        record=dict(status='incomplete_diagnostic',reason=type(exc).__name__+': '+str(exc),phase=current_phase,
                    elapsed=time.perf_counter()-began,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    checkpoint=str(DB),independent_test_opened=False,validation_accessed=False)
        if store:
            # Persist only the last fully committed state; SQLite rolls back interrupted transactions.
            if store.db.in_transaction:store.db.rollback()
            if runner:
                row=store.db.execute('SELECT payload FROM stream_states WHERE portfolio=? ORDER BY revision DESC LIMIT 1',(runner.key,)).fetchone()
                record['last_checkpoint']=json.loads(row[0]) if row else None
            record['last_prepared']=store.db.execute("SELECT max(at) FROM stream_input WHERE kind='report'").fetchone()[0]
        write(OUT/(('preparation' if args.phase=='prepare' else name)+'_interruption.json'),record)
        raise
    finally:
        signal.alarm(0)
        if store:store.close()

if __name__=='__main__': main()
