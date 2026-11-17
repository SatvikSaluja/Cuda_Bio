# Workflow and Colab examples

## Snakemake / Nextflow

Install the respective workflow engine separately, then run from the repository root:

```sh
snakemake --snakefile examples/pipelines/Snakefile --cores 4
nextflow run examples/pipelines/main.nf --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa
```

The examples run the actual CLI with bounded CPU threads and memory. Pipeline executors were not available for testing in this environment. Container recipes and platform-specific cluster configuration remain deployment choices.

## Colab without committing local work

The notebook normally clones the public repository. To use your current uncommitted source instead:

```sh
python scripts/package_colab.py --output /tmp/warpalign-colab.zip
```

Upload that source archive in Colab and extract it under `/content/warpalign`, then skip the notebook's clone command and run its installation/validation cells. The archive includes Git-listed source and untracked nonignored files, so review its contents before uploading. Ignored dependencies, generated native binaries and local SQLite data are excluded.

Select a GPU runtime and verify both `nvidia-smi` and `nvcc --version`. All CUDA checks must actually execute; compilation and skipped tests are not correctness evidence. Colab sends uploaded data to cloud infrastructure, unlike local Studio. Use the synthetic fixtures until hardware correctness is established.
