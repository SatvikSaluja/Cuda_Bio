# Exact and fast modes

Exact WFA explores all score-reachable diagonals within the sequence rectangle. Checkpointing and penalty normalization preserve its recurrence and optimum. Resource exhaustion raises an error; it never changes exact mode to heuristic mode.

Fast mode restricts diagonals to ±bandwidth. Every successful result remains marked heuristic. With `adaptive_band=True`, an unreachable alignment causes the bandwidth to double until success or `max_bandwidth` is reached. The returned bandwidth and `heuristic_retries` describe the actual execution. Memory exhaustion is not treated as a reason to expand the band.

```python
from warpalign import Aligner
r = Aligner(mode="fast", bandwidth=8, adaptive_band=True,
            max_bandwidth=256).align("A"*100, "A"*80)
assert r.heuristic_used
print(r.bandwidth, r.heuristic_retries)
```

A successful narrow-band result can still be suboptimal; automatic retry is not an exactness certificate. An unchanged score after expansion is also insufficient proof. Studio's measured agreement is empirical and reports its reference source.
