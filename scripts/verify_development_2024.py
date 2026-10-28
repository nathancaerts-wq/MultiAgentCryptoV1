"""Read-only complete-run audit. No simulation, no archive access."""
import json
import sqlite3
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from crypto.development_2024 import START, ENTRY, END, COINS, COSTS, filters, policy, source
from crypto.readiness import dt
from crypto.sim_execution import digest
from scripts.development_2024 import OUT, DB, STEP, file_hash, code_hashes, write


def verify(completed_only=False):
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert manifest['files']==code_hashes()
    db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert db.execute('SELECT count(*) FROM orders').fetchone()[0]==0
    results={}
    for benchmark in ('aligned_trend','ema_trend'):
        for scenario in COSTS:
            name=benchmark+'_'+scenario;p=OUT/(name+'.json')
            if not p.exists():continue
            result=json.loads(p.read_text())
            if result['status']!='complete':continue
            key=result['portfolio']['portfolio'];cash=D(200);held=None;seen=set();fees=D(0);net=D(0);buy_count=sell_count=0
            costs=policy(scenario).decision.costs
            actions=Counter();pauses=[];prev='0'*64
            for i,(raw,) in enumerate(db.execute("SELECT payload FROM stream_history WHERE portfolio=? AND kind='events' ORDER BY seq",(key,))):
                e=json.loads(raw);assert e['previous']==prev and e['sequence']==i
                assert digest({k:v for k,v in e.items() if k!='hash'})==e['hash'];prev=e['hash'];actions[e['action']]+=1
                if 'pause' in e['action'] or 'emergency' in e['action']:pauses.append(e)
                if e['action'] not in ('buy','sell'):continue
                at=dt(e['at']);assert ENTRY<=at<=END
                d=e['details'];q=D(d['quantity']);price=D(d['price'] if e['action']=='buy' else d['exit'])
                rawprice=D(d['raw']);side=e['action'];rule=filters()[d['metadata']['symbol']] if side=='buy' else filters()[held['symbol']]
                assert costs.price(rawprice,side,rule.tick)==price
                assert rule.check(q,price,at) is None
                fee=costs.charge(q,price);fees+=fee
                order_id=d['order_id'] if side=='buy' else d['exit_id'];assert order_id not in seen;seen.add(order_id)
                if side=='buy':
                    assert held is None and fee==D(d['fee'])
                    assert D(d['planned_risk'])<=min(D(200),cash)*D('.005')
                    assert q*price<=cash*D('.5') and q*price+fee<=cash
                    cash-=q*price+fee;buy_count+=1
                    held=dict(symbol=rule.symbol,q=q,entry=price,fee=fee)
                else:
                    assert held and q==held['q']
                    pnl=q*(price-held['entry'])-held['fee']-fee
                    assert pnl==D(d['net']) and held['fee']+fee==D(d['fees'])
                    cash+=q*price-fee;net+=pnl;held=None;sell_count+=1
                assert cash>=0 and cash==D(d['snapshot']['cash'])
            assert held is None and cash==D(result['equity']) and net==D(result['net']) and fees==D(result['fees'])
            assert buy_count==sell_count==result['trades'] and len(seen)==result['unique_fills']
            expected=ENTRY;last_at=None;count=0;prior='0'*64;checkpoint_prior='0'*64
            initial_count=0;state_pauses=Counter()
            for revision,raw in db.execute('SELECT revision,payload FROM stream_states WHERE portfolio=? ORDER BY revision',(key,)):
                s=json.loads(raw);proof=s.pop('checkpoint_hash');assert digest(s)==proof
                assert s['previous']==prior and s['checkpoint_previous']==checkpoint_prior
                prior=s['hash'];checkpoint_prior=proof
                assert D(s['ledger']['cash'])>=0
                if s['kind']=='initial':initial_count+=1;assert D(s['ledger']['cash'])==200;continue
                at=dt(s['at'])
                if at!=last_at:
                    assert at==expected
                    expected+=STEP;count+=1;last_at=at
                for flag in ('day_paused','drawdown_paused'):
                    state_pauses[flag]+=bool(s['ledger'][flag])
                state_pauses['emergency_stopped']+=bool(s['stopped'])
            assert initial_count==1 and expected==END+STEP and count==result['processed_boundaries']
            assert not s['ledger']['position'] and not s['pending']
            assert sum(D(m['net']) for m in result['per_month'].values())==net and len(result['per_month'])==12
            assert sum(D(c['net']) for c in result['per_coin'].values())==net
            results[name]=dict(verified=True,one_initial_portfolio=True,all_boundaries=count,
                unique_fills=len(seen),buy_count=buy_count,sell_count=sell_count,
                final_cash=str(cash),net=str(net),fees=str(fees),audit_actions=dict(actions),
                pause_events=pauses,checkpoint_pause_counts=dict(state_pauses),
                last_state_hash=prior,last_checkpoint_hash=checkpoint_prior)
    accesses=[json.loads(row[0]) for row in db.execute('SELECT payload FROM research_exposures')]
    assert accesses and all(x['stage']=='development' and dt(x['period']['start'])==START and dt(x['period']['end'])==END for x in accesses)
    portfolio_count=db.execute('SELECT count(DISTINCT portfolio) FROM stream_states').fetchone()[0]
    if not completed_only: assert portfolio_count==len(results)==6
    db.close()
    output=dict(verified=True,scope='completed_studies_only' if completed_only else 'all_six_registered_studies',
        incomplete_portfolios=portfolio_count-len(results),studies=results,sqlite_integrity='ok',paper_orders=0,
        access_records=accesses,validation_accessed=False,independent_test_opened=False,
        database_sha256=None if completed_only else file_hash(DB),database_bytes=DB.stat().st_size,
        database_hash_note='Omitted while writer active' if completed_only else 'All replay processes closed',
        verifier_sha256=file_hash(__file__))
    write(OUT/('verification_completed_prefix.json' if completed_only else 'verification.json'),output)
    print(json.dumps({k:v for k,v in output.items() if k not in ('studies','access_records')},indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--completed-only',action='store_true')
    verify(p.parse_args().completed_only)
