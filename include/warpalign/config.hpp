#pragma once
#include <cstddef>
#include <cmath>
#include <stdexcept>
#include <string>
namespace warpalign {
struct Config {
 int mismatch=4, gap_open=6, gap_extend=2, bandwidth=64, checkpoint_interval=0, max_bandwidth=4096;
 std::string backend="auto", mode="exact", ambiguous="literal";
 std::size_t memory_limit=512ull*1024*1024;
 bool score_only=false, allow_fallback=true, adaptive_band=false;
 double timeout_seconds=0;
 void validate() const {
  if(!std::isfinite(timeout_seconds) || timeout_seconds<0) throw std::invalid_argument("timeout_seconds must be finite and nonnegative");
  if(mismatch<=0 || gap_open<0 || gap_extend<=0 || mismatch>1000000 || gap_open>1000000 || gap_extend>1000000) throw std::invalid_argument("penalties must be positive (gap_open may be zero) and <= 1000000");
  if(backend!="auto" && backend!="cpu" && backend!="cuda") throw std::invalid_argument("backend must be auto, cpu or cuda");
  if(mode!="exact" && mode!="fast") throw std::invalid_argument("mode must be exact or fast");
  if(ambiguous!="literal" && ambiguous!="wildcard" && ambiguous!="mismatch") throw std::invalid_argument("ambiguous must be literal, wildcard or mismatch");
  if(adaptive_band && (mode!="fast" || max_bandwidth<bandwidth))throw std::invalid_argument("adaptive band requires fast mode and max_bandwidth >= bandwidth");
  if(checkpoint_interval<0 || checkpoint_interval>1000000)throw std::invalid_argument("invalid checkpoint interval");
  if(bandwidth<0 || memory_limit<1024) throw std::invalid_argument("invalid bandwidth or memory limit");
 }
};
struct ResourceError : std::runtime_error { using std::runtime_error::runtime_error; };
}
