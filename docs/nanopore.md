# Oxford Nanopore workflow

Install minimap2 separately and confirm `minimap2 --version` works. Supply a reference and reads:

```sh
warpalign map --reference reference.fa --reads nanopore_reads.fastq   --mapper minimap2 --preset map-ont --backend auto --output nanopore.refined.paf
```

Minimap2 discovers candidate intervals. WarpAlign globally aligns each reported query interval against its target interval, reverse-complementing negative-strand query intervals. This refines base-level alignment within fixed candidate endpoints, not the full mapping search. High-divergence reads can exceed the memory budget; failure is explicit. Do not interpret successful synthetic low-divergence long-read tests as nanopore validation.
