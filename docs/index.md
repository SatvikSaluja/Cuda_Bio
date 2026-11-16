# WarpAlign

## Explore alignment. Measure the evidence.

Long reads expose a practical problem: dense alignment matrices grow with both sequence lengths. Wavefront alignment instead advances through increasing edit costs, making similar long sequences tractable.

WarpAlign combines a C++17 affine WFA engine with Python, a streaming CLI and a private local workbench. **Version 0.1.0 is a CPU research release with an experimental, unvalidated CUDA score kernel.** It is not clinically validated and has no established GPU speedup.

[Install WarpAlign](installation.md) · [Run your first alignment](quickstart.md) · [Inspect measured benchmarks](benchmarks.md)

```text
FASTA / FASTQ → CLI or Studio → Python bindings → C++ affine WFA
                         ↓                          ↓
                    local results               score + CIGAR
minimap2 → candidate intervals → global refinement
```

- Exact global affine costs and auditable traceback.
- Explicit heuristic banding and CPU fallback metadata.
- Memory budgets and score-only rolling wavefront history.
- Canvas alignment inspection and measurements from the real engine.

The source is in this monorepo. A public GitHub repository has not been configured; no repository URL is invented. See [prior art](prior_art.md) for the upstream projects this work builds on conceptually.

```sh
python -m pip install '.[studio]'
warpalign align-pairs --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa --output results.paf
```
