"""Run a protocol-compatible external baseline on exactly the same synthetic pairs."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import time
from warpalign import Aligner
from warpalign.benchmark import generate_pairs,hardware

def run(command,pairs):
    start=time.perf_counter()
    output=subprocess.run(command,input=''.join(q+'\t'+t+'\n' for q,t in pairs),text=True,capture_output=True,check=True,timeout=600)
    wall=time.perf_counter()-start
    rows=[json.loads(line) for line in output.stdout.splitlines()]
    if len(rows)!=len(pairs):raise ValueError('External adapter returned the wrong result count')
    return rows,wall

def main():
    p=argparse.ArgumentParser();p.add_argument('--length',type=int,default=1000);p.add_argument('--pairs',type=int,default=16)
    p.add_argument('--repeats',type=int,default=5);p.add_argument('--error-rate',type=float,default=.01);p.add_argument('--indel-rate',type=float,default=.01)
    p.add_argument('--seed',type=int,default=1729);p.add_argument('--output',default='benchmarks/results/external.json')
    p.add_argument('--baseline-version',required=True);p.add_argument('adapter',nargs=argparse.REMAINDER);a=p.parse_args()
    if not a.adapter or a.repeats<1 or a.pairs<1:p.error('Adapter command and positive repeat/pair counts required')
    # Catch incompatible score/sign conventions before reporting performance.
    checks,_=run(a.adapter,[('A','T'),('A','AA'),('ACGT','ACGT')])
    if [r['score'] for r in checks]!=[4,8,0]:raise ValueError('Baseline scoring does not match x=4,o=6,e=2')
    pairs=generate_pairs(a.length,a.pairs,a.error_rate,a.indel_rate,a.seed);cpu=Aligner(backend='cpu')
    expected=[cpu.align(q,t).score for q,t in pairs]
    run(a.adapter,pairs) # warm-up, excluded
    cpu.align_batch([q for q,t in pairs],[t for q,t in pairs])
    runs=[]
    for _ in range(a.repeats):
        rows,wall=run(a.adapter,pairs)
        if [r['score'] for r in rows]!=expected:raise ValueError('Baseline score disagreement')
        start=time.perf_counter();cpu.align_batch([q for q,t in pairs],[t for q,t in pairs]);cpu_wall=time.perf_counter()-start
        runs.append(dict(external_process_seconds=wall,external_engine_seconds=sum(r['seconds'] for r in rows),warpalign_batch_seconds=cpu_wall))
    result=dict(hardware=hardware(),arguments=vars(a),scores=expected,runs=runs,
                note='Process wall time includes startup and parsing. Engine time is adapter-reported; no automatic speedup claim.',
                medians={k:statistics.median(r[k] for r in runs) for k in runs[0]})
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2))

if __name__=='__main__':main()
