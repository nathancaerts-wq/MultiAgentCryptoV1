"""Eén gedeelde EUR-ledger voor expliciet offline multi-coinonderzoek (fase 6A)."""
from copy import deepcopy, copy
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
from types import SimpleNamespace
from typing import Literal
from urllib.parse import urlsplit
from pydantic import Field
from .analysis import boundary
from .data import Candle, utc, validate_series
from .models import Model, Message, Limits, now
from .protocol import ResearchPlan, report_digest
from .offline_optimizer import OfflineResearchOptimizer
from .orchestrator import Orchestrator, Task
from .risk import RiskEngine
from .sim_execution import OfflineLedger, SpotFilters, canonical, digest
from .research_execution import ledger_state, restore_ledger, ResearchExecutionEngine
from .trade_agents import DecisionPolicy, DecisionAgent, EntryAgent, ExitAgent


class JointPolicy(Model):
    version: Literal['phase6a-v1'] = 'phase6a-v1'
    starting_cash: Literal['200'] = '200'
    max_open_positions: Literal[1] = 1
    priority: Literal['scanner_desc_utc_rotating_ties'] = 'scanner_desc_utc_rotating_ties'
    decision: DecisionPolicy = Field(default_factory=DecisionPolicy)


class JointPortfolio:
    """Een expliciete portefeuille per ResearchPlan, nooit één startkapitaal per coin.

    evaluate reserveert; execute boekt uitsluitend op expliciete aanroep. Elke
    mutatie vergelijkt de gelezen revisie in BEGIN IMMEDIATE met de actuele staat.
    Agents krijgen alleen kopieën. Een Python-/SQLite-beheerder is geen sandbox.
    """
    _max_bars = 192

    def _decision(self, symbol, at, report):
        return DecisionAgent(self.plan,self.policy.decision,symbol,at,report)

    def __init__(self, store, plan, policy, filters, reports, bars):
        self.store = store
        self.plan = ResearchPlan.model_validate(plan.model_dump())
        self.policy = JointPolicy.model_validate(policy.model_dump())
        self.rules = {s: SpotFilters.model_validate(f.model_dump()) for s,f in filters.items()}
        self.reports = tuple(Message.model_validate(r.model_dump()) for r in reports)
        self.bars = {s: tuple(Candle.model_validate(c.model_dump()) for c in rows) for s,rows in bars.items()}
        self.key = 'joint:'+self.plan.fingerprint
        p = self.policy.decision
        if set(self.rules)!=set(self.plan.coins) or set(self.bars)!=set(self.plan.coins):
            raise ValueError('Filters en candles vereist voor de gehele watchlist')
        if p.hypothesis not in self.plan.hypotheses or p.planned_risk>self.plan.planned_risk or p.costs.fee!=self.plan.fee or p.costs.slippage!=self.plan.slippage:
            raise ValueError('Beleid wijkt af van het onderzoeksplan')
        if report_digest(self.reports)!=self.plan.report_hashes[0]:
            raise ValueError('Rapportbundel wijkt af van preregistratie')
        ranges = set()
        for s,rows in self.bars.items():
            if self.rules[s].symbol!=s or not 1<=len(rows)<=self._max_bars:
                raise ValueError('Verkeerde filters of geen kleine candlebatch')
            validate_series(rows,s,'15m',rows[0].opened,rows[-1].closed,now())
            if rows[0].opened<self.plan.development.start or rows[-1].closed>self.plan.development.end:
                raise ValueError('Alleen ontwikkeling; onafhankelijke test gesloten')
            ranges.add((rows[0].opened,rows[-1].closed))
            for c in rows:
                if not c.source.startswith('fixture:') and (not c.source.startswith('https://') or urlsplit(c.source).hostname not in ('data.binance.vision','data-api.binance.vision')):
                    raise ValueError('Officiële Binance-bron of expliciete fixture vereist')
        if len(ranges)!=1: raise ValueError('Gezamenlijke uniforme candledekking vereist')
        seen = set()
        for r in self.reports:
            at = datetime.fromisoformat(r.data['as_of']); utc(at)
            if r.coin not in self.plan.coins or not self.plan.development.contains(at) or at+timedelta(hours=4)>self.plan.development.end:
                raise ValueError('Rapport buiten ontwikkeling of uitkomsthorizon')
            if (r.coin,at) in seen: raise ValueError('Dubbele coin/tijdstip')
            seen.add((r.coin,at))
        self.risk = RiskEngine(Limits(),Limits(trade_risk=p.planned_risk))
        self.manifest = self._manifest()
        OfflineResearchOptimizer(store).register(self.plan)
        with store.transaction():
            old = self._get('joint_protocols',self.key)
            if old is not None and old!=self.manifest: raise ValueError('Gezamenlijk protocol al bevroren')
            if old is None:
                store.put('joint_protocols',self.key,self.manifest)
                # Eén daadwerkelijke startbalans, ongeacht het aantal coins.
                ledger = OfflineLedger(p.costs,self.rules[self.plan.coins[0]],p.planned_risk)
                ledger.audit('joint_started',self.plan.development.start,cash=D(200),coins=self.plan.coins)
                state = dict(portfolio=self.key,at=self.plan.development.start.isoformat(),checked_at=None,
                             active_rules=self.plan.coins[0],mark=None,pending=None,stopped=False)
                self._save(None,state,ledger,'initial')
        self._read()

    def _get(self, table, key):
        row = self.store.db.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()
        if row is None: return None
        value=json.loads(row[0])
        return dict(id=key,**value) if table=='joint_batches' else value

    def _bar_metadata(self,s,rows):
        cache=getattr(self,'_bar_cache',{})
        old=cache.get(s)
        if old is None or old[0] is not rows:
            old=(rows,digest([c.model_dump(mode='json') for c in rows]),{c.opened:c for c in rows})
            cache[s]=old;self._bar_cache=cache
        return old

    def _report_digest(self):
        from .tracked_payload import Revision,tracked
        if getattr(self,'_report_identity',None) is not self.reports:
            self._report_revision=Revision()
            self.reports=tuple(r.model_copy(update={'data':tracked(r.data,self._report_revision),'result':tracked(r.result,self._report_revision)}) for r in self.reports)
            self._report_identity=self.reports
            self._report_cached_version=None
        version=self._report_revision.value
        if not self._report_revision.cacheable or self._report_cached_version!=version:
            self._report_cached_hash=report_digest(self.reports)
            self._report_cached_version=version
        return self._report_cached_hash

    def _reports_at(self, at):
        # _frozen heeft de bundel eerst gevalideerd; herbouw index na elke mutatie.
        self._report_digest()
        token=(id(self.reports),self._report_revision.value)
        if not self._report_revision.cacheable or getattr(self,'_report_index_token',None)!=token:
            index={}
            for r in self.reports:
                index.setdefault(datetime.fromisoformat(r.data['as_of']),[]).append(r)
            self._report_time_index={t:tuple(values) for t,values in index.items()};self._report_index_token=token
        return self._report_time_index.get(at,())

    def _manifest(self):
        return dict(plan=self.plan.fingerprint,policy=self.policy.model_dump(mode='json'),
                    filters={s:self.rules[s].model_dump(mode='json') for s in sorted(self.rules)},
                    reports=self._report_digest(),bars={s:self._bar_metadata(s,self.bars[s])[1] for s in sorted(self.bars)},
                    stage='development',independent_test_authorization=None)

    def _frozen(self):
        if self._manifest()!=self.manifest or self._get('joint_protocols',self.key)!=self.manifest:
            raise ValueError('Bevroren gezamenlijke configuratie gewijzigd')
        if self.risk.hard!=Limits() or self.risk.limits!=Limits(trade_risk=self.policy.decision.planned_risk):
            raise ValueError('Centrale risicolimieten gewijzigd')

    def _read(self):
        self._frozen()
        epoch = self.store.db.execute('SELECT value FROM joint_mutation_epoch WHERE singleton=1').fetchone()[0]
        cache = getattr(self,'_chain_prefix',None)
        previous, revision, anchor = '0'*64, -1, None
        state = None
        if cache and cache[0]==epoch:
            row = self.store.db.execute('SELECT payload FROM joint_states WHERE rowid=?',(cache[1],)).fetchone()
            # De anchor controle detecteert ook rollback/verwijdering en rowid-hergebruik.
            if row and row[0]==cache[4]:
                _,anchor,revision,previous,raw=cache
                state=json.loads(raw)
        query="SELECT rowid,payload FROM joint_states WHERE json_extract(payload,'$.portfolio')=?"
        params=(self.key,)
        if anchor is not None:
            query+=' AND rowid>?';params+=(anchor,)
        rows = self.store.db.execute(query+' ORDER BY rowid',params).fetchall()
        raw = cache[4] if state is not None else None
        for rowid,payload in rows:
            state = json.loads(payload)
            revision+=1
            if state['revision']!=revision or state['previous']!=previous or digest({k:v for k,v in state.items() if k!='hash'})!=state['hash']:
                raise ValueError('Inconsistente portefeuille-hashketen')
            previous = state['hash'];anchor=rowid;raw=payload
        if state is None: raise ValueError('Portefeuilletoestand ontbreekt')
        ledger = restore_ledger(state['ledger'],self.policy.decision,self.rules[state['active_rules']])
        self._validate(state,ledger,audit_verified=state['hash'] in getattr(self,'_audit_proofs',()))
        if state.get('valuation')!=self._valuation(state,ledger): raise ValueError('Portefeuillewaardering inconsistent')
        self._remember_audit_proof(state['hash'])
        self.risk.stopped = self.risk.stopped or state['stopped']
        self._chain_prefix=(epoch,anchor,revision,previous,raw)
        return state,ledger

    def _remember_audit_proof(self, state_hash):
        from collections import OrderedDict
        if not hasattr(self,'_audit_proofs'):self._audit_proofs=OrderedDict()
        self._audit_proofs[state_hash]=True;self._audit_proofs.move_to_end(state_hash)
        if len(self._audit_proofs)>8:self._audit_proofs.popitem(last=False)

    def _validate(self, state, ledger, audit_verified=False):
        ledger.reconcile()
        for n in (ledger.cash,ledger.realized,ledger.fees,ledger.peak,ledger.day_start,ledger.last_equity):
            if not n.is_finite(): raise ValueError('Niet-eindige administratie')
        if sum((D(t['net']) for t in ledger.trades),D(0))!=ledger.realized:
            raise ValueError('Gerealiseerd resultaat niet verklaard door transacties')
        fees = sum((D(t['fees']) for t in ledger.trades),D(0)) + (ledger.position.entry_fee if ledger.position else D(0))
        if fees!=ledger.fees: raise ValueError('Kostenadministratie inconsistent')
        if not audit_verified:
            previous = '0'*64
            for index,e in enumerate(ledger.events):
                if e['sequence']!=index or e['previous']!=previous or digest({k:v for k,v in e.items() if k!='hash'})!=e['hash']:
                    raise ValueError('Ledger-auditketen inconsistent')
                previous=e['hash']
        p = ledger.position
        if p and (p.symbol!=state['active_rules'] or p.quantity<=0 or p.average_price<=0 or state['mark'] is None):
            raise ValueError('Inconsistente positie of ontbrekende waardering')
        pending = state['pending']
        if pending:
            amount = D(pending['cash'])
            if not amount.is_finite() or not 0<=amount<=ledger.cash:
                raise ValueError('Ongeldige saldoreservering')
            if pending['side']=='buy':
                if p: raise ValueError('Positie en instapreservering overschrijden limiet')
                risk,exposure=D(pending['risk']),D(pending['exposure'])
                if not all(x.is_finite() and x>=0 for x in (risk,exposure)) or risk>min(D(200),ledger.cash)*self.policy.decision.planned_risk or exposure>ledger.cash*ledger.limits.exposure:
                    raise ValueError('Reservering overschrijdt centraal risico of exposure')
            if pending['side']=='sell' and (not p or D(pending['quantity'])!=p.quantity):
                raise ValueError('Exitreservering overschrijdt bezit')

    def _save(self, before, state, ledger, kind):
        state = dict(state)
        state.update(ledger=ledger_state(ledger),kind=kind,stopped=state['stopped'] or self.risk.stopped,
                     revision=0 if before is None else before['revision']+1,
                     previous='0'*64 if before is None else before['hash'])
        state.pop('hash',None)
        self._validate(state,ledger)
        state['valuation']=self._valuation(state,ledger)
        state['hash']=digest(state)
        self.store.put('joint_states',self.key+':'+str(state['revision']),state)
        self._remember_audit_proof(state['hash'])
        self.store.audit('joint_'+kind,canonical(dict(portfolio=self.key,revision=state['revision'],hash=state['hash'])))

    def _compare(self, before):
        current,_ = self._read()
        if current['hash']!=before['hash']: raise ValueError('Portefeuille gewijzigd; evalueer de gehele batch opnieuw')

    def _bar(self,symbol,opened):
        return self._bar_metadata(symbol,self.bars[symbol])[2].get(opened)

    def _risk_reason(self,candidate,ledger,raw=None):
        # Hergebruik alle fase-5-risicocontroles en dezelfde centrale RiskEngine.
        context = SimpleNamespace(symbol=candidate.coin,policy=self.policy.decision,plan=self.plan)
        return ResearchExecutionEngine(self.store,self.risk,context).reason(candidate,ledger,raw)

    def _valuation(self,state,l):
        mark = D(state['mark']) if state['mark'] is not None else D(1)
        reserved = D(state['pending']['cash']) if state['pending'] else D(0)
        result = l.snapshot(mark)
        value=result['equity']-l.cash
        result.update(mark=mark if state['mark'] is not None else None,exposure=value,
                      exposure_fraction=value/result['equity'] if result['equity']>0 else D(0),
                      fees_by_coin={s:sum((D(t['fees']) for t in l.trades if t['symbol']==s),D(0))+
                                    (l.position.entry_fee if l.position and l.position.symbol==s else D(0)) for s in self.plan.coins})
        result.update(portfolio=self.key,valuation_at=state['at'],reserved_cash=reserved,available_cash=l.cash-reserved,
                      reserved_quantity=state['pending']['quantity'] if state['pending'] else '0',
                      reserved_risk=state['pending'].get('risk','0') if state['pending'] else '0',
                      reserved_exposure=state['pending'].get('exposure','0') if state['pending'] else '0',
                      pending=state['pending'],realized_by_coin={s:sum((D(t['net']) for t in l.trades if t['symbol']==s),D(0)) for s in self.plan.coins},
                      mode='joint_offline_research',max_open_positions=1)
        return json.loads(canonical(result))

    def snapshot(self):
        state,_ = self._read()
        return deepcopy(state['valuation'])

    def stop(self):
        """Duurzame centrale noodstop; geen automatische herstart of hogere limieten."""
        with self.store.transaction():
            before,ledger=self._read()
            self.risk.stopped=True
            state=dict(before);state['stopped']=True
            ledger.audit('joint_emergency_stop',datetime.fromisoformat(state['at']))
            self._save(before,state,ledger,'emergency_stop')

    async def evaluate(self, at):
        try: return await self._evaluate(at)
        except Exception as exc:
            self.store.audit('joint_evaluation_rejected',canonical(dict(portfolio=self.key,at=at,reason=str(exc))))
            raise

    async def _evaluate(self, at):
        utc(at)
        before,ledger = self._read()
        if at>now() or boundary(at,'15m')!=at or not self.plan.development.start<=at<=self.plan.development.end:
            raise ValueError('Uitsluitend afgesloten ontwikkelgrenzen; onafhankelijke test gesloten')
        batch_id = digest(dict(portfolio=self.key,at=at))
        old = self._get('joint_batches',batch_id)
        if old: return old
        if at<datetime.fromisoformat(before['at']): raise ValueError('Terugwaartse portefeuille-evaluatie')
        state = dict(before)
        expired = None
        if state['pending']:
            if state['pending']['side']=='sell': raise ValueError('Open exit eerst expliciet afhandelen')
            expired = state['pending']['batch']
            state['pending']=None
        p = ledger.position
        if p:
            expected = datetime.fromisoformat(state['checked_at'])+timedelta(minutes=15)
            if at!=expected: raise ValueError('Iedere volgende 15m-candle van open positie vereist')
        policy = self.policy.decision
        o = Orchestrator(self.store,evaluation_time=at,reuse_results=True)
        tasks = []
        current_reports=self._reports_at(at)
        for s in self.plan.coins:
            r = next((r for r in current_reports if r.coin==s),None)
            # Signaal op zichzelf; centrale portfolio-/slotcontrole volgt afzonderlijk.
            decision = self._decision(s,at,r)
            view = ledger.analysis_view()
            if not view.position: view.rules=self.rules[s]
            entry = EntryAgent(policy,s,at,view,self._bar(s,at-timedelta(minutes=15)))
            for agent in (decision,entry): o.register(agent.id,agent)
            tasks.extend([Task(decision.id,decision.id),Task(entry.id,entry.id,(decision.id,))])
        if p:
            exit_agent = ExitAgent(policy,p.symbol,at,ledger,self._bar(p.symbol,at-timedelta(minutes=15)),self.risk.stopped)
            o.register(exit_agent.id,exit_agent);tasks.append(Task(exit_agent.id,exit_agent.id))
        accepted = await o.execute(tasks)
        candidates=[]
        rotation = int(at.timestamp())//900 % len(self.plan.coins)
        order = self.plan.coins[rotation:]+self.plan.coins[:rotation]
        # Ontbrekende marktkennis beïnvloedt de hele gelijktijdige selectie: geen
        # instap met een onvolledig of niet-gevalideerd vergelijkingsuniversum.
        source_reports=current_reports
        scanner_ids={r.data.get('dependencies',[])[-1] for r in source_reports if len(r.data.get('dependencies',[]))==5}
        incomplete=len(source_reports)!=len(self.plan.coins) or len(scanner_ids)!=1 or any(len(r.data.get('dependencies',[]))!=5 for r in source_reports)
        for s in self.plan.coins:
            d,e = accepted.get('decision:'+s),accepted.get('entry:'+s)
            score=None
            if d and d.result.get('analysis_validation')=='validated':
                rankings=d.result['contributions']['scanner']['ranking']
                try:
                    score=D(next(r['score'] for r in rankings if r['symbol']==s))
                    if not score.is_finite() or not 0<=score<=100: score=None
                except (ValueError, ArithmeticError, KeyError, StopIteration): score=None
                if score is None: incomplete=True
            else: incomplete=True
            if d and d.result.get('missing'): incomplete=True
            reason = e.result['reason'] if e else 'Agentfout; geen gevalideerd voorstel'
            eligible = bool(d and e and d.result['action']=='BUY_CANDIDATE' and e.result['action']=='ENTRY_CANDIDATE')
            candidates.append(dict(symbol=s,score=str(score) if score is not None else None,tie_priority=order.index(s),
                                   eligible=eligible,selected=False,risk_approved=None,reason=reason,agent_reason=reason,entry=e.model_dump(mode='json') if e else None,
                                   decision=d.model_dump(mode='json') if d else None))
        candidates.sort(key=lambda r:(r['score'] is None,-D(r['score']) if r['score'] is not None else D(0),r['tie_priority']))
        for rank,c in enumerate(candidates,1):
            c.update(rank=rank,ranking_reason=f"scannerscore {c['score']}; dalend; bij gelijkheid UTC-rotatieprioriteit {c['tie_priority']}")
        pending=None
        exit_result=None
        if p:
            bar=self._bar(p.symbol,at-timedelta(minutes=15))
            m=accepted.get('exit:'+p.symbol)
            if bar is None or m is None: raise ValueError('Exitdata of Exit Agent ontbreekt')
            if m.result['action']=='HOLD_POSITION' and m.result['reason']!='Geen exitvoorwaarde geraakt':
                raise ValueError('Onzekere exitcontrole: '+m.result['reason'])
            ledger.observe(at,bar.low);ledger.observe(at,bar.close)
            state.update(mark=str(bar.close),checked_at=at.isoformat())
            reason=self._risk_reason(m,ledger)
            exit_result=dict(candidate=m.model_dump(mode='json'),approved=reason is None,reason=reason or m.result['reason'])
            if m.result['action']=='EXIT_CANDIDATE' and reason is None:
                pending=dict(batch=batch_id,side='sell',candidate=m.model_dump(mode='json'),cash='0',quantity=str(p.quantity))
        for c in candidates:
            if p: c['reason']='centrale positielimiet: één open positie'
            elif incomplete: c['reason']='onvolledig vergelijkingsuniversum; geen nieuwe instap'
            elif c['eligible']:
                view=copy(ledger);view.rules=self.rules[c['symbol']]
                m=Message.model_validate(c['entry'])
                reason=self._risk_reason(m,view)
                c['risk_approved']=reason is None
                if reason: c['reason']=reason
                elif pending: c['reason']='positieplaats en cash gereserveerd voor hoger gerangschikte kandidaat'
                else:
                    r=m.result
                    debit=D(r['quantity'])*D(r['price'])+policy.costs.charge(D(r['quantity']),D(r['price']))
                    if debit>ledger.cash: c['reason']='onvoldoende vrij saldo inclusief kosten'
                    else:
                        c.update(selected=True,reason='centrale Risk Engine akkoord; cash en positieplaats gereserveerd')
                        pending=dict(batch=batch_id,side='buy',candidate=m.model_dump(mode='json'),cash=str(debit),quantity=r['quantity'],risk=r['planned_risk'],exposure=str(D(r['quantity'])*D(r['price'])))
        state.update(pending=pending,at=at.isoformat())
        ledger.audit('joint_evaluated',at,batch=batch_id,selected=pending['candidate']['coin'] if pending else None)
        result=json.loads(canonical(dict(id=batch_id,portfolio=self.key,at=at,priority=self.policy.priority,tie_order=order,
                    candidates=candidates,exit=exit_result,reservation=pending,independent_test_opened=False)))
        state['batch_hash']=digest(result)
        with self.store.transaction():
            old=self._get('joint_batches',batch_id)
            if old: return old
            self._compare(before)
            if expired:
                self.store.put('joint_settlements',expired,dict(portfolio=self.key,batch=expired,success=False,reason='reservering verlopen bij volgende evaluatie',kind='expiry'))
            self.store.put('joint_batches',batch_id,{k:v for k,v in result.items() if k!='id'})
            exposure_id=self.key+':development'
            if not self._get('research_exposures',exposure_id):
                self.store.put('research_exposures',exposure_id,dict(plan=self.plan.fingerprint,coins=self.plan.coins,stage='development',
                               period=self.plan.development.model_dump(mode='json'),viewed_at=now().isoformat(),previously_exposed=True))
            self._save(before,state,ledger,'reserved' if pending else 'evaluated')
        return result

    def execute(self, batch_id):
        try: return self._execute(batch_id)
        except Exception as exc:
            self.store.audit('joint_execution_rejected',canonical(dict(portfolio=self.key,batch=batch_id,reason=str(exc))))
            raise

    def _execute(self,batch_id):
        # Reservering, hercontrole, fill en vrijgave binnen dezelfde transactie.
        with self.store.transaction():
            before,ledger=self._read()
            old=self._get('joint_settlements',batch_id)
            if old:
                if old['portfolio']!=self.key: raise ValueError('Andere portefeuille')
                return dict(old,replay=True)
            pending=before['pending']
            if not pending or pending['batch']!=batch_id: raise ValueError('Geen centrale reservering voor deze batch')
            batch=self._get('joint_batches',batch_id)
            if batch is None or batch['reservation']!=pending or digest(batch)!=before['batch_hash']: raise ValueError('Reservering wijkt af van goedgekeurde batch')
            m=Message.model_validate(pending['candidate'])
            stored=self._get('results',str(m.event_id))
            if stored!=m.model_dump(mode='json'): raise ValueError('Gevalideerde agentherkomst ontbreekt of gewijzigd')
            state=dict(before);at=m.timestamp;r=m.result
            raw=D(r['reference'])
            failure=None
            if pending['side']=='buy':
                if ledger.position: raise ValueError('Positieplaats reeds bezet')
                ledger.rules=self.rules[m.coin];state['active_rules']=m.coin
                bar=self._bar(m.coin,at)
                if bar is None: failure='volgende uitvoeringscandle ontbreekt'
                else: raw=bar.open  # Geen high/low/close van N+1 voor instap.
                price=self.policy.decision.costs.price(raw,'buy',ledger.rules.tick)
                debit=D(r['quantity'])*price+self.policy.decision.costs.charge(D(r['quantity']),price)
                if debit>D(pending['cash']): failure='ongunstige open overschrijdt gereserveerde cash; geen automatische verhoging'
            failure=failure or self._risk_reason(m,ledger,raw)
            if failure:
                success=ledger.reject(batch_id,at,failure)
            elif pending['side']=='buy':
                success=ledger.buy(batch_id,at,raw,D(r['quantity']),D(r['stop']),datetime.fromisoformat(r['deadline']))
            else:
                success=ledger.sell(batch_id,at,raw,r['reason'],r.get('ambiguous',False))
                if success: ledger.trades[-1]['symbol']=m.coin
            if success and pending['side']=='buy': state.update(mark=str(raw),checked_at=at.isoformat())
            if success and pending['side']=='sell': state.update(mark=None,checked_at=None)
            state['pending']=None
            reason=failure or (r['reason'] if success else ledger.events[-1]['details']['reason'])
            result=dict(portfolio=self.key,batch=batch_id,coin=m.coin,side=pending['side'],success=success,reason=reason,
                        kind='fill' if success else 'rejected',cash=str(ledger.cash),realized=str(ledger.realized),fees=str(ledger.fees))
            self.store.put('joint_settlements',batch_id,result)
            self._save(before,state,ledger,'settled')
        return result
