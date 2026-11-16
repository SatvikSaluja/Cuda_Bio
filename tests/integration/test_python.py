import io
import json
from pathlib import Path
import subprocess
import sys
import pytest
from warpalign import Aligner, as_dict, ResourceError
from warpalign.io import parse_records, paf
from warpalign.mapping import refine_candidate

@pytest.mark.parametrize('q,t,score,cigar',[('ACGT','ACGT',0,'4='),('A','T',4,'1X'),('AC','A',8,'1=1I'),('A','AC',8,'1=1D'),('','',0,''),('','AAA',12,'3D')])
def test_align(q,t,score,cigar):
    r=Aligner().align(q,t)
    assert (r.score,r.cigar)==(score,cigar)

def test_validation_and_fallback():
    with pytest.raises(ValueError):Aligner(mismatch=0)
    with pytest.raises(ValueError):Aligner().align('Z','A')
    with pytest.raises(ValueError):Aligner().align_batch(['A'],[])
    with pytest.raises(ResourceError):Aligner(memory_limit=1024).align('A'*100,'C'*100)
    r=Aligner(backend='cuda').align('A','A')
    assert r.cpu_fallback and r.backend=='cpu' and r.fallback_reason
    assert not Aligner().align('A','A').cpu_fallback
    assert Aligner().align('acgtn','ACGTN').score==0
    assert Aligner(ambiguous='mismatch').align('N','N').score==4
    assert Aligner(ambiguous='wildcard').align('N','A').score==0
    assert as_dict(Aligner(score_only=True).align('A','T'))['edit_distance'] is None

def test_io():
    assert list(parse_records(io.StringIO('>a desc\nAC\nGT\n>b\nN\n')))==[('a','ACGT'),('b','N')]
    assert list(parse_records(io.StringIO('@a\nAC\nGT\n+\n!!\n!!\n')))==[('a','ACGT')]
    with pytest.raises(ValueError):list(parse_records(io.StringIO('@a\nAC\n+\n!\n')))
    with pytest.raises(ValueError):list(parse_records(io.StringIO('>\nAC\n')))

def test_mapping_reverse_and_coordinates():
    fields='q 8 2 6 - t 10 3 7 4 4 42'.split()
    row=refine_candidate(fields,{'q':'NNACGTNN'},{'t':'NNNACGTNNN'},Aligner())
    assert row['score']==0 and row['strand']=='-' and row['mapq']==42
    assert row['query_start']==2 and row['target_start']==3
    assert paf(row).split('\t')[:12]==['q','8','2','6','-','t','10','3','7','4','4','42']
    fields='q 6 1 5 - t 4 0 4 4 4 31'.split()
    row=refine_candidate(fields,{'q':'NAACGN'},{'t':'CGTT'},Aligner())
    assert row['query_sequence']=='CGTT' and row['score']==0

def test_cli(tmp_path):
    output=tmp_path/'result.paf'
    run=subprocess.run([sys.executable,'-m','warpalign.cli','align-pairs','--queries','tests/fixtures/queries.fa','--targets','tests/fixtures/targets.fa','--output',str(output)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert len(output.read_text().splitlines())==2
    assert json.loads(run.stderr)['alignments']==2
    bad=tmp_path/'bad.fa';bad.write_text('>bad\nZ\n');output.write_text('preserve')
    run=subprocess.run([sys.executable,'-m','warpalign.cli','align-pairs','--queries',str(bad),'--targets','tests/fixtures/targets.fa','--output',str(output)],capture_output=True,text=True)
    assert run.returncode==2 and output.read_text()=='preserve'
