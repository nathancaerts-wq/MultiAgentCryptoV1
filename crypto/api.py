from fastapi import FastAPI
from .storage import SQLiteStore
from .orchestrator import Orchestrator
from .risk import PortfolioManager
from .models import Limits
from .agents import COMPONENTS


def create_app(store=None):
    store = store or SQLiteStore(':memory:')
    orchestrator = Orchestrator(store)
    portfolio = PortfolioManager(store)
    app = FastAPI(title='MultiAgentCryptoV1 — onderzoek en paper infrastructuur')
    app.state.store, app.state.orchestrator = store, orchestrator

    @app.get('/health')
    def health():
        store.db.execute('SELECT 1').fetchone()
        return {'status': 'ok', 'mode': 'paper-only', 'live_execution': False}

    @app.get('/agents')
    def agents():
        return {'registered': orchestrator.statuses(), 'interfaces': COMPONENTS}

    @app.get('/portfolio')
    def account():
        return portfolio.snapshot()

    @app.get('/risk-limits')
    def limits():
        return {'hard': Limits().model_dump(mode='json'), 'operational': Limits().model_dump(mode='json')}

    @app.get('/audit')
    def audit():
        return store.audits()

    @app.get('/scanner')
    def scanner():
        from .models import Message
        return [dict(record, usable=Message.model_validate({k:v for k,v in record.items() if k != 'id'}).usable())
                for record in store.list('scan_runs')]

    @app.get('/analyses')
    def analyses():
        from .models import Message
        return [dict(record, usable=Message.model_validate({k:v for k,v in record.items() if k != 'id'}).usable())
                for record in store.list('analyses')]

    def reader(table):
        def read():
            return store.list(table)
        return read

    for route, table in {'coins': 'pairs', 'market': 'regimes', 'signals': 'results', 'research': 'research_results', 'errors': 'errors', 'candles': 'candles', 'data-quality': 'data_rejections', 'backtests': 'backtest_runs', 'simulation-protocols': 'simulation_protocols', 'decisions': 'trade_decisions', 'research-trade-reviews': 'research_trade_reviews', 'research-fills': 'research_fills'}.items():
        app.add_api_route('/'+route, reader(table), methods=['GET'])
    return app
