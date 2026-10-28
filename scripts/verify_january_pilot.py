"""Read-only verification of completed pilot; never replay or place a simulated order."""
import sqlite3,json,hashlib
from pathlib import Path
from decimal import Decimal as D
from crypto.january_pilot import ENTRY,END

def verify():
 out=Path('experiments/january_pilot');m=json.loads((out/'manifest.json').read_text());r=json.loads((out/'result.json').read_text())
 assert r['status']=='complete'
 for p,sha in m['files'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha,p
 db=sqlite3.connect('file:/workspace/january_pilot.sqlite3?mode=ro',uri=True)
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 states=[json.loads(x[0]) for x in db.execute('SELECT payload FROM stream_states ORDER BY revision')]
 assert len({s['portfolio'] for s in states})==1
 assert all(D(s['ledger']['cash'])>=0 for s in states)
 events=[json.loads(x[0]) for x in db.execute("SELECT payload FROM stream_history WHERE kind='events' ORDER BY seq")]
 fills=[e for e in events if e['action'] in ('buy','sell')]
 ids=[e['details']['order_id'] for e in fills if e['action']=='buy']+[e['details']['exit_id'] for e in fills if e['action']=='sell']
 assert len(ids)==len(set(ids))==6
 assert all(ENTRY.isoformat()<=e['at']<=END.isoformat() for e in fills)
 trades=[json.loads(x[0]) for x in db.execute("SELECT payload FROM stream_history WHERE kind='trades' ORDER BY seq")]
 assert len(trades)==r['trades']==3
 assert sum((D(t['net']) for t in trades),D(0))==D(r['net'])
 assert sum((D(t['fees']) for t in trades),D(0))==D(r['total_fees'])
 assert D(200)+D(r['net'])==D(r['portfolio']['equity'])
 assert not states[-1]['ledger']['position'] and not states[-1]['pending']
 settlements=[json.loads(x[0]) for x in db.execute('SELECT payload FROM joint_settlements')]
 rejected=[x for x in settlements if not x['success']]
 assert len(settlements)==10 and len(rejected)==4
 assert db.execute('SELECT count(*) FROM orders').fetchone()[0]==0
 db.close()
 h=hashlib.sha256()
 with open('/workspace/january_pilot.sqlite3','rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 evidence={'verified':True,'sqlite_integrity':'ok','one_portfolio':True,'unique_fills':len(ids),'rejected_fills':rejected,'trades':trades,'fill_audit':fills,'last_revision':states[-1]['revision'],'last_state_hash':states[-1]['hash'],'last_checkpoint_hash':states[-1]['checkpoint_hash'],'database_sha256':h.hexdigest(),'database_bytes':Path('/workspace/january_pilot.sqlite3').stat().st_size,'paper_orders':0}
 (out/'verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
 print(json.dumps({k:v for k,v in evidence.items() if k not in ('trades','fill_audit','rejected_fills')},indent=2))
if __name__=='__main__':verify()
