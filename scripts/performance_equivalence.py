"""Inhoudelijke vergelijking echte agent/fillketen met bestaande synthetische fixtures."""
import asyncio,json,sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_joint_portfolio import inputs,switched_inputs
from test_trade_agents import AT
from crypto.joint_portfolio import JointPortfolio
from crypto.storage import SQLiteStore

def capture():
 out={}
 for name in ('normal','switch','emergency'):
  s=SQLiteStore();args=switched_inputs() if name=='switch' else inputs()
  runner=JointPortfolio(s,**args)
  for i in range(20):
   b=asyncio.run(runner.evaluate(AT+timedelta(minutes=15*i)))
   if b['reservation']:runner.execute(b['id'])
   if i==0 and name=='emergency':runner.stop()
  out[name]={t:s.list(t) for t in ('joint_batches','joint_settlements','joint_states','results')}
  runner._read()[1].reconcile();s.close()
 return out
if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(capture(),sort_keys=True,indent=2)+'\n')
