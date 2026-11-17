"""Minimap2 candidate discovery; global refinement of its reported intervals."""
import subprocess
import tempfile
from . import as_dict
from .io import SequenceIndex
from pathlib import Path
from .diagnostics import command

def reverse_complement(sequence):
    return sequence.translate(str.maketrans('ACGTNacgtn', 'TGCANtgcan'))[::-1]

def refine_candidate(fields, queries, targets, aligner):
    qid, qlen, qs, qe, strand, tid, tlen, ts, te = fields[:9]
    qlen, qs, qe, tlen, ts, te = map(int, (qlen, qs, qe, tlen, ts, te))
    qsize=queries.length(qid) if isinstance(queries,SequenceIndex) else len(queries[qid])
    tsize=targets.length(tid) if isinstance(targets,SequenceIndex) else len(targets[tid])
    if qsize != qlen or tsize != tlen or not (0 <= qs <= qe <= qlen and 0 <= ts <= te <= tlen) or strand not in ('+', '-'):
        raise ValueError('Invalid candidate coordinates')
    query = queries.fetch(qid,qs,qe) if isinstance(queries,SequenceIndex) else queries[qid][qs:qe]
    if strand == '-':
        query = reverse_complement(query)
    target = targets.fetch(tid,ts,te) if isinstance(targets,SequenceIndex) else targets[tid][ts:te]
    row = as_dict(aligner.align(query, target, qid, tid))
    row['parameters']={**aligner.options,'threads':aligner.threads,'cuda_max_score':aligner.cuda_max_score}
    row.update(query_length=qlen, target_length=tlen, query_start=qs, query_end=qe,
               target_start=ts, target_end=te, strand=strand, mapq=int(fields[11]),
               query_sequence=query, target_sequence=target, mapq_source='minimap2 (not recalibrated)')
    return row

def map_reads(reference, reads, aligner, preset='map-ont', mapper='minimap2'):
    if preset not in ('map-ont', 'map-hifi'):
        raise ValueError('Supported presets: map-ont, map-hifi')
    argv=[mapper,'-c','-x',preset,str(reference),str(reads)]
    mapper_version=command([mapper,'--version'])
    with tempfile.TemporaryDirectory(prefix='warpalign-index-') as directory:
        targets=SequenceIndex(Path(directory)/'targets.sqlite3')
        queries=SequenceIndex(Path(directory)/'queries.sqlite3')
        try:
            targets.load(reference);queries.load(reads)
            with tempfile.TemporaryFile(mode='w+t') as candidates, tempfile.TemporaryFile(mode='w+t') as errors:
                proc=subprocess.run(argv,stdout=candidates,stderr=errors,timeout=3600)
                if proc.returncode:
                    errors.seek(0)
                    raise RuntimeError(f'minimap2 failed ({proc.returncode}): {errors.read(4000)}')
                candidates.seek(0)
                for line in candidates:
                    fields=line.rstrip().split('\t')
                    if len(fields)<12:raise ValueError('Malformed mapper PAF')
                    row=refine_candidate(fields,queries,targets,aligner)
                    row.update(mapper_version=mapper_version,mapper_command=argv)
                    yield row
        finally:
            targets.close();queries.close()
