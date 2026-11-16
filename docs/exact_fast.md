# Exact and fast modes

Exact mode explores all score-reachable diagonals within the input rectangle. The terminal state at the first reachable cost has the optimum under the configured model. Resource exhaustion raises an exception, never a heuristic substitute.

Fast mode uses a fixed symmetric band. A successful result may exclude a cheaper path and is always marked heuristic, with bandwidth recorded. Widening a band and observing an unchanged score alone is not a proof of exactness. A future exact retry implementation must use a lower-bound certificate or expand to all reachable diagonals.

Studio's agreement chart compares measured heuristic scores against CPU exact scores on identical generated pairs. That empirical agreement is not a guarantee on other inputs.
