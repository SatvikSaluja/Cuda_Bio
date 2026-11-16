#pragma once
#include "memory_manager.cuh"
#include "config.hpp"
#include "sequence.hpp"
#include <algorithm>
#include <limits>
namespace warpalign::experimental {
constexpr int absent=-1000000000;
__device__ inline int load(const int* data,int s,int state,int k,int low,int width,int ring) {
 if(s<0||k<low||k>=low+width)return absent;
 return data[((s%ring)*3+state)*static_cast<std::size_t>(width)+k-low];
}
__device__ inline int bounded(int h,int k,int n,int m) {return h>=0&&h<=n&&h-k>=0&&h-k<=m?h:absent;}
// Exactly one FULL warp per block. No lane exits independently.
__global__ void score_kernel(const char* q,const char* t,int n,int m,int x,int o,int e,int maxscore,int low,int width,int ring,int ambiguous,int* wf,int* result) {
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
inline int cuda_score(std::string query,std::string target,const Config& c,DeviceArena& arena,int max_score) {
 c.validate();query=normalize(std::move(query));target=normalize(std::move(target));
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
