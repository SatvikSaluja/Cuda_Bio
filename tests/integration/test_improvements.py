import json
import random
import subprocess
import sys
import pytest
from warpalign import Aligner,ResourceError
from warpalign.benchmark import measure,generate_pairs
from warpalign.cli import pair_rows
from warpalign.reference import affine_score
from warpalign.store import Store

def test_strict_backend_and_deadline(monkeypatch):
    monkeypatch.delenv('WARPALIGN_EXPERIMENTAL_CUDA',raising=False)
    with pytest.raises(ResourceError):Aligner(backend='cuda',allow_fallback=False).align('A','A')
    with pytest.raises(ResourceError,match='deadline'):Aligner(timeout_seconds=1e-12).align('A'*500,'C'*500)
    with pytest.raises(ValueError):Aligner(timeout_seconds=float('nan'))
    with pytest.raises(ValueError):Aligner(threads=0)

def test_threads_and_checkpoint():
    q=['ACGT','A'*100,'','AGTGCG'];t=['ACT','A'*20+'C'+'A'*79,'GG','AGTCG']
    serial=Aligner().align_batch(q,t)
    parallel=Aligner(threads=3,checkpoint_interval=9).align_batch(q,t)
    assert [(r.score,r.cigar) for r in serial]==[(r.score,r.cigar) for r in parallel]

def test_identifier_pairing(tmp_path):
    q=tmp_path/'q.fa';t=tmp_path/'t.fa';q.write_text('>a\nAA\n>b\nCG\n');t.write_text('>b\nCG\n>a\nAA\n')
    rows=list(pair_rows(q,t,Aligner(threads=2),pairing='id'))
    assert [r['score'] for r in rows]==[0,0]
    assert [r['query_id'] for r in rows]==['a','b']
    t.write_text('>z\nAA\n')
    with pytest.raises(ValueError):list(pair_rows(q,t,Aligner(),pairing='id'))

def test_persistent_store_and_global_search(tmp_path):
    s=Store(tmp_path/'jobs.sqlite3');s.create('test',{});s.update('test','running')
    for i in range(205):
        s.append('test',dict(query_id=f'read-{i:03}',score=205-i,edit_distance=0,execution_time=.01,query_sequence='AC',target_sequence='AC'))
    s.update('test','complete');s=Store(tmp_path/'jobs.sqlite3')
    assert s.job('test')['completed']==205
    count,rows=s.results('test',search='read-204')
    assert count==1 and rows[0]['result_index']==204 and 'query_sequence' not in rows[0]
    assert s.detail('test',204)['query_sequence']=='AC'
    assert s.results('test',sort='score')[1][0]['query_id']=='read-204'
    assert len(list(s.export('test')))==205
    with pytest.raises(ValueError):s.results('test',sort='score; DROP TABLE jobs')
    s.create('unfinished',{});s.recover();assert s.job('unfinished')['status']=='interrupted'
    s.clear();assert s.jobs()==[]

def test_indel_benchmark_and_independent_reference():
    pairs=generate_pairs(80,3,.02,.1,1729)
    assert pairs==generate_pairs(80,3,.02,.1,1729)
    for q,t in pairs:assert Aligner().align(q,t).score==affine_score(q,t)
    row=measure(length=80,batch_size=2,indel_rate=.05,repeats=2)
    assert row['score_agreement']==1 and row['reference']=='independent affine DP'
    assert row['seconds']>0 and len(row['raw_seconds'])==2 and row['dataset_sha256']

def test_doctor_cli():
    run=subprocess.run([sys.executable,'-m','warpalign.cli','doctor'],text=True,capture_output=True)
    assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['native_extension']

def test_disk_index_and_reverse_refinement(tmp_path):
    from warpalign.io import SequenceIndex
    from warpalign.mapping import refine_candidate
    qfile=tmp_path/'q.fa';tfile=tmp_path/'t.fa'
    qfile.write_text('>q\nNAACGN\n');tfile.write_text('>t\nCGTT\n')
    q=SequenceIndex(tmp_path/'q.db');t=SequenceIndex(tmp_path/'t.db')
    try:
        q.load(qfile);t.load(tfile)
        r=refine_candidate('q 6 1 5 - t 4 0 4 4 4 31'.split(),q,t,Aligner())
        assert r['score']==0 and r['query_sequence']=='CGTT'
        assert q.length('q')==6 and q.fetch('q',1,5)=='AACG'
        with pytest.raises(ValueError):q.load(qfile)
    finally:q.close();t.close()

def test_adaptive_band_is_always_heuristic():
    r=Aligner(mode='fast',bandwidth=2,adaptive_band=True,max_bandwidth=64).align('A'*100,'A'*80)
    assert r.score==46 and r.heuristic_used and r.bandwidth==32 and r.heuristic_retries==4
    with pytest.raises(ResourceError):Aligner(mode='fast',bandwidth=2,adaptive_band=True,max_bandwidth=16).align('A'*100,'A'*80)
    with pytest.raises(ValueError):Aligner(adaptive_band=True)

def test_fastq_blank_header_never_silently_truncates():
    import io
    from warpalign.io import parse_records
    with pytest.raises(ValueError,match='Blank FASTQ'):
        list(parse_records(io.StringIO('@a\nA\n+\n!\n\n@b\nC\n+\n!\n')))

def test_checkpoint_fits_budget_that_full_traceback_exceeds():
    q,t=generate_pairs(10000,1,.02,.01,1729)[0]
    with pytest.raises(ResourceError):Aligner(memory_limit=3*1024**2).align(q,t)
    full=Aligner().align(q,t)
    small=Aligner(memory_limit=3*1024**2,checkpoint_interval=128).align(q,t)
    assert (small.score,small.cigar)==(full.score,full.cigar)
    assert small.wavefront_bytes<=3*1024**2<full.wavefront_bytes

def test_cuda_dispatch_uses_device_traceback_without_cpu_realignment(monkeypatch):
    """Dispatch contract only: a stub is NOT evidence of device execution."""
    import types
    import warpalign
    fake=types.SimpleNamespace(api_version=2,available=lambda:True,last_arena_bytes=lambda:4096,
        alignments=lambda *args:[dict(score=8,cigar='1=1D',query_end=1,target_end=2,
            matches=1,mismatches=0,insertions=0,deletions=1,edit_distance=1,backend='cuda')])
    monkeypatch.setattr(warpalign,'_cuda',fake,raising=False)
    monkeypatch.setenv('WARPALIGN_EXPERIMENTAL_CUDA','1')
    aligner=Aligner(backend='cuda',allow_fallback=False)
    def forbidden(*args):raise AssertionError('CPU alignment must not run')
    monkeypatch.setattr(aligner,'_native',forbidden)
    result=aligner.align('A','AA')
    assert result.backend=='cuda' and result.cigar=='1=1D' and result.gpu_memory_bytes==4096

def test_old_cuda_extension_rejected(monkeypatch):
    import types
    import warpalign
    monkeypatch.setattr(warpalign,'_cuda',types.SimpleNamespace(api_version=1),raising=False)
    monkeypatch.setenv('WARPALIGN_EXPERIMENTAL_CUDA','1')
    with pytest.raises(ResourceError,match='Rebuild'):
        Aligner(backend='cuda',allow_fallback=False).align('A','A')

@pytest.mark.parametrize('backend',['cuda','auto'])
def test_gpu_resource_failure_obeys_fallback_policy(monkeypatch,backend):
    """Routing contract only, not a GPU execution test."""
    import types
    import warpalign
    def exhaust(*args):raise RuntimeError('CUDA traceback history exceeds memory budget')
    fake=types.SimpleNamespace(api_version=2,available=lambda:True,alignments=exhaust)
    monkeypatch.setattr(warpalign,'_cuda',fake,raising=False)
    monkeypatch.setenv('WARPALIGN_EXPERIMENTAL_CUDA','1')
    with pytest.raises(ResourceError,match='memory budget'):
        Aligner(backend=backend,allow_fallback=False).align('ACGT','ACGTT')
    result=Aligner(backend=backend,allow_fallback=True).align('ACGT','ACGTT')
    assert result.backend=='cpu' and result.cpu_fallback and result.score==8
    assert 'memory budget' in result.fallback_reason
