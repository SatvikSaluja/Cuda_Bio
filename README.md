# WarpAlign

Affine wavefront alignment with a C++17 engine, Python bindings, a streaming CLI and a private local workbench.

**0.2.0 development status:** CPU alignment is validated against independent affine DP. CUDA batch scoring, device traceback and Python dispatch are experimental and still require compiler/device validation. Full CUDA requests now use device traceback with host CIGAR replay; this new path is not GPU-validated. No external GPU-speedup claim is established.

[Source](https://github.com/SatvikSaluja/Cuda_Bio) · [Installation](docs/installation.md) · [Development report](docs/development_report.md) · [Limitations](docs/limitations.md)

## Install and run

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[studio,test,docs]'
(cd apps/studio && npm ci && npm run build)
warpalign doctor
warpalign align-pairs --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa --output results.paf
warpalign-studio --port 8000
# Open http://localhost:8000
```

The Studio dashboard includes a **Try a real demo** action, so no external data is needed to test the complete job flow. A release wheel built after the frontend includes the Studio assets. Data stays on local disk by default; Colab is explicitly a cloud workflow.

```python
from warpalign import Aligner
aligner = Aligner(backend='cpu', threads=4, checkpoint_interval=128)
results = aligner.align_batch(['ACGT', 'AAA'], ['ACGTT', 'AA'])
for result in results:
    print(result.score, result.cigar, result.backend)
```

## What is implemented

- Genuine affine M/I/D WFA, optimal global costs, traceback, extended SAM CIGAR and configurable N handling.
- Indexed score history, exact penalty normalization, rolling score-only storage and checkpoint/recompute traceback.
- Separate heuristic banding with optional expansion/retry and explicit parameters.
- CPU batch threads with a shared wavefront budget, deadlines and strict no-fallback requests.
- FASTA/FASTQ/gzip CLI, atomic PAF/JSONL output, input-order or identifier pairing and environment diagnostics.
- Minimap2 refinement adapter with disk-backed sequence indexing and mapper provenance.
- Persistent SQLite Studio history, cancellable process-isolated jobs, full-dataset search/sort and streamed exports.
- Responsive light/dark UI, demo jobs, indexed canvas viewer with variant navigation, and actual measurement charts.
- Synthetic substitution/indel benchmarks, isolated-process RSS, independent DP checks for small cases, an external-baseline protocol and WFA2 adapter source.
- Colab validation notebook, Nextflow/Snakemake examples and expanded CI definitions.

Scoring minimizes mismatch × substitutions + Σ(gap_open + gap_extend × gap_length). `I` consumes query, `D` consumes reference. Coordinates are zero-based, half-open. Exact resource exhaustion is an error, never silent truncation or heuristic substitution.

## Build and validate

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
python -m pytest -q
(cd apps/studio && npm test)
python -m mkdocs build --strict
```

C++ consumers can include `warpalign/warpalign.hpp` directly or use the installed `WarpAlign::warpalign` target. Python/CUDA are not required for the CPU C++ library.

For experimental CUDA on an equipped machine, use [the Colab notebook](notebooks/colab_cuda.ipynb) or `scripts/validate_cuda.sh`. Opt-in is required through `WARPALIGN_EXPERIMENTAL_CUDA=1`. Use `allow_fallback=False` or CLI `--no-fallback` when GPU execution is mandatory.

## Evidence and limits

The test suite includes 4,000 randomized comparisons against independent affine DP, CIGAR replay, checkpoint equivalence and low-divergence tests through 100 kb. Recorded 0.2.0 CPU experiments include substitution/indel workloads and memory/runtime trade-offs; see [benchmark methodology](docs/benchmarks.md).

Outstanding: hardware validation, real mapper/dataset execution, external baseline measurements and live browser validation in a permitted environment. No clinical-readiness claim is made. See [prior art](docs/prior_art.md), [contributing](CONTRIBUTING.md) and the [development report](docs/development_report.md) for precise validation status.
