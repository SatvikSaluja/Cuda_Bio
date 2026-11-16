# Troubleshooting

- `ResourceError`: increase the memory budget, use score-only when CIGAR is unnecessary, or choose a mature low-memory WFA backend outside WarpAlign. Fast mode changes the optimality guarantee.
- CUDA request reports CPU: the production backend in this release is CPU-only; the prototype is a separate C++ target.
- `minimap2` not found: install it separately and add it to PATH, or specify `--mapper` in the CLI.
- `_native` import failure: build/install the package for the active Python interpreter. Extensions are Python/platform-specific.
- Studio root returns 404: build `apps/studio/dist` before starting the API, or point `WARPALIGN_STUDIO_DIST` at your built bundle.
- Package downloads fail: the development sandbox had restricted DNS. Local dependency reuse allowed core/frontend validation, but a clean network-enabled installation remains a release gate.
- FASTQ error: verify sequence/quality lengths and `+` separators. General IUPAC ambiguity symbols other than N are unsupported.
