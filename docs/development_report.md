# 0.2.0 development report

Updated 2026-11-17. Work is left uncommitted. This report describes implemented behavior and executed checks, not completion of the entire GPU research roadmap.

## Implemented

| Area | Change |
|---|---|
| CPU WFA | Indexed history, exact penalty normalization, checkpoint/recompute traceback, CPU deadlines, explicit adaptive heuristic retries |
| Python/CLI | Batch threads with shared wavefront budget, strict CUDA requests, doctor/version commands, ID pairing, richer provenance and timing scope |
| CUDA source | Resource-sized batches, independent warp blocks, reusable arena limits, optional pybind11 module, opt-in dispatch and GPU/CPU score agreement |
| Mapping | Disk-backed sequence indexing and interval fetch, mapper version/command metadata |
| Studio service | SQLite persistence, process-isolated cancellation/deadlines, restart interruption states, global result search/sort, metadata/detail separation, streamed JSONL/PAF |
| Studio UI | Redesigned responsive light/dark workbench, real demo action, drag/drop, resource controls, indexed viewer, variant navigation, zoom/text accessibility, measured comparison plots |
| Packaging | Portable npm lockfile; Studio bundled into built wheels; dependency notices; tested installation outside checkout |
| Validation tooling | Expanded unit/integration tests, real-device test script, actual-browser E2E script, compiler/Python matrices and manual external-comparison workflow |
| Reproducibility | Indel generator, independent small-case DP reference, isolated RSS, checkpoint comparison records, source hashes, baseline protocol/WFA2 adapter source |
| Examples | Nextflow, Snakemake, Colab validation notebook and source-archive helper |

## Executed evidence

- CMake/CTest CPU build: 1/1 CTest target passing.
- Independent oracle: 4,000 randomized and 1,922 exhaustive short-pair comparisons; CIGAR replay/rescoring, full/checkpoint/score-only agreement and low-divergence lengths through 100 kb.
- Python/API suite: 26 passed, 2 skipped (CUDA extension/device and actual minimap2 unavailable). Includes real worker subprocesses, durable search/detail/export, cancellation, deadlines, indexed refinement and memory-budget tests.
- CPU AddressSanitizer/UndefinedBehaviorSanitizer run passed with leak detection disabled for sandbox compatibility.
- Frontend TypeScript/Vite build and five CIGAR-index tests passed.
- Clean isolated frontend `npm ci --offline` from cached registry packages, followed by build/tests, passed with a portable integrity lockfile. The final expanded source also builds with the installed dependencies.
- Native wheel built using available SDK headers, installed with no dependencies into a fresh virtualenv, and checked from outside the checkout. Native alignment, packaged Studio discovery and installed `warpalign doctor` passed.
- Recorded 0.2.0 CPU/indel and checkpoint and 20/50/100 kb low-divergence experiments include actual repeats, wavefront storage and isolated process RSS. Checkpointing lowers accounted wavefront storage on larger recorded cases while increasing runtime.
- Documentation navigation and local links passed static validation.

## Explicitly outstanding

- CUDA compilation, GPU runtime equivalence and device sanitizers: no NVCC/validated device environment available. CUDA source is experimental.
- Native GPU traceback source is implemented with host-tested shared logic, but remains uncompiled and unexecuted on a device. Multi-warp scheduling and asynchronous transfers remain unimplemented.
- WFA2 adapter compilation/execution, WFA-GPU/GASAL2 adapters and external performance comparisons: unvalidated or unsupplied. No external speedup/novelty claim.
- Real minimap2 workloads and public sequencing datasets: not run locally. The real mapper test is skipped when the executable is absent.
- Live browser E2E: sandbox denies loopback binding; the available browser also lacks libasound. Browser script/CI are provided but are not passing execution evidence.
- MkDocs build: package downloads are unavailable and MkDocs is not installed. Source/link validation is not a full docs build.
- CUDA/Nextflow/Snakemake/Colab workflows and newly defined GitHub Actions require execution in their intended environments.

## Run this workspace

```sh
.venv/bin/python -m warpalign.cli doctor
.venv/bin/python -m warpalign.cli align-pairs \
  --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa \
  --threads 2 --checkpoint-interval 128 --output /tmp/warpalign-results.paf
WARPALIGN_DATA_DIR="$PWD/.local-data" .venv/bin/python -m warpalign.api --port 8000
# Open http://localhost:8000 from a terminal with permitted loopback binding.
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q
/home/satvik/CN_project/build-tools/cmake/data/bin/ctest --test-dir build/cmake --output-on-failure
(cd apps/studio && npm ci && npm run build && npm test)
```

On a clean network-enabled machine follow [installation](installation.md). Build the public docs using `python -m mkdocs build --strict` after installing the docs extra. [Workflow examples](workflows.md) explain using Colab with uncommitted source. Nothing in this development pass has been staged, committed or pushed.

## Follow-up validation pass

The CUDA full-result path now implements device traceback (extension API 2).
Its shared host/device routine passes the same 5,922 short-case CIGAR checks as
the CPU engine, plus AddressSanitizer/UndefinedBehaviorSanitizer checks on the
host. This is algorithm evidence, not GPU execution evidence.

`python scripts/validate_release.py` writes individual logs and a JSON report,
returning exit 2 for blocked prerequisites and exit 1 for failures. The local
report in `benchmarks/results/release-validation/report.json` records four
blocked checks: CUDA tools/device, MkDocs, installed browser dependencies, and
a built WFA2 checkout. DNS resolution and localhost socket creation are also
unavailable in this sandbox. No external benchmark or browser pass is claimed.

On a network-enabled machine, install the documented dependencies and run:

```sh
python scripts/validate_release.py --checks docs,browser
python scripts/validate_release.py --checks cuda
python scripts/validate_release.py --checks external --wfa2-root /path/to/WFA2-lib
```

The external runner compiles the adapter and measures both high-memory WFA2
and ultralow-memory BiWFA using a recorded clean source revision.
