from warpalign import Aligner
aligner=Aligner()
print(aligner.align('ACGT','ACGTT').cigar)
for result in aligner.align_batch(['AA','CG'],['AT','CG']):
    print(result.score,result.cigar)
