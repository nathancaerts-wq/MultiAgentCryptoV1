"""Expliciet offline fase-5-pad: bericht -> Risk Engine -> onderzoeksuitvoering.

Geen call naar ExecutionEngine.propose, geen paper-orders en geen netwerkclient.
Een sessie is één geïsoleerd coin/hypothese-experiment met EUR 200.
"""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, date, timedelta
from decimal import Decimal as D
import json
from .data import Candle, validate_series, utc
from .models import Limits, MarketRules, Message, Proposal, now
from .orchestrator import Orchestrator, Task
from .protocol import ResearchPlan, report_digest
from .offline_optimizer import OfflineResearchOptimizer
from .risk import ExecutionEngine, RiskEngine
from .sim_execution import OfflineLedger, SpotFilters, Position, canonical, digest
from .trade_agents import DecisionPolicy, DecisionAgent, EntryAgent, ExitAgent


def ledger_state(ledger):
    values = {k:v for k,v in vars(ledger).items() if k not in ('costs','rules','limits','position','ids')}
    values['position'] = asdict(ledger.position) if ledger.position else None
    values['ids'] = sorted(ledger.ids)
    return json.loads(canonical(values))


def restore_ledger(state, policy, rules):
    ledger = OfflineLedger(policy.costs, rules, policy.planned_risk)
    numeric = ('risk','cash','realized','fees','peak','day_start','max_drawdown','last_equity')
    for key, value in state.items():
        if key in numeric: value = D(value)
        elif key=='day': value = date.fromisoformat(value) if value else None
        elif key=='ids': value = set(value)
        elif key=='position' and value:
            value = dict(value)
            for field in ('quantity','average_price','entry_fee','raw_entry','stop','target'):
                value[field] = D(value[field]) if value[field] is not None else None
            for field in ('entered_at','deadline'): value[field] = datetime.fromisoformat(value[field])
            value = Position(**value)
        setattr(ledger, key, value)
    ledger.reconcile()
    return ledger


def market_rules(filters, at):
    # Timestamp is het tijdstip waarop de expliciete simulatie-aanname wordt gebruikt,
    # geen claim dat historische beursmetadata op dat tijdstip is opgevraagd.
    return MarketRules(symbol=filters.symbol, enabled=True, min_qty=max(filters.min_qty,filters.market_min_qty),
                       max_qty=min(filters.max_qty,filters.market_max_qty or filters.max_qty),
                       step=filters.quantity_step, tick=filters.tick,
                       min_notional=max(filters.min_notional if filters.min_notional_market else D(0),
                                        filters.notional_min if filters.notional_apply_min_market else D(0)),
                       max_notional=filters.notional_max if filters.notional_apply_max_market else None, timestamp=at)


class ResearchExecutionEngine(ExecutionEngine):
    """Gescheiden adapter op dezelfde Risk/Execution-contracten; uitsluitend offline."""
    def __init__(self, store, risk, session):
        super().__init__(store, risk)
        self.session = session

    def propose(self, *args, **kwargs):
        raise ValueError('Paper-voorstelroute niet beschikbaar in onderzoek')

    def reason(self, candidate, ledger, raw=None):
        try:
            return self._reason(candidate, ledger, raw)
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            return 'ongeldig onderzoeksvoorstel: '+str(exc)

    def _reason(self, candidate, ledger, raw=None):
        r, at, s = candidate.result, candidate.timestamp, self.session
        if candidate.coin!=s.symbol or candidate.data.get('policy')!=s.policy.fingerprint or not candidate.usable(at):
            return 'verkeerd onderzoeksbericht'
        if r['action'] not in ('ENTRY_CANDIDATE','EXIT_CANDIDATE'):
            return r.get('reason','geen kandidaat')
        expected_agent = ('entry:' if r['action']=='ENTRY_CANDIDATE' else 'exit:')+s.symbol
        if candidate.agent_id!=expected_agent or not s.plan.development.start<=at<=s.plan.development.end:
            return 'verkeerde agent of buiten ontwikkelperiode'
        side = 'buy' if r['action']=='ENTRY_CANDIDATE' else 'sell'
        reference = D(r['reference']) if raw is None else raw
        price = s.policy.costs.price(reference,side,ledger.rules.tick)
        q = D(r['quantity'])
        failure = ledger.rules.check(q,price,at)
        if failure: return failure
        if side=='sell':
            p = ledger.position
            if not p or p.symbol!=candidate.coin or p.order_id!=r['position_id'] or q!=p.quantity:
                return 'positie ontbreekt, is gewijzigd of hoeveelheid overschrijdt bezit'
            return self.risk.check_exit(quantity=q,price=price,available=p.quantity,
                                        rules=market_rules(ledger.rules,at),timestamp=at,evaluation_time=at)
        if ledger.position: return 'bestaande positie; geen tweede exposure'
        preview = ledger.analysis_view()
        preview.observe(at,reference)
        if preview.day_paused: return 'dagverliespauze'
        if preview.drawdown_paused: return 'drawdownpauze'
        losses = 0
        for trade in reversed(ledger.trades):
            if D(trade['net'])>=0: break
            losses += 1
        if losses>=s.policy.max_consecutive_losses: return 'verliesreekspauze'
        stop = D(r['stop'])
        if not 0<stop<reference: return 'ongeldige stop na koersgap'
        sell = s.policy.costs.price(stop,'sell',ledger.rules.tick)
        loss = q*(price-sell)+s.policy.costs.charge(q,price)+s.policy.costs.charge(q,sell)
        if loss>min(D(200),ledger.cash)*s.policy.planned_risk: return 'gepland risico inclusief kosten'
        if q*price+s.policy.costs.charge(q,price)>ledger.cash: return 'onvoldoende saldo inclusief kosten'
        try:
            proposal = Proposal(event_id=candidate.event_id, symbol=candidate.coin, quantity=q,price=price,stop=stop,timestamp=at)
            return self.risk.check(proposal,market_rules(ledger.rules,at),cash=ledger.cash,equity=ledger.cash,
                                   exposure=0,daily_loss=max(D(0),preview.day_start-ledger.cash),peak=preview.peak,
                                   correlation=0,evaluation_time=at)
        except (ValueError, ArithmeticError) as exc:
            return str(exc)

    def review(self, candidate):
        s = self.session
        s.check_frozen()
        identity = digest(dict(session=s.key,candidate=candidate.model_dump(mode='json'),state=ledger_state(s.ledger),stopped=self.risk.stopped))
        old = self.store.db.execute('SELECT payload FROM research_trade_reviews WHERE id=?',(identity,)).fetchone()
        if old: return dict(id=identity,**json.loads(old[0]))
        reason = self.reason(candidate,s.ledger)
        record = dict(session=s.key,candidate=candidate.model_dump(mode='json'),approved=reason is None,
                      reason=reason or 'Risk Engine akkoord voor expliciete offline simulatie',
                      ledger_sha256=digest(ledger_state(s.ledger)),mode='offline_research_only')
        with self.store.transaction():
            self.store.put('research_trade_reviews',identity,record)
            self.store.audit('research_risk_decision',canonical(dict(id=identity,approved=reason is None,reason=record['reason'])))
        return dict(id=identity,**record)

    def simulate(self, review_id):
        """Uitsluitend expliciet aangeroepen. Hercontrole, atomair auditrecord, geen paper-fill."""
        s = self.session
        s.check_frozen()
        row = self.store.db.execute('SELECT payload FROM research_trade_reviews WHERE id=?',(review_id,)).fetchone()
        if not row: raise ValueError('Onbekend risicobesluit')
        review = json.loads(row[0])
        if review['session']!=s.key or not review['approved']: raise ValueError('Geen goedgekeurd onderzoeksvoorstel')
        candidate = Message.model_validate(review['candidate'])
        if not self.store.db.execute('SELECT 1 FROM results WHERE id=? AND payload=?',
                                    (str(candidate.event_id),json.dumps(candidate.model_dump(mode='json'),default=str,allow_nan=False))).fetchone():
            raise ValueError('Voorstel ontbreekt in gevalideerde orchestratorresultaten')
        r, at = candidate.result, candidate.timestamp
        # Semantische uitvoering is onafhankelijk van event-ID of gewijzigde toelichting.
        key = digest(dict(session=s.key,action=r['action'],at=at,position=r.get('position_id')))
        existing = self.store.db.execute('SELECT payload FROM research_fills WHERE id=?',(key,)).fetchone()
        if existing:
            s.ledger = restore_ledger(s.latest_state(),s.policy,s.filters)
            return dict(json.loads(existing[0]),replay=True)
        if review['ledger_sha256']!=digest(ledger_state(s.ledger)): raise ValueError('Ledger gewijzigd; nieuw risicobesluit vereist')
        raw = D(r['reference'])
        if r['action']=='ENTRY_CANDIDATE':
            bar = s.bars_by_open.get(at)
            if not bar: raise ValueError('Volgende historische uitvoeringscandle ontbreekt')
            # Alleen de open van N+1; high/low/close bepalen geen instap.
            raw = bar.open
        trial = deepcopy(s.ledger)
        failure = self.reason(candidate,trial,raw)
        if failure:
            trial.reject(key,at,failure)
            success = False
        elif r['action']=='ENTRY_CANDIDATE':
            success = trial.buy(key,at,raw,D(r['quantity']),D(r['stop']),datetime.fromisoformat(r['deadline']))
        else:
            success = trial.sell(key,at,raw,r['reason'],r.get('ambiguous',False))
        record = dict(session=s.key,review=review_id,at=at.isoformat(),action=r['action'],success=success,
                      reason=trial.events[-1]['details'].get('reason',r['reason']),state=ledger_state(trial),
                      candle_sha256=digest(s.bars_by_open[at].model_dump(mode='json')) if r['action']=='ENTRY_CANDIDATE' else digest(candidate.data['bar']),
                      mode='offline_research_only')
        with self.store.transaction():
            # Eén schrijver; herstart/concurrent gewijzigde state wordt niet overschreven.
            latest = s.latest_state()
            if latest is not None and digest(latest)!=digest(ledger_state(s.ledger)):
                raise ValueError('Ledger door andere sessie gewijzigd')
            self.store.put('research_fills',key,record)
            self.store.put('research_ledger_states',key,dict(session=s.key,at=at.isoformat(),kind='fill',state=record['state']))
            self.store.audit('research_simulated',canonical(dict(id=key,success=success,reason=record['reason'])))
        s.ledger = trial
        return record


class ResearchTradingSession:
    """Kleine ontwikkeltest, vooraf gebonden data/beleid; geen validatie-/testpoort."""
    def __init__(self, store, plan, policy, symbol, filters, reports, bars):
        self.store = store
        self.plan = ResearchPlan.model_validate(plan.model_dump())
        self.policy = DecisionPolicy.model_validate(policy.model_dump())
        self.symbol = symbol
        self.filters = SpotFilters.model_validate(filters.model_dump())
        self.reports = tuple(Message.model_validate(r.model_dump()) for r in reports)
        self.bars = tuple(Candle.model_validate(b.model_dump()) for b in bars)
        if symbol not in self.plan.coins or filters.symbol!=symbol or policy.hypothesis not in self.plan.hypotheses:
            raise ValueError('Watchlist, filters of hypothese wijken af')
        if policy.costs.fee!=plan.fee or policy.costs.slippage!=plan.slippage or policy.planned_risk>plan.planned_risk:
            raise ValueError('Kosten of risico wijken af van onderzoeksplan')
        if report_digest(self.reports)!=plan.report_hashes[0]: raise ValueError('Rapportbundel wijkt af van preregistratie')
        if not 1<=len(self.bars)<=192: raise ValueError('Alleen kleine tests van maximaal 192 candles')
        validate_series(self.bars,symbol,'15m',self.bars[0].opened,self.bars[-1].closed,now())
        if self.bars[0].opened<plan.development.start or self.bars[-1].closed>plan.development.end:
            raise ValueError('Uitsluitend ontwikkeldata; onafhankelijke test gesloten')
        identities = set()
        for r in self.reports:
            at = datetime.fromisoformat(r.data['as_of']); utc(at)
            if not plan.development.contains(at) or at+timedelta(hours=4)>plan.development.end or r.coin not in plan.coins:
                raise ValueError('Rapport buiten ontwikkeling of horizon')
            if (r.coin,at) in identities: raise ValueError('Dubbele coin/tijdstip in rapportbundel')
            identities.add((r.coin,at))
        from urllib.parse import urlsplit
        for b in self.bars:
            if not b.source.startswith('fixture:') and (not b.source.startswith('https://') or urlsplit(b.source).hostname not in ('data.binance.vision','data-api.binance.vision')):
                raise ValueError('Alleen officiële Binance-bronnen of expliciete fixtures')
        self.bars_by_open = {b.opened:b for b in self.bars}
        self.manifest = self.manifest_value()
        self.key = plan.fingerprint+':'+symbol
        self.risk = RiskEngine(Limits(),Limits(trade_risk=policy.planned_risk))
        optimizer = OfflineResearchOptimizer(store)
        optimizer.register(self.plan)
        old = store.db.execute('SELECT payload FROM decision_protocols WHERE id=?',(self.key,)).fetchone()
        if old and json.loads(old[0])!=self.manifest: raise ValueError('Beslisregels of data zijn al bevroren voor dit plan/coin')
        if not old:
            with store.transaction():
                store.put('decision_protocols',self.key,self.manifest)
                store.audit('decision_policy_frozen',self.key)
        state = self.latest_state()
        self.ledger = restore_ledger(state,policy,filters) if state else OfflineLedger(policy.costs,filters,policy.planned_risk)
        if state is None:
            at = self.plan.development.start
            self.ledger.audit('research_ledger_started',at,cash=D(200),currency='EUR',policy=self.policy.fingerprint)
            with store.transaction():
                store.put('research_ledger_states',digest(dict(session=self.key,kind='initial')),
                          dict(session=self.key,at=at.isoformat(),kind='initial',state=ledger_state(self.ledger)))
                store.audit('research_ledger_started',self.key)
        self.execution = ResearchExecutionEngine(store,self.risk,self)

    def manifest_value(self):
        return dict(plan=self.plan.fingerprint,policy=self.policy.model_dump(mode='json'),filters=self.filters.model_dump(mode='json'),
                    reports=report_digest(self.reports),bars=digest([b.model_dump(mode='json') for b in self.bars]),
                    stage='development',independent_test_authorization=None)

    def check_frozen(self):
        if self.bars_by_open!={b.opened:b for b in self.bars}: raise ValueError('Bevroren candle-index gewijzigd')
        if self.manifest_value()!=self.manifest: raise ValueError('Bevroren protocol gewijzigd')
        expected = Limits(trade_risk=self.policy.planned_risk)
        if self.risk.limits!=expected or self.risk.hard!=Limits(): raise ValueError('Risicoconfiguratie gewijzigd')
        if self.ledger.rules!=self.filters or self.ledger.costs!=self.policy.costs or self.ledger.risk!=self.policy.planned_risk or self.ledger.limits!=Limits():
            raise ValueError('Ledgerconfiguratie gewijzigd')

    def latest_state(self):
        records = self.store.db.execute('SELECT payload FROM research_ledger_states ORDER BY rowid').fetchall()
        own = [json.loads(r[0]) for r in records if json.loads(r[0])['session']==self.key]
        return own[-1]['state'] if own else None

    async def evaluate(self, at):
        utc(at); self.check_frozen()
        if at>now() or not self.plan.development.start<=at<=self.plan.development.end:
            raise ValueError('Uitsluitend historische ontwikkeling; test gesloten')
        states = [r for r in self.store.list('research_ledger_states') if r['session']==self.key]
        last_at = max((datetime.fromisoformat(r['at']) for r in states),default=None)
        if last_at and at<last_at: raise ValueError('Geen terugwaartse ledger-evaluatie')
        latest = self.latest_state()
        if latest is not None and digest(latest)!=digest(ledger_state(self.ledger)):
            raise ValueError('Ledger door andere sessie gewijzigd; heropen de sessie')
        if self.ledger.position:
            start = self.ledger.position.entered_at
            expected = (last_at or start)+timedelta(minutes=15)
            if at<start+timedelta(minutes=15) or at not in (last_at,expected):
                raise ValueError('Open positie vereist elke volgende afgesloten 15m-candle; geen overslaan')
        report = next((r for r in self.reports if r.coin==self.symbol and datetime.fromisoformat(r.data['as_of'])==at),None)
        reference = self.bars_by_open.get(at-timedelta(minutes=15))
        # Alleen ontwikkeling registreren; geen inspectie van onafhankelijke test.
        exposure_id = self.key+':decision-development'
        if not self.store.db.execute('SELECT 1 FROM research_exposures WHERE id=?',(exposure_id,)).fetchone():
            self.store.put('research_exposures',exposure_id,dict(plan=self.plan.fingerprint,stage='development',coins=[self.symbol],
                           period=self.plan.development.model_dump(mode='json'),viewed_at=now().isoformat(),previously_exposed=True))
        decision = DecisionAgent(self.plan,self.policy,self.symbol,at,report,self.ledger.position)
        entry = EntryAgent(self.policy,self.symbol,at,self.ledger,reference)
        exit_agent = ExitAgent(self.policy,self.symbol,at,self.ledger,reference,self.risk.stopped)
        o = Orchestrator(self.store,evaluation_time=at,reuse_results=True)
        for agent in (decision,entry,exit_agent): o.register(agent.id,agent)
        accepted = await o.execute([Task(decision.id,decision.id),Task(entry.id,entry.id,(decision.id,)),Task(exit_agent.id,exit_agent.id)])
        reviews = []
        for agent in (decision,entry,exit_agent):
            m = accepted.get(agent.id)
            if m is None: continue  # Fout is door orchestrator opgeslagen; geen instap.
            if not self.store.db.execute('SELECT 1 FROM trade_decisions WHERE id=?',(str(m.event_id),)).fetchone():
                self.store.put('trade_decisions',m.event_id,m.model_dump(mode='json'))
            if agent is not decision: reviews.append(self.execution.review(m))
        exit_message = accepted.get(exit_agent.id)
        if self.ledger.position and exit_message and exit_message.result.get('reason')=='Geen exitvoorwaarde geraakt':
            identity = digest(dict(session=self.key,position=self.ledger.position.order_id,at=at,kind='observation'))
            if not self.store.db.execute('SELECT 1 FROM research_ledger_states WHERE id=?',(identity,)).fetchone():
                trial = deepcopy(self.ledger)
                trial.observe(at,reference.low)
                trial.observe(at,reference.close)
                trial.audit('position_observed',at,candle_sha256=digest(reference.model_dump(mode='json')))
                with self.store.transaction():
                    if digest(self.latest_state())!=digest(ledger_state(self.ledger)):
                        raise ValueError('Ledger door andere sessie gewijzigd')
                    self.store.put('research_ledger_states',identity,dict(session=self.key,at=at.isoformat(),kind='observation',state=ledger_state(trial)))
                    self.store.audit('research_position_observed',identity)
                self.ledger = trial
        return dict(messages=accepted,reviews=reviews,independent_test_opened=False,mode='offline_research_only')
