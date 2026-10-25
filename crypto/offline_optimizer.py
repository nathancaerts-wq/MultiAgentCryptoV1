"""Preregistratie en gecontroleerde blootstelling aan historische deelverzamelingen."""
from datetime import datetime,timedelta
from .models import now,Message
from .protocol import ResearchPlan,Period,BENCHMARKS,unavailable_performance,report_digest
from .quant import QuantResearcher


class OfflineResearchOptimizer:
    def __init__(self,store): self.store=store

    def mark_external_view(self,coins,period,reason):
        """Registreer ook eerder bekeken datasets buiten deze onderzoeksworkflow."""
        from uuid import uuid4
        period=Period.model_validate(period)
        import re
        coins=tuple(sorted(set(c.replace('/','').upper() for c in coins)))
        if not coins or not reason.strip() or any(not re.fullmatch(r'[A-Z0-9]+EUR',c) for c in coins): raise ValueError('EUR-coins en reden vereist')
        self.store.put('research_exposures',uuid4(),{'plan':'external','stage':'external',
            'coins':tuple(coins),'period':period.model_dump(mode='json'),'reason':reason,
            'viewed_at':now().isoformat(),'previously_exposed':True})
        self.store.audit('research_external_view',reason)

    def _plan(self,key):
        record=next((r for r in self.store.list('research_plans') if r['id']==key),None)
        if record is None: raise KeyError('Plan eerst preregistreren')
        return ResearchPlan.model_validate(record['plan'])

    def register(self,plan):
        plan=ResearchPlan.model_validate(plan.model_dump() if isinstance(plan,ResearchPlan) else plan)
        if any(r['id']==plan.fingerprint for r in self.store.list('research_plans')): return plan.fingerprint
        # Niet alleen dataset-ID: hernoemen van dezelfde marktperiode maakt die niet onafhankelijk.
        with self.store.transaction():
            for exposure in self.store.list('research_exposures'):
                if set(plan.coins)&set(exposure['coins']) and (plan.independent_test.overlaps(Period.model_validate(exposure['period'])) or plan.validation.overlaps(Period.model_validate(exposure['period']))):
                    raise ValueError('Validatie- of onafhankelijke testperiode is al bekeken')
            self.store.put('research_plans',plan.fingerprint,{'plan':plan.model_dump(mode='json'),'registered_at':now().isoformat()})
            self.store.audit('research_preregistered',plan.fingerprint)
        return plan.fingerprint

    def inspect(self,key,stage,reports,dataset_sha256):
        """Bekijk uitsluitend vooraf geregistreerde signalen; geen prestatiesimulatie.

        Testblootstelling wordt vóór resultaatberekening duurzaam vastgelegd, ook
        wanneer invoervalidatie later faalt. Hergebruik is nooit onafhankelijk.
        """
        if stage not in ('development','validation','independent_test'): raise ValueError('Onbekende fase')
        plan=self._plan(key)
        if dataset_sha256!=plan.dataset_sha256: raise ValueError('Dataset wijkt af van preregistratie')
        reports=list(reports)
        expected=plan.report_hashes[('development','validation','independent_test').index(stage)]
        if report_digest(reports)!=expected: raise ValueError('Rapportinhoud wijkt af van preregistratie')
        period=getattr(plan,stage)
        exposure_id=f'{key}:{stage}'
        with self.store.transaction():
            exposures=self.store.list('research_exposures')
            touched=any(set(plan.coins)&set(e['coins']) and period.overlaps(Period.model_validate(e['period'])) for e in exposures)
            if not any(e['id']==exposure_id for e in exposures):
                self.store.put('research_exposures',exposure_id,{'plan':key,'stage':stage,'coins':plan.coins,'period':period.model_dump(mode='json'),'viewed_at':now().isoformat(),'previously_exposed':touched})
            self.store.audit('research_view_started',exposure_id)
        evaluated=[]; rejected=[]; seen=set()
        for raw in reports:
            try:
                report=Message.model_validate(raw)
                at=datetime.fromisoformat(report.data['as_of'])
                if not period.contains(at) or at+timedelta(hours=plan.horizon_hours)>period.end:
                    raise ValueError('Signaal of uitkomsthorizon buiten periode')
                identity=(report.coin,at)
                if identity in seen: raise ValueError('Dubbel coin/tijdstip')
                seen.add(identity)
                evaluated.append(QuantResearcher(plan).evaluate(report,at))
            except Exception as exc: rejected.append({'reason':str(exc)})
        evaluated.sort(key=lambda r:(r['decision_at'],r['coin']))
        names=tuple(plan.hypotheses)+BENCHMARKS
        result={'plan':key,'stage':stage,'period':period.model_dump(mode='json'),
                'independent_test_untouched':False if stage=='independent_test' else not any(set(plan.coins)&set(e['coins']) and plan.independent_test.overlaps(Period.model_validate(e['period'])) for e in self.store.list('research_exposures')),
                'independent_first_view':stage=='independent_test' and not touched,
                'period_previously_exposed':touched,
                'selections':evaluated,'rejections':rejected,
                'performance':{coin:{name:unavailable_performance() for name in names} for coin in plan.coins},
                'walk_forward':plan.walk_forward(),
                'multiple_testing':{'hypotheses':len(plan.hypotheses),'coins':len(plan.coins),'planned_family_size':len(plan.hypotheses)*len(plan.coins),
                    'bonferroni_alpha':str(plan.family_alpha/(len(plan.hypotheses)*len(plan.coins))),
                    'registered_plans':len(self.store.list('research_plans')),'note':'Geen p-waarden of statistisch bewijs berekend; hergebruik en planselectie vereisen aanvullende correctie'},
                'status':'interfaces_only_no_validated_backtest','evidence':'insufficient_evidence'}
        from uuid import uuid4
        self.store.put('research_results',uuid4(),result)
        self.store.audit('research_inspected',exposure_id)
        return result
