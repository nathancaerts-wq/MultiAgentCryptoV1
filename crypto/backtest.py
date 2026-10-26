"""Begrensde offline backtests; afzonderlijke onderzoeksopslag, geen papertrading."""
from datetime import datetime,timedelta
from decimal import Decimal
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field,model_validator
from .models import Model,now
from .data import Candle,validate_series
from .protocol import ResearchPlan
from .offline_optimizer import OfflineResearchOptimizer
from .sim_execution import D,FillCosts,SpotFilters,OfflineLedger,canonical,digest


class SimulationProtocol(Model):
    version: Literal['conservative-ohlcv-v1'] = 'conservative-ohlcv-v1'
    costs: FillCosts = Field(default_factory=FillCosts)
    filters: tuple[SpotFilters,...]
    candle_hashes: tuple[str,str,str]
    interval: Literal['15m','1h'] = '1h'
    data_kind: Literal['binance_spot','synthetic_fixture'] = 'binance_spot'
    benchmarks: tuple[Literal['ema_trend'],...] = ('ema_trend',)
    independent_test_authorization: str | None = None

    @model_validator(mode='after')
    def valid(self):
        import re
        if max(self.costs.fee,self.costs.spread,self.costs.slippage)>D('.1'): raise ValueError('Basiskosten maximaal 10%; stressscenario verdubbelt')
        if not self.filters or len({r.symbol for r in self.filters})!=len(self.filters): raise ValueError('Unieke filters per coin vereist')
        if len(set(self.benchmarks))!=len(self.benchmarks): raise ValueError('Dubbele benchmarks')
        if any(not re.fullmatch(r'[0-9a-f]{64}',x) for x in self.candle_hashes): raise ValueError('Candlehashes vereist')
        if self.independent_test_authorization is not None and len(self.independent_test_authorization.strip())<16:
            raise ValueError('Expliciete voorafgaande testautorisatie vereist')
        return self


def candle_digest(by_coin):
    return digest({coin:[Candle.model_validate(c).model_dump(mode='json') for c in rows] for coin,rows in by_coin.items()})


def metrics(ledger, exposed_seconds, period_seconds, minimum_trades):
    trades=ledger.trades; values=[t['net'] for t in trades]
    wins=[v for v in values if v>0]; losses=[v for v in values if v<0]
    total=sum(values,D(0)); without=total-sum(sorted(wins,reverse=True)[:3],D(0))
    return {'trades':len(trades),'net_result':ledger.cash-D(200) if ledger.position is None else None,
            'realized':ledger.realized,'winrate':D(len(wins))/len(trades) if trades else None,
            'average_win':sum(wins)/len(wins) if wins else None,'average_loss':sum(losses)/len(losses) if losses else None,
            'expectancy':total/len(trades) if trades else None,'profit_factor':sum(wins,D(0))/-sum(losses) if losses else None,
            'profit_factor_note':'undefined_without_losses' if not losses else None,
            'max_drawdown':ledger.max_drawdown,'market_exposure':D(exposed_seconds)/D(period_seconds),
            'net_without_top_3_winners':without if ledger.position is None else None,'evidence':'insufficient_evidence' if len(trades)<minimum_trades else 'requires_independent_statistical_validation',
            'complete':ledger.position is None}


def simulate(plan,rule,costs,bars,selections,hypothesis):
    """Reeds gevalideerde historische candles; selectie nooit uit toekomstige OHLC."""
    if not bars: raise ValueError('Ontbrekende candles')
    bars=[Candle.model_validate(c.model_dump()) for c in bars]
    validate_series(bars,rule.symbol,bars[0].interval,bars[0].opened,bars[-1].closed,now())
    ledger=OfflineLedger(costs,rule,plan.planned_risk)
    ledger.audit('initial_balance',bars[0].opened,cash=D(200))
    signals={}
    for selection in selections:
        at=datetime.fromisoformat(selection['decision_at'])
        if at in signals: raise ValueError('Dubbel signaaltijdstip')
        signals[at]=selection
    exposed=0
    for i,bar in enumerate(bars):
        ledger.observe(bar.opened,bar.open)
        # Tijdexit wordt op open afgehandeld voordat er een nieuwe instap komt.
        if ledger.position and bar.opened>=ledger.position.deadline:
            ledger.sell(f'horizon:{i}',bar.opened,bar.open,'horizon')
        selection=signals.pop(bar.opened,None)
        if selection is not None:
            eligible=selection['hypotheses'].get(hypothesis,{}).get('eligible',False) if hypothesis in plan.hypotheses else selection['benchmarks'].get(hypothesis,False)
            if eligible:
                order_id='entry:'+selection['event_id']
                if i==0: ledger.reject(order_id,bar.opened,'vorige_afgesloten_prijs_ontbreekt')
                else:
                    distance=D(selection['features']['1h']['atr'])*plan.stop_atr
                    if not distance.is_finite() or distance<=0:
                        ledger.reject(order_id,bar.opened,'ongeldige_ATR_afstand')
                    else:
                        qty,stop=ledger.size(bars[i-1].close,distance)
                        ledger.buy(order_id,bar.opened,bar.open,qty,stop,
                                   datetime.fromisoformat(selection['decision_at'])+timedelta(hours=plan.horizon_hours))
        if ledger.position:
            exposed+=int((bar.closed-bar.opened).total_seconds())
            ledger.process_bar(bar,i)
        # Pessimistische intrabar-exposure telt de hele bar als in de markt.
        equity=ledger.observe(bar.closed-timedelta(microseconds=1),bar.close)
        ledger.curve.append({'at':bar.closed.isoformat(),**ledger.snapshot(bar.close)})
    for at,selection in signals.items():
        ledger.reject('entry:'+selection['event_id'],at,'signaal_niet_op_uitvoeringsgrens')
    if ledger.position:
        ledger.sell('period_end',bars[-1].closed-timedelta(microseconds=1),bars[-1].close,'period_end')
        ledger.curve.append({'at':bars[-1].closed.isoformat(),**ledger.snapshot(bars[-1].close)})
    ledger.reconcile()
    ledger.audit('final_snapshot',bars[-1].closed,snapshot=ledger.snapshot(bars[-1].close))
    return {'metrics':metrics(ledger,exposed,int((bars[-1].closed-bars[0].opened).total_seconds()),plan.minimum_trades),
            'trades':ledger.trades,'events':ledger.events,'equity_curve':ledger.curve,
            'ending_ledger':ledger.snapshot(bars[-1].close),
            'assumptions':{'filters':rule.model_dump(mode='json'),'costs':costs.model_dump(mode='json'),
                           'intrabar':'stop_first; portfolio breach at worst bar price; exposure rounded to full bar',
                           'portfolio':'isolated EUR 200 per coin/hypothesis; one position; no cross-coin aggregation'}}


class BacktestRunner:
    def __init__(self,store):
        self.store=store; self.optimizer=OfflineResearchOptimizer(store)

    def register(self,plan,protocol):
        plan=ResearchPlan.model_validate(plan.model_dump())
        protocol=SimulationProtocol.model_validate(protocol.model_dump())
        if {r.symbol for r in protocol.filters}!=set(plan.coins): raise ValueError('Filteruniversum wijkt af')
        if protocol.costs.fee!=plan.fee or protocol.costs.slippage!=plan.slippage: raise ValueError('Kosten wijken af van plan')
        plan_id=self.optimizer.register(plan)
        payload={'plan_id':plan_id,'protocol':protocol.model_dump(mode='json')}
        key=digest(payload)
        prior=next((x for x in self.store.list('simulation_protocols') if x['plan_id']==plan_id),None)
        if prior and prior['id']!=key: raise ValueError('Uitvoeringsprotocol voor plan is al vastgelegd')
        if not prior:
            self.store.put('simulation_protocols',key,payload)
            self.store.audit('simulation_preregistered',key)
        return key

    def run(self,protocol_id,stage,reports,by_coin):
        if stage not in ('development','validation','independent_test'): raise ValueError('Onbekende fase')
        record=next((x for x in self.store.list('simulation_protocols') if x['id']==protocol_id),None)
        if record is None: raise KeyError('Uitvoeringsprotocol eerst registreren')
        spec=SimulationProtocol.model_validate(record['protocol'])
        if stage=='independent_test' and spec.independent_test_authorization is None:
            raise PermissionError('Onafhankelijke test is gesloten in dit protocol')
        plan=self.optimizer._plan(record['plan_id']); period=getattr(plan,stage)
        if set(by_coin)!=set(plan.coins): raise ValueError('Onvolledig coin-universum')
        if candle_digest(by_coin)!=spec.candle_hashes[('development','validation','independent_test').index(stage)]:
            raise ValueError('Candles wijken af van preregistratie')
        # Elke daadwerkelijke evaluatie wordt vóór resultaten in het blootstellingsregister opgenomen.
        inspection=self.optimizer.inspect(plan.fingerprint,stage,reports,plan.dataset_sha256)
        run_id=digest({'protocol':protocol_id,'stage':stage})
        cached=next((r for r in self.store.list('backtest_runs') if r['id']==run_id),None)
        if cached: return {**cached,'replay':True}
        try:
            if inspection['rejections']: raise ValueError('Onderzoeksselecties afgewezen: '+canonical(inspection['rejections']))
            output={}
            for coin in plan.coins:
                bars=[Candle.model_validate(c.model_dump() if isinstance(c,Candle) else c) for c in by_coin[coin]]
                validate_series(bars,coin,spec.interval,period.start,period.end,now())
                for bar in bars:
                    url=urlsplit(bar.source)
                    if spec.data_kind=='binance_spot' and not (url.scheme=='https' and ((url.hostname=='data.binance.vision' and url.path.startswith('/data/spot/')) or (url.hostname in ('data-api.binance.vision','api.binance.com') and url.path=='/api/v3/klines'))):
                        raise ValueError('Bron is geen publieke Binance Spot-databron')
                    if spec.data_kind=='synthetic_fixture' and not bar.source.startswith('fixture:'):
                        raise ValueError('Fixturebron niet expliciet gemarkeerd')
                rule=next(r for r in spec.filters if r.symbol==coin)
                selections=[r for r in inspection['selections'] if r['coin']==coin]
                output[coin]={}
                for name in tuple(plan.hypotheses)+spec.benchmarks:
                    normal=simulate(plan,rule,spec.costs,bars,selections,name)
                    stress=simulate(plan,rule,FillCosts(fee=spec.costs.fee*2,spread=spec.costs.spread*2,slippage=spec.costs.slippage*2),bars,selections,name)
                    normal['metrics']['double_cost_net']=stress['metrics']['net_result']
                    normal['double_cost_scenario']=stress
                    output[coin][name]=normal
                output[coin]['buy_and_hold']={'status':'not_simulated','reason':'Ongeremde buy-and-hold zonder stop past niet binnen 0,5% gepland risico; geen stilzwijgende benchmarkwijziging'}
            result={'protocol':protocol_id,'plan':plan.fingerprint,'stage':stage,'period':period.model_dump(mode='json'),
                    'results':output,'inspection':inspection,'status':'offline_simulation_not_statistical_proof'}
            # JSON-native resultaat blijft identiek na herstart.
            import json
            result=json.loads(canonical(result))
            self.store.put('backtest_runs',run_id,result)
            self.store.audit('backtest_completed',run_id)
            return {'id':run_id,**result,'replay':False}
        except Exception as exc:
            self.store.audit('backtest_failed',canonical({'run':run_id,'reason':str(exc)}))
            raise
