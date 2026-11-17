# Validation

The C++ suite compares WFA against independent affine DP on 4,000 seeded random pairs with varied penalties and N policies, replays/rescores CIGARs and compares checkpoint/full/score-only results. It covers empty/unequal inputs, gaps, lowercase, resource failures and low-divergence lengths from 100 bp through 100 kb. Checkpointing preserves the full implementation's tie rules.

Python tests cover strict fallback, deadlines, threaded batches, identifier pairing, adaptive heuristic retries, independent benchmark scores, disk-backed sequence intervals, malformed FASTQ, CLI atomic output, persistence, global result search, demo submission, detail fetch, real job cancellation and streamed downloads.

Frontend tests cover SAM I/D orientation, indexed coordinates, malformed CIGAR rejection and viewport access near the end of many-run alignments. TypeScript and Vite build checks run separately. Live browser checks are defined in `tests/e2e/studio.mjs`; they submit a real demo to a running local service.

```sh
ctest --test-dir build --output-on-failure
python -m pytest -q
(cd apps/studio && npm ci && npm run build && npm test)
```

CI definitions include GCC/Clang, sanitizers, a Python matrix, built-wheel installation outside the checkout, documentation builds and a live browser job. Actual CI execution must be confirmed in GitHub Actions; workflow definitions alone are not passing evidence.

CUDA has separate C++ and Python device tests plus Compute Sanitizer scripts. Missing hardware is a skip. CPU/GPU runtime correctness, WFA2 compilation, real minimap2 data and workflow-engine execution remain unvalidated in this environment.
