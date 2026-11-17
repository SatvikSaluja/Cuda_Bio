#pragma once
#include <cstddef>
#ifdef __CUDACC__
#define WARPALIGN_HD __host__ __device__
#else
#define WARPALIGN_HD
#endif
namespace warpalign::experimental {
// Full score history, with M/I/D states. Shared by device code and host tests.
struct TraceHistory {
 const int* data; int low,width,levels;
 WARPALIGN_HD int get(int s,int state,int k) const {
  if(s<0||s>=levels||k<low||k>=low+width)return -1000000000;
  return data[(static_cast<std::size_t>(s)*3+state)*width+k-low];
 }
};
// Reverse SAM operations. Negative return means invalid history/capacity.
WARPALIGN_HD inline int trace_history(TraceHistory w,int n,int m,int score,int x,int o,int e,char* out,int capacity) {
 int s=score,k=n-m,h=n,state=0,length=0;
 while(s>0||h>0||h-k>0){
  if(s<0||h<0||h>n||h-k<0||h-k>m)return -1;
  if(state==0){
   int sub=w.get(s-x,0,k)+1;
   if(sub<1||sub>n||sub-k<1||sub-k>m)sub=-1000000000;
   const int ins=w.get(s,1,k),del=w.get(s,2,k);
   int base=sub>ins?sub:ins;base=base>del?base:del;
   if(s==0&&k==0)base=0;
   if(base<0||base>h)return -1;
   while(h>base){if(length>=capacity)return -1;out[length++]='=';--h;}
   if(s==0&&k==0&&h==0)break;
   if(base==ins)state=1;
   else if(base==del)state=2;
   else {if(length>=capacity)return -1;out[length++]='X';--h;s-=x;}
  } else if(state==1){
   if(h==0||length>=capacity)return -1;
   const bool opening=w.get(s-o-e,0,k-1)>=w.get(s-e,1,k-1);
   out[length++]='I';--h;--k;s-=opening?o+e:e;if(opening)state=0;
  } else {
   if(h-k==0||length>=capacity)return -1;
   const bool opening=w.get(s-o-e,0,k+1)>=w.get(s-e,2,k+1);
   out[length++]='D';++k;s-=opening?o+e:e;if(opening)state=0;
  }
 }
 return s==0&&h==0&&k==0?length:-1;
}
}
#undef WARPALIGN_HD
