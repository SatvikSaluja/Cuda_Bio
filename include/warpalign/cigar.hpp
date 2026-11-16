#pragma once
#include <string>
#include <algorithm>
namespace warpalign {
inline std::string encode_cigar(std::string ops) {
 std::reverse(ops.begin(),ops.end()); std::string out;
 for(std::size_t p=0;p<ops.size();) {std::size_t e=p+1;while(e<ops.size()&&ops[e]==ops[p])++e;out+=std::to_string(e-p);out+=ops[p];p=e;}
 return out;
}
}
