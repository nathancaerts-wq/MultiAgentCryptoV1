"""Voor/na-controle van de bestaande synthetische risicopauzefixtures."""
import asyncio,json,sys
from pathlib import Path
from datetime import timedelta,datetime,timezone
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_joint_portfolio import inputs,reports_at,COINS
from test_trade_agents import AT,bar,rules,session,candidate,evaluate
from crypto.storage import SQLiteStore
from crypto.joint_portfolio import JointPortfolio
from crypto.models import Message
import crypto.storage as storage

def capture():
 out={}
 for gap in ('70','.02'):
  s=SQLiteStore();args=inputs(reports=reports_at()+reports_at(AT+timedelta(minutes=45)))
  v=D(gap);args['bars']['BTCEUR'][2]=bar(1,open=v,high=v+D('.01'),low=v-D('.01'),close=v)
  args['filters']={sym:rules(sym,min_notional=0) for sym in COINS}
  r=JointPortfolio(s,**args)
  for i in range(4):
   b=asyncio.run(r.evaluate(AT+timedelta(minutes=15*i)))
   if b['reservation']:r.execute(b['id'])
  out[gap]={t:s.list(t) for t in ('joint_states','joint_batches','joint_settlements','results')}
  out[gap]['audit']=s.audits();s.close()
 s=SQLiteStore();r=session(s);row=candidate(evaluate(r));m=Message.model_validate(row['candidate'])
 r.ledger.trades=[{'net':'-1'}]*3
 out['loss_streak']=r.execution.reason(m,r.ledger);s.close()
 return out
if __name__=='__main__':
 storage.now=lambda:datetime(2026,10,27,tzinfo=timezone.utc)
 Path(sys.argv[1]).write_text(json.dumps(capture(),indent=2,sort_keys=True)+'\n')
