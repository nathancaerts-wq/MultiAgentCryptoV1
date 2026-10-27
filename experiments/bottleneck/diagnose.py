"""Diagnostiek; uitsluitend synthetisch, maximaal 200 stappen; geen productiewijzigingen."""
import asyncio,cProfile,json,pstats,resource,time,sys,ast,signal,os
from collections import Counter
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from crypto.analysis import run_research
from crypto.data import Candle,DataEngine,SECONDS
from crypto.readiness import dt
from crypto.readiness_runner import FixtureJointRunner
from crypto.joint_portfolio import JointPolicy
from crypto.protocol import ResearchPlan,Period,report_digest
from crypto.sim_execution import SpotFilters
from crypto.storage import SQLiteStore

COINS=('BTCEUR','ETHEUR','SOLEUR');EPOCH=dt('2024-01-01');AT=dt('2024-01-08')

def candle(s,tf,t):
 values=[]
 for i in range(SECONDS[tf]//900):
  h=int((t-EPOCH).total_seconds())//3600+i//4
  values.append(D(100)+D(h)*D('.2')+(D(0),D(1),D(-1),D('.2'))[h%4])
 return Candle(symbol=s,interval=tf,opened=t,closed=t+timedelta(seconds=SECONDS[tf]),open=values[0],high=max(values)+1,low=min(values)-1,close=values[-1],volume=1000*len(values),quote_volume=100000*len(values),source='fixture:bottleneck-v1')

class Synthetic:
 def fetch(self,s,tf,start,end):
  return [candle(s,tf,start+timedelta(seconds=i*SECONDS[tf])) for i in range(int((end-start).total_seconds())//SECONDS[tf])]

def main(n,mode):
 assert n in (50,100,200) and mode in ('empty','chain')
 out=Path('experiments/bottleneck')/f'{mode}_{n}'
 prof=cProfile.Profile();queries=Counter();technical_windows=Counter();members=Counter();phase='setup'
 # Profile callback telt aanroepen zonder code/agenten te vervangen.
 def sql(statement):queries[(phase,statement.split()[0].upper())]+=1
 import crypto.analysis as analysis
 original=analysis.technical
 def counted(rows,config):
  technical_windows[(rows[0].symbol,rows[0].interval,rows[0].opened.isoformat(),rows[-1].closed.isoformat())]+=1
  for c in rows:members[(c.symbol,c.interval,c.opened.isoformat())]+=1
  return original(rows,config)
 analysis.technical=counted
 prof.enable();begun=time.perf_counter();store=SQLiteStore();store.db.set_trace_callback(sql)
 timings={};step_times=[];reports=[];engine=DataEngine(store,Synthetic())
 def interrupted(*_):
  prof.disable();prof.dump_stats(str(out)+'.partial.prof')
  partial=dict(n_requested=n,mode=mode,status='timeout',phase=phase,elapsed=time.perf_counter()-begun,completed_step_times=step_times,phases_completed=timings,technical_calls=sum(technical_windows.values()),unique_windows=len(technical_windows),queries={str(k):v for k,v in queries.items()})
  Path(str(out)+'.partial.json').write_text(json.dumps(partial,indent=2)+'\n')
  os._exit(124)
 signal.signal(signal.SIGTERM,interrupted)

 bars={s:[candle(s,'15m',AT+timedelta(minutes=15*i)) for i in range(-1,n+18)] for s in COINS}
 timings['setup']=time.perf_counter()-begun
 phase='analysis';t=time.perf_counter()
 async def analyses():
  for i in range(n):
   x=time.perf_counter();reports.extend(await run_research(engine,AT+timedelta(minutes=15*i),COINS));step_times.append(time.perf_counter()-x)
 if mode=='chain':asyncio.run(analyses())
 timings[phase]=time.perf_counter()-t;analysis_steps=step_times[:];step_times=[]
 phase='initialize';t=time.perf_counter()
 plan=ResearchPlan(coins=COINS,source='fixture:bottleneck-v1',dataset_sha256='1'*64,report_hashes=(report_digest(reports),report_digest([]),report_digest([])),development=Period(start=AT-timedelta(minutes=15),end=AT+timedelta(days=4)),validation=Period(start=dt('2025-02-01'),end=dt('2025-03-01')),independent_test=Period(start=dt('2026-01-01'),end=dt('2026-10-01')))
 rules={s:SpotFilters(symbol=s,source='fixture:bottleneck-v1',status='assumed',note='synthetic',tick='.01',min_qty='.001',max_qty='1000',step='.001') for s in COINS}
 runner=FixtureJointRunner(store=store,plan=plan,policy=JointPolicy(),filters=rules,reports=reports,bars=bars)
 timings[phase]=time.perf_counter()-t;phase='replay';t=time.perf_counter()
 sizes=[]
 async def replay():
  for i in range(n):
   x=time.perf_counter();await runner.run([AT+timedelta(minutes=15*i)]);step_times.append(time.perf_counter()-x)
   # Metingen buiten het SQL-traceprofiel om tellers niet te vervuilen.
   if i in (0,49,99,199):
    state,l=runner._read();sizes.append(dict(step=i+1,events=len(l.events),state_bytes=len(json.dumps(state)),reports=len(reports)))
 asyncio.run(replay());timings[phase]=time.perf_counter()-t
 prof.disable();prof.dump_stats(str(out)+'.prof');store.db.set_trace_callback(None)
 rows=[];names={}
 for (file,line,fn),v in pstats.Stats(prof).stats.items():
  if file not in names:
   names[file]={}
   if Path(file).is_file() and file.endswith('.py'):
    try:
     for cls in ast.parse(Path(file).read_text()).body:
      if isinstance(cls,ast.ClassDef):
       for f in cls.body:
        if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)):names[file][f.lineno]=cls.name+'.'+f.name
    except (OSError,SyntaxError):pass
  name=names[file].get(line,fn)
  rows.append(dict(file=file,line=line,function=name,primitive_calls=v[0],calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]))
 rows.sort(key=lambda r:-r['cumulative_seconds'])
 result=dict(n=n,mode=mode,elapsed_profiled=sum(timings.values()),phases=timings,replay_steps=step_times,analysis_steps=analysis_steps,sql={p:{op:c for (ph,op),c in queries.items() if ph==p} for p in set(x[0] for x in queries)},technical_calls=sum(technical_windows.values()),unique_windows=len(technical_windows),repeated_identical_windows=sum(v-1 for v in technical_windows.values()),candle_visits=sum(members.values()),unique_analyzed_candles=len(members),max_visits_same_candle=max(members.values(),default=0),sizes=sizes,profile=rows,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,trades=len(runner._read()[1].trades))
 Path(str(out)+'.json').write_text(json.dumps(result,indent=2)+'\n')
 analysis.technical=original;store.close();print(mode,n,round(result['elapsed_profiled'],3),flush=True)
if __name__=='__main__':main(int(sys.argv[1]),sys.argv[2])
