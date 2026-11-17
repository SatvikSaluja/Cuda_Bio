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
import hashlib
from .reference import affine_score
from .diagnostics import capabilities
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
                gpu=capabilities()["gpu"],cuda=capabilities()["cuda_version"],warpalign=__version__)

def generate_pairs(length,batch_size,error_rate,indel_rate,seed):
    rng=random.Random(seed);pairs=[]
    for _ in range(batch_size):
        q=''.join(rng.choice('ACGT') for _ in range(length));t=[]
        for base in q:
            if rng.random()<indel_rate/2:t.append(rng.choice('ACGT'))
            if rng.random()<indel_rate/2:continue
            t.append(rng.choice('ACGT'.replace(base,'')) if rng.random()<error_rate else base)
        pairs.append((q,''.join(t)))
    return pairs

def measure(length=1000,batch_size=4,mode='exact',bandwidth=64,backend='cpu',repeats=3,error_rate=.01,
            seed=1729,score_only=False,indel_rate=0,timeout_seconds=30,threads=1,checkpoint_interval=0,allow_fallback=True):
    if length<1 or batch_size<1 or repeats<1 or not 0<=error_rate<=1 or not 0<=indel_rate<=1:
        raise ValueError('Invalid benchmark dimensions or error rates')
    pairs=generate_pairs(length,batch_size,error_rate,indel_rate,seed)
    queries,targets=map(list,zip(*pairs))
    a=Aligner(backend=backend,mode=mode,bandwidth=bandwidth,score_only=score_only,timeout_seconds=timeout_seconds,threads=threads,checkpoint_interval=checkpoint_interval,allow_fallback=allow_fallback)
    gold=[affine_score(q,t) if len(q)*len(t)<=100000 else Aligner(score_only=True,timeout_seconds=timeout_seconds).align(q,t).score for q,t in pairs]
    a.align_batch(queries,targets) # warm up the same batch shape
    times=[];rows=[]
    for _ in range(repeats):
        start=time.perf_counter();rows=a.align_batch(queries,targets);times.append(time.perf_counter()-start)
    median=statistics.median(times)
    return dict(length=length,target_lengths=[len(t) for t in targets],batch_size=batch_size,mode=mode,bandwidth=bandwidth,requested_backend=backend,
                backend='+'.join(sorted({r.backend for r in rows})),score_only=score_only,threads=threads,checkpoint_interval=checkpoint_interval,repeats=repeats,seed=seed,error_rate=error_rate,indel_rate=indel_rate,
                mismatch=4,gap_open=6,gap_extend=2,seconds=median,min_seconds=min(times),max_seconds=max(times),
                stdev_seconds=statistics.stdev(times) if len(times)>1 else 0,raw_seconds=times,
                alignments_per_second=batch_size/median,bases_per_second=sum(len(q)+len(t) for q,t in pairs)/median,
                gpu_memory_bytes=max((r.gpu_memory_bytes for r in rows if r.backend!='cpu'),default=None),wavefront_bytes=max(r.wavefront_bytes for r in rows),
                cpu_fallback_fraction=sum(r.cpu_fallback for r in rows)/batch_size,
                score_agreement=sum(r.score==s for r,s in zip(rows,gold))/batch_size,scores=[r.score for r in rows],
                reference='independent affine DP' if all(len(q)*len(t)<=100000 for q,t in pairs) else 'CPU exact WFA (not independent)',
                dataset_sha256=hashlib.sha256(json.dumps(pairs).encode()).hexdigest(),speedup=None)

def save_report(rows,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    source_root=Path(__file__).resolve().parents[2]
    sources=list((source_root/'include/warpalign').glob('*.hpp'))+[Path(__file__)]
    hashes={str(p.relative_to(source_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()}
    payload=dict(hardware=hardware(),source_sha256=hashes,command=sys.argv,provenance='Synthetic substitution/indel DNA generated with Python random; seed in each row; original generated data, CC0',measurements=rows)
    (directory/'raw.json').write_text(json.dumps(payload,indent=2))
    with (directory/'raw.csv').open('w') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    # Standalone SVG plot, with real recorded values only.
    max_x=max(r['length'] for r in rows);max_y=max(r['seconds'] for r in rows)
    circles=''.join(f'<circle cx="{50+500*r["length"]/max_x}" cy="{250-200*r["seconds"]/max_y}" r="4"><title>{r["length"]} bp: {r["seconds"]:.6f}s</title></circle>' for r in rows)
    (directory/'runtime.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="620" height="300"><rect width="620" height="300" fill="white"/><path d="M50 40V250H570" stroke="black" fill="none"/><g fill="#087f8c">{circles}</g><text x="50" y="25">Measured CPU batch runtime (seconds; max {max_y:.4f})</text><text x="200" y="280">Sequence length (bp; max {max_x})</text></svg>')
