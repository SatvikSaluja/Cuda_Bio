#pragma once
#include "cpu_backend.hpp"
namespace warpalign {
class Aligner {
 Config config_;
public:
 explicit Aligner(Config c={}):config_(std::move(c)){config_.validate();}
 Result align(std::string query,std::string target,std::string query_id="",std::string target_id="") const {
  query=normalize(std::move(query));target=normalize(std::move(target));
  auto r=cpu_align(query,target,config_);r.query_id=std::move(query_id);r.target_id=std::move(target_id);
  if(config_.backend=="cuda") {r.cpu_fallback=true;r.fallback_reason="CUDA execution is unavailable in the validated CPU backend";}
  return r;
 }
 std::vector<Result> align_batch(const std::vector<std::string>& q,const std::vector<std::string>& t)const {
  if(q.size()!=t.size())throw std::invalid_argument("batch lengths differ");
  std::vector<Result> out;out.reserve(q.size());for(std::size_t j=0;j<q.size();++j)out.push_back(align(q[j],t[j]));return out;
 }
};
}
