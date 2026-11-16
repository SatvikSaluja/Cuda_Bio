# Limitations and roadmap

This is an initial functional CPU release, **not completion of the full CUDA research roadmap**.

- CUDA score prototype has not compiled or executed here; GPU traceback, automatic GPU dispatch, concurrent adaptive batching and measured performance improvements are outstanding.
- Exact CPU traceback retains O(s²) history; high-divergence long reads may hit the resource budget. 100 kb testing covers low-divergence synthetic pairs only.
- Fast mode is a fixed band, not adaptive. No exactness certificate for narrowed bands is implemented.
- CPU batches run sequentially. CLI is Python-based. Studio is local, session-only, bounded and unauthenticated.
- Mapping uses fixed minimap2 candidate endpoints and loads reference/read records in memory. Real mapper execution and real-data validation remain outstanding where minimap2 is unavailable.
- External WFA2/WFA-GPU/GASAL2 benchmark comparisons, indel/error-rate sweeps, peak RSS/VRAM instrumentation and sustained GPU resource tests are not complete.
- No public repository URL, release publication, clinical validation or GPU speedup claim is provided.

Priorities: validate CUDA recurrence on hardware; implement checkpointed traceback and transparent dispatch; compare against WFA2/WFA-GPU; improve long-read resource scheduling based on evidence.
