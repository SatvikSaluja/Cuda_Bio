/* Original adapter, MIT. WFA2-lib is separately built and licensed (MIT).
 * Protocol: query<TAB>target per line; one JSON object per pair on stdout.
 * Compile with -I/path/to/WFA2-lib -L/path/to/WFA2-lib/lib -lwfa -lm.
 */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "wavefront/wavefront_align.h"
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char** argv){
 wavefront_aligner_attr_t attr=wavefront_aligner_attr_default;
 attr.distance_metric=gap_affine;attr.alignment_scope=compute_alignment;
 attr.alignment_form.span=alignment_end2end;
 attr.heuristic.strategy=wf_heuristic_none;
 attr.affine_penalties.match=0;
 attr.affine_penalties.mismatch=argc>2?atoi(argv[2]):4;
 attr.affine_penalties.gap_opening=argc>3?atoi(argv[3]):6;
 attr.affine_penalties.gap_extension=argc>4?atoi(argv[4]):2;
 attr.memory_mode=argc>1&&strcmp(argv[1],"ultralow")==0?wavefront_memory_ultralow:wavefront_memory_high;
 wavefront_aligner_t* aligner=wavefront_aligner_new(&attr);
 if(!aligner)return 2;
 char* line=NULL;size_t capacity=0;ssize_t length;
 while((length=getline(&line,&capacity,stdin))>=0){
  while(length&&(line[length-1]=='\n'||line[length-1]=='\r'))line[--length]='\0';
  char* target=strchr(line,'\t');if(!target){fprintf(stderr,"Missing tab delimiter\n");free(line);wavefront_aligner_delete(aligner);return 2;}
  *target++='\0';
  double start=now();
  int status=wavefront_align(aligner,target,strlen(target),line,strlen(line));
  double elapsed=now()-start;
  if(status!=0){fprintf(stderr,"WFA2 status %d\n",status);free(line);wavefront_aligner_delete(aligner);return 3;}
  // WFA2 score conventions are normalized to the positive-cost WarpAlign model.
  printf("{\"score\":%d,\"seconds\":%.9f,\"backend\":\"wfa2\"}\n",abs(aligner->cigar->score),elapsed);
 }
 free(line);wavefront_aligner_delete(aligner);return 0;
}
