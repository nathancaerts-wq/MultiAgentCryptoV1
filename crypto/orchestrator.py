import asyncio
from dataclasses import dataclass
from typing import Protocol
from .models import Message


class Agent(Protocol):
    async def run(self, inputs: tuple[Message, ...]) -> Message: ...


@dataclass(frozen=True)
class Task:
    id: str
    agent: str
    dependencies: tuple[str, ...] = ()


class Orchestrator:
    def __init__(self, store, timeout=5, evaluation_time=None, reuse_results=False):
        if timeout <= 0:
            raise ValueError('Positieve timeout vereist')
        if evaluation_time is not None:
            from .data import utc
            utc(evaluation_time)
        self.reuse_results = reuse_results
        self.evaluation_time = evaluation_time
        self.store, self.timeout = store, timeout
        self.agents, self.paused = {}, set()

    def register(self, name, agent):
        if not name or name in self.agents:
            raise ValueError('Ongeldige of dubbele agent')
        self.agents[name] = agent
        self.store.agent_status(name, 'ready')
        self.store.audit('register', name)

    def pause(self, name):
        if name not in self.agents:
            raise KeyError(name)
        self.paused.add(name)
        self.store.agent_status(name, 'paused')
        self.store.audit('pause', name)

    def resume(self, name):
        if name not in self.agents:
            raise KeyError(name)
        self.paused.discard(name)
        self.store.agent_status(name, 'ready')
        self.store.audit('resume', name)

    def statuses(self):
        return [{'agent_id': n, 'status': 'paused' if n in self.paused else 'ready'} for n in self.agents]

    async def execute(self, tasks):
        tasks = list(tasks)
        pending = {t.id: t for t in tasks}
        if len(pending) != len(tasks):
            raise ValueError('Dubbele taak')
        # Valideer de hele DAG voordat een agent wordt uitgevoerd.
        visited = set()
        while len(visited) < len(tasks):
            ready = [t for t in tasks if t.id not in visited and set(t.dependencies) <= visited]
            if not ready or any(t.agent not in self.agents for t in tasks):
                self.store.audit('invalid_plan', 'Cyclus, ontbrekende afhankelijkheid of agent')
                raise ValueError('Ongeldig taakplan')
            visited.update(t.id for t in ready)
        results, failed = {}, set()
        while pending:
            for key, task in list(pending.items()):
                if not set(task.dependencies) <= (results.keys() | failed):
                    continue
                del pending[key]
                try:
                    if task.agent in self.paused or set(task.dependencies) & failed:
                        raise ValueError('Agent gepauzeerd of afhankelijkheid mislukt')
                    inputs = tuple(results[d].model_copy(deep=True) for d in task.dependencies)
                    if any(not m.usable(self.evaluation_time) for m in inputs):
                        raise ValueError('Verlopen afhankelijkheid')
                    self.store.audit('scheduled', key)
                    raw = await asyncio.wait_for(self.agents[task.agent].run(inputs), self.timeout)
                    message = Message.model_validate(raw.model_dump() if isinstance(raw, Message) else raw)
                    if message.agent_id != task.agent or not message.usable(self.evaluation_time):
                        raise ValueError('Ongeldig, verlopen of verkeerd toegeschreven resultaat')
                    if self.reuse_results:
                        from .models import Message as ResultMessage
                        import json
                        existing = self.store.db.execute('SELECT payload FROM results WHERE id=?', (str(message.event_id),)).fetchone()
                        if existing:
                            previous = ResultMessage.model_validate(json.loads(existing[0]))
                            if previous.model_dump(mode='json') != message.model_dump(mode='json'):
                                raise ValueError('Event-ID inhoudsconflict')
                            results[key] = previous
                            self.store.audit('reused', str(message.event_id))
                            continue
                    with self.store.transaction():
                        self.store.put('results', message.event_id, message.model_dump(mode='json'))
                        self.store.audit('accepted', str(message.event_id))
                    results[key] = message
                except Exception as exc:
                    failed.add(key)
                    self.store.audit('rejected', f'{key}: {type(exc).__name__}')
                    from uuid import uuid4
                    self.store.put('errors', uuid4(), {'task': key, 'error': type(exc).__name__})
        return results
