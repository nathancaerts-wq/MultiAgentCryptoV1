"""Begrensde combinatie van bestaande analyseberichten; geen handelsorders."""
from datetime import datetime,timedelta
from decimal import Decimal
from .data import SECONDS,utc
from .analysis import boundary
from .models import Message
from .protocol import HYPOTHESES,BENCHMARKS


class QuantResearcher:
    def __init__(self,plan): self.plan=plan

    def evaluate(self,report,decision_at):
        utc(decision_at)
        report=Message.model_validate(report)
        if report.coin not in self.plan.coins or not report.agent_id.startswith('research_report:') or not report.usable(decision_at):
            raise ValueError('Verkeerd, verlopen of toekomstig onderzoeksbericht')
        if datetime.fromisoformat(report.data['as_of'])!=decision_at:
            raise ValueError('Onderzoeksmoment komt niet overeen')
        if report.data['parameters']!=self.plan.indicators.model_dump(mode='json'):
            raise ValueError('Parameters wijken af van preregistratie')
        frames=report.data['frames']
        features={}
        for tf in ('15m','1h','4h'):
            f=frames[tf]
            if f['status']!='complete': raise ValueError('Ontbrekende indicatoren of datagaten')
            start,end=datetime.fromisoformat(f['start']),datetime.fromisoformat(f['end'])
            utc(start); utc(end)
            if end!=boundary(decision_at,tf) or start>=end or (end-start).total_seconds()!=f['count']*SECONDS[tf] or not f.get('sources') or len(f.get('sha256',''))!=64:
                raise ValueError('Ongeldige bron, candlegrens of dekking')
            features[tf]=f
        # Gebruik exact de meegestuurde, provenance-gebonden technische kenmerken.
        from .indicators import classify
        regime=classify(features['1h'],self.plan.indicators)
        directions={tf:f['direction'] for tf,f in features.items()}
        c=report.result.get('components',{})
        if c.get('regime',{}).get('classification')!=regime or c.get('multi_timeframe',{}).get('directions')!=directions or c.get('technical',{}).get('frames')!=frames:
            raise ValueError('Analysecomponenten inconsistent')
        rsi=Decimal(features['1h']['rsi']); momentum=Decimal(features['1h']['momentum'])
        matched={
            'regime_momentum':regime=='bullish' and momentum>0 and 40<=rsi<=70,
            'aligned_trend':regime=='bullish' and all(d=='up' for d in directions.values()),
            'sideways_recovery':regime=='sideways' and rsi<40 and Decimal(features['15m']['momentum'])>0,
        }
        return {'coin':report.coin,'decision_at':decision_at.isoformat(),'event_id':str(report.event_id),
                'plan':self.plan.fingerprint,'features':features,
                'hypotheses':{h:{'eligible':matched[h],'definition':HYPOTHESES[h]} for h in self.plan.hypotheses},
                'benchmarks':{'buy_and_hold':True,'ema_trend':features['1h']['direction']=='up'},
                'meaning':'onderzoeksselectie; geen trade, uitkomst of rendement'}
