# WarpAlign

A working C++17 affine wavefront aligner, Python package, streaming CLI and local sequence-alignment studio.

**Status: initial CPU release. CUDA score code is experimental and unvalidated.** This repository does not establish a new GPU WFA algorithm or a performance improvement over existing projects. Read [prior art](docs/prior_art.md) and [limitations](docs/limitations.md).

## Build and run

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[studio,test,docs]'
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
python -m pytest -q
warpalign align-pairs --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa --output results.paf
```

```python
import warpalign
r = warpalign.Aligner().align('ACGTACGT', 'ACGTTACGT')
print(r.score, r.cigar, r.backend)
```

```sh
cd apps/studio
npm install
npm run build
npm test
cd ../..
warpalign-studio
# Open http://127.0.0.1:8000
mkdocs build --strict
```

C++ consumers can include `warpalign/warpalign.hpp` directly or use the installed `WarpAlign::warpalign` CMake target. Python and CUDA are not mandatory dependencies of the CPU C++ core. The CLI is Python-based.

## Implemented

- Genuine M/I/D affine WFA recurrence, global optimal cost and traceback.
- Extended SAM CIGAR (`= X I D`), structured results and configurable N handling.
- Dynamic wavefront storage, explicit resource errors, rolling score-only history.
- Separate fixed-band heuristic mode with metadata.
- FASTA/FASTQ/gzip streaming pairwise CLI and minimap2 candidate refinement adapter.
- Pybind11 bindings with GIL release; local FastAPI jobs and React/TypeScript Studio.
- Canvas viewport, actual measurement charts, reproducible CPU benchmark files.
- Independent affine-DP randomized validation, integration tests and CI definitions.

Scoring minimizes a nonnegative cost: mismatch × substitutions + Σ(gap_open + gap_extend × gap_length). `I` consumes query; `D` consumes reference. Coordinates are zero-based, half-open. Pairing is by input order. Exact resource exhaustion is an error, never silent heuristic substitution.

## Validation limits

CPU tests include 4,000 seeded DP comparisons and low-divergence inputs through 100 kb. This is not a general ultra-long-read performance guarantee. The production backend is CPU; CUDA requests explicitly report fallback. The isolated warp-tiled CUDA score prototype requires NVCC and device validation, and has no GPU traceback or batch scheduler. Actual minimap2 execution and external WFA2/WFA-GPU/GASAL2 comparisons require separately installed tools.

See [development report](docs/development_report.md), [architecture](docs/architecture.md), [API documentation](docs/python_api.md), [benchmark methodology](docs/benchmarks.md) and [contribution guide](CONTRIBUTING.md). No public GitHub repository has been configured in this workspace.
