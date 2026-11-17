#pragma once
#include <string>
#include <cstddef>
namespace warpalign {
struct Result {
 std::string query_id, target_id, cigar, backend="cpu", fallback_reason, timing_scope="cpu_engine";
 int score=0, edit_distance=0, query_start=0, query_end=0, target_start=0, target_end=0;
 int matches=0, mismatches=0, insertions=0, deletions=0, bandwidth=0, heuristic_retries=0;
 double execution_time=0;
 bool heuristic_used=false, cpu_fallback=false, has_traceback=true;
 std::size_t wavefront_bytes=0, gpu_memory_bytes=0;
};
}
