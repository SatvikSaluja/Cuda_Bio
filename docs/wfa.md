# How affine WFA works

Let h be the consumed query length and k = query_position − target_position. Each state stores the furthest reachable h on a diagonal at an exact cost s. With mismatch x, gap opening o and extension e:

```text
I[s,k] = max(M[s-o-e,k-1], I[s-e,k-1]) + 1
D[s,k] = max(M[s-o-e,k+1], D[s-e,k+1])
X[s,k] = M[s-x,k] + 1
M[s,k] = extend_matches(max(X[s,k], I[s,k], D[s,k]))
```

Invalid predecessor levels/diagonals are unreachable. Moves outside the sequence rectangle are invalid. Initialization is M[0,0] followed by greedy match extension. The first score reaching h=query_length at k=query_length−target_length is optimal, because costs are positive (opening may be zero) and every lower score was explored.

Traceback reverses these state transitions and match extensions, then run-length encodes `=`, `X`, `I`, `D`. `I` consumes query only; `D` consumes target only. Ties can have different optimal CIGARs. The independent test oracle uses affine dense dynamic programming, not this recurrence.

The full history costs O(s²) storage in the usual WFA regime. Score-only discards score levels older than the largest predecessor distance; no CIGAR statistics are available in that mode.
