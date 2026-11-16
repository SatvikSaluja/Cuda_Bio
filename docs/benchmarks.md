# Performance benchmarks

No GPU speedup or external-baseline comparison has been established. See the checked-in `benchmarks/results/local/raw.json`, CSV and SVG for actual CPU measurements and host metadata.

```sh
python benchmarks/scripts/run.py --lengths 100,500,1000,5000,10000,20000,50000,100000   --batches 1,4 --repeats 3 --error-rate 0.001
```

The harness generates synthetic substitution-only DNA with seed 1729, performs an unmeasured warm-up and records all timed repeats, medians and min/max. It compares traceback and rolling score-only history. `wavefront_bytes` is accounted algorithm storage, not process peak RSS. GPU memory is null. These low-divergence synthetic results do not characterize real nanopore performance or indel-heavy workloads.

External comparisons must use the same sequence pairs, scoring convention, modes and output scope. Use WFA2's suitable memory mode; confirm WFA-GPU and GASAL2 build-time/resource limits. Measure minimap2 at the full mapping pipeline level. Record versions, compiler flags and machine details; do not import speedups from published machines. External binaries are not installed here.
