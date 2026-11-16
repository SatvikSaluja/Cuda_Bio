# Prior art and attribution

Audit date: 2026-11-16. No third-party alignment implementation is copied or vendored.

| Project | Approach and modes | Execution, memory and integration | Implications for WarpAlign |
|---|---|---|---|
| [WFA2-lib](https://github.com/Marco-Sola-Lab/WFA2-lib) | Exact and heuristic WFA; global and ends-free; affine and other distance models | CPU C/C++ API; reusable aligners; BiWFA ultralow mode uses O(s) memory | Mature long-read baseline. WarpAlign's full-history traceback is less memory efficient; comparison must select the appropriate WFA2 memory mode. |
| [WFA-GPU](https://github.com/Marco-Sola-Lab/WFA-GPU) | GPU global affine WFA, score and traceback, heuristic banding | Cooperative GPU workers; configurable threads, batch size and error budget; over-budget alignments fall back to CPU; C/CUDA library and executable | GPU WFA, cooperative diagonal computation, banding and fallback already exist. These are not new contributions. |
| [GenomeWorks](https://github.com/NVIDIA-Genomics-Research/GenomeWorks) | GPU toolkit with pairwise alignment, mapping, seed extension and partial-order alignment modules | CUDA/C++ SDK and Python package; per-module batching and device storage | A broader toolkit, not a directly interchangeable affine-WFA baseline. Verify each module's scoring, supported modes and memory configuration before comparison. |
| [GASAL2](https://github.com/nahmedraja/GASAL2) | GPU affine DP, local/global/semiglobal; optional traceback | Packed sequence batches, CUDA streams, reusable host/device storage that grows with demand; C/CUDA interface | Different algorithm and score convention. Build-time maximum query length and padding require explicit compatibility checks for ultra-long inputs. |
| [minimap2](https://github.com/lh3/minimap2) | Minimizer seeds, chaining and alignment; long-read and spliced mapping | CPU SIMD implementation, index and CLI; C API, separate Python binding ecosystem | Use as candidate discovery. Pairwise refinement cannot recover loci omitted by mapping; compare full pipelines separately. |

## Licenses

WFA2-lib and WFA-GPU publish MIT licenses (see repository LICENSE files). GenomeWorks and GASAL2 publish Apache-2.0 licenses. Minimap2 publishes MIT in LICENSE.txt. Preserve notices and license copies when distributing dependencies; Apache redistribution also requires applicable NOTICE and modification notices. External executables remain separately installed. Pybind11 is BSD-style; React/Vite are MIT; FastAPI is MIT. This repository's original implementation is MIT. Audit pinned dependency versions before redistribution.

## Contribution and evaluation plan

The defensible engineering target is transparent resource accounting across an accessible local stack: explicit exact/heuristic results, reproducible CIGAR validation, bounded wavefront allocation and measured fallback reporting. A tiled warp kernel can exchange neighboring predecessor offsets through shuffles while loading tile boundaries from global memory. Comparable cooperative execution exists already. A measurable improvement over WFA-GPU has **not** been established. Benchmark rolling score history against retained traceback history as an internal memory improvement; do not characterize it as algorithmic novelty.

An ultra-long low-divergence sequence can be inexpensive for WFA; a shorter high-divergence pair can exhaust memory. Length alone is not a support guarantee. BiWFA/checkpointed traceback and truly concurrent resource-aware GPU batches remain optimization targets.
