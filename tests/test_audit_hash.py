import asyncio
from datetime import timedelta
import pytest
from crypto.streaming import streamed_hash, DiskList
from test_streaming import args_active, prepare, open_runner, logical
from crypto.streaming import StreamingStore
from test_trade_agents import AT


def test_all_active_checkpoints_hash_compatible(tmp_path):
    s=StreamingStore(tmp_path/'audit.sqlite3');args=args_active();prepare(s,args);r=open_runner(s,args)
    for i in range(3):
        asyncio.run(r.run([AT+timedelta(minutes=15*i)]))
        state,l=r._read()
        payload={k:v for k,v in state.items() if k!='hash'}
        assert streamed_hash(payload)==streamed_hash(payload,True)==state['hash']
        assert len(l.events.pending)==0
    r.verify_history();s.close()


def test_warm_cache_only_reads_tail_and_appends(tmp_path):
    s=StreamingStore(tmp_path/'audit.sqlite3');args=args_active();prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT]));state,_=r._read();q=[];s.db.set_trace_callback(q.append)
    streamed_hash(state,True);s.db.set_trace_callback(None)
    assert not any("seq>=0" in query for query in q)
    assert s._event_prefix['size']<=s._event_cache_limit;s.close()


def test_rollback_drops_uncommitted_cache(tmp_path):
    s=StreamingStore(tmp_path/'audit.sqlite3');args=args_active();prepare(s,args);r=open_runner(s,args)
    before=logical(r._read()[0]);audit=s.audit
    def fail(action,details):
        if action=='joint_reserved':raise RuntimeError('after hashing')
        audit(action,details)
    s.audit=fail
    with pytest.raises(RuntimeError):asyncio.run(r.evaluate(AT))
    assert not hasattr(s,'_event_prefix')
    assert logical(r._read()[0])==before
    s.audit=audit;assert asyncio.run(r.run([AT]))[0]['holdings'];r.verify_history();s.close()


def test_cache_limit_falls_back_exactly(tmp_path):
    s=StreamingStore(tmp_path/'audit.sqlite3');args=args_active();prepare(s,args);s._event_cache_limit=1
    r=open_runner(s,args);asyncio.run(r.run([AT]))
    state,_=r._read();assert streamed_hash(state)==streamed_hash(state,True)
    assert not hasattr(s,'_event_prefix');s.close()


def test_illicit_old_event_mutation_rejected_with_warm_cache(tmp_path):
    s=StreamingStore(tmp_path/'audit.sqlite3');args=args_active();prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT]));state,_=r._read()
    s.db.execute('DROP TRIGGER stream_history_UPDATE')
    s.db.execute("UPDATE stream_history SET payload=json_set(payload,'$.action','tampered') WHERE kind='events' AND seq=0")
    with pytest.raises(ValueError,match='Auditprefix'):streamed_hash(state,True)
    with pytest.raises(ValueError,match='auditketen'):open_runner(s,args)
    s.close()


def test_external_commit_invalidates_cache(tmp_path):
    path=tmp_path/'audit.sqlite3';s=StreamingStore(path);args=args_active();prepare(s,args);r=open_runner(s,args)
    state,_=r._read();streamed_hash(state,True);old=s._event_prefix
    other=StreamingStore(path);other.audit('external','synthetic');other.close()
    assert streamed_hash(state,True)==streamed_hash(state)
    assert s._event_prefix is not old;s.close()


def test_cold_reopen_rebuilds_no_persisted_hash_context(tmp_path):
    path=tmp_path/'audit.sqlite3';args=args_active();s=StreamingStore(path);prepare(s,args);r=open_runner(s,args)
    asyncio.run(r.run([AT]));before=logical(r._read()[0]);s.close()
    s=StreamingStore(path);r=open_runner(s,args)
    assert not hasattr(s,'_event_prefix')
    assert logical(r._read()[0])==before
    asyncio.run(r.run([AT+timedelta(minutes=15)]));r.verify_history();s.close()


def test_process_crash_inside_sqlite_audit_insert(tmp_path):
    import subprocess,sys
    path=tmp_path/'audit.sqlite3';args=args_active();s=StreamingStore(path);prepare(s,args);r=open_runner(s,args)
    batch=asyncio.run(r.evaluate(AT));before=r.snapshot();audits=s.audits();s.close()
    program='''
import sys,os
sys.path.insert(0,'tests')
from test_streaming import args_active,open_runner
from crypto.streaming import StreamingStore
s=StreamingStore(sys.argv[1]);r=open_runner(s,args_active())
s.db.create_function('crash',0,lambda:os._exit(78))
s.db.execute("CREATE TEMP TRIGGER crash_audit BEFORE INSERT ON audit WHEN NEW.action='joint_settled' BEGIN SELECT crash(); END")
r.execute(sys.argv[2])
'''
    p=subprocess.run([sys.executable,'-c',program,str(path),batch['id']],capture_output=True,text=True,timeout=20)
    assert p.returncode==78,p.stderr
    s=StreamingStore(path);r=open_runner(s,args)
    assert r.snapshot()==before and s.audits()==audits and not s.list('joint_settlements')
    assert r.execute(batch['id'])['success'];after=r.snapshot()
    assert r.execute(batch['id'])['replay'] and r.snapshot()==after
    r.verify_history();s.close()
