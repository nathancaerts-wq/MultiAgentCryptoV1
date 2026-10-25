import asyncio
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D

import pytest
from fastapi.testclient import TestClient
from crypto.analysis import AnalysisContext,TechnicalAnalysisAgent,MarketRegimeAgent,MultiTimeframeAgent,NewsSentimentAgent,run_research
from crypto.data import Candle,DataEngine,SECONDS
from crypto.indicators import IndicatorConfig,ema,wilder,technical,classify
from crypto.news import NewsItem,news_report,NoNews
from crypto.storage import SQLiteStore
from crypto.api import create_app

ASOF=datetime(2025,1,11,12,tzinfo=timezone.utc)

class Synthetic:
    BASE='fixture:phase3-v1'
    def __init__(self,mode='up'): self.mode=mode
    def fetch(self,symbol,interval,start,end):
        n=int((end-start).total_seconds())//SECONDS[interval]
        rows=[]
        delta=1 if self.mode=='up' else -1 if self.mode=='down' else 0
        if self.mode=='conflict': delta=1 if interval=='15m' else -1
        for i in range(n):
            value=D(100+i*delta)
            t=start+timedelta(seconds=i*SECONDS[interval])
            rows.append(Candle(symbol=symbol,interval=interval,opened=t,closed=t+timedelta(seconds=SECONDS[interval]),open=value,high=value+1,low=value-1,close=value,volume=10,quote_volume=1000,source=self.BASE))
        return rows

@pytest.fixture
def store():
    s=SQLiteStore(); yield s; s.close()

def test_ema_known():
    assert ema([D(1),D(2),D(3),D(4)],3)==D(3)
    assert wilder([D(1),D(2),D(3),D(4)],3)==D(8)/3

@pytest.mark.parametrize('mode,expected',[('up','bullish'),('down','bearish'),('flat','sideways')])
def test_regimes(mode,expected):
    rows=Synthetic(mode).fetch('BTCEUR','1h',ASOF-timedelta(hours=32),ASOF)
    result=technical(rows,IndicatorConfig())
    assert classify(result,IndicatorConfig())==expected
    assert result['rsi']==('100' if mode=='up' else '0' if mode=='down' else '50')
    assert D(result['atr'])==2


def test_uncertain_and_missing():
    assert classify({'status':'incomplete'},IndicatorConfig())=='uncertain'
    f={'status':'complete','ema_gap':'.01','momentum':'-.01','structure':'mixed'}
    assert classify(f,IndicatorConfig())=='uncertain'
    assert technical([],IndicatorConfig())['status']=='incomplete'

@pytest.mark.parametrize('bad',[dict(fast=21,slow=9),dict(rsi=0),dict(sideways='NaN')])
def test_parameters(bad):
    with pytest.raises(ValueError): IndicatorConfig(**bad)


def test_boundaries_no_future(store):
    at=ASOF+timedelta(minutes=37)
    ctx=AnalysisContext(DataEngine(store,Synthetic()),'BTCEUR',at)
    assert ctx.frames['15m']['end'].endswith('12:30:00+00:00')
    assert ctx.frames['1h']['end'].endswith('12:00:00+00:00')
    assert ctx.frames['4h']['end'].endswith('12:00:00+00:00')
    assert all(datetime.fromisoformat(f['end'])<=at for f in ctx.frames.values())


def test_future_and_stale_rows(store):
    class Bad(Synthetic):
        def fetch(self,*args):
            rows=super().fetch(*args)
            return rows[1:]+[rows[-1].model_copy(update={'closed':ASOF+timedelta(days=1)})]
    ctx=AnalysisContext(DataEngine(store,Bad()),'BTCEUR',ASOF)
    assert all(f['status']=='incomplete' for f in ctx.frames.values())


def test_timezone(store):
    with pytest.raises(ValueError): AnalysisContext(DataEngine(store,Synthetic()),'BTCEUR',ASOF.replace(tzinfo=None))


def item(**changes):
    return dict(id='one',symbol='BTCEUR',source='https://example.org/article',title='Expliciet synthetisch testartikel',published=ASOF-timedelta(minutes=30),available=ASOF-timedelta(minutes=20),expires=ASOF+timedelta(minutes=10))|changes

class Feed:
    def __init__(self,items): self.items=items
    def fetch(self,symbol,as_of):return self.items


def test_news_unknown():
    result=news_report(NoNews(),'BTCEUR',ASOF)
    assert result['status']=='geen betrouwbare data' and result['sentiment']=='unknown'

@pytest.mark.parametrize('changes',[dict(available=ASOF+timedelta(seconds=1)),dict(expires=ASOF),dict(symbol='ETHEUR'),dict(source='bad'),dict(published=ASOF+timedelta(days=1))])
def test_unreliable_news(changes):
    report=news_report(Feed([item(**changes)]),'BTCEUR',ASOF)
    assert report['items']==[] and report['sentiment']=='unknown'
    assert report['rejections']


def test_news_duplicates():
    report=news_report(Feed([item(),item()]),'BTCEUR',ASOF)
    assert len(report['items'])==1 and len(report['rejections'])==1


def test_news_expiry_propagation(store):
    ctx=AnalysisContext(DataEngine(store,Synthetic()),'BTCEUR',ASOF)
    m=asyncio.run(NewsSentimentAgent(ctx,Feed([item(expires=ASOF+timedelta(seconds=30))])).run(()))
    assert m.ttl_seconds==30
    assert not m.usable(ASOF+timedelta(seconds=31))


def test_full_research_reproducible(store):
    engine=DataEngine(store,Synthetic('conflict'))
    first=asyncio.run(run_research(engine,ASOF,['BTCEUR','ETHEUR']))
    second=asyncio.run(run_research(engine,ASOF,['BTCEUR','ETHEUR']))
    assert [m.event_id for m in first]==[m.event_id for m in second]
    assert len(store.list('analyses'))==2
    assert len(store.list('results'))==11
    for m in first:
        assert m.result['components']['multi_timeframe']['agreement']=='conflict'
        assert m.result['conflicts'] and 'geen betrouwbare nieuwsdata' in m.result['missing']
        assert not m.usable() and m.usable(ASOF)
    assert not store.list('orders') and not store.list('proposals')
    with TestClient(create_app(store)) as client:
        result=client.get('/analyses').json()
        assert len(result)==2 and result[0]['usable'] is False


def test_missing_higher_timeframe(store):
    class Missing(Synthetic):
        def fetch(self,symbol,interval,start,end):
            if interval=='4h': return []
            return super().fetch(symbol,interval,start,end)
    report=asyncio.run(run_research(DataEngine(store,Missing()),ASOF,['BTCEUR']))[0]
    assert report.result['components']['multi_timeframe']['agreement']=='incomplete'
    assert any('4h:' in text for text in report.result['missing'])


def test_everything_missing(store):
    class Missing:
        def fetch(self,*args): return []
    report=asyncio.run(run_research(DataEngine(store,Missing()),ASOF,['BTCEUR']))[0]
    assert report.result['status']=='blocked'
    assert store.list('errors')


def test_mixed_rsi_and_gap_atr():
    cfg=IndicatorConfig(fast=2,slow=3,rsi=2,atr=2,momentum=1,structure=2)
    rows=Synthetic('flat').fetch('BTCEUR','1h',ASOF-timedelta(hours=4),ASOF)
    values=[D(10),D(11),D(10),D(11)]
    rows=[r.model_copy(update={'open':v,'close':v,'high':v+1,'low':v-1}) for r,v in zip(rows,values)]
    result=technical(rows,cfg)
    assert D(result['rsi'])==75
    rows[-1]=rows[-1].model_copy(update={'open':D(20),'close':D(20),'high':D(21),'low':D(19)})
    assert D(technical(rows,cfg)['atr'])==D('6.5')


def test_custom_warmup(store):
    config=IndicatorConfig(slow=40)
    ctx=AnalysisContext(DataEngine(store,Synthetic()),'BTCEUR',ASOF,config)
    assert all(f['status']=='incomplete' for f in ctx.frames.values())


def test_future_evaluation_rejected(store):
    from crypto.models import now
    with pytest.raises(ValueError,match='toekomst'):
        asyncio.run(run_research(DataEngine(store,Synthetic()),now()+timedelta(days=1),['BTCEUR']))


def test_future_dependency_message(store):
    from crypto.orchestrator import Orchestrator,Task
    class Future:
        async def run(self,inputs):
            from crypto.models import Message
            return Message(agent_id='future',coin='BTCEUR',timeframe='1h',timestamp=ASOF+timedelta(seconds=1),data={'test':True},result={'test':True},rationale='fixture',ttl_seconds=60)
    o=Orchestrator(store,evaluation_time=ASOF);o.register('future',Future())
    assert asyncio.run(o.execute([Task('future','future')]))=={}


def test_expiry_in_combined_report(store):
    reports=asyncio.run(run_research(DataEngine(store,Synthetic()),ASOF,['BTCEUR'],news=Feed([item(expires=ASOF+timedelta(seconds=30))])))
    assert reports[0].ttl_seconds==30
    assert not reports[0].usable(ASOF+timedelta(seconds=31))


def test_changed_future_information_does_not_change_prefix(store,tmp_path):
    import json
    from crypto.data import LocalAdapter
    snapshots=[]
    for value in (D(100),D(999999)):
        rows=[]
        for tf in ('15m','1h','4h'):
            rows.extend(Synthetic().fetch('BTCEUR',tf,ASOF-timedelta(seconds=32*SECONDS[tf]),ASOF))
            future=Synthetic().fetch('BTCEUR',tf,ASOF,ASOF+timedelta(seconds=SECONDS[tf]))[0]
            rows.append(future.model_copy(update={'open':value,'close':value,'high':value+1,'low':value-1}))
        path=tmp_path/f'{value}.json'
        path.write_text(json.dumps([r.model_dump(mode='json') for r in rows]))
        snapshots.append(AnalysisContext(DataEngine(store,LocalAdapter(path)),'BTCEUR',ASOF).frames)
    assert snapshots[0]==snapshots[1]
