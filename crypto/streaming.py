"""Disk-backed, fixture-only replay; existing agents/risk/fills remain authoritative.

Input sealing is enforced by SQLite triggers, not by file mtimes. A database owner
who drops triggers is outside this local integrity boundary (as in existing storage).
"""
import hashlib
import json
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal as D

from .data import Candle, utc
from .models import Message, Limits, now
from .joint_portfolio import JointPortfolio, JointPolicy
from .readiness_runner import FixtureJointRunner
from .readiness import LOCKS, admission
from .protocol import ResearchPlan
from .offline_optimizer import OfflineResearchOptimizer
from .risk import RiskEngine
from .research_execution import restore_ledger
from .sim_execution import OfflineLedger, SpotFilters, canonical, digest
from .storage import SQLiteStore


def pieces(value, event_cache=False):
    """Exactly canonical JSON, including spaces, without materialising histories."""
    if isinstance(value, DiskList):
        if event_cache and getattr(value, 'kind', None) == 'events' and not value.pending:
            yield from value.store.event_pieces(value)
            return
        yield '['
        for i, raw in enumerate(value.raws()):
            if i: yield ', '
            yield raw
        yield ']'
    elif isinstance(value, dict):
        yield '{'
        for i, key in enumerate(sorted(value)):
            if i: yield ', '
            yield json.dumps(key) + ': '
            yield from pieces(value[key], event_cache)
        yield '}'
    else:
        yield canonical(value)


def streamed_hash(value, event_cache=False):
    h = hashlib.sha256()
    for part in pieces(value, event_cache): h.update(part if isinstance(part, (bytes,bytearray)) else part.encode())
    return h.hexdigest()


class StreamingStore(SQLiteStore):
    """Persistent bounded SQLite cache; immutable input and append-only checkpoints."""
    def __init__(self, path):
        if str(path) == ':memory:': raise ValueError('Streaming vereist een bestand')
        super().__init__(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA cache_size=-8192')
        self.db.execute('PRAGMA mmap_size=0')
        self.db.execute('PRAGMA temp_store=FILE')
        self.db.execute('PRAGMA wal_autocheckpoint=256')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS stream_input(
            kind TEXT, coin TEXT, tf TEXT, at TEXT, ordinal INTEGER, payload TEXT NOT NULL,
            PRIMARY KEY(kind,coin,tf,at));
        CREATE INDEX IF NOT EXISTS stream_input_order ON stream_input(kind,ordinal);
        CREATE INDEX IF NOT EXISTS stream_input_time ON stream_input(kind,at,ordinal);
        CREATE TABLE IF NOT EXISTS stream_seal(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stream_history(
            portfolio TEXT, kind TEXT, seq INTEGER, payload TEXT NOT NULL,
            PRIMARY KEY(portfolio,kind,seq));
        CREATE TABLE IF NOT EXISTS stream_ids(
            portfolio TEXT, value TEXT, seq INTEGER, PRIMARY KEY(portfolio,value), UNIQUE(portfolio,seq));
        CREATE TABLE IF NOT EXISTS stream_states(
            portfolio TEXT, revision INTEGER, payload TEXT NOT NULL,
            PRIMARY KEY(portfolio,revision));
        ''')
        self.db.execute('CREATE TABLE IF NOT EXISTS stream_hash_epoch (id INTEGER PRIMARY KEY, value INTEGER NOT NULL)')
        self.db.execute('INSERT OR IGNORE INTO stream_hash_epoch VALUES (1,0)')
        for op in ('UPDATE','DELETE'):
            self.db.execute(f'CREATE TRIGGER IF NOT EXISTS stream_hash_{op} AFTER {op} ON stream_history BEGIN UPDATE stream_hash_epoch SET value=value+1 WHERE id=1; END')
        for table in ('stream_input','stream_seal','stream_history','stream_ids','stream_states'):
            for op in ('UPDATE','DELETE'):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only streaming data'); END")
        self.db.execute("CREATE TRIGGER IF NOT EXISTS stream_input_sealed BEFORE INSERT ON stream_input WHEN EXISTS(SELECT 1 FROM stream_seal) BEGIN SELECT RAISE(ABORT,'sealed input'); END")
        for table, group, column in (('stream_history','portfolio=NEW.portfolio AND kind=NEW.kind','seq'),('stream_ids','portfolio=NEW.portfolio','seq'),('stream_states','portfolio=NEW.portfolio','revision')):
            self.db.execute(f"CREATE TRIGGER IF NOT EXISTS {table}_append BEFORE INSERT ON {table} WHEN NEW.{column} != (SELECT coalesce(max({column})+1,0) FROM {table} WHERE {group}) BEGIN SELECT RAISE(ABORT,'non-contiguous append'); END")

    @contextmanager
    def transaction(self):
        # One sequential owner per connection, as for SQLiteStore. Nested agent
        # commits become savepoints inside a single preparation timestamp.
        if not self.db.in_transaction:
            try:
                with super().transaction(): yield
            except BaseException:
                self.__dict__.pop("_event_prefix",None)
                raise
            return
        depth=getattr(self,'_savepoint_depth',0)+1
        self._savepoint_depth=depth
        name=f'stream_savepoint_{depth}'
        self.db.execute(f'SAVEPOINT {name}')
        try:
            yield
            self.db.execute(f'RELEASE {name}')
        except BaseException:
            self.__dict__.pop('_event_prefix',None)
            self.db.execute(f'ROLLBACK TO {name}')
            self.db.execute(f'RELEASE {name}')
            raise
        finally:
            self._savepoint_depth=depth-1

    _event_cache_limit = 2 * 1024 * 1024

    def event_pieces(self, events):
        """Exact JSON bytes; one bounded prefix, anchored to the actual SQL tail.

        Only immutable events are cached. IDs sort globally and cannot use this
        append representation. No digest/context, financial state or proof is cached.
        """
        version=self.db.execute('PRAGMA data_version').fetchone()[0]
        epoch=self.db.execute('SELECT value FROM stream_hash_epoch WHERE id=1').fetchone()[0]
        cache=getattr(self,'_event_prefix',None)
        if cache and cache['epoch']!=epoch:raise ValueError('Auditprefix gewijzigd')
        if cache and cache['key']==events.key and cache['version']==version and cache['count']<=events.count:
            row=self.db.execute("SELECT payload FROM stream_history WHERE portfolio=? AND kind='events' AND seq=?",
                                (events.key,cache['count']-1)).fetchone() if cache['count'] else None
            if cache['count'] and (row is None or row[0]!=cache['tail']):cache=None
        else:cache=None
        if cache is None:
            cache=dict(key=events.key,version=version,epoch=epoch,count=0,size=0,chunks=[],tail=None)
        self._event_prefix=cache
        for (raw,) in self.db.execute("SELECT payload FROM stream_history WHERE portfolio=? AND kind='events' AND seq>=? AND seq<? ORDER BY seq",
                                     (events.key,cache['count'],events.count)):
            data=(b', ' if cache['count'] else b'')+raw.encode()
            if cache['size']+len(data)>self._event_cache_limit:
                self.__dict__.pop('_event_prefix',None)
                yield '['
                for i,raw in enumerate(events.raws()):
                    if i:yield ', '
                    yield raw
                yield ']'
                return
            if not cache['chunks'] or len(cache['chunks'][-1])+len(data)>65536:
                cache['chunks'].append(bytearray())
            cache['chunks'][-1].extend(data)
            cache['size']+=len(data);cache['count']+=1;cache['tail']=raw
        if cache['count']!=events.count:raise ValueError('Auditprefix ontbreekt')
        yield b'['
        yield from cache['chunks']
        yield b']'

    async def prepare_research(self, engine, at, coins):
        """One causal timestamp, all its analyses and reports committed together.

        Caller resumes preparation at the next timestamp after its last committed
        report. Repeated timestamps are rejected, not silently reinterpreted.
        """
        from .analysis import run_research
        if engine.store is not self:raise ValueError('Eén gezamenlijke opslag vereist')
        if self.db.execute('SELECT 1 FROM stream_seal').fetchone():raise ValueError('Invoer reeds verzegeld')
        utc(at)
        if any(a<=at<b for a,b in LOCKS):raise ValueError('Gesloten periode')
        with self.transaction():
            if self.db.execute("SELECT 1 FROM stream_input WHERE kind='report' AND at=?",(at.isoformat(),)).fetchone():
                raise ValueError('Tijdstip reeds voorbereid')
            reports=await run_research(engine,at,coins)
            self.add_reports(reports)
        return reports

    def _accept_source(self, source):
        return source.startswith('fixture:')

    def add_candles(self, kind, rows):
        if kind not in ('bars','history'): raise ValueError('Onbekende invoer')
        with self.transaction():
            for row in rows:
                c = Candle.model_validate(row.model_dump())
                if not self._accept_source(c.source): raise ValueError('Alleen synthetische candles')
                if c.closed > now() or any(c.opened < b and a < c.closed for a,b in LOCKS):
                    raise ValueError('Gesloten periode of onvolledige candle')
                self.db.execute('INSERT INTO stream_input VALUES (?,?,?,?,?,?)',
                    (kind,c.symbol,c.interval,c.opened.isoformat(),None,canonical(c.model_dump(mode='json'))))

    def add_reports(self, reports):
        with self.transaction():
            ordinal = self.db.execute("SELECT count(*) FROM stream_input WHERE kind='report'").fetchone()[0]
            for raw in reports:
                r = Message.model_validate(raw.model_dump())
                at = datetime.fromisoformat(r.data['as_of']); utc(at)
                if any(a<=at<b for a,b in LOCKS): raise ValueError('Gesloten periode')
                for frame in r.data['frames'].values():
                    if any(not self._accept_source(s) for s in frame.get('sources',[])):
                        raise ValueError('Alleen fixtureanalyses')
                self.db.execute('INSERT INTO stream_input VALUES (?,?,?,?,?,?)',
                    ('report',r.coin,'',at.isoformat(),ordinal,canonical(r.model_dump(mode='json'))))
                ordinal += 1

    def report_hash(self):
        h = hashlib.sha256(b'[')
        for i,(raw,) in enumerate(self.db.execute("SELECT payload FROM stream_input WHERE kind='report' ORDER BY payload")):
            if i: h.update(b', ')
            h.update(json.dumps(raw).encode())
        h.update(b']'); return h.hexdigest()

    def input_hash(self):
        h = hashlib.sha256()
        for row in self.db.execute('SELECT kind,coin,tf,at,ordinal,payload FROM stream_input ORDER BY kind,coin,tf,at'):
            h.update(canonical(row).encode()); h.update(b'\n')
        return h.hexdigest()

    def seal(self):
        value = dict(input_hash=self.input_hash(),reports=self.report_hash())
        with self.transaction(): self.db.execute('INSERT INTO stream_seal VALUES (1,?)',(canonical(value),))
        return value

    def verify_inputs(self):
        row = self.db.execute('SELECT payload FROM stream_seal WHERE id=1').fetchone()
        if not row or json.loads(row[0]) != dict(input_hash=self.input_hash(),reports=self.report_hash()):
            raise ValueError('Onvolledige of gewijzigde invoer')
        return json.loads(row[0])

    def candles(self, kind, coin, tf, start=None, end=None):
        query = 'SELECT payload FROM stream_input WHERE kind=? AND coin=? AND tf=?'
        args = (kind,coin,tf)
        if start is not None: query += ' AND at>=?'; args += (start.isoformat(),)
        if end is not None: query += ' AND at<?'; args += (end.isoformat(),)
        for (raw,) in self.db.execute(query+' ORDER BY at',args): yield Candle.model_validate_json(raw)


class DiskList(Sequence):
    """Immutable persisted prefix + tiny transaction-local append buffer."""
    def __init__(self, store, key, kind, count=0):
        self.store,self.key,self.kind,self.count = store,key,kind,count
        self.pending = []

    def __len__(self): return self.count + len(self.pending)

    def raws(self):
        for (raw,) in self.store.db.execute('SELECT payload FROM stream_history WHERE portfolio=? AND kind=? AND seq<? ORDER BY seq', (self.key,self.kind,self.count)):
            yield raw
        for value in self.pending: yield canonical(value)

    def __iter__(self):
        for raw in self.raws(): yield json.loads(raw)

    def __getitem__(self, index):
        if isinstance(index,slice): raise TypeError('Gebruik expliciete begrensde iteratie')
        if index < 0: index += len(self)
        if not 0<=index<len(self): raise IndexError(index)
        if index>=self.count: return self.pending[index-self.count]
        row=self.store.db.execute('SELECT payload FROM stream_history WHERE portfolio=? AND kind=? AND seq=?',(self.key,self.kind,index)).fetchone()
        if row is None: raise ValueError('Historie ontbreekt')
        return json.loads(row[0])

    def append(self, value): self.pending.append(value)

    def flush(self):
        for i,value in enumerate(self.pending,self.count):
            self.store.db.execute('INSERT INTO stream_history VALUES (?,?,?,?)',(self.key,self.kind,i,canonical(value)))
        self.count += len(self.pending); self.pending=[]


class DiskIds:
    def __init__(self, store, key, count=0):
        self.store,self.key,self.count=store,key,count; self.pending=set()
    def __contains__(self,value):
        return value in self.pending or self.store.db.execute('SELECT 1 FROM stream_ids WHERE portfolio=? AND value=? AND seq<?',(self.key,value,self.count)).fetchone() is not None
    def add(self,value):
        if value not in self:self.pending.add(value)
    def flush(self):
        for value in sorted(self.pending):
            self.store.db.execute('INSERT INTO stream_ids VALUES (?,?,?)',(self.key,value,self.count)); self.count+=1
        self.pending=set()


class IdList(DiskList):
    def __init__(self, ids): self.ids=ids
    def raws(self):
        if self.ids.pending: raise ValueError('IDs eerst atomair opslaan')
        for (value,) in self.ids.store.db.execute('SELECT value FROM stream_ids WHERE portfolio=? AND seq<? ORDER BY value',(self.ids.key,self.ids.count)):
            yield canonical(value)


class StreamingFixtureRunner(FixtureJointRunner):
    """Same decision/execution methods, bounded windows and disk history.

    Inputs are streamed to disk and sealed before evaluation. This two-pass design
    preserves preregistered report hashes without retaining the bundle in memory.
    Checkpoints, history appends, fills and reservations share BEGIN IMMEDIATE.
    """
    def _accept_plan(self):
        return self.plan.source.startswith('fixture:')

    def __init__(self, *, store, plan, policy, filters, benchmark='aligned_trend'):
        if not isinstance(store,StreamingStore): raise ValueError('StreamingStore vereist')
        self.store=store
        self.plan=ResearchPlan.model_validate(plan.model_dump())
        self.policy=JointPolicy.model_validate(policy.model_dump())
        self.rules={s:SpotFilters.model_validate(f.model_dump()) for s,f in filters.items()}
        self.benchmark=benchmark
        if benchmark not in ('aligned_trend','ema_trend'): raise ValueError('Onbekende benchmark')
        if not self._accept_plan(): raise ValueError('Historische rendementen niet toegestaan')
        if any(self.plan.development.start<b and a<self.plan.development.end for a,b in LOCKS): raise ValueError('Gesloten periode')
        if set(self.rules)!=set(self.plan.coins): raise ValueError('Filters voor gehele watchlist vereist')
        p=self.policy.decision
        if p.hypothesis not in self.plan.hypotheses or p.planned_risk>self.plan.planned_risk or p.costs.fee!=self.plan.fee or p.costs.slippage!=self.plan.slippage:
            raise ValueError('Beleid wijkt af van onderzoeksplan')
        seal=store.verify_inputs()
        if seal['reports']!=self.plan.report_hashes[0]: raise ValueError('Rapportbundel wijkt af')
        self.key='joint:'+self.plan.fingerprint
        self._input_seal=seal
        self._bar_hashes={}
        ranges=set()
        for s in self.plan.coins:
            if self.rules[s].symbol!=s: raise ValueError('Verkeerde filters')
            h=hashlib.sha256(b'['); first=last=None
            for i,c in enumerate(store.candles('bars',s,'15m')):
                if c.opened<self.plan.development.start or c.closed>self.plan.development.end: raise ValueError('Candle buiten ontwikkeling')
                if last is not None and c.opened!=last: raise ValueError('Datagat op blokgrens')
                if first is None:first=c.opened
                last=c.closed
                if i:h.update(b', ')
                h.update(canonical(c.model_dump(mode='json')).encode())
            if first is None: raise ValueError('Ontbrekende candles')
            h.update(b']');self._bar_hashes[s]=h.hexdigest();ranges.add((first,last))
        if len(ranges)!=1: raise ValueError('Ongelijke candledekking')
        for kind,s,tf in store.db.execute('SELECT DISTINCT kind,coin,tf FROM stream_input'):
            if s not in self.plan.coins or (kind=='bars' and tf!='15m'): raise ValueError('Invoer buiten watchlist/timeframe')
        for (raw,) in store.db.execute("SELECT payload FROM stream_input WHERE kind='report'"):
            r=Message.model_validate_json(raw);at=datetime.fromisoformat(r.data['as_of'])
            if not self.plan.development.contains(at) or at+timedelta(hours=4)>self.plan.development.end:
                raise ValueError('Rapport buiten ontwikkelhorizon')
        # Bind the same financial policy; storage uses a separate versioned manifest.
        self.risk=RiskEngine(Limits(),Limits(trade_risk=p.planned_risk))
        self.manifest=self._manifest()
        OfflineResearchOptimizer(store).register(self.plan)
        with store.transaction():
            old=self._get('joint_protocols',self.key)
            if old is not None and old!=self.manifest: raise ValueError('Protocol gewijzigd')
            if old is None:
                store.put('joint_protocols',self.key,self.manifest)
                ledger=OfflineLedger(p.costs,self.rules[self.plan.coins[0]],p.planned_risk)
                ledger.events=DiskList(store,self.key,'events');ledger.trades=DiskList(store,self.key,'trades');ledger.curve=DiskList(store,self.key,'curve');ledger.ids=DiskIds(store,self.key)
                ledger.audit('joint_started',self.plan.development.start,cash=D(200),coins=self.plan.coins)
                state=dict(portfolio=self.key,at=self.plan.development.start.isoformat(),checked_at=None,active_rules=self.plan.coins[0],mark=None,pending=None,stopped=False)
                self._save(None,state,ledger,'initial')
        self.verify_history()
        self._read()

    def _manifest(self):
        # Separate storage identity. Report/plan IDs, execution rules and audit
        # state hashes remain the same. Full history cannot be in every manifest.
        return dict(plan=self.plan.fingerprint,policy=self.policy.model_dump(mode='json'),
                    filters={s:self.rules[s].model_dump(mode='json') for s in sorted(self.rules)},
                    reports=self._input_seal['reports'],bars=self._bar_hashes,
                    stage='development',independent_test_authorization=None,
                    technical_fixture_only=True,benchmark=self.benchmark,
                    streaming_input=self._input_seal['input_hash'],format='stream-v1')

    def _reports_at(self, at):
        return tuple(Message.model_validate_json(raw) for (raw,) in self.store.db.execute("SELECT payload FROM stream_input WHERE kind='report' AND at=? ORDER BY ordinal",(at.isoformat(),)))

    def _bar(self,symbol,opened):
        return next(self.store.candles('bars',symbol,'15m',opened,opened+timedelta(minutes=15)),None)

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
        return JointPortfolio._risk_reason(self,candidate,ledger,raw)

    def _ledger_value(self,ledger):
        values={k:v for k,v in vars(ledger).items() if k not in ('costs','rules','limits','position','ids')}
        values['position']=asdict(ledger.position) if ledger.position else None
        values['ids']=IdList(ledger.ids)
        return values

    def _save(self,before,state,ledger,kind):
        # Called only inside the existing atomic portfolio transaction.
        if not self.store.db.in_transaction: raise ValueError('Atomische transactie vereist')
        self._validate(state,ledger,audit_verified=True)
        previous=ledger.events[ledger.events.count-1]['hash'] if ledger.events.count else '0'*64
        for i,e in enumerate(ledger.events.pending,ledger.events.count):
            if e['sequence']!=i or e['previous']!=previous or digest({k:v for k,v in e.items() if k!='hash'})!=e['hash']:raise ValueError('Ledger-auditketen inconsistent')
            previous=e['hash']
        for name in ('events','trades','curve','ids'):getattr(ledger,name).flush()
        state=dict(state)
        state.update(ledger=self._ledger_value(ledger),kind=kind,stopped=state['stopped'] or self.risk.stopped,
                     revision=0 if before is None else before['revision']+1,previous='0'*64 if before is None else before['hash'])
        state.pop('hash',None);state['valuation']=self._valuation(state,ledger)
        state['hash']=streamed_hash(state, event_cache=True)
        compact=dict(state);compact['ledger']=dict(state['ledger'])
        for name in ('events','trades','curve','ids'):
            compact['ledger'][name]={'count':getattr(ledger,name).count}
        compact=json.loads(canonical(compact))
        prior=self.store.db.execute('SELECT payload FROM stream_states WHERE portfolio=? ORDER BY revision DESC LIMIT 1',(self.key,)).fetchone()
        compact['checkpoint_previous']=json.loads(prior[0])['checkpoint_hash'] if prior else '0'*64
        compact['checkpoint_hash']=digest(compact)
        self.store.db.execute('INSERT INTO stream_states VALUES (?,?,?)',(self.key,state['revision'],canonical(compact)))
        self.store.audit('joint_'+kind,canonical(dict(portfolio=self.key,revision=state['revision'],hash=state['hash'])))

    def _decode(self,compact):
        counts={k:compact['ledger'][k]['count'] for k in ('events','trades','curve','ids')}
        base=dict(compact['ledger'])
        for name in counts:base[name]=[]
        ledger=restore_ledger(base,self.policy.decision,self.rules[compact['active_rules']])
        for name in ('events','trades','curve'):setattr(ledger,name,DiskList(self.store,self.key,name,counts[name]))
        ledger.ids=DiskIds(self.store,self.key,counts['ids'])
        state={k:v for k,v in compact.items() if k not in ('checkpoint_hash','checkpoint_previous')}
        state['ledger']=self._ledger_value(ledger)
        return state,ledger

    def _read(self):
        self._frozen()
        row=self.store.db.execute('SELECT payload FROM stream_states WHERE portfolio=? ORDER BY revision DESC LIMIT 1',(self.key,)).fetchone()
        if row is None:raise ValueError('Checkpoint ontbreekt')
        compact=json.loads(row[0]);proof=compact.pop('checkpoint_hash')
        if digest(compact)!=proof:raise ValueError('Checkpoint gewijzigd')
        state,ledger=self._decode(compact)
        self._validate(state,ledger,audit_verified=True)
        if state['valuation']!=self._valuation(state,ledger):raise ValueError('Portefeuillewaardering inconsistent')
        self.risk.stopped=self.risk.stopped or state['stopped']
        return state,ledger

    def verify_history(self):
        """Bounded full verification on reopen, before trusting immutable prefixes."""
        previous='0'*64
        for i,(raw,) in enumerate(self.store.db.execute("SELECT payload FROM stream_history WHERE portfolio=? AND kind='events' ORDER BY seq",(self.key,))):
            e=json.loads(raw)
            if e['sequence']!=i or e['previous']!=previous or digest({k:v for k,v in e.items() if k!='hash'})!=e['hash']:raise ValueError('Ledger-auditketen inconsistent')
            previous=e['hash']
        previous='0'*64
        checkpoint_previous='0'*64
        last=None
        for revision,raw in self.store.db.execute('SELECT revision,payload FROM stream_states WHERE portfolio=? ORDER BY revision',(self.key,)):
            c=json.loads(raw);proof=c.pop('checkpoint_hash')
            if digest(c)!=proof or c['revision']!=revision or c['previous']!=previous or c['checkpoint_previous']!=checkpoint_previous:raise ValueError('Checkpointketen inconsistent')
            previous=c['hash'];checkpoint_previous=proof;last=c
        if last is None:raise ValueError('Checkpoint ontbreekt')
        state,ledger=self._decode(last)
        if streamed_hash({k:v for k,v in state.items() if k!='hash'})!=state['hash']:raise ValueError('Historie wijkt af van checkpoint')
        for name in ('events','trades','curve','ids'):
            table='stream_ids' if name=='ids' else 'stream_history'
            query=f'SELECT count(*) FROM {table} WHERE portfolio=?';args=(self.key,)
            if name!='ids':query+=' AND kind=?';args+=(name,)
            if self.store.db.execute(query,args).fetchone()[0]!=getattr(ledger,name).count:raise ValueError('Niet-gecommitteerde historie')

    async def run(self, times):
        """Compatibility for small blocks; stream() is the unbounded iterator API."""
        from itertools import islice
        block=list(islice(iter(times),101))
        if len(block)>100:raise ValueError('Maximaal 100 stappen per block; gebruik stream')
        return await super().run(block)

    async def stream(self,times):
        """Yield one snapshot; caller must consume, not accumulate, long runs.

        Replaying the last timestamp resolves a pending reservation exactly once.
        An interrupted later step is retried from the durable last checkpoint.
        """
        for at in times:
            yield (await super().run((at,)))[0]
