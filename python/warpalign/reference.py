"""Independent affine DP oracle for bounded validation cases, not production WFA."""
def affine_score(query,target,mismatch=4,gap_open=6,gap_extend=2):
    if len(query)*len(target)>4_000_000:raise ValueError('Reference DP input too large')
    inf=10**15;m=len(target)
    previous=[0]+[gap_open+j*gap_extend for j in range(1,m+1)]
    insert=[inf]*(m+1)
    for i,q in enumerate(query,1):
        current=[gap_open+i*gap_extend]+[inf]*m
        new_insert=[current[0]]+[inf]*m
        deletion=inf
        for j,t in enumerate(target,1):
            new_insert[j]=min(previous[j]+gap_open+gap_extend,insert[j]+gap_extend)
            deletion=min(current[j-1]+gap_open+gap_extend,deletion+gap_extend)
            current[j]=min(previous[j-1]+(0 if q==t else mismatch),new_insert[j],deletion)
        previous,insert=current,new_insert
    return previous[-1]
