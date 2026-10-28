"""Synthetic only; exact old/new financial and audit equivalence, durable recovery."""
import asyncio
import json
import sqlite3
from datetime import timedelta, datetime, timezone
from decimal import Decimal as D
import pytest
from crypto.streaming import StreamingStore, StreamingFixtureRunner, pieces, streamed_hash
from crypto.readiness_runner import FixtureJointRunner
from crypto.storage import SQLiteStore
from crypto.sim_execution import canonical, digest
from crypto.protocol import report_digest
from test_joint_portfolio import inputs, reports_at, switched_inputs, COINS
from test_trade_agents import AT, bar
from test_readiness import history


def freeze(monkeypatch):
    monkeypatch.setattr('crypto.storage.now',lambda:datetime(2026,10,27,tzinfo=timezone.utc))
    class FixedImportTime(datetime):
        @classmethod
        def now(cls,tz=None):return datetime(2026,10,27,tzinfo=timezone.utc)
    monkeypatch.setattr('crypto.data.datetime',FixedImportTime)


def args_active():
    args=switched_inputs()
    args['history']={s:{tf:[c.model_copy(update={'symbol':s}) for c in rows] for tf,rows in history().items()} for s in COINS}
    return args


def prepare(store,args):
    for rows in args['bars'].values():store.add_candles('bars',iter(rows))
    for frames in args.get('history',{}).values():
        for rows in frames.values():store.add_candles('history',iter(rows))
    store.add_reports(iter(args['reports']))
    assert store.seal()['reports']==report_digest(args['reports'])


def open_runner(store,args):
    return StreamingFixtureRunner(store=store,**{k:v for k,v in args.items() if k in ('plan','policy','filters','benchmark')})


def logical(state):return json.loads(''.join(pieces(state)))


def comparable(store):
    return {t:store.list(t) for t in ('results','joint_batches','joint_settlements')}|{'audit':store.audits()}


@pytest.mark.parametrize('active',[False,True])
def test_exact_reference_all_states_audit_fills_costs(tmp_path,monkeypatch,active):
    freeze(monkeypatch);args=args_active() if active else inputs(reports=[])
    if not active:args['plan']=args['plan'].model_copy(update={'report_hashes':(report_digest([]),)*3})
    old=SQLiteStore();new=StreamingStore(tmp_path/'stream.sqlite3');prepare(new,args)
    a=FixtureJointRunner(store=old,**args);b=open_runner(new,args)
    for i in range(3):
        at=AT+timedelta(minutes=15*i)
        assert asyncio.run(a.run([at]))==asyncio.run(b.run([at]))
        assert logical(b._read()[0])==a._read()[0]
        assert comparable(old)==comparable(new)
    if active:assert len(b._read()[1].trades)==1
    new.close();old.close()


def test_pending_resume_and_open_position_survive(tmp_path,monkeypatch):
    freeze(monkeypatch);args=args_active();path=tmp_path/'stream.sqlite3'
    s=StreamingStore(path);prepare(s,args);r=open_runner(s,args)
    batch=asyncio.run(r.evaluate(AT));before=r.snapshot()
    assert D(before['reserved_cash'])>0
    s.close();s=StreamingStore(path);r=open_runner(s,args)
    assert r.snapshot()==before
    result=asyncio.run(r.run([AT]))[0];assert result['holdings'] and D(result['cash'])<200
    count=len(s.list('joint_settlements'));s.close()
    s=StreamingStore(path);r=open_runner(s,args)
    assert r.snapshot()==result
    assert asyncio.run(r.run([AT]))[0]==result
    assert len(s.list('joint_settlements'))==count
    assert asyncio.run(r.run([AT+timedelta(minutes=15)]))[0]['holdings']=={}
    s.close()


def test_atomic_failure_after_history_append(tmp_path,monkeypatch):
    args=args_active();s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);r=open_runner(s,args)
    batch=asyncio.run(r.evaluate(AT));before=logical(r._read()[0]);original=s.audit
    def fail(action,details):
        if action=='joint_settled':raise RuntimeError('injected after state/history/fill')
        original(action,details)
    monkeypatch.setattr(s,'audit',fail)
    with pytest.raises(RuntimeError):r.execute(batch['id'])
    assert logical(r._read()[0])==before and not s.list('joint_settlements')
    r.verify_history();monkeypatch.setattr(s,'audit',original)
    r=open_runner(s,args);assert r.execute(batch['id'])['success'];s.close()


def test_chronology_gap_across_blocks_and_stream_generator(tmp_path):
    args=inputs(reports=[]);s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);r=open_runner(s,args)
    async def one():
        async for snapshot in r.stream(iter([AT])):assert snapshot['cash']=='200'
    asyncio.run(one());before=r.snapshot()
    with pytest.raises(ValueError,match='chronologische'):asyncio.run(r.run([AT+timedelta(minutes=30)]))
    assert r.snapshot()==before;s.close()


def test_gap_in_input_blocks_rejected_before_initial_cash(tmp_path):
    args=inputs();s=StreamingStore(tmp_path/'stream.sqlite3')
    args['bars'][COINS[0]].pop(5);prepare(s,args)
    with pytest.raises(ValueError,match='Datagat'):open_runner(s,args)
    assert not s.list('joint_protocols');s.close()


def test_emergency_pause_survives_resume_and_matches(tmp_path,monkeypatch):
    freeze(monkeypatch);args=args_active();a=SQLiteStore();b=StreamingStore(tmp_path/'stream.sqlite3');prepare(b,args)
    old=FixtureJointRunner(store=a,**args);new=open_runner(b,args)
    for r in (old,new):asyncio.run(r.run([AT]));r.stop()
    new=open_runner(b,args)
    assert new.risk.stopped
    assert asyncio.run(old.run([AT+timedelta(minutes=15)]))==asyncio.run(new.run([AT+timedelta(minutes=15)]))
    assert comparable(a)==comparable(b);a.close();b.close()


def test_sealed_input_and_append_only_history(tmp_path):
    args=inputs();s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);open_runner(s,args)
    with pytest.raises(sqlite3.IntegrityError):s.add_candles('bars',[bar(25)])
    for table in ('stream_input','stream_states','stream_history','stream_seal'):
        with pytest.raises(sqlite3.IntegrityError):s.db.execute(f'DELETE FROM {table}')
    s.close()


def test_disk_required_and_historical_denied(tmp_path):
    with pytest.raises(ValueError):StreamingStore(':memory:')
    args=inputs();s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args)
    args['plan']=args['plan'].model_copy(update={'source':'https://data.binance.vision'})
    with pytest.raises(ValueError,match='Historische'):open_runner(s,args)
    s.close()


def test_independent_test_candles_not_ingested(tmp_path):
    s=StreamingStore(tmp_path/'stream.sqlite3')
    t=datetime(2026,1,1,tzinfo=timezone.utc)
    c=bar(0).model_copy(update={'opened':t,'closed':t+timedelta(minutes=15)})
    with pytest.raises(ValueError,match='Gesloten'):s.add_candles('bars',[c])
    assert not s.db.execute('SELECT 1 FROM stream_input').fetchone();s.close()


def test_checkpoint_corruption_detected_on_restart(tmp_path):
    args=inputs();s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT]))
    # Simulate external file tampering, beyond the normal append-only API.
    s.db.execute('DROP TRIGGER stream_states_UPDATE')
    s.db.execute("UPDATE stream_states SET payload=json_set(payload,'$.ledger.cash','201') WHERE revision=1")
    with pytest.raises(ValueError,match='Checkpoint'):open_runner(s,args)
    s.close()


@pytest.mark.parametrize('gap',['70','.02'])
def test_daily_loss_drawdown_pause_exact_across_reopen(tmp_path,monkeypatch,gap):
    from test_trade_agents import rules
    freeze(monkeypatch);args=inputs();args['history']=args_active()['history']
    args['reports']=reports_at()+reports_at(AT+timedelta(minutes=45))
    args['plan']=args['plan'].model_copy(update={'report_hashes':(report_digest(args['reports']),report_digest([]),report_digest([]))})
    value=D(gap);args['bars']['BTCEUR'][2]=bar(1,open=value,high=value+D('.01'),low=value-D('.01'),close=value)
    args['filters']={s:rules(s,min_notional=0) for s in COINS}
    a=SQLiteStore();path=tmp_path/'stream.sqlite3';b=StreamingStore(path);prepare(b,args)
    old=FixtureJointRunner(store=a,**args);new=open_runner(b,args)
    for i in range(4):
        at=AT+timedelta(minutes=15*i)
        assert asyncio.run(old.run([at]))==asyncio.run(new.run([at]))
        assert logical(new._read()[0])==old._read()[0]
        b.close();b=StreamingStore(path);new=open_runner(b,args)
    assert new._read()[1].day_paused
    if gap=='.02':assert new._read()[1].drawdown_paused
    assert comparable(a)==comparable(b);a.close();b.close()


def test_actual_process_crash_rolls_back_checkpoint_and_fill(tmp_path):
    import subprocess,sys,os
    from pathlib import Path
    args=args_active();path=tmp_path/'crash.sqlite3';s=StreamingStore(path);prepare(s,args);r=open_runner(s,args)
    batch=asyncio.run(r.evaluate(AT));before=r.snapshot();audit_before=s.audits();s.close()
    program='''
import os,sys
sys.path.insert(0,'tests')
from test_streaming import args_active,open_runner
from crypto.streaming import StreamingStore
s=StreamingStore(sys.argv[1]);r=open_runner(s,args_active());audit=s.audit
s.audit=lambda action,details: os._exit(77) if action=='joint_settled' else audit(action,details)
r.execute(sys.argv[2])
'''
    proc=subprocess.run([sys.executable,'-c',program,str(path),batch['id']],timeout=20,capture_output=True,text=True)
    assert proc.returncode==77,proc.stderr
    s=StreamingStore(path);r=open_runner(s,args)
    assert r.snapshot()==before and not s.list('joint_settlements')
    assert s.audits()==audit_before
    assert r.execute(batch['id'])['success'];r.verify_history();s.close()


def test_large_block_rejected_without_financial_changes(tmp_path):
    args=inputs(reports=[]);s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);r=open_runner(s,args)
    before=r.snapshot()
    with pytest.raises(ValueError,match='100 stappen'):
        asyncio.run(r.run(AT+timedelta(minutes=15*i) for i in range(101)))
    assert r.snapshot()==before;s.close()


def test_input_mutation_detected_before_resume(tmp_path):
    args=inputs();s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);open_runner(s,args)
    s.db.execute('DROP TRIGGER stream_input_UPDATE')
    s.db.execute("UPDATE stream_input SET payload=json_set(payload,'$.close','999') WHERE kind='bars' AND coin='BTCEUR'")
    with pytest.raises(ValueError,match='gewijzigde invoer'):open_runner(s,args)
    s.close()


def test_checkpoint_chain_binds_old_state_not_only_latest(tmp_path):
    args=inputs(reports=[]);s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT,AT+timedelta(minutes=15)]))
    raw=s.db.execute('SELECT payload FROM stream_states WHERE revision=1').fetchone()[0]
    c=json.loads(raw);c['ledger']['cash']='199';c.pop('checkpoint_hash');c['checkpoint_hash']=digest(c)
    s.db.execute('DROP TRIGGER stream_states_UPDATE')
    s.db.execute('UPDATE stream_states SET payload=? WHERE revision=1',(canonical(c),))
    with pytest.raises(ValueError,match='Checkpointketen'):open_runner(s,args)
    s.close()


def test_report_objects_are_fresh_and_causal_at_lookup(tmp_path):
    args=args_active();s=StreamingStore(tmp_path/'stream.sqlite3');prepare(s,args);r=open_runner(s,args)
    first=r._reports_at(AT);first[0].result['conflicts']=['caller change']
    assert r._reports_at(AT)[0].result['conflicts']!=['caller change']
    assert not r._reports_at(AT-timedelta(minutes=15))
    assert all(x.timestamp==AT for x in r._reports_at(AT));s.close()


def test_three_losses_pause_preserved_and_identical(tmp_path,monkeypatch):
    from test_trade_agents import FixtureData
    freeze(monkeypatch)
    reports=[r for i in range(8) for r in reports_at(AT+timedelta(minutes=15*i))]
    args=inputs(reports=reports)
    for s in COINS:
        for i in (0,2,4):args['bars'][s][i+1]=bar(i,symbol=s,open='106.4',high=107,low=99,close=100)
    args['history']={s:{tf:[c.model_copy(update={'quote_volume':D(20000)}) for c in FixtureData().fetch(s,tf,AT-timedelta(days=7),AT+timedelta(hours=3))] for tf in ('15m','1h')} for s in COINS}
    a=SQLiteStore();path=tmp_path/'stream.sqlite3';b=StreamingStore(path);prepare(b,args)
    old=FixtureJointRunner(store=a,**args);new=open_runner(b,args)
    for i in range(8):
        at=AT+timedelta(minutes=15*i)
        assert asyncio.run(old.run([at]))==asyncio.run(new.run([at]))
        assert logical(new._read()[0])==old._read()[0]
        if i==5:
            assert len(new._read()[1].trades)==3
            b.close();b=StreamingStore(path);new=open_runner(b,args)
    batch=b.list('joint_batches')
    assert any('verliesreekspauze' in c['reason'] for row in batch for c in row['candidates'])
    assert comparable(a)==comparable(b);a.close();b.close()


def test_history_gap_at_boundary_fails_closed(tmp_path,monkeypatch):
    freeze(monkeypatch);args=args_active();args['history']['BTCEUR']['15m'].pop(-1)
    a=SQLiteStore();b=StreamingStore(tmp_path/'stream.sqlite3');prepare(b,args)
    old=FixtureJointRunner(store=a,**args);new=open_runner(b,args)
    assert asyncio.run(old.run([AT]))==asyncio.run(new.run([AT]))
    assert comparable(a)==comparable(b)
    assert any('Ontbrekende candles' in c['reason'] for row in b.list('joint_batches') for c in row['candidates'])
    a.close();b.close()


def test_full_analysis_chain_spooled_and_reference_equal(tmp_path,monkeypatch):
    from crypto.analysis import run_research
    from crypto.data import DataEngine
    from test_trade_agents import FixtureData
    freeze(monkeypatch);old=SQLiteStore();new=StreamingStore(tmp_path/'chain.sqlite3')
    ea,eb=DataEngine(old,FixtureData()),DataEngine(new,FixtureData());reports=[]
    for i in range(16):
        at=AT+timedelta(minutes=15*i)
        a=asyncio.run(run_research(ea,at,COINS));b=asyncio.run(new.prepare_research(eb,at,COINS))
        assert [r.model_dump(mode='json') for r in a]==[r.model_dump(mode='json') for r in b]
        reports.extend(a)
    args=inputs(reports=reports)
    for rows in args['bars'].values():new.add_candles('bars',rows)
    assert new.seal()['reports']==report_digest(reports)
    a=FixtureJointRunner(store=old,**args);b=open_runner(new,args)
    for i in range(16):
        at=AT+timedelta(minutes=15*i)
        assert asyncio.run(a.run([at]))==asyncio.run(b.run([at]))
        assert logical(b._read()[0])==a._read()[0]
    assert comparable(old)==comparable(new)
    for table in ('analyses','regimes','scan_runs','datasets'):assert old.list(table)==new.list(table)
    old.close();new.close()


def test_fixed_size_checkpoints_keep_audit_once(tmp_path):
    args=inputs(reports=[])
    args['bars']={s:[bar(i,symbol=s) for i in range(-1,151)] for s in COINS}
    from crypto.protocol import Period
    args['plan']=args['plan'].model_copy(update={'development':Period(start=args['plan'].development.start,end=AT+timedelta(days=2)), 'validation':Period(start=AT+timedelta(days=2,hours=4),end=AT+timedelta(days=3)), 'independent_test':Period(start=AT+timedelta(days=4),end=AT+timedelta(days=5))})
    s=StreamingStore(tmp_path/'long.sqlite3');prepare(s,args);r=open_runner(s,args)
    async def replay():
        count=0
        async for snapshot in r.stream(AT+timedelta(minutes=15*i) for i in range(150)):
            assert snapshot['cash']=='200';count+=1
        return count
    assert asyncio.run(replay())==150
    state,ledger=r._read();assert len(ledger.events)==151 and not ledger.events.pending
    assert s.db.execute("SELECT count(*) FROM stream_history WHERE kind='events'").fetchone()[0]==151
    assert s.db.execute('SELECT max(length(payload)) FROM stream_states').fetchone()[0]<2500
    reopened=open_runner(s,args);assert reopened.snapshot()==r.snapshot()
    assert not s.list('joint_states');s.close()


def test_preparation_timestamp_is_atomic_retryable(tmp_path,monkeypatch):
    from crypto.data import DataEngine
    from test_trade_agents import FixtureData
    s=StreamingStore(tmp_path/'prepare.sqlite3');engine=DataEngine(s,FixtureData())
    original=s.add_reports
    def fail(rows):original(rows);raise RuntimeError('crash after preparation')
    monkeypatch.setattr(s,'add_reports',fail)
    with pytest.raises(RuntimeError):asyncio.run(s.prepare_research(engine,AT,COINS))
    for table in ('results','analyses','datasets','scan_runs','stream_input','audit'):
        assert s.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
    monkeypatch.setattr(s,'add_reports',original)
    assert len(asyncio.run(s.prepare_research(engine,AT,COINS)))==2
    with pytest.raises(ValueError,match='reeds voorbereid'):asyncio.run(s.prepare_research(engine,AT,COINS))
    s.close()


def test_pending_exit_survives_crash_boundary_without_duplicate_sell(tmp_path):
    args=args_active();path=tmp_path/'exit.sqlite3';s=StreamingStore(path);prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT]))
    batch=asyncio.run(r.evaluate(AT+timedelta(minutes=15)))
    assert batch['reservation']['side']=='sell';snap=r.snapshot();s.close()
    s=StreamingStore(path);r=open_runner(s,args);assert r.snapshot()==snap
    assert r.execute(batch['id'])['success'];after=r.snapshot()
    assert r.execute(batch['id'])['replay'] and r.snapshot()==after
    assert len(r._read()[1].trades)==1 and not after['holdings'];s.close()
