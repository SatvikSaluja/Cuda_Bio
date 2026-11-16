#pragma once
#include <vector>
namespace warpalign {
constexpr int unreachable=-1000000000;
struct Wavefront {
 int lo=0, hi=-1;
 std::vector<int> m,i,d;
 Wavefront()=default;
 Wavefront(int l,int h):lo(l),hi(h),m(h-l+1,unreachable),i(m),d(m){}
 int get(char state,int k) const { if(k<lo||k>hi)return unreachable; return (state=='M'?m:state=='I'?i:d)[k-lo]; }
 std::size_t bytes() const {return sizeof(Wavefront)+3*m.size()*sizeof(int)+64;}
};
}
