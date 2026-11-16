# Contributing

Start with the repository CONTRIBUTING.md and known limitations. Changes to recurrence, traceback or scoring must pass the independent DP/CIGAR suite. GPU changes require device execution and sanitizer evidence; report exact hardware/toolkit details. New benchmark claims require raw reproducible measurements, comparable modes and baseline versions.

Use synthetic/publicly licensed fixtures. Never submit private genomic data, credentials or large binaries. Keep CPU consumers independent of Python/CUDA. Document any output-format or scoring-convention changes as API changes.
