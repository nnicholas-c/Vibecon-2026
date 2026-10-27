import sys, time; sys.path.insert(0,'/app/backend')
from datetime import date
from collections import defaultdict
from seed.build import build_seed
from engine.jobs import seed_jobs
from engine.insertion import run_engine
from engine.matrix import make_travel
from engine.timing import fmt_time
dd=date(2026,10,24)
d=build_seed(dd, []); s=d['businesses'][0]['settings']
acc=defaultdict(list)
for r in d['run_history']: acc[r['stop_key']].append(r['actual_service_minutes'])
sm={k:round(sum(v)/len(v),2) for k,v in acc.items()}
ctx=[]
for u in d['units']:
    st=sorted([dict(x, service_minutes=sm[x['key']]) for x in d['stops'] if x['unit_key']==u['key']], key=lambda x:x['seq'])
    ctx.append((u,st))
tr=make_travel(s)
jobs=seed_jobs(dd)
for n,j in jobs.items():
    if j['job_status']!='ready': print(n, 'CANT', j['job_reason']); continue
    job=j['job']; f=job['frequency']; same = f['type']=='one_off' and f['date']==dd.isoformat()
    t=time.perf_counter(); out=run_engine(ctx, job, s, tr, 600, same); ms=(time.perf_counter()-t)*1000
    print(f"#{n} {ms:.0f}ms", j['job_summary'])
    for r in out['results']:
        if r['feasible']: print('   ', r['unit_name'], r['added_minutes'], r['added_miles'], r['added_cost'], r['price'], [x['arrival_label']+'@'+x['after'] for x in r['new_stops']])
        else: print('   ', r['unit_name'], r['reason'], r['where'])
    w=out['winner']
    if w: print('  WIN', w['explanation'], '|', w['pass_by']['line'], '|', w['market_line'], '|', w['hand_check'])
    if out['shifted']: 
        sh=out['shifted']; print('  SHIFT', sh['line'], sh.get('winner',{}).get('explanation'))
