# Memory and traceback

CPU wavefront offsets use indexed score history. Affine penalties are divided by their greatest common divisor internally, then scores are restored to the caller's convention. This eliminates unreachable score levels without changing the optimum.

Three storage policies are available:

| Policy | Configuration | Behavior |
|---|---|---|
| Full traceback | `checkpoint_interval=0` | Retains all wavefront levels; fastest default traceback |
| Checkpointed traceback | `checkpoint_interval=128` | Retains rolling snapshots and recomputes intervening segments during traceback |
| Score only | `score_only=True` | Retains only predecessor levels; no CIGAR/counts |

Checkpoint intervals count **normalized score levels**, not bases. The forward pass retains the recurrence's predecessor window at each checkpoint. Reverse traversal restores the preceding checkpoint, recomputes a bounded segment and traces backward until another restore is needed. Ties use the same rules as full traceback. This is exact recomputation, not diagonal pruning.

All retained snapshot and segment wavefront bytes are included in the reported peak accounting. The budget still excludes input/output copies, allocator overhead and application state; it is not a hard RSS limit. CPU `threads` divides the supplied wavefront budget among active alignment workers. Parallel calls outside one batch have independent budgets.

Checkpointing is not guaranteed to save memory for every interval/workload. The supplied experiment shows lower wavefront memory and higher runtime for the larger synthetic examples; raw records are under `benchmarks/results/checkpoint-v020/`. Isolated benchmark workers also report process peak RSS including imports, generation, reference computation and warm-up.

CUDA batches reserve an arena based on the caller budget and free device memory, retain a 20% free-memory margin for growth, and reuse capacity across calls. Each pair has its own ring scratch slice. `gpu_memory_bytes` describes the allocated arena, not total driver/context VRAM. Full-result requests first determine scores with rolling storage, then retain all levels through the attained score for device traceback. They process traceback one pair at a time and reject allocations exceeding the memory budget. GPU checkpoint/recompute traceback is not implemented.
