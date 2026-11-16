#pragma once
#include <string>
#include <stdexcept>
#include <cctype>
#include <limits>
namespace warpalign {
inline std::string normalize(std::string s) {
 if(s.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()/4)) throw std::length_error("sequence exceeds 32-bit coordinate capacity");
 for(char& c:s) { c=static_cast<char>(std::toupper(static_cast<unsigned char>(c))); if(std::string("ACGTN").find(c)==std::string::npos) throw std::invalid_argument("DNA must contain only A,C,G,T,N"); }
 return s;
}
inline bool equal_base(char a,char b,const std::string& policy) {
 if(a=='N'||b=='N') return policy=="wildcard" || (policy=="literal" && a==b);
 return a==b;
}
}
