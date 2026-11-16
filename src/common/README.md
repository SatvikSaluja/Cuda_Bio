# Source organization

CPU implementation resides in include/warpalign/cpu_backend.hpp to support header-oriented consumption. Python bindings compile that exact implementation from python/bindings.cpp. CUDA device code and the reusable arena reside in include/warpalign/*.cuh; tests/cuda/score.cu is the standalone experimental target. Input and mapping orchestration reside in python/warpalign/io.py and mapping.py.
