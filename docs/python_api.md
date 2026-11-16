# Python API

```python
from warpalign import Aligner, as_dict, ResourceError
aligner = Aligner(backend="auto", mode="exact", mismatch=4,
                  gap_open=6, gap_extend=2, memory_limit=512*1024**2)
result = aligner.align("ACGT", "ACGTT", query_id="read1", target_id="ref")
print(as_dict(result))
results = aligner.align_batch(["AA", "CG"], ["AT", "CG"])
```

Additional options: `ambiguous="literal"|"wildcard"|"mismatch"`, `score_only`, `bandwidth`. Fast mode applies a fixed symmetric band around diagonal zero and sets `heuristic_used`. A CUDA request currently uses CPU and sets `cpu_fallback` with a reason. Auto chooses the available CPU without labeling ordinary CPU selection as fallback.

The pybind11 calls release the GIL while executing C++. PyTorch is not a package dependency. Strings must contain only DNA letters ACGTN, case-insensitive; no whitespace is removed by the core API.
