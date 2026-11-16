import argparse
from warpalign.benchmark import measure,save_report
p=argparse.ArgumentParser();p.add_argument('--lengths',default='100,500,1000,5000,10000,20000,50000,100000');p.add_argument('--batches',default='1,4');p.add_argument('--repeats',type=int,default=3);p.add_argument('--error-rate',type=float,default=.001);p.add_argument('--output',default='benchmarks/results/local');a=p.parse_args()
rows=[]
for n in map(int,a.lengths.split(',')):
 for batch in map(int,a.batches.split(',')):
  for score_only in (False,True):
   row=measure(n,batch,repeats=a.repeats,error_rate=a.error_rate,score_only=score_only);rows.append(row);print(n,batch,score_only,row['seconds'],flush=True)
save_report(rows,a.output)
