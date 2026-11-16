from typing import Any
class ResourceError(RuntimeError): ...
class Result:
    query_id: str
    target_id: str
    cigar: str
    backend: str
    fallback_reason: str
    score: int
    edit_distance: int
    query_start: int
    query_end: int
    target_start: int
    target_end: int
    matches: int
    mismatches: int
    insertions: int
    deletions: int
    bandwidth: int
    wavefront_bytes: int
    execution_time: float
    heuristic_used: bool
    cpu_fallback: bool
    has_traceback: bool
class Aligner:
    def __init__(self, backend: str = "auto", mode: str = "exact", mismatch: int = 4, gap_open: int = 6, gap_extend: int = 2, bandwidth: int = 64, ambiguous: str = "literal", memory_limit: int = 536870912, score_only: bool = False) -> None: ...
    def align(self, query: str, target: str, query_id: str = "", target_id: str = "") -> Result: ...
    def align_batch(self, queries: list[str], targets: list[str]) -> list[Result]: ...
def as_dict(result: Result) -> dict[str, Any]: ...
__version__: str
