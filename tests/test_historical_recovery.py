"""Synthetic integration only; no historical database read."""
import asyncio
from copy import deepcopy
from datetime import timedelta
import pytest
from crypto.historical_recovery import HistoricalRecoveryRunner,RecoveryStore,SOURCE
from crypto.streaming import StreamingStore
from crypto.recovery_research import RecoveryResearchPortfolio
from crypto.storage import SQLiteStore
from crypto.sim_execution import canonical
from test_recovery_research import args,AT,trigger,tick,close,entry
from test_readiness import history

class SyntheticRecovery(HistoricalRecoveryRunner):
    def _accept_plan(self):return self.plan.source.startswith('fixture:')

def prepare(tmp_path):
    a=args();s=StreamingStore(tmp_path/'recovery.sqlite3')
    for rows in a['bars'].values():s.add_candles('bars',rows)
    for symbol in a['plan'].coins:
        for rows in history(AT).values():
            s.add_candles('history',[c.model_copy(update={'symbol':symbol}) for c in rows])
    s.add_reports(a['reports']);s.seal()
    kw={k:a[k] for k in ('plan','policy','filters')}
    return s,kw,SyntheticRecovery(store=s,**kw)

def test_streaming_matches_reference_finances(tmp_path):
    st,kw,r=prepare(tmp_path);a=args();old=SQLiteStore()
    try:
        ref=RecoveryResearchPortfolio(old,enabled=True,**a)
        for runner in (r,ref):
            b=tick(runner,AT);assert runner.execute(b['id'])['success']
        x,y=r.snapshot(),ref.snapshot()
        for k in ('cash','holdings','fees','equity','cost_basis','average_price'):assert x[k]==y[k]
        assert r._read()[0]['recovery']==ref._read()[0]['recovery']
        r.verify_history()
    finally:st.close();old.close()

def test_stream_epoch_restart_and_no_duplicate_closes(tmp_path):
    st,kw,r=prepare(tmp_path)
    end=trigger(r);tick(r,end)
    before=r._read()[0]['recovery'];path=st.db.execute('PRAGMA database_list').fetchone()[2];st.close()
    st=StreamingStore(path)
    try:
        r=SyntheticRecovery(store=st,**kw);assert r._read()[0]['recovery']==before
        tick(r,end);assert r._read()[0]['recovery']==before
        for i in range(3,6):close(r,i,at=end+timedelta(minutes=15*(i-2)))
        assert r._read()[0]['recovery']['loss_count']==3
        r.verify_history();assert len(r._read()[1].trades)==6
    finally:st.close()

def test_stream_close_and_expiry_rollback(tmp_path,monkeypatch):
    st,kw,r=prepare(tmp_path);end=trigger(r);before=r._read()[0]['recovery'];original=st.audit
    def fail(action,details):
        original(action,details)
        if action=='joint_cooldown_expired':raise RuntimeError('crash')
    try:
        with monkeypatch.context() as m:
            m.setattr(st,'audit',fail)
            with pytest.raises(RuntimeError):tick(r,end)
        assert r._read()[0]['recovery']==before
        r.verify_history();tick(r,end);r.verify_history()
    finally:st.close()

def test_production_adapter_rejects_fixture_plan(tmp_path):
    st,kw,r=prepare(tmp_path)
    try:
        with pytest.raises(ValueError):HistoricalRecoveryRunner(store=st,**kw)
    finally:st.close()

def test_copy_of_admission_gate_matches_existing():
    import inspect
    from crypto.streaming import StreamingFixtureRunner
    base=inspect.getsource(StreamingFixtureRunner._risk_reason)
    new=inspect.getsource(HistoricalRecoveryRunner._risk_reason)
    assert base[base.index("        if candidate.result"):base.index('        return JointPortfolio')]==new[new.index("        if candidate.result"):new.index('        state,_=')]

def test_historical_store_rejects_other_dates(tmp_path):
    from test_trade_agents import bar
    st=RecoveryStore(tmp_path/'guard.sqlite3')
    try:
        with pytest.raises(ValueError):st.add_candles('bars',[bar()])
    finally:st.close()
