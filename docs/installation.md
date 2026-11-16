# Installation

Requirements: C++17 compiler, CMake >=3.18 for C++ tests/install, Python >=3.10 for bindings/CLI, Node >=20.19 for Studio. CUDA is optional and currently experimental.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[studio,test,docs]'
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
cmake --install build --prefix "$PWD/install"
cd apps/studio
npm install
npm run build
```

The installed C++ package supports `find_package(WarpAlign CONFIG REQUIRED)` and `WarpAlign::warpalign`. A simple consumer can instead include the `include/` directory directly. No Python dependency is required.

For the prototype on an equipped host:

```sh
cmake -S . -B build-cuda -DWARPALIGN_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=native
cmake --build build-cuda
ctest --test-dir build-cuda --output-on-failure
compute-sanitizer build-cuda/test-cuda
```

Use an explicit CUDA architecture if your CMake does not support `native`. CUDA compilation is not evidence of runtime correctness. The Python package currently always uses CPU WFA.
