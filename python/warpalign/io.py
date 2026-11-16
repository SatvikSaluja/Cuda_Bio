"""Streaming FASTA and multiline FASTQ, optionally gzip compressed."""
from pathlib import Path
import gzip

def records(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='ascii') as handle:
        yield from parse_records(handle)

def parse_records(lines):
    it = iter(lines)
    header = next((line.strip() for line in it if line.strip()), '')
    if not header:
        return
    if header.startswith('>'):
        seq = []
        for line in it:
            line = line.strip()
            if line.startswith('>'):
                yield identifier(header), ''.join(seq)
                header, seq = line, []
            else:
                seq.append(line)
        yield identifier(header), ''.join(seq)
    elif header.startswith('@'):
        while header:
            if not header.startswith('@'):
                raise ValueError('FASTQ record must begin with @')
            name = identifier(header)
            seq = []
            for line in it:
                if line.startswith('+'):
                    break
                seq.append(line.strip())
            else:
                raise ValueError('FASTQ missing + separator')
            sequence = ''.join(seq)
            quality_length = 0
            # Empty FASTQ sequences require an empty quality line.
            while quality_length < len(sequence) or not sequence:
                quality = next(it, None)
                if quality is None:
                    raise ValueError('FASTQ quality is truncated')
                quality_length += len(quality.rstrip('\r\n'))
                if not sequence:
                    break
            if quality_length != len(sequence):
                raise ValueError('FASTQ quality length differs from sequence')
            yield name, sequence
            header = next(it, '').strip()
    else:
        raise ValueError('Expected FASTA (>) or FASTQ (@)')

def identifier(header):
    fields = header[1:].split()
    if not fields:
        raise ValueError('Sequence identifier is empty')
    return fields[0]

def unique_records(path):
    result = {}
    for name, seq in records(path):
        if name in result:
            raise ValueError(f'Duplicate identifier: {name}')
        result[name] = seq
    return result

def paf(row):
    if not row['has_traceback']:
        raise ValueError('PAF requires traceback; use JSONL for score-only')
    fields = [row['query_id'], row.get('query_length', row['query_end']), row['query_start'], row['query_end'],
              row.get('strand', '+'), row['target_id'], row.get('target_length', row['target_end']),
              row['target_start'], row['target_end'], row['matches'],
              row['matches'] + row['mismatches'] + row['insertions'] + row['deletions'], row.get('mapq', 255)]
    # wc is a positive cost, not SAM AS (higher-is-better). Mapper MAPQ is retained unchanged.
    tags = [f"wc:i:{row['score']}", f"NM:i:{row['edit_distance']}", f"cg:Z:{row['cigar']}",
            f"wb:Z:{row['backend']}", f"wh:i:{int(row['heuristic_used'])}"]
    return '\t'.join(map(str, fields + tags))
