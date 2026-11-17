"""Seeded benchmark matrix, explicitly recording failures instead of hiding them."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from warpalign.benchmark import measure,save_report
p=argparse.ArgumentParser()
p.add_argument('--lengths',default='100,500,1000,5000,10000,20000,50000,100000')
p.add_argument('--batches',default='1,4');p.add_argument('--repeats',type=int,default=3)
p.add_argument('--error-rate',type=float,default=.001);p.add_argument('--indel-rate',type=float,default=0)
p.add_argument('--no-fallback',action='store_true')
p.add_argument('--backend',choices=['cpu','cuda','auto'],default='cpu');p.add_argument('--threads',type=int,default=1)
p.add_argument('--mode',choices=['exact','fast'],default='exact');p.add_argument('--bandwidth',type=int,default=64)
p.add_argument('--checkpoint-interval',type=int,default=0);p.add_argument('--output',default='benchmarks/results/local-v020')
a=p.parse_args();rows=[];failures=[]
for n in map(int,a.lengths.split(',')):
 for batch in map(int,a.batches.split(',')):
  for score_only in (False,True):
   try:
    options=dict(length=n,batch_size=batch,repeats=a.repeats,error_rate=a.error_rate,indel_rate=a.indel_rate,backend=a.backend,threads=a.threads,mode=a.mode,bandwidth=a.bandwidth,score_only=score_only,checkpoint_interval=a.checkpoint_interval,allow_fallback=not a.no_fallback)
    run=subprocess.run([sys.executable,'-m','warpalign.benchmark_worker',json.dumps(options)],capture_output=True,text=True,timeout=600)
    if run.returncode:raise RuntimeError(run.stderr[-3000:])
    row=json.loads(run.stdout)
    rows.append(row);print(n,batch,score_only,row['backend'],row['seconds'],flush=True)
   except RuntimeError as error:
    failure=dict(length=n,batch_size=batch,score_only=score_only,error=str(error));failures.append(failure);print(failure,flush=True)
Path(a.output).mkdir(parents=True,exist_ok=True)
Path(a.output,'failures.json').write_text(json.dumps(failures,indent=2))
if rows:save_report(rows,a.output)
if failures:raise SystemExit(1)
