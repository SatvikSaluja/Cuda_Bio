"""Hardware tests; skipped when the CUDA extension/device is unavailable."""
import os
import pytest
from warpalign import Aligner
cuda=pytest.importorskip('warpalign._cuda')
pytestmark=pytest.mark.skipif(not cuda.available(),reason='Actual CUDA device required')

def test_score_batch_and_device_traceback(monkeypatch):
    monkeypatch.setenv('WARPALIGN_EXPERIMENTAL_CUDA','1')
    q=['ACGT','A'*31,'G'*32,'T'*33,''];t=['ACGTT','A'*30,'G'*32,'A'*33,'AA']
    cpu=Aligner(backend='cpu').align_batch(q,t)
    gpu=Aligner(backend='cuda',allow_fallback=False,score_only=True).align_batch(q,t)
    assert [r.score for r in gpu]==[r.score for r in cpu]
    assert all(r.backend=='cuda' for r in gpu)
    mixed=Aligner(backend='cuda',allow_fallback=False).align_batch(q,t)
    assert all(r.backend=='cuda' for r in mixed)
    assert [r.cigar for r in mixed]==[r.cigar for r in cpu]
