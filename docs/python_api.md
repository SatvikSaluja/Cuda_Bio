# Python API

```python
from warpalign import Aligner, as_dict
aligner = Aligner(backend="cpu", mode="exact", mismatch=4,
                  gap_open=6, gap_extend=2, memory_limit=256*1024**2,
                  threads=4, checkpoint_interval=128, timeout_seconds=30)
result = aligner.align("ACGT", "ACGTT", query_id="read1", target_id="ref")
print(as_dict(result))
results = aligner.align_batch(["AA", "CG"], ["AT", "CG"])
```

| Option | Meaning |
|---|---|
| `backend` | cpu, auto or cuda; experimental CUDA requires explicit environment opt-in |
| `allow_fallback` | False makes an unavailable explicit CUDA request an error |
| `score_only` | Omits CIGAR/counts; JSON count fields are null |
| `threads` | CPU batch workers, 1–64; total wavefront budget is divided among active workers |
| `checkpoint_interval` | 0 retains history; positive values retain normalized-score checkpoints and recompute traceback segments |
| `timeout_seconds` | CPU alignment deadline, including checkpoint recomputation; 0 disables it |
| `ambiguous` | literal, wildcard or mismatch treatment of N |
| `bandwidth` | Fast-mode diagonal half-width |
| `adaptive_band`, `max_bandwidth` | Optional fast-mode failure retries; results remain heuristic |
| `cuda_max_score` | Explicit experimental GPU score budget; exhaustion errors or falls back according to policy |

GIL release permits CPU batch threads. No PyTorch dependency is required. Input accepts case-insensitive ACGTN only. Empty strings are valid. Invalid configuration raises ValueError; resource/deadline errors raise ResourceError.

GPU score-only and device traceback results report `cuda`. Full results receive a linear host CIGAR replay/rescore check; no CPU alignment is recomputed. The optional extension API version is now 2 and older extensions must be rebuilt. GPU batch timings are amortized and labeled in `timing_scope`; benchmark wall timings are recorded separately. `gpu_memory_bytes` is allocated arena capacity, not total VRAM usage. A Python CPU deadline does not preempt a running CUDA kernel; Studio's process-level job timeout can terminate the worker.
