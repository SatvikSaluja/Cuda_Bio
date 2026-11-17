#include <warpalign/warpalign.hpp>
#include <warpalign/traceback.hpp>
#include <random>
#include <iostream>
#include <cstdlib>
using namespace warpalign;
void require(bool v){if(!v)throw std::runtime_error("test failed");}
int dp(const std::string&q,const std::string&t,const Config& c){
 int n=q.size(),m=t.size(),inf=100000000;std::vector<int>a((n+1)*(m+1),inf),i(a),d(a);auto at=[&](int x,int y){return x*(m+1)+y;};a[0]=0;
 for(int x=0;x<=n;++x)for(int y=0;y<=m;++y){if(x==0&&y==0)continue;int p=at(x,y);
 if(x)i[p]=std::min(a[at(x-1,y)]+c.gap_open+c.gap_extend,i[at(x-1,y)]+c.gap_extend);
 if(y)d[p]=std::min(a[at(x,y-1)]+c.gap_open+c.gap_extend,d[at(x,y-1)]+c.gap_extend);
 a[p]=std::min(i[p],d[p]);if(x&&y)a[p]=std::min(a[p],a[at(x-1,y-1)]+(equal_base(q[x-1],t[y-1],c.ambiguous)?0:c.mismatch));
 }return a.back();
}
// Host execution of the exact device traceback routine. Independent dense DP
// above supplies the optimum; this builder supplies complete WFA history.
std::string device_trace_host(const std::string& q,const std::string& t,const Config& c,int optimum){
 int n=q.size(),m=t.size(),width=n+m+1,low=-m;
 std::vector<int> data(static_cast<std::size_t>(optimum+1)*3*width,unreachable);
 experimental::TraceHistory w{data.data(),low,width,optimum+1};
 auto valid=[&](int h,int k){return h>=0&&h<=n&&h-k>=0&&h-k<=m?h:unreachable;};
 for(int s=0;s<=optimum;++s)for(int k=low;k<=n;++k){
  int i=valid(std::max(w.get(s-c.gap_open-c.gap_extend,0,k-1),w.get(s-c.gap_extend,1,k-1))+1,k);
  int d=valid(std::max(w.get(s-c.gap_open-c.gap_extend,0,k+1),w.get(s-c.gap_extend,2,k+1)),k);
  int sub=valid(w.get(s-c.mismatch,0,k)+1,k);
  if(i==0)i=unreachable;if(d!=unreachable&&d-k==0)d=unreachable;
  if(sub!=unreachable&&(sub==0||sub-k==0))sub=unreachable;
  int h=s==0&&k==0?0:std::max({i,d,sub});
  while(h>=0&&h<n&&h-k<m&&equal_base(q[h],t[h-k],c.ambiguous))++h;
  auto at=static_cast<std::size_t>(s)*3*width+k-low;data[at]=h;data[at+width]=i;data[at+2*width]=d;
 }
 std::string ops(n+m,' ');
 int count=experimental::trace_history(w,n,m,optimum,c.mismatch,c.gap_open,c.gap_extend,ops.data(),n+m);
 require(count>=0);
 if(count>0)require(experimental::trace_history(w,n,m,optimum,c.mismatch,c.gap_open,c.gap_extend,ops.data(),count-1)==-1);
 // The capacity failure may have overwritten a prefix with the same operations.
 ops.resize(count);return encode_cigar(ops);
}
void check(std::string q,std::string t,Config c={}){
 auto r=Aligner(c).align(q,t);q=normalize(q);t=normalize(t);require(r.score==dp(q,t,c));
 require(device_trace_host(q,t,c,r.score)==r.cigar);
 int qi=0,ti=0,score=0,count=0,ed=0;for(char op:r.cigar){if(op>='0'&&op<='9'){count=count*10+op-'0';continue;}require(count>0);
 if(op=='I'||op=='D'){score+=c.gap_open+count*c.gap_extend;ed+=count;if(op=='I')qi+=count;else ti+=count;}
 else for(int z=0;z<count;++z){require(qi<(int)q.size()&&ti<(int)t.size());bool eq=equal_base(q[qi++],t[ti++],c.ambiguous);require(eq==(op=='='));if(!eq){score+=c.mismatch;++ed;}}count=0;}
 require(qi==(int)q.size()&&ti==(int)t.size()&&score==r.score&&ed==r.edit_distance);
 c.checkpoint_interval=7;
 auto checkpoint=Aligner(c).align(q,t);
 require(checkpoint.score==r.score && checkpoint.cigar==r.cigar);
 c.score_only=true;require(Aligner(c).align(q,t).score==r.score);
}
int main(){
 for(auto p:std::vector<std::pair<std::string,std::string>>{{"",""},{"A",""},{"","ACGT"},{"ACGT","ACGT"},{"A","T"},{"AAAAACCCCC","AAAAAGGGGGCCCCC"},{"acgtn","ACGTN"}})check(p.first,p.second);
 std::vector<std::string> exhaustive{""};
 for(int length=1;length<=4;++length)for(int bits=0;bits<(1<<length);++bits){std::string sequence;for(int j=0;j<length;++j)sequence+=(bits&(1<<j))?'A':'C';exhaustive.push_back(sequence);}
 for(const auto& q:exhaustive)for(const auto& t:exhaustive){check(q,t);Config zero_open;zero_open.gap_open=0;check(q,t,zero_open);}
 std::mt19937 rng(1729);for(int test=0;test<4000;++test){std::string q,t;int n=rng()%35,m=rng()%35;for(int j=0;j<n;++j)q+="ACGTN"[rng()%5];for(int j=0;j<m;++j)t+="ACGTN"[rng()%5];Config c;c.mismatch=1+rng()%7;c.gap_open=rng()%6;c.gap_extend=1+rng()%4;c.ambiguous=std::vector<std::string>{"literal","wildcard","mismatch"}[rng()%3];check(q,t,c);}
 for(int n:{100,500,1000,5000,10000,20000,50000,100000}){std::string q(n,'A'),t=q;t[n/2]='C';auto r=Aligner{}.align(q,t);require(r.score==4&&r.matches==n-1&&r.mismatches==1);require(device_trace_host(q,t,Config{},r.score)==r.cigar);}
 require(Aligner{}.align(std::string(100000,'A'), "").cigar=="100000I");
 Config c;c.memory_limit=1024;bool failed=false;try{Aligner(c).align(std::string(100,'A'),std::string(100,'C'));}catch(const ResourceError&){failed=true;}require(failed);
 c={};c.mode="fast";c.bandwidth=0;require(Aligner(c).align("ACGT","ACCT").heuristic_used);
 std::cout<<"4000 randomized and 1922 exhaustive DP/CIGAR comparisons, checkpoint/score-only, edge cases and low-divergence lengths through 100kb passed\n";
}
