"""Real external-mapper integration; absence is reported as a skip."""
import random
import shutil
import pytest
from warpalign import Aligner
from warpalign.mapping import map_reads,reverse_complement

@pytest.mark.skipif(shutil.which('minimap2') is None,reason='minimap2 executable is not installed')
def test_real_minimap2_forward_and_reverse(tmp_path):
    rng=random.Random(1729);reference=''.join(rng.choice('ACGT') for _ in range(20000))
    ref=tmp_path/'ref.fa';reads=tmp_path/'reads.fa'
    ref.write_text('>reference\n'+reference+'\n')
    reads.write_text('>forward\n'+reference[2000:7000]+'\n>reverse\n'+reverse_complement(reference[8000:13000])+'\n')
    rows=list(map_reads(ref,reads,Aligner(backend='cpu')))
    byid={r['query_id']:r for r in rows}
    assert byid['forward']['score']==0 and byid['forward']['strand']=='+'
    assert byid['reverse']['score']==0 and byid['reverse']['strand']=='-'
    assert byid['forward']['mapper_version']
