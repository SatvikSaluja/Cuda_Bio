# FASTA / FASTQ inputs

FASTA supports multiline sequences and identifier descriptions; the first whitespace-delimited token is the ID. FASTQ supports multiline sequence and quality records, checks equal lengths and requires `+`. CLI accepts `.gz` inputs through gzip. Studio accepts uncompressed uploads up to 32 MiB combined.

Only A, C, G, T and N are supported. Lowercase is normalized. Other IUPAC ambiguity letters are rejected. Empty FASTA sequences and empty API strings are valid. Empty FASTQ sequences require an empty quality line.

N handling defaults to literal equality (`N=N`, `N!=A`). Wildcard matches N against any base. Mismatch treats even N=N as a substitution. The selected model determines the meaning of `=` and edit counts; these are not biological confidence estimates. Refinement requires unique IDs and builds temporary SQLite indexes. Each input record is materialized while indexing; refinement reads interval slices.
