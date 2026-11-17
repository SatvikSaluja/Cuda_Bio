# CLI

```sh
warpalign doctor
warpalign --version
warpalign align-pairs --queries reads.fa --targets targets.fa \
  --backend cpu --mode exact --threads 4 --checkpoint-interval 128 \
  --batch-size 256 --memory-mb 512 --timeout-seconds 30 --output results.paf
warpalign align-pairs --queries reads.fa --targets targets.fa \
  --pairing id --score-only --format jsonl --output scores.jsonl
warpalign align-pairs --queries reads.fa --targets targets.fa \
  --mode fast --bandwidth 8 --adaptive-band --max-bandwidth 256 --output fast.jsonl
warpalign map --reference reference.fa --reads reads.fq \
  --mapper minimap2 --preset map-ont --output refined.paf
```

Pairing defaults to input order. Identifier pairing requires unique, identical ID sets and currently materializes the paired records. Order mode streams bounded batches. Different record counts are errors. Threads execute CPU pairs concurrently; batch size controls buffering. Output is replaced atomically after successful completion.

Explicit CUDA requests can use `--no-fallback` and configure the score bound with `--cuda-max-score`. Experimental GPU dispatch requires its separately built extension and `WARPALIGN_EXPERIMENTAL_CUDA=1`. C++ consumers remain independent of this Python CLI.

JSONL rows include scoring/resource configuration, software version, backend, timing scope, fallback reason and heuristic parameters. PAF uses unknown MAPQ 255 for pairwise jobs; refinement preserves mapper MAPQ. `wc:i` is positive affine cost, `NM:i` is edit distance, `cg:Z` is extended CIGAR, `wb:Z` is actual backend and `wh:i` is heuristic status. Score-only requires JSONL.
