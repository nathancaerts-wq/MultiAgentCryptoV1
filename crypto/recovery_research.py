"""Opt-in synthetic offline recovery. No production policy or risk modification."""
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal as D
from types import SimpleNamespace
from .data import utc
from .analysis import boundary
from .models import Proposal, now
from .joint_portfolio import JointPortfolio
from .research_execution import ResearchExecutionEngine, market_rules
from .sim_execution import digest

PROTOCOL = 'phase6g-recovery24h-v1'


class _RecoveryReview(ResearchExecutionEngine):
    # Baseline _reason copied verbatim except its loss-streak gate. All central
    # RiskEngine calls and financial checks remain; regression test guards drift.
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
        if s.recovery['pause_until'] is not None: return 'verliesreekspauze'
        if s.recovery['resume_at'] and at < datetime.fromisoformat(s.recovery['resume_at']):
            return 'voorstel van vóór hervatting'
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


def initial():
    return dict(protocol=PROTOCOL,epoch=0,epoch_anchor=0,loss_count=0,
                pause_started_at=None,pause_until=None,resume_at=None,
                processed=0,prefix=digest([]),last_close_at=None)


def advance(previous, trades):
    """Pure transition over definitive ledger closes, never fabricated signals."""
    r=deepcopy(previous)
    n=r['processed']
    if len(trades)<n or digest(trades[:n])!=r['prefix']:
        raise ValueError('Gewijzigde definitieve tradeprefix')
    seen={t['exit_id'] for t in trades[:n]}
    if len(seen)!=n: raise ValueError('Dubbele definitieve close')
    for t in trades[n:]:
        at=datetime.fromisoformat(t['exited_at']);utc(at)
        net=D(t['net'])
        if not net.is_finite() or t['exit_id'] in seen:
            raise ValueError('Ongeldige of dubbele close')
        if r['pause_until'] is not None:
            raise ValueError('Onverwachte definitieve trade tijdens afkoeling')
        if r['last_close_at'] and at<datetime.fromisoformat(r['last_close_at']):
            raise ValueError('Teruggedateerde close')
        if r['resume_at'] and at<datetime.fromisoformat(r['resume_at']):
            raise ValueError('Close vóór hervatting')
        seen.add(t['exit_id']);r['last_close_at']=at.isoformat()
        r['loss_count']=r['loss_count']+1 if net<0 else 0
        if r['loss_count']==3:
            r['pause_started_at']=at.isoformat()
            r['pause_until']=(at+timedelta(seconds=86400)).isoformat()
    r['processed']=len(trades);r['prefix']=digest(trades)
    return r


class RecoveryResearchPortfolio(JointPortfolio):
    """Separate opt-in joint ledger; fixture-only until separate historical approval.

    Disabled uses the original namespace, state, review and execution unchanged.
    Enabled state and closes commit in the existing BEGIN IMMEDIATE transaction.
    """
    def __init__(self,store,*,enabled=False,**kwargs):
        self.enabled=enabled
        p=kwargs['plan']
        if enabled:
            if (not p.source.startswith('fixture:') or
                p.development.start.year!=2024 or
                p.development.end>datetime(2025,1,1,tzinfo=p.development.end.tzinfo) or
                set(p.coins)!= {'BTCEUR','ETHEUR','SOLEUR'} or
                kwargs['policy'].decision.hypothesis!='aligned_trend' or
                kwargs['policy'].decision.max_consecutive_losses!=3):
                raise ValueError('Alleen synthetisch 2024 aligned_trend-onderzoek')
            for rows in kwargs['bars'].values():
                if any(not c.source.startswith('fixture:') for c in rows):
                    raise ValueError('Alleen synthetische candles')
            for report in kwargs['reports']:
                if any(not source.startswith('fixture:') for f in report.data['frames'].values() for source in f.get('sources',[])):
                    raise ValueError('Alleen synthetische analyses')
        super().__init__(store,**kwargs)

    def _manifest(self):
        if not self.enabled: return super()._manifest()
        self.key='offline-recovery:'+self.plan.fingerprint
        return super()._manifest()|{'offline_recovery':PROTOCOL,'fixture_only':True}

    def _save(self,before,state,ledger,kind):
        if not self.enabled: return super()._save(before,state,ledger,kind)
        state=dict(state)
        r=state.get('recovery') if kind=='cooldown_expired' else (before['recovery'] if before else initial())
        if before:
            for trade in ledger.trades[r['processed']:]:
                if not datetime.fromisoformat(before['at']) <= datetime.fromisoformat(trade['exited_at']) <= datetime.fromisoformat(state['at']):
                    raise ValueError('Close buiten huidige auditvolgorde')
        updated=advance(r,ledger.trades)
        if updated['pause_until'] and not r['pause_until']:
            ledger.audit('cooldown_started',datetime.fromisoformat(updated['pause_started_at']),
                         protocol=PROTOCOL,epoch=updated['epoch'],until=updated['pause_until'])
        state['recovery']=updated
        super()._save(before,state,ledger,kind)

    def _validate(self,state,ledger,audit_verified=False):
        super()._validate(state,ledger,audit_verified)
        if self.enabled:
            r=state.get('recovery')
            if not isinstance(r,dict) or set(r)!=set(initial()) or r['protocol']!=PROTOCOL:
                raise ValueError('Hersteltoestand ontbreekt')
            if (r['processed']!=len(ledger.trades) or r['prefix']!=digest(ledger.trades) or
                not 0<=r['epoch_anchor']<=r['processed'] or not 0<=r['loss_count']<=3):
                raise ValueError('Inconsistente hersteltoestand')
            suffix=ledger.trades[r['epoch_anchor']:]
            expected=0
            for t in suffix: expected=expected+1 if D(t['net'])<0 else 0
            if expected!=r['loss_count']: raise ValueError('Verliesreeks inconsistent')
            if bool(r['pause_until'])!=(r['loss_count']==3):
                raise ValueError('Pauzetimer inconsistent')
            if r['pause_until'] and (datetime.fromisoformat(r['pause_until'])-
                datetime.fromisoformat(r['pause_started_at'])).total_seconds()!=86400:
                raise ValueError('Verkeerde pauzeduur')

    def _risk_reason(self,candidate,ledger,raw=None):
        if not self.enabled: return super()._risk_reason(candidate,ledger,raw)
        state,_=self._read()
        # No entry in the exit batch, even for a non-loss exit.
        last=state['recovery']['last_close_at']
        if candidate.result.get('action')=='ENTRY_CANDIDATE' and last and candidate.timestamp<=datetime.fromisoformat(last):
            return 'geen instap in exitbatch'
        context=SimpleNamespace(symbol=candidate.coin,policy=self.policy.decision,
                                plan=self.plan,recovery=state['recovery'])
        return _RecoveryReview(self.store,self.risk,context).reason(candidate,ledger,raw)

    async def evaluate(self,at):
        if self.enabled:
            utc(at)
            if boundary(at,'15m')!=at or at>now() or not self.plan.development.contains(at):
                raise ValueError('Ongeldige synthetische beslisgrens')
            with self.store.transaction():
                before,ledger=self._read();r=before['recovery']
                if at<datetime.fromisoformat(before['at']): raise ValueError('Terugwaartse evaluatie')
                if r['pause_until'] and at>=datetime.fromisoformat(r['pause_until']):
                    if ledger.position or before['pending']:
                        raise ValueError('Onverwachte positie of reservering bij expiry')
                    state=deepcopy(before);r=deepcopy(r)
                    r.update(epoch=r['epoch']+1,epoch_anchor=r['processed'],loss_count=0,
                             pause_started_at=None,pause_until=None,resume_at=at.isoformat())
                    state.update(recovery=r,at=at.isoformat())
                    ledger.audit('cooldown_expired',at,protocol=PROTOCOL,epoch=r['epoch'])
                    self._save(before,state,ledger,'cooldown_expired')
        return await super().evaluate(at)
