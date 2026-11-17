# Architecture

```text
React Studio → loopback FastAPI → SQLite job/result store
                         ↓
                cancellable worker process
                         ↓
                   Python Aligner
                 /                \
          pybind11 CPU       optional CUDA module
               ↓                   ↓
       indexed affine WFA     batched warp scoring
               ↓                   ↓
      full/checkpoint trace   CPU trace for full results

minimap2 → candidate PAF → disk-backed sequence slices → Aligner
```

The CPU C++ API is header-oriented and dependency-free. CPU hot paths use indexed score history and normalized penalties. Pybind11 releases the GIL; Python batch threads share the configured wavefront budget.

Studio keeps sequence/result records in local SQLite and uses separate processes for cancellable jobs. Paginated metadata excludes sequences; the viewer fetches an individual detail payload on demand. Downloads stream rows. A single POSIX service owns a data directory; interrupted jobs are marked on restart.

The CUDA API remains experimental. Independent warp blocks consume per-alignment slices in a reusable arena. Python opt-in distinguishes `cuda` execution and explicit CPU fallback. Full device traceback retains bounded history, reconstructs operations on-device, and validates/encodes them on the host. The ordinary C++ Aligner remains CPU-only; its experimental CUDA functions are separately callable.

The release build copies the compiled React bundle into the wheel. Static documentation remains separate from the local application. No external service or telemetry is needed for ordinary use.
