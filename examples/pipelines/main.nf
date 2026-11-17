nextflow.enable.dsl=2
params.queries = 'tests/fixtures/queries.fa'
params.targets = 'tests/fixtures/targets.fa'
params.outdir = 'results'
process ALIGN_PAIRS {
    cpus 4
    memory '1 GB'
    publishDir params.outdir, mode: 'copy'
    input:
    path queries
    path targets
    output:
    path 'pairs.paf'
    script:
    """
    warpalign align-pairs --queries '${queries}' --targets '${targets}' \
      --backend cpu --threads ${task.cpus} --memory-mb 1024 --output pairs.paf
    """
}
workflow {
    ALIGN_PAIRS(file(params.queries, checkIfExists: true), file(params.targets, checkIfExists: true))
}
