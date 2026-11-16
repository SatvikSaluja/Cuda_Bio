#include <warpalign/cuda_backend.cuh>
#include <warpalign/warpalign.hpp>
#include <iostream>
#include <random>
int main(){int devices=0;if(cudaGetDeviceCount(&devices)!=cudaSuccess||devices==0){std::cerr<<"SKIP: no CUDA device\n";return 77;}
 warpalign::experimental::DeviceArena arena;std::mt19937 rng(1729);
 for(int n:{0,1,31,32,33,65,100,500,1000,50000,100000}){std::string q(n,'A'),t=q;if(n)t[n/2]='C';warpalign::Config c;auto cpu=warpalign::Aligner(c).align(q,t);if(warpalign::experimental::cuda_score(q,t,c,arena,64)!=cpu.score)return 1;}
 for(int trial=0;trial<1000;++trial){std::string q,t;for(int n=rng()%90;n--;)q+="ACGT"[rng()%4];for(int n=rng()%90;n--;)t+="ACGT"[rng()%4];warpalign::Config c;auto cpu=warpalign::Aligner(c).align(q,t);if(warpalign::experimental::cuda_score(q,t,c,arena,800)!=cpu.score)return 1;}
 std::cout<<"GPU score equivalence passed on a real device\n";
}
