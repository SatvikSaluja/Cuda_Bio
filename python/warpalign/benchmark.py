"""Measured, seeded CPU experiments. CUDA fallback is never counted as GPU throughput."""
import csv
from functools import lru_cache
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path
from . import Aligner, __version__

@lru_cache(maxsize=1)
def hardware():
    cpu = platform.processor()
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                cpu=line.split(':',1)[1].strip();break
    except OSError:
        pass
    try:
        compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0]
    except OSError:
        compiler='unavailable'
    return dict(cpu=cpu,platform=platform.platform(),python=sys.version,compiler=compiler,
                gpu=None,cuda=None,warpalign=__version__)

def measure(length=1000,batch_size=4,mode='exact',bandwidth=64,backend='cpu',repeats=3,error_rate=.01,seed=1729,score_only=False):
    rng=random.Random(seed)
    pairs=[]
    for _ in range(batch_size):
        q=''.join(rng.choice('ACGT') for _ in range(length));t=''.join(rng.choice('ACGT'.replace(b,'')) if rng.random()<error_rate else b for b in q);pairs.append((q,t))
    a=Aligner(backend=backend,mode=mode,bandwidth=bandwidth,score_only=score_only)
    gold=[Aligner(score_only=True).align(q,t).score for q,t in pairs]
    a.align(*pairs[0]) # unmeasured warm-up
    times=[];rows=[]
    for _ in range(repeats):
        start=time.perf_counter();rows=[a.align(q,t) for q,t in pairs];times.append(time.perf_counter()-start)
    median=statistics.median(times)
    return dict(length=length,batch_size=batch_size,mode=mode,bandwidth=bandwidth,requested_backend=backend,
                backend='cpu',score_only=score_only,repeats=repeats,seed=seed,error_rate=error_rate,
                mismatch=4,gap_open=6,gap_extend=2,seconds=median,min_seconds=min(times),max_seconds=max(times),
                raw_seconds=times,alignments_per_second=batch_size/median,bases_per_second=length*batch_size*2/median,
                gpu_memory_bytes=None,wavefront_bytes=max(r.wavefront_bytes for r in rows),
                cpu_fallback_fraction=sum(r.cpu_fallback for r in rows)/batch_size,
                score_agreement=sum(r.score==s for r,s in zip(rows,gold))/batch_size,scores=[r.score for r in rows],
                speedup=None)

def save_report(rows,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    payload=dict(hardware=hardware(),command=sys.argv,provenance='Synthetic substitution-only DNA generated with Python random; seed in each row; original generated data, CC0',measurements=rows)
    (directory/'raw.json').write_text(json.dumps(payload,indent=2))
    with (directory/'raw.csv').open('w') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    # Standalone SVG plot, with real recorded values only.
    max_x=max(r['length'] for r in rows);max_y=max(r['seconds'] for r in rows)
    circles=''.join(f'<circle cx="{50+500*r["length"]/max_x}" cy="{250-200*r["seconds"]/max_y}" r="4"><title>{r["length"]} bp: {r["seconds"]:.6f}s</title></circle>' for r in rows)
    (directory/'runtime.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="620" height="300"><rect width="620" height="300" fill="white"/><path d="M50 40V250H570" stroke="black" fill="none"/><g fill="#087f8c">{circles}</g><text x="50" y="25">Measured CPU batch runtime (seconds; max {max_y:.4f})</text><text x="200" y="280">Sequence length (bp; max {max_x})</text></svg>')
