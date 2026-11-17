#pragma once
#include "memory_manager.cuh"
#include "config.hpp"
#include "sequence.hpp"
#include "traceback.hpp"
#include "result.hpp"
#include "cigar.hpp"
#include <algorithm>
#include <limits>
#include <vector>
#include <cstring>
namespace warpalign::experimental {
constexpr int absent=-1000000000;
__device__ inline int load(const int* data,int s,int state,int k,int low,int width,int ring) {
 if(s<0||k<low||k>=low+width)return absent;
 return data[((s%ring)*3+state)*static_cast<std::size_t>(width)+k-low];
}
__device__ inline int bounded(int h,int k,int n,int m) {return h>=0&&h<=n&&h-k>=0&&h-k<=m?h:absent;}
// Exactly one FULL warp per block. No lane exits independently.
__device__ inline void score_one(const char* q,const char* t,int n,int m,int x,int o,int e,int maxscore,int low,int width,int ring,int ambiguous,int* wf,int* result) {
 int lane=threadIdx.x;const unsigned mask=0xffffffffu;
 for(int s=0;s<=maxscore;++s){
  bool done=false;
  for(int tile=0;tile<width;tile+=32){
   int k=low+tile+lane;
   int mo=load(wf,s-o-e,0,k,low,width,ring);
   int ie=load(wf,s-e,1,k,low,width,ring);
   int de=load(wf,s-e,2,k,low,width,ring);
   // All lanes execute all exchanges; edge lanes fetch across tile boundaries.
   int ml=__shfl_up_sync(mask,mo,1), il=__shfl_up_sync(mask,ie,1);
   int mr=__shfl_down_sync(mask,mo,1), dr=__shfl_down_sync(mask,de,1);
   if(lane==0){ml=load(wf,s-o-e,0,k-1,low,width,ring);il=load(wf,s-e,1,k-1,low,width,ring);}
   if(lane==31){mr=load(wf,s-o-e,0,k+1,low,width,ring);dr=load(wf,s-e,2,k+1,low,width,ring);}
   int a=bounded(max(ml,il)+1,k,n,m),b=bounded(max(mr,dr),k,n,m);
   int sub=bounded(load(wf,s-x,0,k,low,width,ring)+1,k,n,m);
   if(a==0)a=absent;if(b!=absent&&b-k==0)b=absent;
   if(sub!=absent&&(sub==0||sub-k==0))sub=absent;
   int h=s==0&&k==0?0:max(sub,max(a,b));
   if(k<low+width){
    while(h>=0&&h<n&&h-k<m){char qa=q[h],ta=t[h-k];bool eq=(qa==ta);if(qa=='N'||ta=='N')eq=ambiguous==1||(ambiguous==0&&qa==ta);if(!eq)break;++h;}
    auto pos=(s%ring)*3*static_cast<std::size_t>(width)+k-low;
    wf[pos]=h;wf[pos+width]=a;wf[pos+2*width]=b;
    done=done||(k==n-m&&h==n);
   }
  }
  __syncwarp(mask); // order global stores before the next score reads them
  if(__any_sync(mask,done)){if(lane==0)*result=s;return;}
 }
 if(lane==0)*result=-1;
}
static __global__ void score_kernel(const char* q,const char* t,int n,int m,int x,int o,int e,int maxscore,int low,int width,int ring,int ambiguous,int* wf,int* result) {
 score_one(q,t,n,m,x,o,e,maxscore,low,width,ring,ambiguous,wf,result);
}
struct BatchItem {
 int n,m,low,width,maxscore;
 std::size_t qoffset,toffset,wfoffset;
};
static __global__ void batch_score_kernel(const char* sequences,const BatchItem* items,int count,int x,int o,int e,int ring,int ambiguous,int* wf,int* results) {
 const int index=blockIdx.x;
 if(index>=count)return; // block-uniform, all 32 lanes participate below
 const auto item=items[index];
 score_one(sequences+item.qoffset,sequences+item.toffset,item.n,item.m,x,o,e,item.maxscore,item.low,item.width,ring,ambiguous,wf+item.wfoffset,results+index);
}
// Host batches adapt to both the caller budget and currently free device memory.
// Each block is one full warp, independent of every other alignment.
inline std::vector<int> cuda_scores(std::vector<std::string> queries,std::vector<std::string> targets,const Config& c,DeviceArena& arena,int max_score) {
 c.validate();arena.limit(c.memory_limit);
 if(queries.size()!=targets.size())throw std::invalid_argument("batch lengths differ");
 if(c.mode!="exact")throw std::invalid_argument("CUDA prototype supports exact scoring only");
 if(max_score<0||max_score>1000000)throw ResourceError("invalid CUDA score budget");
 for(auto& q:queries)q=normalize(std::move(q));
 for(auto& t:targets)t=normalize(std::move(t));
 std::vector<int> scores; scores.reserve(queries.size());
 const int ring=std::max(c.mismatch,c.gap_open+c.gap_extend)+1;
 std::size_t first=0;
 while(first<queries.size()) {
  std::size_t free=0,total=0;cuda_check(cudaMemGetInfo(&free,&total));
  // Existing arena is reusable. Growth also temporarily retains its old allocation.
  const std::size_t budget=std::min(c.memory_limit,std::max(arena.capacity(),free-free/5));
  std::vector<BatchItem> items;std::vector<char> sequences;std::size_t cells=0;
  for(std::size_t index=first;index<queries.size()&&items.size()<65535;++index) {
   const int n=queries[index].size(),m=targets[index].size();
   const long long bound=static_cast<long long>(std::min(n,m))*c.mismatch+(n==m?0:c.gap_open+static_cast<long long>(std::abs(n-m))*c.gap_extend);
   const int cap=static_cast<int>(std::min<long long>(max_score,bound));
   const int radius=cap/c.gap_extend,low=-std::min(m,radius),width=std::min(n,radius)-low+1;
   const std::size_t nextcells=cells+static_cast<std::size_t>(width)*ring*3;
   const std::size_t nextseq=sequences.size()+n+m;
   const std::size_t estimate=(items.size()+1)*(sizeof(BatchItem)+sizeof(int))+nextseq+nextcells*sizeof(int)+32;
   if(estimate>budget){if(items.empty())throw ResourceError("alignment exceeds CUDA batch memory budget");break;}
   BatchItem item{n,m,low,width,cap,sequences.size(),sequences.size()+n,cells};
   sequences.insert(sequences.end(),queries[index].begin(),queries[index].end());
   sequences.insert(sequences.end(),targets[index].begin(),targets[index].end());items.push_back(item);cells=nextcells;
  }
  const std::size_t descriptors=items.size()*sizeof(BatchItem);
  const std::size_t seqbytes=(sequences.size()+7)/8*8;
  const std::size_t bytes=descriptors+seqbytes+(cells+items.size())*sizeof(int);
  char* base=static_cast<char*>(arena.reserve(bytes));
  auto* device_items=reinterpret_cast<BatchItem*>(base);char* device_sequences=base+descriptors;
  int* wf=reinterpret_cast<int*>(device_sequences+seqbytes);int* output=wf+cells;
  cuda_check(cudaMemcpy(device_items,items.data(),descriptors,cudaMemcpyHostToDevice));
  if(!sequences.empty())cuda_check(cudaMemcpy(device_sequences,sequences.data(),sequences.size(),cudaMemcpyHostToDevice));
  batch_score_kernel<<<static_cast<unsigned>(items.size()),32>>>(device_sequences,device_items,items.size(),c.mismatch,c.gap_open,c.gap_extend,ring,c.ambiguous=="wildcard"?1:c.ambiguous=="mismatch"?2:0,wf,output);
  cuda_check(cudaGetLastError());cuda_check(cudaDeviceSynchronize());
  std::vector<int> chunk(items.size());cuda_check(cudaMemcpy(chunk.data(),output,chunk.size()*sizeof(int),cudaMemcpyDeviceToHost));
  for(int score:chunk){if(score<0)throw ResourceError("CUDA score budget exhausted");scores.push_back(score);}
  first+=items.size();
 }
 return scores;
}
// Traceback is serial within each alignment; all scoring uses the full warp.
static __global__ void trace_kernel(const int* wf,int low,int width,int levels,int n,int m,int score,int x,int o,int e,char* ops,int* length) {
 if(threadIdx.x==0&&blockIdx.x==0)*length=trace_history({wf,low,width,levels},n,m,score,x,o,e,ops,n+m);
}
inline std::vector<Result> cuda_alignments(std::vector<std::string> queries,std::vector<std::string> targets,const Config& c,DeviceArena& arena,int max_score) {
 // Determine exact scores with rolling storage first, then allocate history only
 // through the attained score, not the caller's potentially large score budget.
 auto scores=cuda_scores(queries,targets,c,arena,max_score);
 std::vector<Result> results;results.reserve(scores.size());
 for(std::size_t index=0;index<scores.size();++index){
  auto q=normalize(std::move(queries[index])),t=normalize(std::move(targets[index]));
  int n=q.size(),m=t.size(),score=scores[index],levels=score+1;
  int radius=score/c.gap_extend,low=-std::min(m,radius),width=std::min(n,radius)-low+1;
  std::size_t cells=static_cast<std::size_t>(width)*levels*3;
  std::size_t seqbytes=(static_cast<std::size_t>(n)+m+3)/4*4;
  if(cells>c.memory_limit/sizeof(int))throw ResourceError("CUDA traceback history exceeds memory budget");
  std::size_t bytes=seqbytes*2+(cells+2)*sizeof(int);
  if(bytes>c.memory_limit)throw ResourceError("CUDA traceback arena exceeds memory budget");
  char* base=static_cast<char*>(arena.reserve(bytes));
  int* wf=reinterpret_cast<int*>(base+seqbytes);int* output=wf+cells;int* length=output+1;
  char* ops=reinterpret_cast<char*>(length+1);
  if(n)cuda_check(cudaMemcpy(base,q.data(),n,cudaMemcpyHostToDevice));
  if(m)cuda_check(cudaMemcpy(base+n,t.data(),m,cudaMemcpyHostToDevice));
  score_kernel<<<1,32>>>(base,base+n,n,m,c.mismatch,c.gap_open,c.gap_extend,score,low,width,levels,c.ambiguous=="wildcard"?1:c.ambiguous=="mismatch"?2:0,wf,output);
  cuda_check(cudaGetLastError());cuda_check(cudaDeviceSynchronize());
  int attained=-1;cuda_check(cudaMemcpy(&attained,output,sizeof(int),cudaMemcpyDeviceToHost));
  if(attained!=score)throw std::logic_error("CUDA scoring passes disagree");
  trace_kernel<<<1,32>>>(wf,low,width,levels,n,m,score,c.mismatch,c.gap_open,c.gap_extend,ops,length);
  cuda_check(cudaGetLastError());cuda_check(cudaDeviceSynchronize());
  int count=-1;cuda_check(cudaMemcpy(&count,length,sizeof(int),cudaMemcpyDeviceToHost));
  if(count<0||count>n+m)throw std::logic_error("CUDA traceback failed");
  std::string reverse(count,' ');if(count)cuda_check(cudaMemcpy(reverse.data(),ops,count,cudaMemcpyDeviceToHost));
  // Linear host replay verifies device operations, never recomputes a DP alignment.
  Result r;r.backend="cuda";r.score=score;r.query_end=n;r.target_end=m;r.wavefront_bytes=cells*sizeof(int);
  int qi=0,ti=0;long long cost=0;char previous=0;
  for(auto it=reverse.rbegin();it!=reverse.rend();++it){char op=*it;
   if(op=='I'||op=='D'){
    cost+=c.gap_extend+(previous==op?0:c.gap_open);
    if(op=='I'){++qi;++r.insertions;}else{++ti;++r.deletions;}
   }else{
    if(qi>=n||ti>=m||equal_base(q[qi],t[ti],c.ambiguous)!=(op=='='))throw std::logic_error("CUDA traceback base mismatch");
    ++qi;++ti;if(op=='=')++r.matches;else if(op=='X'){++r.mismatches;cost+=c.mismatch;}else throw std::logic_error("Invalid CUDA CIGAR operation");
   }
   if(qi>n||ti>m)throw std::logic_error("CUDA traceback coordinate overflow");previous=op;
  }
  if(qi!=n||ti!=m||cost!=score)throw std::logic_error("CUDA traceback rescore failed");
  r.edit_distance=r.mismatches+r.insertions+r.deletions;r.cigar=encode_cigar(std::move(reverse));results.push_back(std::move(r));
 }
 return results;
}
inline int cuda_score(std::string query,std::string target,const Config& c,DeviceArena& arena,int max_score) {
 c.validate();arena.limit(c.memory_limit);query=normalize(std::move(query));target=normalize(std::move(target));
 if(c.mode!="exact")throw std::invalid_argument("experimental CUDA prototype supports exact score only");
 if(max_score<0||max_score>1000000)throw ResourceError("invalid experimental CUDA score budget");
 int n=query.size(),m=target.size(),radius=max_score/c.gap_extend;
 int low=-std::min(m,radius),high=std::min(n,radius),width=high-low+1,ring=std::max(c.mismatch,c.gap_open+c.gap_extend)+1;
 std::size_t cells=static_cast<std::size_t>(width)*ring*3;
 if(cells>(c.memory_limit/sizeof(int)))throw ResourceError("CUDA score scratch exceeds budget");
 std::size_t seqbytes=(static_cast<std::size_t>(n)+m+3)/4*4;
 std::size_t bytes=seqbytes+(cells+1)*sizeof(int);
 if(bytes>c.memory_limit)throw ResourceError("CUDA arena exceeds budget");
 char* ptr=static_cast<char*>(arena.reserve(bytes));int* wf=reinterpret_cast<int*>(ptr+seqbytes);int* output=wf+cells;
 cuda_check(cudaMemcpy(ptr,query.data(),n,cudaMemcpyHostToDevice));cuda_check(cudaMemcpy(ptr+n,target.data(),m,cudaMemcpyHostToDevice));
 score_kernel<<<1,32>>>(ptr,ptr+n,n,m,c.mismatch,c.gap_open,c.gap_extend,max_score,low,width,ring,c.ambiguous=="wildcard"?1:c.ambiguous=="mismatch"?2:0,wf,output);
 cuda_check(cudaGetLastError());cuda_check(cudaDeviceSynchronize());int score;cuda_check(cudaMemcpy(&score,output,sizeof(int),cudaMemcpyDeviceToHost));
 if(score<0)throw ResourceError("CUDA score budget exhausted; retry or CPU fallback required");return score;
}
}
