"""Lange technische replay. Alleen expliciete fixturebronnen; geen historische vrijgave."""
from datetime import datetime, timedelta
from decimal import Decimal as D
from .joint_portfolio import JointPortfolio
from .trade_agents import message
from .readiness import LOCKS, admission


class EMAAgent:
 def __init__(self,portfolio,symbol,at,report):
  self.p,self.symbol,self.at,self.report=portfolio,symbol,at,report
  self.id='decision:'+symbol
 async def run(self,inputs):
  r=self.report
  result=dict(action='HOLD',missing=[],conflicts=[],contributions={},research_only=True)
  try:
   if r is None or r.timestamp!=self.at or not r.usable(self.at): raise ValueError('Ontbrekend/verouderd rapport')
   from .analysis import boundary
   from .data import SECONDS
   from .indicators import IndicatorConfig
   if r.data['parameters']!=IndicatorConfig().model_dump(mode='json'): raise ValueError('Parameters gewijzigd')
   for tf in ('15m','1h','4h'):
    frame=r.data['frames'][tf]
    end=datetime.fromisoformat(frame['end']); start=datetime.fromisoformat(frame['start'])
    if end!=boundary(self.at,tf) or (end-start).total_seconds()!=frame['count']*SECONDS[tf] or frame['count']!=32:
     raise ValueError('Toekomstige of onvolledige indicatorhistorie')
   f=r.data['frames']['1h']
   if f['end']!=self.at.replace(minute=0,second=0,microsecond=0).isoformat(): raise ValueError('Verkeerde candlegrens')
   if any(v['status']!='complete' for v in r.data['frames'].values()): raise ValueError('Onvolledige frames')
   gap=D(f['ema_gap']); atr=D(f['atr'])
   if not gap.is_finite() or not atr.is_finite() or atr<=0: raise ValueError('Ongeldige indicator')
   # Rang op EMA-gap, monotone begrensde transformatie (geen winstkans).
   score=D(50)+D(50)*gap/(1+abs(gap))
   result.update(analysis_validation='validated',atr=str(atr),eligible=gap>D('.002'),
                 contributions={'scanner':{'ranking':[{'symbol':self.symbol,'score':str(score)}]}})
   if gap>D('.002') and self.at+timedelta(hours=4,minutes=15)<=self.p.plan.development.end:
    result['action']='BUY_CANDIDATE'
  except (ValueError,KeyError,TypeError) as exc: result['missing'].append(str(exc))
  return message('decision',self.symbol,self.at,self.p.policy.decision,result,(r,) if r else ())


class FixtureJointRunner(JointPortfolio):
 """Behoud één ledger over alle batches. Historische bronnen worden vóór opslag geweigerd."""
 _max_bars=1_000_000
 def __init__(self,*args,benchmark='aligned_trend',history=None,**kwargs):
  if args: raise ValueError('Gebruik expliciete benoemde fixture-invoer')
  if benchmark not in ('aligned_trend','ema_trend'): raise ValueError('Onbekende benchmark')
  plan=kwargs['plan']
  if not plan.source.startswith('fixture:'): raise ValueError('Historische rendementen niet toegestaan')
  for a,b in LOCKS:
   if plan.development.start<b and a<plan.development.end: raise ValueError('Gesloten periode')
  for rows in kwargs['bars'].values():
   if any(not c.source.startswith('fixture:') for c in rows): raise ValueError('Alleen fixturecandles')
  for r in kwargs['reports']:
   for f in r.data['frames'].values():
    if any(not s.startswith('fixture:') for s in f.get('sources',[])): raise ValueError('Alleen fixtureanalyses')
  self.history=history or {}
  for frames in self.history.values():
   for rows in frames.values():
    if any(not c.source.startswith('fixture:') for c in rows): raise ValueError('Alleen fixturehistorie')
  self.benchmark=benchmark
  super().__init__(**kwargs)
 def _manifest(self):
  return super()._manifest()|{'technical_fixture_only':True,'benchmark':self.benchmark,
   'history':{s:{tf:[c.model_dump(mode='json') for c in rows] for tf,rows in frames.items()} for s,frames in self.history.items()}}
 def _risk_reason(self,candidate,ledger,raw=None):
  if candidate.result.get('action')=='ENTRY_CANDIDATE':
   if candidate.timestamp+timedelta(hours=4,minutes=15)>self.plan.development.end: return 'periode-einde'
   try:
    reason=admission(self.history[candidate.coin],candidate.coin,candidate.timestamp)
    if reason: return reason
   except (ValueError,KeyError) as exc: return 'toelatingshistorie ontbreekt: '+str(exc)
  return super()._risk_reason(candidate,ledger,raw)
 def _decision(self,symbol,at,report):
  if self.benchmark=='ema_trend': return EMAAgent(self,symbol,at,report)
  return super()._decision(symbol,at,report)
 async def run(self,times):
  """Aanroeper kan opeenvolgende batches op hetzelfde object of heropende store verwerken."""
  out=[]
  for at in times:
   state,_=self._read()
   last=datetime.fromisoformat(state['at'])
   if at<last: raise ValueError('Terugwaartse replay')
   if at>last and state.get('batch_hash') and at-last!=timedelta(minutes=15):
    raise ValueError('Ontbrekende chronologische batch')
   batch=await self.evaluate(at)
   if batch['reservation']: self.execute(batch['id'])
   out.append(self.snapshot())
  return out
