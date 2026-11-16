# Development and acceptance report

Date: 2026-11-16. This is a functional CPU vertical slice, not completion of the full requested CUDA ecosystem.

## Files and architecture

- `include/warpalign/`: C++17 configuration/results, DNA handling, affine M/I/D WFA, CIGAR traceback, score-only history and experimental CUDA score/arena headers.
- `CMakeLists.txt`, `examples/basic.cpp`: dependency-free CPU build, CTest, installable CMake/header package; opt-in CUDA test target.
- `python/bindings.cpp`, `python/warpalign/`: pybind11 wrapper, typed package, streaming FASTA/FASTQ CLI, PAF/JSONL output, minimap2 adapter, FastAPI jobs and measurement engine.
- `apps/studio/`: six-screen React/TypeScript local application, result table, CIGAR-indexed canvas and measurement SVGs.
- `tests/`: independent affine DP/CIGAR validation, Python/CLI/API integration, CUDA device tests and synthetic fixtures.
- `benchmarks/`: seeded CPU runner, provenance, real raw CSV/JSON and SVG output.
- `docs/`, `mkdocs.yml`: technical and user documentation, local static-site configuration, prior-art/license audit and limitations.
- Root governance files and `.github/`: MIT licence, contribution/security/conduct/citation/versioning files, issue/PR templates, CPU/Python/frontend/docs CI and manual GPU runner workflow.

## Executed successfully

- GCC 13.3.0 C++17 compile; CMake 4.4.4 build; CTest 1/1; installed CMake package consumed successfully by a separate project.
- 4,000 seeded WFA vs independent affine-DP comparisons with CIGAR replay/rescoring and score-only equivalence.
- Edge cases, N policies, lowercase, gaps, resource rejection and low-divergence sequence lengths 100, 500, 1k, 5k, 10k, 20k, 50k and 100k. Empty-target 100k path has a direct exact single-gap calculation.
- AddressSanitizer/UndefinedBehaviorSanitizer CPU run (leak detection disabled for sandbox compatibility).
- Python extension compiled manually from existing pybind11 headers; 12 pytest checks pass, including real in-process ASGI upload, alignment, download and measurement. No mock alignment responses.
- TypeScript and Vite production build; two frontend CIGAR viewport tests pass.
- 16 recorded CPU benchmark configurations: eight lengths × traceback/score-only, one pair per batch, three repeats after a warm-up, substitution probability 0.001. See raw files for exact timings and hardware.

## Not validated / remaining work

- No NVCC, driver tool or GPU available. CUDA source has not compiled or executed. The prototype has score-only output, sequential calls and no GPU traceback or adaptive batch scheduler. Production CUDA requests explicitly fall back to CPU.
- No external minimap2, WFA2, WFA-GPU or GASAL2 binary available. Reverse-strand adapter logic is unit tested; real mapper execution and external comparative benchmarks remain unrun.
- No live browser/network test: sandbox denies binding 127.0.0.1:8000. In-process API checks passed; this is not a browser end-to-end pass.
- Documentation navigation and local Markdown links passed static validation. MkDocs is unavailable and package downloads fail DNS resolution. Documentation source and navigation exist; the MkDocs build is unrun.
- Clean wheel/editable install and clean npm installation remain unverified. Validation reused existing local Python packages and frontend dependencies. Generated extensions/bundles, virtualenv and local symlinks are ignored.
- No adaptive heuristic expansion, BiWFA/checkpointed traceback, parallel CPU batching, production GPU dispatch, real-data ultra-long validation, complete indel benchmark sweep, peak RSS measurement or measured external improvement.
- No public repository/publishing setup. Protected `.git` is not a usable repository; no commits were made.

## Current-workspace commands

```sh
# Python extension has been built locally; .venv has validation-only paths.
.venv/bin/python -m warpalign.cli align-pairs \
  --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa \
  --backend auto --output /tmp/warpalign-results.paf
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
/home/satvik/CN_project/build-tools/cmake/data/bin/ctest --test-dir build/cmake --output-on-failure
(cd apps/studio && npm run build && npm test)
.venv/bin/python benchmarks/scripts/run.py --batches 1 --repeats 3 --error-rate 0.001
.venv/bin/python -m warpalign.api
# Studio URL when local binding is permitted: http://127.0.0.1:8000
```

For a clean machine, use [installation](installation.md). After installing the docs extra, build with `python -m mkdocs build --strict`. The package installs `warpalign` and `warpalign-studio` entry points. There is no claim that unavailable checks passed.
