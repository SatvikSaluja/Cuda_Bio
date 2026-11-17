# WarpAlign v1.0.0

First CPU-first research release of WarpAlign: exact affine sequence alignment,
Python and CLI interfaces, and a local Studio for viewing variants and measuring
alignment performance.

## Included

- C++17 global affine WFA with score-only mode, full CIGAR traceback, checkpoint
  recomputation, configurable ambiguous bases, resource limits and deadlines.
- Python bindings, threaded pair batches, FASTA/FASTQ inputs, PAF/JSONL exports,
  and optional minimap2 candidate-region refinement.
- Local Studio with durable SQLite results, cancellation, search, exports,
  a virtualized canvas viewer and measured performance charts.
- File-free demo using 1.2 kb synthetic variants and real CPU measurements.
- CPU Docker/Compose packaging; Docker is optional for localhost use.
- Experimental CUDA batch scoring and device traceback with host CIGAR replay,
  explicit opt-in, and strict/allowed CPU fallback policies.

## Validation evidence

The development environment passed CPU CTest builds with CUDA OFF and AUTO,
29 Python/API tests (one CUDA skip), the TypeScript/Vite build,
five viewer tests, and native wheel installation outside the checkout. The real
minimap2 2.26-r1175 integration test passed on forward/reverse synthetic 5 kb reads. CPU tests
include 4,000 randomized and 1,922 exhaustive affine-DP comparisons. Shared
traceback logic has also passed host sanitizer checks.

Recorded benchmark data retains its original 0.2.0 development provenance.
At 100 kb, 1% sampled substitutions and 0.2% sampled indels, checkpointing reduced
process peak RSS from 119.56 to 32.39 MiB, while median latency increased from
362.20 to 646.41 ms. This is a local CPU memory/time trade-off, not an external
aligner or GPU speedup comparison.

## Known limitations

- CUDA source remains uncompiled and runtime-unvalidated here: no NVCC/device
  was available. GPU functionality is experimental, not validated support.
- Docker execution, live browser testing, full MkDocs build and real external
  aligner comparisons remain pending in environments with their prerequisites.
- Synthetic long-read tests do not guarantee capacity for arbitrary high-error
  ultra-long reads. Exact mode reports resource failures rather than truncating.
- This is a local research application, not clinical or public multi-user software.

## Installation

From the source checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[studio]'
(cd apps/studio && npm ci && npm run build)
warpalign-studio --port 8000
```

Open http://localhost:8000 and choose **Try a real demo**. Release wheels include
Studio assets; install a wheel matching your Python/platform with the `studio`
extra. The supplied CI wheel is a native Linux CPython 3.12 build, not a universal
or audited manylinux wheel. Other environments can build from source. No PyPI
publication is claimed.
