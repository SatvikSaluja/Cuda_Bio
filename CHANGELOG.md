# Changelog

## 1.0.0 — release preparation

First CPU-first research release: exact/checkpointed affine WFA, CLI and Python APIs, local Studio with a real variant demo, persisted results and measured charts, optional minimap2 refinement, CPU Docker packaging and reproducible benchmarks. CUDA scoring/device traceback remain experimental and hardware-unvalidated. See [release notes](RELEASE_NOTES.md) for scope, evidence and limitations. No tag or public release has been created by this preparation.

## 0.2.0 — development, 2026-11-17

Indexed/normalized CPU WFA; checkpointed exact traceback; threaded batches and deadlines; adaptive heuristic retries; strict backend requests; experimental CUDA batching/device traceback and Python dispatch with explicit fallback metadata; disk-indexed mapper inputs; persistent cancellable Studio jobs; global search, streamed exports, demo jobs and redesigned light/dark UI; indexed variant navigation; portable frontend lockfile and bundled wheels; expanded benchmarks, CI and workflow examples. Added a multi-stage CPU Docker demo, OFF/ON/AUTO CUDA build selection, a 1.2 kb synthetic variant demo with measured charts, and full/checkpoint comparison tables. Hardware-dependent validation remains outstanding.

## 0.1.0 — initial CPU implementation

Affine WFA, traceback/score-only, fixed-band heuristic mode, Python/CLI/local Studio and isolated CUDA score prototype. No GPU-support or external-speedup claim.
