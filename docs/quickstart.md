# Quick start

```python
from warpalign import Aligner
result = Aligner().align("ACGTACGT", "ACGTTACGT")
print(result.score, result.cigar, result.backend)
# Cost 8; one reference deletion under default penalties; CPU.
```

```sh
warpalign align-pairs --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa --backend auto --output results.paf
warpalign-studio
```

Build Studio first (`cd apps/studio && npm ci && npm run build`). Open http://127.0.0.1:8000. Upload the fixture files in New alignment, wait for the real job to complete, select a result, then inspect its CIGAR. Performance lab creates seeded synthetic inputs and times the installed engine.
