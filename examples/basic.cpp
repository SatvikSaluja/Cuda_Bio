#include <warpalign/warpalign.hpp>
#include <iostream>
int main(){auto r=warpalign::Aligner{}.align("ACGTACGT","ACGTTACGT");std::cout<<r.score<<"\t"<<r.cigar<<"\n";}
