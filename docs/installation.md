# Installation

Requirements: a C++17 compiler, Python >=3.10 for Python/CLI, CMake >=3.18 for the CPU C++ package, and a supported Node release (CI uses Node 22) for frontend builds. CUDA is optional and experimental.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[studio,test,docs]' build twine
(cd apps/studio && npm ci && npm run build && npm test)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
python -m pytest -q
warpalign doctor
warpalign-studio
```

To distribute a wheel with Studio, build the frontend **before** `python -m build`; `scripts/build_release.sh` does this and checks the distributions. CPU-only C++ consumers need neither Python nor CUDA:

```sh
cmake --install build --prefix "$PWD/install"
```

Use `find_package(WarpAlign CONFIG REQUIRED)` and link `WarpAlign::warpalign`, or include `include/` directly.

## Experimental CUDA

On a compatible NVIDIA host with NVCC, install the Python package editable and pybind11, then run:

```sh
python -m pip install -e '.[test]' pybind11 cmake
bash scripts/validate_cuda.sh
```

The script uses a CMake version supporting `CMAKE_CUDA_ARCHITECTURES=native`; use an explicit architecture if needed. It copies the compiled optional extension into the editable Python package. Installed non-editable packages require installing/copying the extension into their own package directory. Compilation does not imply runtime correctness. See the CUDA architecture page and Colab notebook.

Offline packagers can set `PYBIND11_INCLUDE_DIR` to an existing SDK's include directory and build without build isolation, using installed setuptools/wheel. This is an explicit packaging option, not a runtime PyTorch dependency.
