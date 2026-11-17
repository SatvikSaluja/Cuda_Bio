"""Run identical full/checkpoint workloads and emit a README-ready real table."""
import json
from pathlib import Path
import subprocess
import sys
from warpalign.benchmark import save_report
rows=[]
out=Path('benchmarks/results/judge-v020')
for rate in (.001,.01):
    for length in (1000,10000,100000):
        for checkpoint in (0,128):
            options=dict(length=length,batch_size=1,repeats=3,error_rate=rate,indel_rate=.002,
                         backend='cpu',checkpoint_interval=checkpoint,timeout_seconds=60)
            run=subprocess.run([sys.executable,'-m','warpalign.benchmark_worker',json.dumps(options)],capture_output=True,text=True,timeout=300,check=True)
            row=json.loads(run.stdout);rows.append(row)
            save_report(rows,out) # preserve completed measurements if a later case fails
            print(length,rate,checkpoint,row['seconds'],flush=True)
lines=['| Length | Substitutions | Storage | Median ms | Alignments/s | Peak RSS MiB | Wavefront MiB |',
       '|---:|---:|---|---:|---:|---:|---:|']
for r in rows:
    lines.append(f"| {r['length']:,} | {r['error_rate']:.1%} | {'Checkpoint 128' if r['checkpoint_interval'] else 'Full history'} | {r['seconds']*1000:.2f} | {r['alignments_per_second']:.2f} | {r['process_peak_rss_bytes']/1048576:.2f} | {r['wavefront_bytes']/1048576:.2f} |")
(out/'comparison.md').write_text('\n'.join(lines)+'\n')
