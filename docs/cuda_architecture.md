# Experimental CUDA architecture

The optional CUDA API remains **uncompiled and runtime-unvalidated in the development environment**. Do not interpret its existence as certified GPU support.

## Execution mapping

`experimental::cuda_scores` groups pairs into batches according to their scratch estimates, the configured budget and available device memory. A batch launches one full 32-thread block per alignment. Blocks are independent. Lane l computes diagonal low + tile*32 + l; wide wavefronts iterate through tiles.

Gap-opening M predecessors and gap-extension I/D predecessors are exchanged with full-mask `__shfl_up_sync`/`__shfl_down_sync`. Tile-edge neighbors are loaded from global memory. Every physical lane executes each exchange; logical lanes outside the final tile do not write. `__syncwarp` orders wavefront stores before the next score reads them. `__any_sync` broadcasts completion. No cross-warp communication is assumed.

Scratch retains max(mismatch, gap_open+gap_extend)+1 levels. Width is bounded by the explicit score budget and input rectangle; failure to reach the endpoint raises a resource error. Allocation, transfer, launch and synchronization errors are checked. Kernel definitions have internal linkage to permit header inclusion in multiple translation units.

## Public Python behavior

Build and install the optional `_cuda` extension, then explicitly set:

```sh
export WARPALIGN_EXPERIMENTAL_CUDA=1
```

- `backend="cuda", score_only=True`: GPU scoring when available; strict requests can disable fallback.
- Full result requests: rolling GPU scoring determines the exact score; a second warp scoring pass retains full history through that score. Lane 0 of a separate kernel reconstructs reverse SAM operations. Host code replays/rescores those operations in linear time and encodes CIGAR, without CPU alignment recomputation. Results report `cuda`. Each traceback runs separately with explicit capacity checks and CPU fallback on resource failure.
- `backend="auto"`: considers experimental CUDA only when explicitly opted in.
- Fast mode remains a CPU implementation.

GPU result timings are amortized batch wall time (`timing_scope="amortized_batch_wall"`), not isolated per-pair kernel timings. CPU results report CPU engine timing. Benchmarks measure complete batch wall time separately.

C++ consumers can call the experimental CUDA functions directly; the ordinary `Aligner` remains the validated CPU API. Headers using GPU code still require CUDA compilation and runtime support.

## Validation

Run `scripts/validate_cuda.sh` on an actual CUDA host. It builds C++ and Python targets, executes CPU/GPU equivalence tests, runs memcheck/initcheck/synccheck and tests public Python dispatch. The Colab notebook provides the same workflow. No-GPU tests skip explicitly.

The shared host/device traceback routine is tested on the CPU against 4,000 randomized and 1,922 exhaustive cases. This does not validate GPU compilation, memory ordering or device execution.

Remaining optimization work includes checkpointed GPU history, batched traceback, asynchronous transfers, streams, per-pair recovery inside failed batches, and alternative multi-warp mappings. No external speedup claim is established.

Reference: [NVIDIA CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/).
