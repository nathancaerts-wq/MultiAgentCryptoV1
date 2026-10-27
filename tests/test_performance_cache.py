"""Cache mag integriteit, chronologie en financiële inhoud niet veranderen."""
import asyncio,json
from copy import deepcopy
from datetime import timedelta
import pytest
from crypto.storage import SQLiteStore
from crypto.joint_portfolio import JointPortfolio
from test_joint_portfolio import inputs,switched_inputs
from test_trade_agents import AT

class Reference(JointPortfolio):
 def _read(self):
  self._chain_prefix=None
  return super()._read()

def workflow(cls):
 s=SQLiteStore();r=cls(s,**switched_inputs())
 for i in range(12):
  b=asyncio.run(r.evaluate(AT+timedelta(minutes=15*i)))
  if b['reservation']:r.execute(b['id'])
 tables={t:s.list(t) for t in ('joint_states','joint_batches','joint_settlements','results')}
 r._read()[1].reconcile();s.close();return tables

def test_economic_and_messages_equal_without_prefix_cache():
 assert workflow(Reference)==workflow(JointPortfolio)

def test_old_record_update_invalidates_cache():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());r.snapshot()
 row=s.db.execute('SELECT id,payload FROM joint_states').fetchone()
 payload=json.loads(row[1]);payload['ledger']['cash']='199'
 s.db.execute('UPDATE joint_states SET payload=? WHERE id=?',(json.dumps(payload),row[0]))
 with pytest.raises((ValueError,ArithmeticError)):r.snapshot()
 s.close()

def test_delete_anchor_detected():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());r.snapshot()
 s.db.execute('DELETE FROM joint_states')
 with pytest.raises(ValueError):r.snapshot()
 s.close()

def test_rollback_prefix_does_not_hide_invalid_history():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());original=r.snapshot()
 with pytest.raises(RuntimeError):
  with s.transaction():
   s.db.execute('DELETE FROM joint_states')
   raise RuntimeError()
 assert r.snapshot()==original;s.close()

def test_other_connection_invalidates(tmp_path):
 path=tmp_path/'state.db';s=SQLiteStore(path);r=JointPortfolio(s,**inputs());r.snapshot()
 other=SQLiteStore(path);other.db.execute('DELETE FROM joint_states');other.close()
 with pytest.raises(ValueError):r.snapshot()
 s.close()

def test_insertion_before_verified_prefix_rechecked():
 s=SQLiteStore();r=JointPortfolio(s,**inputs());r.snapshot()
 raw=s.db.execute('SELECT payload FROM joint_states').fetchone()[0]
 s.db.execute('INSERT INTO joint_states(rowid,id,payload) VALUES (-1,?,?)',('unexpected',raw))
 with pytest.raises(ValueError):r.snapshot()
 s.close()

def test_long_corpus_cache_and_replaced_tuple():
 from crypto.readiness_runner import FixtureJointRunner
 from crypto.protocol import Period,report_digest
 from test_trade_agents import bar
 from crypto.readiness import dt
 s=SQLiteStore();args=inputs();start=dt('2024-01-01')
 args['reports']=[]
 args['plan']=args['plan'].model_copy(update={'development':Period(start=start,end=start+timedelta(days=15)),'report_hashes':(report_digest([]),)*3})
 args['bars']={sym:[bar(0,symbol=sym).model_copy(update={'opened':start+timedelta(minutes=15*i),'closed':start+timedelta(minutes=15*(i+1))}) for i in range(1000)] for sym in args['plan'].coins}
 r=FixtureJointRunner(store=s,**args)
 asyncio.run(r.run([start,start+timedelta(minutes=15)]))
 assert r.snapshot()['cash']=='200'
 sym=args['plan'].coins[0];rows=r.bars[sym]
 r.bars[sym]=(rows[0].model_copy(update={'quote_volume':rows[0].quote_volume+1}),)+rows[1:]
 with pytest.raises(ValueError):r.snapshot()
 s.close()
