# What is WarpAlign?

WarpAlign is a global pairwise DNA aligner and local inspection tool. A result minimizes mismatch × substitutions plus gap_open + gap_extend × length for every insertion or deletion run. Matches cost zero. Scores are nonnegative costs, not similarity scores.

The C++ core has no Python or proprietary-library dependency. Pybind11 wraps that same core. The CLI pairs records in input order and the local API calls those functions directly. The map command delegates locus discovery to minimap2.

This initial release emphasizes validation and explicit limits. It does not implement local or ends-free alignment, spliced alignment, clinical interpretation or variant calling. CUDA is experimental and requires explicit environment opt-in before automatic dispatch considers it.
