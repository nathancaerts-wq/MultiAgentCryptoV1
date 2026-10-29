"""Explicitly approved 2024-only offline recovery adapter; separate database."""
from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace
from decimal import Decimal as D
from .analysis import boundary
from .data import utc
from .models import now
from .readiness import admission
from .development_2024 import DevelopmentStore, COINS, START, ENTRY, END, policy, filters
from .streaming import StreamingFixtureRunner
from .recovery_research import PROTOCOL, initial, advance, _RecoveryReview
from .sim_execution import digest

SOURCE='assumption:phase6h-b:recovery24h:2024:baseline-costs'

class RecoveryStore(DevelopmentStore):
    pass

class HistoricalRecoveryRunner(StreamingFixtureRunner):
    enabled=True

    def _accept_plan(self):
        return (type(self.store) is RecoveryStore and self.plan.source==SOURCE and
                self.plan.coins==COINS and self.plan.development.start==START and
                self.plan.development.end==END and self.plan.hypotheses==('aligned_trend',) and
                self.policy==policy('baseline') and self.rules==filters() and
                self.benchmark=='aligned_trend')

    def _manifest(self):
        self.key='historical-recovery:'+self.plan.fingerprint
        return super()._manifest()|{'technical_fixture_only':False,
                'recovery_protocol':PROTOCOL,'hypothetical_filters':True,
                'authorization_scope':'phase6h-b-explicit-hypothetical-filters',
                'entries_from':ENTRY.isoformat()}

    def _save(self,before,state,ledger,kind):
        state=dict(state)
        r=state.get('recovery') if kind=='cooldown_expired' else (before['recovery'] if before else initial())
        if before:
            for trade in list(ledger.trades)[r['processed']:]:
                if not datetime.fromisoformat(before['at']) <= datetime.fromisoformat(trade['exited_at']) <= datetime.fromisoformat(state['at']):
                    raise ValueError('Close buiten huidige auditvolgorde')
        updated=advance(r,list(ledger.trades))
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
            if (r['processed']!=len(ledger.trades) or r['prefix']!=digest(list(ledger.trades)) or
                not 0<=r['epoch_anchor']<=r['processed'] or not 0<=r['loss_count']<=3):
                raise ValueError('Inconsistente hersteltoestand')
            suffix=list(ledger.trades)[r['epoch_anchor']:]
            expected=0
            for t in suffix: expected=expected+1 if D(t['net'])<0 else 0
            if expected!=r['loss_count']: raise ValueError('Verliesreeks inconsistent')
            if bool(r['pause_until'])!=(r['loss_count']==3):
                raise ValueError('Pauzetimer inconsistent')
            if r['pause_until'] and (datetime.fromisoformat(r['pause_until'])-
                datetime.fromisoformat(r['pause_started_at'])).total_seconds()!=86400:
                raise ValueError('Verkeerde pauzeduur')

    def _risk_reason(self,candidate,ledger,raw=None):
        if candidate.result.get('action')=='ENTRY_CANDIDATE':
            at=candidate.timestamp
            if at+timedelta(hours=4,minutes=15)>self.plan.development.end:return 'periode-einde'
            # Match the reference's missing-key reason, including exact text.
            known=self.store.db.execute("SELECT 1 FROM stream_input WHERE kind='history' AND coin=?",(candidate.coin,)).fetchone()
            if not known:return 'toelatingshistorie ontbreekt: '+str(KeyError(candidate.coin))
            frames={}
            for tf in ('15m','1h'):
                end=at if tf=='15m' else at.replace(minute=0,second=0,microsecond=0)
                known=self.store.db.execute("SELECT 1 FROM stream_input WHERE kind='history' AND coin=? AND tf=?",(candidate.coin,tf)).fetchone()
                if not known:return 'toelatingshistorie ontbreekt: '+str(KeyError(tf))
                frames[tf]=list(self.store.candles('history',candidate.coin,tf,end-timedelta(days=7),end))
            try:
                reason=admission(frames,candidate.coin,at)
                if reason:return reason
            except (ValueError,KeyError) as exc:return 'toelatingshistorie ontbreekt: '+str(exc)
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
            if boundary(at,'15m')!=at or at>now() or not ENTRY<=at<=END:
                raise ValueError('Ongeldige synthetische beslisgrens')
            with self.store.transaction():
                before,ledger=self._read();r=before['recovery']
                if at<datetime.fromisoformat(before['at']): raise ValueError('Terugwaartse evaluatie')
                if r['pause_until'] and at>=datetime.fromisoformat(r['pause_until']):
                    if ledger.position or before['pending']:
                        raise ValueError('Onverwachte positie of reservering bij expiry')
                    state=dict(before);r=deepcopy(r)
                    r.update(epoch=r['epoch']+1,epoch_anchor=r['processed'],loss_count=0,
                             pause_started_at=None,pause_until=None,resume_at=at.isoformat())
                    state.update(recovery=r,at=at.isoformat())
                    ledger.audit('cooldown_expired',at,protocol=PROTOCOL,epoch=r['epoch'])
                    self._save(before,state,ledger,'cooldown_expired')
        return await super().evaluate(at)
