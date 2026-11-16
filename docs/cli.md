# CLI

```sh
warpalign align-pairs --queries reads.fa --targets targets.fa   --backend auto --mode exact --mismatch 4 --gap-open 6 --gap-extend 2   --batch-size 256 --memory-mb 512 --output results.paf
warpalign align-pairs --queries reads.fa --targets targets.fa   --score-only --format jsonl --output scores.jsonl
warpalign map --reference reference.fa --reads reads.fq   --mapper minimap2 --preset map-ont --output refined.paf
```

Pairing is by input order, not identifier equality. Different record counts are errors. Input is streamed in bounded batches; batch size controls buffering/progress, not GPU concurrency. Output replacement is atomic, so a failed run does not replace an existing output with partial results.

PAF uses unknown MAPQ 255 for pairwise jobs; refinement preserves mapper MAPQ without recalibration. `wc:i` is positive alignment cost; `NM:i` is edit distance, `cg:Z` is extended CIGAR, `wb:Z` is backend and `wh:i` is heuristic status. JSONL includes fuller provenance. Score-only requires JSONL because PAF needs alignment counts.
