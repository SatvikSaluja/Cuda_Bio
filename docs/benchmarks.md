# Reproducible benchmarks

The repository contains actual CPU measurements, not fabricated GPU values. The original `benchmarks/results/local/` records the initial low-divergence baseline. Version 0.2.0 substitution/indel measurements are in `cpu-v020/`; `checkpoint-v020/` records the checkpoint trade-off. `ultralong-v020/` contains CPU runs at 20, 50 and 100 kb with 1% sampled substitutions and 0.2% sampled indels, checkpoint interval 128 and three measured repeats. These synthetic workloads do not establish arbitrary ultra-long-read support.

```sh
python benchmarks/scripts/run.py --lengths 100,1000,5000,10000 --batches 1,4 \
  --repeats 3 --error-rate .02 --indel-rate .01 --output benchmarks/results/my-cpu
python benchmarks/scripts/run.py --lengths 1000,5000,10000 --batches 1 \
  --repeats 3 --error-rate .02 --indel-rate .01 --checkpoint-interval 128 \
  --output benchmarks/results/my-checkpoint
```

Each configuration runs in an isolated process. Raw records include the deterministic seed, dataset hash, penalties, mode, actual backend, fallback rate, repeat timings, median/range/stdev, source hashes, CPU/compiler metadata, wavefront accounting and process peak RSS. RSS includes imports, input generation, reference computation and warm-up; it is not kernel-only memory. Full-batch warm-up is excluded from timings. Failure records are saved separately and cause a nonzero runner exit.

Small workloads use independent affine DP for score comparison; larger workloads explicitly identify the CPU exact WFA reference as non-independent. Synthetic indels are sampled events, not a calibrated platform error model. No general nanopore/HiFi accuracy claim follows from these data.

The checkpoint comparison holds generated inputs/scoring constant. It reduces retained wavefront memory on the larger recorded workloads at the cost of recomputation time. This established storage technique is an engineering improvement here, not a claim of algorithmic novelty or superiority over BiWFA.

## External comparisons

`benchmarks/scripts/compare_external.py` runs a separately installed protocol adapter on identical pairs. It checks known score conventions and every resulting score before recording timings. Adapter engine time and subprocess wall time remain separate. `benchmarks/adapters/wfa2.c` explicitly disables default heuristics and sets end-to-end alignment, following the [WFA2 configuration documentation](https://github.com/Marco-Sola-Lab/WFA2-lib#15-important-notes-and-clarifications). It provides a source-reviewed adapter for WFA2 high/ultralow modes; it has not compiled or run here. WFA-GPU/GASAL2 adapters and comparative results remain outstanding.

For GPU benchmarking, first pass device validation, then request `--backend cuda --no-fallback` with experimental opt-in. Full CUDA timings include two device scoring passes, device traceback, transfers and linear host replay. GPU arena bytes are distinct from total VRAM; CUDA-event kernel/transfer timing is not yet instrumented. Compare full mapping pipelines separately from pairwise alignment.
