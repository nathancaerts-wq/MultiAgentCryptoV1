import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5
from .data import WATCHLIST, SECONDS, utc
from .models import Message


class CoinScanner:
    """Deterministische relatieve rangschikking; score is geen winstkans."""
    def __init__(self, engine, as_of, interval='1h', watchlist=WATCHLIST, lookback=24, max_age=3600):
        utc(as_of)
        if interval not in SECONDS or lookback < 3 or not 1 <= max_age <= 86400: raise ValueError('Ongeldige scannerconfiguratie')
        symbols=tuple(sorted(set(s.replace('/','').upper() for s in watchlist)))
        if not symbols: raise ValueError('Lege watchlist')
        self.engine,self.as_of,self.interval,self.watchlist,self.lookback,self.max_age=engine,as_of,interval,symbols,lookback,max_age

    async def run(self, inputs):
        end=self.as_of-timedelta(seconds=int(self.as_of.timestamp())%SECONDS[self.interval],microseconds=self.as_of.microsecond)
        start=end-timedelta(seconds=SECONDS[self.interval]*self.lookback)
        ranked,rejected=[],[]
        for symbol in self.watchlist:
            try:
                rows=self.engine.load(symbol,self.interval,start,end,self.as_of)
                if (self.as_of-rows[-1].closed).total_seconds() >= self.max_age:
                    raise ValueError('Verouderde marktdata')
                closes=[r.close for r in rows]
                mean=sum(closes)/len(closes)
                returns=[b/a-1 for a,b in zip(closes,closes[1:])]
                avg=sum(returns)/len(returns)
                variance=sum((r-avg)**2 for r in returns)/len(returns)
                ranked.append({'symbol':symbol,'trend':closes[-1]/mean-1,'momentum':closes[-1]/closes[0]-1,'volatility':variance.sqrt(),'liquidity':sum(r.quote_volume for r in rows),'data_end':end.isoformat(),'sources':sorted({r.source for r in rows}),'availability':'historical_data_only_unverified_tradability'})
            except Exception as exc:
                rejected.append({'symbol':symbol,'reason':str(exc)})
        # Pairwise percentielrangen met gelijke score bij ties; lagere volatiliteit scoort hoger.
        for row in ranked:
            score=Decimal(0)
            for field, direction in [('trend',1),('momentum',1),('volatility',-1),('liquidity',1)]:
                score+=sum(Decimal(1) if direction*(row[field]-other[field])>0 else Decimal('.5') if row[field]==other[field] else Decimal(0) for other in ranked)/len(ranked)*25
            row['score']=str(score)
            row['explanation']=f"trend={row['trend']:.6f}; momentum={row['momentum']:.6f}; volatiliteit={row['volatility']:.6f} (lager beter); quotevolume EUR={row['liquidity']}; vier gelijke ranggewichten; geen winstkans"
        ranked.sort(key=lambda r:(-Decimal(r['score']),r['symbol']))
        result={'ranking':ranked,'rejections':rejected,'as_of':self.as_of.isoformat(),'method':'relative_rank_v1','historical':True}
        identity=json.dumps(result,sort_keys=True,default=str)
        # Timestamp is marktdata-einde, niet importtijd: oude imports worden nooit verse signalen.
        message = Message(agent_id='scanner',event_id=uuid5(NAMESPACE_URL,identity),coin='EUR_UNIVERSE',timestamp=end,timeframe=self.interval,data={'watchlist':self.watchlist,'start':start.isoformat(),'end':end.isoformat()},result=result,rationale='Afgesloten candles; deterministische onderzoeksranking',ttl_seconds=self.max_age,status='ok' if ranked else 'error',errors=() if ranked else ('Geen geldige marktdata',))

        self.engine.record_scan(message)
        return message
