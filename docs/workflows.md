# Workflow and Colab examples

## Snakemake / Nextflow

Install the respective workflow engine separately, then run from the repository root:

```sh
snakemake --snakefile examples/pipelines/Snakefile --cores 4
nextflow run examples/pipelines/main.nf --queries tests/fixtures/queries.fa --targets tests/fixtures/targets.fa
```

The examples run the actual CLI with bounded CPU threads and memory. Pipeline executors were not available for testing in this environment. The root Dockerfile supplies a CPU Studio image; cluster executor configuration remains a deployment choice.

## Colab without committing local work

The notebook accepts an archive of your current uncommitted source:

```sh
python scripts/package_colab.py --output /tmp/warpalign-colab.zip
```

Run the notebook upload cell to extract that source archive into a fresh Colab directory, then run its installation/validation cells. The archive includes Git-listed source and untracked nonignored files, so review its contents before uploading. Ignored dependencies, generated native binaries and local SQLite data are excluded.

Select a GPU runtime and verify both `nvidia-smi` and `nvcc --version`. All CUDA checks must actually execute; compilation and skipped tests are not correctness evidence. Colab sends uploaded data to cloud infrastructure, unlike local Studio. Use the synthetic fixtures until hardware correctness is established.
