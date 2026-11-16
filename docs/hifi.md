# PacBio HiFi workflow

```sh
warpalign map --reference reference.fa --reads hifi_reads.fastq   --preset map-hifi --backend cpu --mode exact --output hifi.refined.paf
```

The `map-hifi` preset belongs to minimap2's candidate discovery stage. WarpAlign uses the configured affine penalties for fixed-interval refinement. Tune them deliberately for your analysis; no sequencing-error model is inferred. Inspect CIGARs and score distributions before downstream use. Mapping quality remains the original mapper value and is not recalibrated after refinement.
