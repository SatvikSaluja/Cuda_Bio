# Build environment

Inspected 2026-11-16, Linux x86_64. Workspace initially contained only protected empty metadata directories; no existing source or usable Git repository.

- GCC 13.3.0; Python 3.12.3; Node 24.22.1; Git available.
- CMake initially absent; reused an existing local CMake 4.4.4 installation for validation.
- No `nvidia-smi`, NVCC or detected CUDA toolkit. GPU model, driver, compute capability and VRAM unavailable.
- CUDA compilation and GPU execution are **not validated** in this environment.
- Network/DNS restrictions prevented dependency downloads. The local `.venv` uses a validation-only .pth pointing at pre-existing Python dependencies. Pybind11 headers were reused from a local installation (no torch runtime dependency). Frontend source builds use available local dependencies; a clean offline npm installation from cached registry packages also passed. Docker and MkDocs are not installed. See the development report for the current validation evidence.
