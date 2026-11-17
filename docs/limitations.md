# Limits and remaining validation

Version 0.2.0 is a functional CPU research release with optional **experimental CUDA batch scoring and traceback**. It is not a finished GPU alignment library or a demonstrated improvement over external WFA implementations.

## Implemented improvements

Indexed CPU wavefront history, penalty normalization, checkpoint/recompute traceback, score-only rolling history, CPU batch threads, strict fallback controls, deadlines, adaptive heuristic retries, persistent/cancellable Studio jobs, global result search, indexed CIGAR inspection, reproducible frontend installation, bundled Studio wheels, disk-backed mapping inputs, and expanded benchmark/CI tooling.

## Outstanding

- No CUDA compiler or compatible device was available here. All CUDA changes require compilation, device execution and Compute Sanitizer before enabling them for research use. Python GPU dispatch is gated by `WARPALIGN_EXPERIMENTAL_CUDA=1`.
- CUDA full-alignment source now performs device traceback and reports `cuda`, with a linear host replay/rescore check. Its shared traceback logic passes host tests, but CUDA compilation/runtime remains unvalidated. Full history is memory bounded; scoring is recomputed for traceback, one pair at a time. Multi-warp scheduling and checkpointed GPU traceback remain unimplemented.
- Checkpointed CPU traceback reduces retained history for some workloads but is not linear-memory BiWFA. Its interval trades recomputation and checkpoint/segment memory; it may use more memory on small cases.
- Adaptive banding widens only after an unreachable endpoint/failure. It is always heuristic; it does not certify optimality or retry a successful suboptimal alignment.
- Real minimap2 execution, real sequencing datasets, WFA2 adapter compilation, and external WFA2/WFA-GPU/GASAL2 performance comparisons remain unrun. WFA-GPU/GASAL2 protocol adapters are not supplied.
- Studio is local, single-service, session-job execution with persistent SQLite results. It is not a public authenticated service. Browser execution is unverified in this sandbox because loopback binding is denied and the browser lacks required system libraries.
- MkDocs source/navigation is present; a local MkDocs build requires unavailable packages. Clean frontend installation was verified from cached registry packages; a clean native wheel was built using locally available SDK headers.
- Nextflow/Snakemake examples and Colab notebook are provided, but their external runtimes were not available for execution here.

A 100 kb low-divergence synthetic test is not a support guarantee for arbitrary 100 kb reads. Resource exhaustion is explicit and never silently truncates inputs.
