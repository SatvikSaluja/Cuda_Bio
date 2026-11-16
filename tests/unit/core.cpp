#include <warpalign/warpalign.hpp>
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
void check(std::string q,std::string t,Config c={}){
 auto r=Aligner(c).align(q,t);q=normalize(q);t=normalize(t);require(r.score==dp(q,t,c));
 int qi=0,ti=0,score=0,count=0,ed=0;for(char op:r.cigar){if(op>='0'&&op<='9'){count=count*10+op-'0';continue;}require(count>0);
 if(op=='I'||op=='D'){score+=c.gap_open+count*c.gap_extend;ed+=count;if(op=='I')qi+=count;else ti+=count;}
 else for(int z=0;z<count;++z){require(qi<(int)q.size()&&ti<(int)t.size());bool eq=equal_base(q[qi++],t[ti++],c.ambiguous);require(eq==(op=='='));if(!eq){score+=c.mismatch;++ed;}}count=0;}
 require(qi==(int)q.size()&&ti==(int)t.size()&&score==r.score&&ed==r.edit_distance);
 c.score_only=true;require(Aligner(c).align(q,t).score==r.score);
}
int main(){
 for(auto p:std::vector<std::pair<std::string,std::string>>{{"",""},{"A",""},{"","ACGT"},{"ACGT","ACGT"},{"A","T"},{"AAAAACCCCC","AAAAAGGGGGCCCCC"},{"acgtn","ACGTN"}})check(p.first,p.second);
 std::mt19937 rng(1729);for(int test=0;test<4000;++test){std::string q,t;int n=rng()%35,m=rng()%35;for(int j=0;j<n;++j)q+="ACGTN"[rng()%5];for(int j=0;j<m;++j)t+="ACGTN"[rng()%5];Config c;c.mismatch=1+rng()%7;c.gap_open=rng()%6;c.gap_extend=1+rng()%4;c.ambiguous=std::vector<std::string>{"literal","wildcard","mismatch"}[rng()%3];check(q,t,c);}
 for(int n:{100,500,1000,5000,10000,20000,50000,100000}){std::string q(n,'A'),t=q;t[n/2]='C';auto r=Aligner{}.align(q,t);require(r.score==4&&r.matches==n-1&&r.mismatches==1);}
 require(Aligner{}.align(std::string(100000,'A'), "").cigar=="100000I");
 Config c;c.memory_limit=1024;bool failed=false;try{Aligner(c).align(std::string(100,'A'),std::string(100,'C'));}catch(const ResourceError&){failed=true;}require(failed);
 c={};c.mode="fast";c.bandwidth=0;require(Aligner(c).align("ACGT","ACCT").heuristic_used);
 std::cout<<"4000 randomized DP/CIGAR comparisons, score-only, edge cases and low-divergence lengths through 100kb passed\n";
}
