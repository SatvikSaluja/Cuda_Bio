#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <warpalign/cuda_backend.cuh>
namespace py=pybind11;
static warpalign::experimental::DeviceArena& arena(){static thread_local warpalign::experimental::DeviceArena value;return value;}
PYBIND11_MODULE(_cuda,m){
 m.attr("api_version")=2;
 m.def("last_arena_bytes",[]{return arena().capacity();});
 m.doc()="Experimental CUDA batch scoring and device traceback. Runtime validation required.";
 m.def("available",[]{int count=0;return cudaGetDeviceCount(&count)==cudaSuccess&&count>0;});
 m.def("alignments",[](std::vector<std::string> q,std::vector<std::string> t,int mismatch,int open,int extend,std::string ambiguous,std::size_t memory,int score_budget){
  warpalign::Config c;c.mismatch=mismatch;c.gap_open=open;c.gap_extend=extend;c.ambiguous=ambiguous;c.memory_limit=memory;
  std::vector<warpalign::Result> results;
  {py::gil_scoped_release release;results=warpalign::experimental::cuda_alignments(std::move(q),std::move(t),c,arena(),score_budget);}
  py::list rows;for(const auto& r:results){py::dict d;
   d["score"]=r.score;d["cigar"]=r.cigar;d["query_end"]=r.query_end;d["target_end"]=r.target_end;
   d["matches"]=r.matches;d["mismatches"]=r.mismatches;d["insertions"]=r.insertions;d["deletions"]=r.deletions;
   d["edit_distance"]=r.edit_distance;d["wavefront_bytes"]=r.wavefront_bytes;d["backend"]="cuda";rows.append(d);
  }return rows;
 });
 m.def("scores",[](std::vector<std::string> q,std::vector<std::string> t,int mismatch,int open,int extend,std::string ambiguous,std::size_t memory,int score_budget){
  warpalign::Config c;c.mismatch=mismatch;c.gap_open=open;c.gap_extend=extend;c.ambiguous=ambiguous;c.memory_limit=memory;
  // Thread-local reuse; no arena is accessed simultaneously by different host threads.
  return warpalign::experimental::cuda_scores(std::move(q),std::move(t),c,arena(),score_budget);
 },py::call_guard<py::gil_scoped_release>());
}
