import asyncio,json
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal as D
import pytest
from crypto.storage import SQLiteStore
from crypto.joint_portfolio import JointPortfolio
from crypto.tracked_payload import Revision,tracked
from crypto.data import DataEngine
from test_joint_portfolio import inputs,switched_inputs
from test_trade_agents import AT,FixtureData


def test_analysis_view_isolated_and_cannot_execute():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());_,ledger=r._read()
 for i in range(1000):ledger.audit('fixture',AT,value=i)
 view=ledger.analysis_view()
 assert len(ledger.events)==1001 and not view.events
 assert ledger.snapshot(D(100))==view.snapshot(D(100))
 view.cash=D(1);view.observe(AT,D(100))
 assert ledger.cash==200 and len(ledger.events)==1001
 with pytest.raises(ValueError):view.buy()
 with pytest.raises(ValueError):view.sell()
 s.close()

@pytest.mark.parametrize('operation',[
 lambda d:d['a']['b'].append({'x':1}),lambda d:d['a']['b'].extend([4]),
 lambda d:d['a']['b'].__setitem__(slice(0,1),[9]),lambda d:d['a'].update({'c':7}),
 lambda d:d['a']['b'].reverse(),lambda d:d['a']['b'].pop(),lambda d:d['a'].setdefault('c',2),
 lambda d:d['a']['b'].__imul__(2),lambda d:d['a'].__ior__({'c':1})])
def test_nested_mutations_tracked(operation):
 revision=Revision();d=tracked({'a':{'b':[1,2,3]}},revision);before=revision.value
 operation(d);assert revision.value>before
 plain=deepcopy(d);plain['a']['new']='copy';assert 'new' not in d['a']


def test_report_hash_cached_until_nested_mutation(monkeypatch):
 import crypto.joint_portfolio as module
 original=module.report_digest;calls=[]
 def counted(values):calls.append(1);return original(values)
 monkeypatch.setattr(module,'report_digest',counted)
 s=SQLiteStore();r=JointPortfolio(s,**inputs());calls.clear()
 r.snapshot();r.snapshot();assert not calls
 r.reports[0].result['components']['technical']['frames']['1h']['missing'].append('tamper')
 with pytest.raises(ValueError):r.snapshot()
 assert calls;s.close()


def test_unsupported_mutable_payload_never_assumed_unchanged():
 args=inputs();args['reports'][0].data['custom_set']={1,2}
 from crypto.protocol import report_digest
 args['plan']=args['plan'].model_copy(update={'report_hashes':(report_digest(args['reports']),report_digest([]),report_digest([]))})
 s=SQLiteStore();r=JointPortfolio(s,**args);r.snapshot()
 r.reports[0].data['custom_set'].add(3)
 with pytest.raises(ValueError):r.snapshot()
 s.close()


def test_dataset_hit_is_single_record_and_reads_current_db(monkeypatch):
 s=SQLiteStore();engine=DataEngine(s,FixtureData())
 start=AT-timedelta(hours=32)
 expected=engine.load('BTCEUR','1h',start,AT,AT)
 monkeypatch.setattr(s,'list',lambda *_: (_ for _ in ()).throw(AssertionError('full scan')))
 assert engine.load('BTCEUR','1h',start,AT,AT)==expected
 row=s.db.execute('SELECT id,payload FROM datasets').fetchone();payload=json.loads(row[1])
 payload['rows'][0]['closed']=(AT+timedelta(days=1)).isoformat()
 s.db.execute('UPDATE datasets SET payload=? WHERE id=?',(json.dumps(payload),row[0]))
 with pytest.raises(ValueError):engine.load('BTCEUR','1h',start,AT,AT)
 s.close()


def test_mid_transaction_error_preserves_all_persisted_content():
 s=SQLiteStore();r=JointPortfolio(s,**switched_inputs());b=asyncio.run(r.evaluate(AT))
 before={t:s.list(t) for t in ('joint_states','joint_settlements')};put=s.put
 def fail(table,*args):
  if table=='joint_states':raise RuntimeError('mid-transaction')
  return put(table,*args)
 s.put=fail
 with pytest.raises(RuntimeError):r.execute(b['id'])
 s.put=put
 assert {t:s.list(t) for t in before}==before
 r=JointPortfolio(s,**switched_inputs());r.execute(b['id']);r._read()[1].reconcile()
 assert len(s.list('joint_settlements'))==1;s.close()


def test_all_golden_scenarios_including_persistent_audit(monkeypatch):
 from datetime import datetime,timezone
 from pathlib import Path
 import crypto.storage as storage
 from scripts.ledger_fix_reference import capture
 monkeypatch.setattr(storage,'now',lambda:datetime(2026,10,27,tzinfo=timezone.utc))
 expected=json.loads(Path('experiments/ledger_optimization/reference_before.json').read_text())
 assert capture()==expected


def test_risk_pauses_match_original_implementation(monkeypatch):
 from datetime import datetime,timezone
 from pathlib import Path
 import crypto.storage as storage
 from scripts.ledger_risk_reference import capture
 monkeypatch.setattr(storage,'now',lambda:datetime(2026,10,27,tzinfo=timezone.utc))
 expected=json.loads(Path('experiments/ledger_optimization/risk_before.json').read_text())
 assert capture()==expected
