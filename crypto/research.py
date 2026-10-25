from datetime import date
from uuid import uuid4


class ResearchOptimizer:
    """Afzonderlijk voorstel/goedkeuringsproces, zonder activatiepad."""
    def __init__(self, store, bounds):
        self.store, self.bounds = store, dict(bounds)

    def hypothesis(self, text):
        if not text.strip():
            raise ValueError('Lege hypothese')
        key = str(uuid4())
        self.store.put('hypotheses', key, {'text': text})
        return key

    def candidate(self, parameters, start: date, end: date, dataset: str, independent=True):
        if start >= end or not dataset.strip() or not parameters:
            raise ValueError('Ongeldig onderzoek')
        if any(k not in self.bounds or not self.bounds[k][0] <= v <= self.bounds[k][1] for k,v in parameters.items()):
            raise ValueError('Buiten onderzoeksbereik')
        key = str(uuid4())
        with self.store.transaction():
            for used in self.store.list('periods'):
                if used['dataset'] == dataset and start.isoformat() < used['end'] and end.isoformat() > used['start'] and independent:
                    raise ValueError('Periode is niet meer onafhankelijk')
            self.store.put('periods', key, {'dataset': dataset, 'start': start.isoformat(), 'end': end.isoformat()})
            self.store.put('research_results', key, {'parameters': parameters, 'status': 'backtest_requested', 'independent': independent})
            self.store.audit('research_candidate', key)
        return key

    def approve(self, key, reviewer, evidence):
        if not reviewer.strip() or not evidence.strip():
            raise ValueError('Reviewer en validatiebewijs vereist')
        if key not in {r['id'] for r in self.store.list('research_results')}:
            raise KeyError(key)
        self.store.put('strategies', key, {'status': 'approved_candidate', 'reviewer': reviewer, 'evidence': evidence, 'active': False})
        self.store.audit('research_approval', key)
