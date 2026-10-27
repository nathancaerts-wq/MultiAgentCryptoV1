import json
import sqlite3
from contextlib import contextmanager
from typing import Protocol
from .models import now

TABLES = ('coins', 'pairs', 'candles', 'agents', 'results', 'regimes', 'hypotheses',
          'strategies', 'proposals', 'risk_decisions', 'orders', 'positions',
          'portfolio_history', 'research_results', 'errors', 'periods', 'datasets', 'data_rejections', 'scan_runs', 'analyses', 'research_plans', 'research_exposures', 'simulation_protocols', 'backtest_runs', 'decision_protocols', 'trade_decisions', 'research_trade_reviews', 'research_fills', 'research_ledger_states', 'joint_protocols', 'joint_states', 'joint_batches', 'joint_settlements')


class Storage(Protocol):
    def put(self, table: str, key: str, value: dict): ...
    def list(self, table: str) -> list[dict]: ...
    def audit(self, action: str, details: str): ...


class SQLiteStore:
    """JSON records met stabiele IDs; adapters kunnen deze repository-interface vervangen."""
    def __init__(self, path=':memory:'):
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA busy_timeout=5000')
        for table in TABLES:
            self.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, payload TEXT NOT NULL CHECK(json_valid(payload)))')
        # Inserts blijven append-only; UPDATE/DELETE maken alle prefixcaches ongeldig.
        self.db.execute('CREATE TABLE IF NOT EXISTS joint_mutation_epoch (singleton INTEGER PRIMARY KEY CHECK(singleton=1), value INTEGER NOT NULL)')
        self.db.execute('INSERT OR IGNORE INTO joint_mutation_epoch VALUES (1,0)')
        for operation in ('UPDATE','DELETE'):
            self.db.execute(f'CREATE TRIGGER IF NOT EXISTS joint_states_{operation.lower()} AFTER {operation} ON joint_states BEGIN UPDATE joint_mutation_epoch SET value=value+1 WHERE singleton=1; END')
        self.db.execute('CREATE TRIGGER IF NOT EXISTS joint_states_nonappend AFTER INSERT ON joint_states WHEN NEW.rowid < (SELECT max(rowid) FROM joint_states) BEGIN UPDATE joint_mutation_epoch SET value=value+1 WHERE singleton=1; END')
        self.db.execute("CREATE INDEX IF NOT EXISTS joint_states_portfolio ON joint_states(json_extract(payload,'$.portfolio'))")
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL, details TEXT NOT NULL)')

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def put(self, table, key, value):
        if table not in TABLES:
            raise ValueError('Onbekende tabel')
        self.db.execute(f'INSERT INTO {table} VALUES (?, ?)', (str(key), json.dumps(value, default=str, allow_nan=False)))

    def list(self, table):
        if table not in TABLES:
            raise ValueError('Onbekende tabel')
        return [dict(id=row[0], **json.loads(row[1])) for row in self.db.execute(f'SELECT id,payload FROM {table} ORDER BY id')]

    def audit(self, action, details):
        self.db.execute('INSERT INTO audit(timestamp,action,details) VALUES (?,?,?)', (now().isoformat(), action, details))

    def agent_status(self, name, status):
        self.db.execute("INSERT INTO agents VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (name, json.dumps({'status': status})))

    def audits(self):
        return [dict(zip(('id','timestamp','action','details'), row)) for row in self.db.execute('SELECT * FROM audit ORDER BY id')]

    def close(self):
        self.db.close()
