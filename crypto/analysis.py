"""Per-coin onderzoeks-DAG; geen ordervoorstellen of activatiepad."""
import hashlib
import json
from datetime import datetime,timedelta
from uuid import NAMESPACE_URL,uuid5
from .data import SECONDS,utc
from .models import Message,now
from .indicators import IndicatorConfig,technical,classify
from .news import NoNews,news_report
from .scanner import CoinScanner
from .orchestrator import Orchestrator,Task

FRAMES=('15m','1h','4h')


def boundary(as_of,interval):
    return as_of-timedelta(seconds=int(as_of.timestamp())%SECONDS[interval],microseconds=as_of.microsecond)


class AnalysisContext:
    """Expliciete gegevenssnapshot; agents ontvangen geen schrijfrechten."""
    def __init__(self,engine,symbol,as_of,config=None,lookback=32):
        utc(as_of)
        if lookback<3 or lookback>40: raise ValueError('Lookback moet 3..40 zijn (kleine datasets)')
        self.symbol,self.as_of,self.config=symbol,as_of,config or IndicatorConfig()
        self.frames={}
        for interval in FRAMES:
            end=boundary(as_of,interval); start=end-timedelta(seconds=lookback*SECONDS[interval])
            try:
                rows=engine.load(symbol,interval,start,end,as_of)
                digest=hashlib.sha256(json.dumps([c.model_dump(mode='json') for c in rows],sort_keys=True).encode()).hexdigest()
                features=engine.technical_features(rows,self.config,technical,digest) if hasattr(engine,'technical_features') else technical(rows,self.config)
                self.frames[interval]=dict(**features,start=start.isoformat(),end=end.isoformat(),count=len(rows),sources=sorted({r.source for r in rows}),sha256=digest)
            except Exception as exc:
                self.frames[interval]=dict(status='incomplete',direction='unknown',missing=[str(exc)],start=start.isoformat(),end=end.isoformat(),count=0,sources=[])

    def message(self,agent,result,inputs=()):
        # Volgende 15m-grens is de eerste mogelijke gegevensverandering.
        stamp=boundary(self.as_of,'15m')
        data={'as_of':self.as_of.isoformat(),'parameters':self.config.model_dump(mode='json'),'frames':self.frames,'dependencies':[str(m.event_id) for m in inputs]}
        normalized=json.loads(json.dumps(result,default=str))
        identity=json.dumps(dict(agent=agent,symbol=self.symbol,timestamp=stamp.isoformat(),data=data,result=normalized),sort_keys=True)
        expires=stamp+timedelta(seconds=900)
        for dependency in inputs:
            expires=min(expires,dependency.timestamp+timedelta(seconds=dependency.ttl_seconds))
        for item in result.get('items',[]):
            expires=min(expires,datetime.fromisoformat(item['expires']))
        ttl=int((expires-stamp).total_seconds())
        if ttl<1: raise ValueError('Verlopen analysebron')
        return Message(agent_id=agent,event_id=uuid5(NAMESPACE_URL,identity),coin=self.symbol,timestamp=stamp,timeframe='15m/1h/4h',data=data,result=normalized,rationale='Deterministisch onderzoek; uitsluitend afgesloten candles; geen handelsadvies',ttl_seconds=ttl)


class TechnicalAnalysisAgent:
    def __init__(self,context): self.context=context; self.id='technical:'+context.symbol
    async def run(self,inputs): return self.context.message(self.id,{'frames':self.context.frames},inputs)


class MarketRegimeAgent:
    def __init__(self,context): self.context=context; self.id='regime:'+context.symbol
    async def run(self,inputs):
        frames={tf:dict(classification=classify(f,self.context.config),features=f) for tf,f in self.context.frames.items()}
        return self.context.message(self.id,{'primary_timeframe':'1h','classification':frames['1h']['classification'],'frames':frames},inputs)


class MultiTimeframeAgent:
    def __init__(self,context): self.context=context; self.id='multi_timeframe:'+context.symbol
    async def run(self,inputs):
        directions={tf:f['direction'] for tf,f in self.context.frames.items()}
        missing=[tf for tf,f in self.context.frames.items() if f['status']!='complete']
        unique=set(directions.values())
        agreement='incomplete' if missing else 'agreement' if len(unique)==1 else 'conflict'
        return self.context.message(self.id,dict(agreement=agreement,directions=directions,missing=missing,ends={tf:f['end'] for tf,f in self.context.frames.items()},note='Elke periode eindigt op eigen laatste afgesloten UTC-grens'),inputs)


class NewsSentimentAgent:
    def __init__(self,context,adapter=None):
        self.context,self.adapter=context,adapter or NoNews(); self.id='sentiment:'+context.symbol
    async def run(self,inputs):
        return self.context.message(self.id,news_report(self.adapter,self.context.symbol,self.context.as_of),inputs)


class CombinedResearchAgent:
    def __init__(self,context): self.context=context; self.id='research_report:'+context.symbol
    async def run(self,inputs):
        components={m.agent_id.split(':')[0]:m.result for m in inputs}
        if 'scanner' in components:
            scan=components['scanner']
            components['scanner']={'ranking':[r for r in scan.get('ranking',[]) if r['symbol']==self.context.symbol], 'rejections':[r for r in scan.get('rejections',[]) if r['symbol']==self.context.symbol]}
        result={'components':components,'limitations':['Geen handelsadvies of voorspelde winstkans'],'conflicts':[], 'missing':[]}
        for tf,frame in self.context.frames.items():
            result['conflicts'].extend(f'{tf}: {c}' for c in frame.get('conflicts',[]))
            result['missing'].extend(f'{tf}: {m}' for m in frame.get('missing',[]))
        mtf=components['multi_timeframe']
        if mtf['agreement']=='conflict': result['conflicts'].append('Timeframes spreken elkaar tegen')
        if components['sentiment']['status']=='geen betrouwbare data': result['missing'].append('geen betrouwbare nieuwsdata')
        result['status']='incomplete' if result['missing'] else 'conflict' if result['conflicts'] else 'complete'
        return self.context.message(self.id,result,inputs)


async def run_research(engine,as_of,watchlist,config=None,lookback=32,news=None):
    """Historische evaluatie expliciet op as_of; werkelijke signal-TTL blijft intact."""
    utc(as_of)
    if as_of>now(): raise ValueError('Evaluatietijd ligt in de toekomst')
    symbols=tuple(sorted(set(s.replace('/','').upper() for s in watchlist)))
    orchestrator=Orchestrator(engine.store,evaluation_time=as_of,reuse_results=True)
    scanner=CoinScanner(engine,as_of,watchlist=symbols,lookback=lookback)
    orchestrator.register('scanner',scanner)
    tasks=[Task('scanner','scanner')]
    contexts={s:AnalysisContext(engine,s,as_of,config,lookback) for s in symbols}
    for symbol,context in contexts.items():
        agents=[TechnicalAnalysisAgent(context),MarketRegimeAgent(context),MultiTimeframeAgent(context),NewsSentimentAgent(context,news),CombinedResearchAgent(context)]
        for agent in agents: orchestrator.register(agent.id,agent)
        technical_id=agents[0].id
        for agent in agents:
            dependencies=('scanner',) if agent is agents[0] or agent is agents[3] else (technical_id,) if agent is agents[1] or agent is agents[2] else tuple(a.id for a in agents[:4])+('scanner',)
            tasks.append(Task(agent.id,agent.id,dependencies))
    accepted=await orchestrator.execute(tasks)
    for message in accepted.values():
        if message.agent_id.startswith('regime:') and not engine.store.db.execute('SELECT 1 FROM regimes WHERE id=?',(str(message.event_id),)).fetchone():
            engine.store.put('regimes',message.event_id,message.model_dump(mode='json'))
    reports=[]
    for symbol,context in contexts.items():
        message=accepted.get('research_report:'+symbol)
        # Ook een volledig ontbrekende scanner/afhankelijkheid blijft zichtbaar.
        if message is None:
            message=context.message('research_report:'+symbol,{'status':'blocked','missing':['Scanner of afhankelijkheid afgewezen; zie audit/errors'],'frames':context.frames})
        key=str(message.event_id)
        if not engine.store.db.execute('SELECT 1 FROM analyses WHERE id=?',(key,)).fetchone():
            engine.store.put('analyses',key,message.model_dump(mode='json'))
            engine.store.audit('research_report',key)
        reports.append(message)
    return reports
