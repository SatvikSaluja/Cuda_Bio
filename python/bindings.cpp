#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <warpalign/warpalign.hpp>
namespace py=pybind11;
using namespace warpalign;
PYBIND11_MODULE(_native,m){
 py::register_exception<ResourceError>(m,"ResourceError",PyExc_RuntimeError);
 py::class_<Config>(m,"Config").def(py::init<>())
#define CFG(x) .def_readwrite(#x,&Config::x)
 CFG(mismatch) CFG(gap_open) CFG(gap_extend) CFG(bandwidth) CFG(backend) CFG(mode) CFG(ambiguous) CFG(memory_limit) CFG(score_only);
#undef CFG
 py::class_<Result>(m,"Result")
#define FIELD(x) .def_readonly(#x,&Result::x)
 FIELD(query_id) FIELD(target_id) FIELD(score) FIELD(edit_distance) FIELD(cigar) FIELD(query_start) FIELD(query_end) FIELD(target_start) FIELD(target_end) FIELD(matches) FIELD(mismatches) FIELD(insertions) FIELD(deletions) FIELD(backend) FIELD(execution_time) FIELD(heuristic_used) FIELD(cpu_fallback) FIELD(fallback_reason) FIELD(has_traceback) FIELD(bandwidth) FIELD(wavefront_bytes);
#undef FIELD
 py::class_<Aligner>(m,"Aligner").def(py::init<Config>()).def("align",&Aligner::align,py::arg("query"),py::arg("target"),py::arg("query_id")="",py::arg("target_id")="",py::call_guard<py::gil_scoped_release>()).def("align_batch",&Aligner::align_batch,py::call_guard<py::gil_scoped_release>());
}
