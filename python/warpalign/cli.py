import argparse
import itertools
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from . import Aligner, as_dict
from .io import records, paf, unique_records
from .diagnostics import capabilities
from . import __version__
import subprocess
from .mapping import map_reads

def pair_rows(queries, targets, aligner, batch_size=256, progress=None, pairing="order"):
    if batch_size<1:raise ValueError("batch_size must be positive")
    if pairing=="id":
        query_records=unique_records(queries);target_records=unique_records(targets)
        if query_records.keys()!=target_records.keys():raise ValueError("Query and target identifier sets differ")
        pairs=iter(((name,seq),(name,target_records[name])) for name,seq in query_records.items())
    elif pairing=="order":pairs=itertools.zip_longest(records(queries),records(targets))
    else:raise ValueError("pairing must be order or id")
    done = 0
    while batch := list(itertools.islice(pairs, batch_size)):
        if any(q is None or t is None for q,t in batch):
            raise ValueError('Query and target record counts differ (pairing is by input order)')
        results=aligner.align_batch([q[1] for q,t in batch],[t[1] for q,t in batch])
        for (q,t),result in zip(batch,results):
            row=as_dict(result)
            row.update(query_id=q[0],target_id=t[0],parameters={**aligner.options,'threads':aligner.threads,'cuda_max_score':aligner.cuda_max_score},software_version=__version__)
            row.update(query_sequence=q[1].upper(), target_sequence=t[1].upper())
            yield row
            done += 1
            if progress:
                progress(done)

def parser():
    p = argparse.ArgumentParser(prog='warpalign', description='Global affine wavefront alignment; positive scores are costs')
    p.add_argument('--version',action='version',version=__version__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor',help='Inspect installed tools and runtime capabilities')
    for name in ('align-pairs', 'map'):
        c = sub.add_parser(name)
        if name == 'align-pairs':
            c.add_argument('--queries', required=True); c.add_argument('--targets', required=True)
        else:
            c.add_argument('--reference', required=True); c.add_argument('--reads', required=True)
            c.add_argument('--mapper', default='minimap2'); c.add_argument('--preset', choices=['map-ont', 'map-hifi'], default='map-ont')
        c.add_argument('--backend', choices=['auto', 'cpu', 'cuda'], default='auto')
        c.add_argument('--mode', choices=['exact', 'fast'], default='exact')
        c.add_argument('--mismatch', type=int, default=4); c.add_argument('--gap-open', type=int, default=6); c.add_argument('--gap-extend', type=int, default=2)
        c.add_argument('--adaptive-band',action='store_true')
        c.add_argument('--max-bandwidth',type=int,default=4096)
        c.add_argument('--bandwidth', type=int, default=64); c.add_argument('--batch-size', type=int, default=256)
        c.add_argument('--memory-mb', type=int, default=512); c.add_argument('--ambiguous', choices=['literal','wildcard','mismatch'], default='literal')
        c.add_argument('--checkpoint-interval',type=int,default=0,help='Retain rolling checkpoints and recompute traceback segments (0 retains full history)')
        c.add_argument('--threads',type=int,default=1)
        c.add_argument('--timeout-seconds',type=float,default=0)
        c.add_argument('--no-fallback',action='store_true')
        c.add_argument('--cuda-max-score',type=int,default=1024)
        c.add_argument('--pairing',choices=['order','id'],default='order')
        c.add_argument('--score-only', action='store_true'); c.add_argument('--output', required=True)
        c.add_argument('--format', choices=['paf','jsonl'], default=None)
    return p

def main():
    args = parser().parse_args()
    try:
        if args.command=='doctor':
            print(json.dumps(capabilities(),indent=2));return 0
        if args.batch_size <= 0:
            raise ValueError('batch-size must be positive')
        fmt = args.format or ('paf' if args.output.endswith('.paf') else 'jsonl')
        if args.score_only and fmt == 'paf':
            raise ValueError('score-only requires JSONL output')
        aligner = Aligner(**{k: getattr(args,k) for k in ['backend','mode','mismatch','gap_open','gap_extend','bandwidth','ambiguous','score_only','threads','timeout_seconds','checkpoint_interval','adaptive_band','max_bandwidth','cuda_max_score']}, memory_limit=args.memory_mb*1024**2,allow_fallback=not args.no_fallback)
        rows = pair_rows(args.queries,args.targets,aligner,args.batch_size,pairing=args.pairing) if args.command=='align-pairs' else map_reads(args.reference,args.reads,aligner,args.preset,args.mapper)
        count = fallback = 0; start=time.perf_counter(); destination=Path(args.output)
        # A failed job never replaces the destination with a partial successful-looking result.
        fd, tmp = tempfile.mkstemp(prefix='.warpalign-', dir=destination.parent)
        try:
            with os.fdopen(fd,'w') as out:
                for row in rows:
                    row.pop('query_sequence',None);row.pop('target_sequence',None)
                    out.write((paf(row) if fmt=='paf' else json.dumps(row))+'\n')
                    count+=1;fallback+=row['cpu_fallback']
                    if count%args.batch_size==0: print(f'Aligned {count} pairs',file=sys.stderr)
            os.replace(tmp,destination)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        print(json.dumps(dict(alignments=count,seconds=time.perf_counter()-start,cpu_fallbacks=fallback,output=str(destination))),file=sys.stderr)
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
        print(f'warpalign: {error}',file=sys.stderr);return 2
    return 0

if __name__=='__main__':
    raise SystemExit(main())
