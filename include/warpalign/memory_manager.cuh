#pragma once
#include <cuda_runtime.h>
#include <stdexcept>
#include <string>
#include <cstddef>
namespace warpalign::experimental {
inline void cuda_check(cudaError_t e) {if(e!=cudaSuccess)throw std::runtime_error(std::string("CUDA: ")+cudaGetErrorString(e));}
// Reuse one arena across calls. Host object must not be shared concurrently.
class DeviceArena {
 void* ptr_=nullptr;std::size_t capacity_=0;
public:
 DeviceArena()=default;DeviceArena(const DeviceArena&)=delete;DeviceArena& operator=(const DeviceArena&)=delete;
 ~DeviceArena(){if(ptr_)cudaFree(ptr_);}
 void* reserve(std::size_t bytes) {
  if(bytes<=capacity_)return ptr_;
  std::size_t free=0,total=0;cuda_check(cudaMemGetInfo(&free,&total));
  if(bytes>free-free/5)throw std::runtime_error("insufficient device memory (20% reserve)");
  void* replacement=nullptr;cuda_check(cudaMalloc(&replacement,bytes));
  if(ptr_) {auto status=cudaFree(ptr_);if(status!=cudaSuccess){cudaFree(replacement);cuda_check(status);}}
  ptr_=replacement;capacity_=bytes;return ptr_;
 }
 std::size_t capacity()const{return capacity_;}
};
}
