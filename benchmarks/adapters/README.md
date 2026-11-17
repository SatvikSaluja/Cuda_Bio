# External baseline protocol

`wfa2.c` is an original thin adapter for a separately installed WFA2-lib. It is not a copy of WFA. Build against a pinned WFA2 revision and preserve that dependency's MIT notices when distributing it. The adapter is source-reviewed but not compiled here because WFA2 is unavailable.

```sh
cc -O3 -I/path/to/WFA2-lib benchmarks/adapters/wfa2.c \
  -L/path/to/WFA2-lib/lib -Wl,-rpath,/path/to/WFA2-lib/lib -lwfa -lm -o /tmp/wfa2-adapter
python benchmarks/scripts/compare_external.py --baseline-version YOUR_WFA2_COMMIT \
  --length 1000 --pairs 16 /tmp/wfa2-adapter ultralow
```

The runner first checks known scores for mismatch, gap and match, then checks every measured pair. It records process wall time separately from adapter engine time. Default affine penalties are x=4,o=6,e=2; match=0. The adapter requests complete alignment, not score-only, to match WarpAlign's measured scope. Compare high and ultralow memory modes.

A WFA-GPU or GASAL2 adapter can implement the same tab-delimited input / JSON-lines output protocol. No compatible adapter or measured result for those projects is currently supplied. Reject incompatible scoring and modes; do not use this pairwise protocol to compare a mapper's seed-and-chain stage.
