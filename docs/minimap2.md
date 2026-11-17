# Minimap2 refinement

`python/warpalign/mapping.py` invokes minimap2 with an argument list, requests `-c -x PRESET` PAF, checks its status and spools candidate output locally. Minimap2 still performs candidate discovery and its own base alignment; WarpAlign then refines the fixed intervals. Measure this extra work at pipeline level rather than assuming a benefit.

Reference and reads are indexed in temporary SQLite files. Interval queries use SQLite substring access, avoiding full-reference dictionaries during refinement. Building the index still materializes one input record at a time, so an individual chromosome can require a substantial transient buffer. Native FASTA offset indexes are a future optimization.

Negative-strand query intervals are reverse-complemented against forward target slices. Original forward query coordinates, target coordinates and mapper MAPQ are preserved; MAPQ is not recalibrated. Outputs include mapper version/argv. Secondary candidates are retained; unmapped reads produce no PAF row. Endpoint extension/optimization and splice-aware refinement are not implemented.

Tests cover asymmetric reverse-complement intervals, coordinates and disk-index access. Actual minimap2 execution and real sequencing workloads remain external validation requirements.
