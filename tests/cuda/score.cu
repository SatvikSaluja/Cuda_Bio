#include <warpalign/cuda_backend.cuh>
#include <warpalign/warpalign.hpp>
#include <iostream>
#include <random>
int main(){int devices=0;if(cudaGetDeviceCount(&devices)!=cudaSuccess||devices==0){std::cerr<<"SKIP: no CUDA device\n";return 77;}
 warpalign::experimental::DeviceArena arena;std::mt19937 rng(1729);
 for(int n:{0,1,31,32,33,65,100,500,1000,50000,100000}){std::string q(n,'A'),t=q;if(n)t[n/2]='C';warpalign::Config c;auto cpu=warpalign::Aligner(c).align(q,t);if(warpalign::experimental::cuda_score(q,t,c,arena,64)!=cpu.score)return 1;}
 for(int trial=0;trial<1000;++trial){std::string q,t;for(int n=rng()%90;n--;)q+="ACGT"[rng()%4];for(int n=rng()%90;n--;)t+="ACGT"[rng()%4];warpalign::Config c;auto cpu=warpalign::Aligner(c).align(q,t);if(warpalign::experimental::cuda_score(q,t,c,arena,800)!=cpu.score)return 1;}
 for(int penalty=1;penalty<=5;++penalty){
  warpalign::Config c;c.mismatch=penalty;c.gap_open=penalty-1;c.gap_extend=penalty;c.ambiguous="wildcard";
  std::vector<std::string> q{"ACGT","N","",std::string(65,'A')},t{"AGT","A","AA",std::string(63,'A')};
  auto scores=warpalign::experimental::cuda_scores(q,t,c,arena,800);
  for(std::size_t j=0;j<q.size();++j)if(scores[j]!=warpalign::Aligner(c).align(q[j],t[j]).score)return 1;
 }
 for(int trial=0;trial<1000;++trial){
  std::string q,t;for(int n=rng()%60;n--;)q+="ACGTN"[rng()%5];for(int n=rng()%60;n--;)t+="ACGTN"[rng()%5];
  warpalign::Config c;c.mismatch=1+rng()%7;c.gap_open=rng()%6;c.gap_extend=1+rng()%4;c.ambiguous=std::vector<std::string>{"literal","wildcard","mismatch"}[rng()%3];
  auto cpu=warpalign::Aligner(c).align(q,t);
  auto gpu=warpalign::experimental::cuda_alignments({q},{t},c,arena,800).front();
  if(gpu.score!=cpu.score||gpu.cigar!=cpu.cigar||gpu.edit_distance!=cpu.edit_distance)return 1;
 }
 for(int n:{0,1,31,32,33,65,1000,50000,100000}){
  std::string q(n,'A'),t=q;if(n)t[n/2]='C';warpalign::Config c;
  auto gpu=warpalign::experimental::cuda_alignments({q},{t},c,arena,64);
  if(gpu.front().cigar!=warpalign::Aligner(c).align(q,t).cigar)return 1;
 }
 {
  warpalign::Config c;
  auto empty=warpalign::experimental::cuda_alignments({"","A",""},{"","","AA"},c,arena,16);
  if(empty[0].cigar!=""||empty[1].cigar!="1I"||empty[2].cigar!="2D")return 1;
  c.memory_limit=1024;bool rejected=false;
  try{warpalign::experimental::cuda_alignments({std::string(100,'A')},{std::string(100,'T')},c,arena,800);}catch(const warpalign::ResourceError&){rejected=true;}
  if(!rejected)return 1;
 }
 std::cout<<"GPU score and device traceback equivalence passed on a real device\n";
}
