# Accuracy and validation

`tests/unit/core.cpp` independently implements affine DP and runs 4,000 deterministic random pairs with varied penalties and N policies. Each WFA result must match the DP optimal cost; each CIGAR is replayed against the inputs and rescored. Score-only is compared against traceback. Equally optimal CIGARs are allowed.

The suite also covers empty/unequal sequences, substitutions, gaps, lowercase, memory failures and low-divergence lengths from 100 bp through 100 kb. Python tests cover API validation, batch mismatches, explicit fallback, input parsing, CLI output and reverse-strand candidate refinement. Local API tests submit real uploaded fixtures and benchmark jobs. Frontend tests verify CIGAR viewport orientation and bounded rendering for 100 kb.

```sh
ctest --test-dir build --output-on-failure
python -m pytest -q
cd apps/studio && npm run build && npm test
```

CUDA tests are separate and must execute on a compatible NVIDIA GPU. No device is a skip, never a pass. Compile-only CI is separately labeled. See the development report for executed checks and environmental limitations.
