# Memory management

CPU wavefronts grow dynamically with score; at score s the safe diagonal radius is floor(s/gap_extend), intersected with physical sequence bounds. Exact mode never heuristically removes an attainable diagonal. Before allocating a level, the engine checks its accounted bytes against the caller's memory budget. It does not truncate inputs or return a partial alignment as exact.

Traceback retains all levels. Score-only evicts levels older than the maximum recurrence predecessor distance and substantially reduces retained wavefront storage. The budget accounts vector payloads plus estimated metadata, not allocator overhead, input copies, output strings or process RSS. It is not an operating-system memory limit.

Fast mode restricts diagonals to ±bandwidth around zero. Results are heuristic even if they happen to be optimal. Failure to reach the endpoint raises a resource error. Adaptive expansion and checkpoint/BiWFA traceback are not implemented.

The CUDA prototype uses a reusable arena and a rolling history. It checks device free memory, retains a 20% reserve and rejects over-budget jobs. Sequential calls permit reuse; concurrent length-aware batching and adaptive GPU scheduling remain unimplemented.
