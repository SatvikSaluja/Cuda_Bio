# Minimap2 integration

The mapper adapter is `python/warpalign/mapping.py`. It executes minimap2 with an argv list (no shell), requests `-c -x PRESET` PAF, spools output to a local temporary file and checks the exit status. Candidate intervals use original forward-strand query coordinates. Negative-strand query slices are reverse-complemented before alignment against forward target slices.

Refined results retain interval coordinates, orientation and MAPQ. The CIGAR is in target-forward orientation. Existing score/CIGAR tags are not reused; new cost and CIGAR tags come from WarpAlign. Unmapped reads produce no PAF row. Secondary candidates are refined too. No candidate padding or endpoint optimization is implemented.

The adapter has unit tests for asymmetric reverse-complement inputs and coordinate preservation. Actual minimap2 pipeline execution requires the external executable and remains a separate integration check. Entire references and reads are loaded into dictionaries; indexed reference access is a roadmap item.
