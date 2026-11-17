#pragma once
#include "cpu_backend.hpp"
namespace warpalign {
class Aligner {
 Config config_;
public:
 explicit Aligner(Config c={}):config_(std::move(c)){config_.validate();}
 Result align(std::string query,std::string target,std::string query_id="",std::string target_id="") const {
  if(config_.backend=="cuda" && !config_.allow_fallback)throw ResourceError("CUDA backend unavailable; fallback is disabled");
  query=normalize(std::move(query));target=normalize(std::move(target));
  Config current=config_;Result r;int retries=0;
  for(;;) {
   try {r=cpu_align(query,target,current);break;}
   catch(const ResourceError& error) {
    if(!current.adaptive_band || current.bandwidth>=current.max_bandwidth || std::string(error.what()).find("heuristic band")==std::string::npos)throw;
    current.bandwidth=static_cast<int>(std::min<long long>(current.max_bandwidth,std::max<long long>(1,static_cast<long long>(current.bandwidth)*2)));
    ++retries;
   }
  }
  r.heuristic_retries=retries;r.query_id=std::move(query_id);r.target_id=std::move(target_id);
  if(config_.backend=="cuda") {r.cpu_fallback=true;r.fallback_reason="CUDA execution is unavailable in the validated CPU backend";}
  return r;
 }
 std::vector<Result> align_batch(const std::vector<std::string>& q,const std::vector<std::string>& t)const {
  if(q.size()!=t.size())throw std::invalid_argument("batch lengths differ");
  std::vector<Result> out;out.reserve(q.size());for(std::size_t j=0;j<q.size();++j)out.push_back(align(q[j],t[j]));return out;
 }
};
}
