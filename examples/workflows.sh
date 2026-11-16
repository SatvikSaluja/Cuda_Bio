#!/usr/bin/env bash
set -euo pipefail
# Replace these paths with local, appropriately licensed inputs.
warpalign align-pairs --queries queries.fa --targets targets.fa --output results.paf
warpalign map --reference reference.fa --reads nanopore.fastq --preset map-ont --output ont.paf
warpalign map --reference reference.fa --reads hifi.fastq --preset map-hifi --output hifi.paf
python benchmarks/scripts/run.py --lengths 100,1000,10000 --batches 1,4
