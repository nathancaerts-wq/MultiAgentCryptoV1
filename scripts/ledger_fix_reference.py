"""Bestaande synthetische vergelijkingsfixtures plus persistente audit; geen marktdata."""
import asyncio,json,sys
from datetime import timedelta,datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_joint_portfolio import inputs,switched_inputs
from test_trade_agents import AT
from crypto.joint_portfolio import JointPortfolio
from crypto.storage import SQLiteStore
import crypto.storage as storage

def capture():
 out={}
 for name in ('normal','switch','emergency','duplicate','restart','rollback','rejected'):
  s=SQLiteStore();args=switched_inputs() if name in ('switch','restart','rollback') else inputs()
  if name=='rejected':
   args['filters']={sym:f.model_copy(update={'min_notional':__import__('decimal').Decimal(10000)}) for sym,f in args['filters'].items()}
  r=JointPortfolio(s,**args)
  for i in range(20):
   at=AT+timedelta(minutes=15*i);b=asyncio.run(r.evaluate(at))
   if b['reservation']:
    if name=='rollback' and i==0:
     put=s.put
     def fail(table,*args):
      if table=='joint_settlements':raise RuntimeError('fixture rollback')
      return put(table,*args)
     s.put=fail
     try:r.execute(b['id'])
     except RuntimeError:pass
     finally:s.put=put
    r.execute(b['id'])
    if name=='duplicate':r.execute(b['id'])
   if i==0 and name=='emergency':r.stop()
   if i==3 and name=='restart':r=JointPortfolio(s,**args)
  r._read()[1].reconcile()
  out[name]={t:s.list(t) for t in ('joint_batches','joint_settlements','joint_states','results')}
  out[name]['audit']=s.audits();s.close()
 return out
if __name__=='__main__':
 storage.now=lambda:datetime(2026,10,27,tzinfo=timezone.utc)
 Path(sys.argv[1]).write_text(json.dumps(capture(),sort_keys=True,indent=2)+'\n')
