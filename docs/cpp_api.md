# C++ API

```cpp
#include <warpalign/warpalign.hpp>
warpalign::Config config;
config.mismatch = 4;
config.gap_open = 6;
config.gap_extend = 2;
config.memory_limit = 512ull * 1024 * 1024;
warpalign::Aligner aligner(config);
auto result = aligner.align("ACGT", "ACGTT", "query", "target");
auto batch = aligner.align_batch({"ACGT", "AA"}, {"ACGTT", "AT"});
```

`align` returns `Result`, with IDs, score, CIGAR, coordinates, edit counts, backend, timing, heuristic/fallback flags and peak accounted wavefront bytes. Coordinates are zero-based, half-open. Global alignments consume both inputs in full.

`score_only=true` omits traceback; consult `has_traceback` before using zero-initialized C++ count fields. Python JSON represents unavailable counts as null. Invalid configuration/alphabet/batch sizes raise `std::invalid_argument`. Memory budget exhaustion raises `ResourceError`; allocation failure may raise `std::bad_alloc`. Inputs longer than the documented integer-coordinate capacity are rejected.

An Aligner is immutable after construction and uses per-call storage. Batch execution is currently sequential. The experimental CUDA arena is mutable and must not be shared concurrently.
