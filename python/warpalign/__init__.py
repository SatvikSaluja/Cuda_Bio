"""Exact global affine WFA. Scores are nonnegative costs; a gap costs open + length*extend."""
from ._native import Config, Result, ResourceError, Aligner as _Aligner
__version__ = "0.1.0"
FIELDS = "query_id target_id score edit_distance cigar query_start query_end target_start target_end matches mismatches insertions deletions backend execution_time heuristic_used cpu_fallback fallback_reason has_traceback bandwidth wavefront_bytes".split()

class Aligner:
    def __init__(self, backend: str = "auto", mode: str = "exact", mismatch: int = 4,
                 gap_open: int = 6, gap_extend: int = 2, bandwidth: int = 64,
                 ambiguous: str = "literal", memory_limit: int = 512 * 1024**2,
                 score_only: bool = False):
        config = Config()
        for key, value in locals().copy().items():
            if key not in {"self", "config"}:
                setattr(config, key, value)
        self._impl = _Aligner(config)

    def align(self, query: str, target: str, query_id: str = "", target_id: str = "") -> Result:
        return self._impl.align(query, target, query_id, target_id)

    def align_batch(self, queries: list[str], targets: list[str]) -> list[Result]:
        return self._impl.align_batch(queries, targets)

def as_dict(result: Result) -> dict:
    data = {key: getattr(result, key) for key in FIELDS}
    if not result.has_traceback:
        for key in ("edit_distance", "matches", "mismatches", "insertions", "deletions"):
            data[key] = None
    return data
