#pragma once
#include "config.hpp"
#include "result.hpp"
#include "sequence.hpp"
#include "wavefront.hpp"
#include "cigar.hpp"
#include <map>
#include <algorithm>
#include <chrono>
#include <cstdint>
namespace warpalign {
inline Result cpu_align(const std::string& q,const std::string& t,const Config& c) {
 const auto begin=std::chrono::steady_clock::now();
 const int n=static_cast<int>(q.size()),m=static_cast<int>(t.size()), oe=c.gap_open+c.gap_extend;
 Result r; r.query_end=n;r.target_end=m;r.heuristic_used=c.mode=="fast";r.bandwidth=r.heuristic_used?c.bandwidth:0;r.has_traceback=!c.score_only;
 // An empty side has exactly one possible global path: a single gap.
 if(n==0 || m==0) {
  const int length=std::max(n,m);
  if(r.heuristic_used && length>c.bandwidth)throw ResourceError("heuristic band excludes alignment");
  const std::int64_t cost=length?static_cast<std::int64_t>(c.gap_open)+static_cast<std::int64_t>(length)*c.gap_extend:0;
  if(cost>std::numeric_limits<int>::max()/2)throw ResourceError("score exceeds integer capacity");
  r.score=static_cast<int>(cost);
  if(!c.score_only && length) {r.cigar=std::to_string(length)+(n?"I":"D");r.insertions=n;r.deletions=m;r.edit_distance=length;}
  r.execution_time=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
  return r;
 }
 std::map<int,Wavefront> history;std::size_t used=0,peak=0;
 auto get=[&](int s,char state,int k) {auto f=history.find(s);return f==history.end()?unreachable:f->second.get(state,k);};
 auto valid=[&](int h,int k) {return h>=0&&h<=n&&h-k>=0&&h-k<=m?h:unreachable;};
 const std::int64_t bound=static_cast<std::int64_t>(std::min(n,m))*c.mismatch+(n==m?0:c.gap_open+static_cast<std::int64_t>(std::abs(n-m))*c.gap_extend);
 if(bound>std::numeric_limits<int>::max()/2)throw ResourceError("score bound exceeds integer capacity");
 int final_score=-1;
 for(int s=0;s<=bound;++s) {
  int width=s/c.gap_extend;
  int lo=std::max(-m,-width), hi=std::min(n,width);
  if(r.heuristic_used) {lo=std::max(lo,-c.bandwidth);hi=std::min(hi,c.bandwidth);}
  if(lo>hi)throw ResourceError("heuristic band excludes alignment");
  std::size_t bytes=sizeof(Wavefront)+64+static_cast<std::size_t>(hi-lo+1)*12;
  if(bytes>c.memory_limit || used>c.memory_limit-bytes)throw ResourceError("wavefront memory limit exceeded; increase memory_limit or use score-only");
  auto [it,inserted]=history.emplace(s,Wavefront(lo,hi)); auto& w=it->second;used+=w.bytes();peak=std::max(peak,used);
  for(int k=lo;k<=hi;++k) {
   int a=valid(std::max(get(s-oe,'M',k-1),get(s-c.gap_extend,'I',k-1))+1,k);
   int b=valid(std::max(get(s-oe,'M',k+1),get(s-c.gap_extend,'D',k+1)),k);
   int x=valid(get(s-c.mismatch,'M',k)+1,k);
   // A mismatch consumes both axes; a zero target/query predecessor is invalid.
   if(x!=unreachable && (x==0||x-k==0))x=unreachable;
   if(a!=unreachable && a==0)a=unreachable;
   if(b!=unreachable && b-k==0)b=unreachable;
   int h=s==0&&k==0?0:std::max({a,b,x});
   w.i[k-lo]=a;w.d[k-lo]=b;
   if(h>=0)while(h<n&&h-k<m&&equal_base(q[h],t[h-k],c.ambiguous))++h;
   w.m[k-lo]=h;
  }
  if(w.get('M',n-m)==n) {final_score=s;break;}
  if(c.score_only) {int keep=s-std::max(c.mismatch,oe);while(!history.empty()&&history.begin()->first<=keep){used-=history.begin()->second.bytes();history.erase(history.begin());}}
 }
 if(final_score<0)throw ResourceError("no alignment within heuristic band");
 r.score=final_score;r.wavefront_bytes=peak;
 if(!c.score_only) {
  int s=final_score,k=n-m,h=n;char state='M';std::string ops;ops.reserve(n+m);
  while(s>0||h>0||h-k>0) {
   if(state=='M') {
    int x=get(s-c.mismatch,'M',k);x=x<0?unreachable:valid(x+1,k);
    if(x!=unreachable&&(x==0||x-k==0))x=unreachable;
    int a=get(s,'I',k),b=get(s,'D',k),base=s==0?0:std::max({x,a,b});
    if(base<0)throw std::logic_error("invalid traceback state");
    while(h>base){ops+='=';++r.matches;--h;}
    if(s==0)break;
    if(base==a)state='I';else if(base==b)state='D';else {ops+='X';++r.mismatches;--h;s-=c.mismatch;}
   } else if(state=='I') {
    bool open=get(s-oe,'M',k-1)>=get(s-c.gap_extend,'I',k-1);
    ops+='I';++r.insertions;--h;--k;s-=open?oe:c.gap_extend;if(open)state='M';
   } else {
    bool open=get(s-oe,'M',k+1)>=get(s-c.gap_extend,'D',k+1);
    ops+='D';++r.deletions;++k;s-=open?oe:c.gap_extend;if(open)state='M';
   }
  }
  r.cigar=encode_cigar(std::move(ops));r.edit_distance=r.mismatches+r.insertions+r.deletions;
 }
 r.execution_time=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();return r;
}
}
