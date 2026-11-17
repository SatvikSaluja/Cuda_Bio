#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
nvidia-smi
nvcc --version
cmake -S . -B build-cuda -DWARPALIGN_CUDA=ON -DWARPALIGN_CUDA_PYTHON=ON -DCMAKE_CUDA_ARCHITECTURES=native -DPython_EXECUTABLE="$(command -v python)"
cmake --build build-cuda -j2
./build-cuda/test-cuda
compute-sanitizer --tool memcheck --error-exitcode 1 ./build-cuda/test-cuda
compute-sanitizer --tool initcheck --error-exitcode 1 ./build-cuda/test-cuda
compute-sanitizer --tool synccheck --error-exitcode 1 ./build-cuda/test-cuda
# Editable installation uses python/warpalign; release installers can copy to
# their installed package directory instead.
cp build-cuda/python/warpalign/_cuda*.so python/warpalign/
WARPALIGN_EXPERIMENTAL_CUDA=1 python -m pytest tests/cuda/test_dispatch.py -q
