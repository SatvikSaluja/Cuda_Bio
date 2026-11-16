"""Minimap2 candidate discovery; global refinement of its reported intervals."""
import subprocess
import tempfile
from . import as_dict
from .io import unique_records

def reverse_complement(sequence):
    return sequence.translate(str.maketrans('ACGTNacgtn', 'TGCANtgcan'))[::-1]

def refine_candidate(fields, queries, targets, aligner):
    qid, qlen, qs, qe, strand, tid, tlen, ts, te = fields[:9]
    qlen, qs, qe, tlen, ts, te = map(int, (qlen, qs, qe, tlen, ts, te))
    q, t = queries[qid], targets[tid]
    if len(q) != qlen or len(t) != tlen or not (0 <= qs <= qe <= qlen and 0 <= ts <= te <= tlen) or strand not in ('+', '-'):
        raise ValueError('Invalid candidate coordinates')
    query = q[qs:qe]
    if strand == '-':
        query = reverse_complement(query)
    target = t[ts:te]
    row = as_dict(aligner.align(query, target, qid, tid))
    row.update(query_length=qlen, target_length=tlen, query_start=qs, query_end=qe,
               target_start=ts, target_end=te, strand=strand, mapq=int(fields[11]),
               query_sequence=query, target_sequence=target, mapq_source='minimap2 (not recalibrated)')
    return row

def map_reads(reference, reads, aligner, preset='map-ont', mapper='minimap2'):
    if preset not in ('map-ont', 'map-hifi'):
        raise ValueError('Supported presets: map-ont, map-hifi')
    targets, queries = unique_records(reference), unique_records(reads)
    # Spool candidate output, avoiding a pipe deadlock and unbounded stdout buffering.
    with tempfile.TemporaryFile(mode='w+t') as candidates, tempfile.TemporaryFile(mode='w+t') as errors:
        proc = subprocess.run([mapper, '-c', '-x', preset, str(reference), str(reads)], stdout=candidates, stderr=errors, timeout=3600)
        if proc.returncode:
            errors.seek(0)
            raise RuntimeError(f'minimap2 failed ({proc.returncode}): {errors.read(4000)}')
        candidates.seek(0)
        for line in candidates:
            fields = line.rstrip().split('\t')
            if len(fields) < 12:
                raise ValueError('Malformed mapper PAF')
            yield refine_candidate(fields, queries, targets, aligner)
