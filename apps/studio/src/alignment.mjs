/** Build a compact CIGAR index once; viewport lookup is O(log runs + visible bases). */
export function indexAlignment(cigar) {
 const runs=[];let q=0,t=0,column=0,consumed=0;
 for(const match of cigar.matchAll(/(\d+)([=XID])/g)){
  if(match.index!==consumed)throw new Error('Invalid CIGAR');
  const n=Number(match[1]),op=match[2];if(!Number.isSafeInteger(n)||n<=0)throw new Error('Invalid CIGAR length');
  runs.push({n,op,q,t,column,end:column+n});
  if(op!=='D')q+=n;if(op!=='I')t+=n;column+=n;consumed+=match[0].length;
 }
 if(consumed!==cigar.length)throw new Error('Invalid CIGAR');
 return {runs,length:column,queryLength:q,targetLength:t,variants:runs.filter(r=>r.op!=='=').map(r=>r.column)};
}
export function indexedViewport(query,target,index,start=0,count=100){
 const out=[];const runs=index.runs;let low=0,high=runs.length;
 while(low<high){const mid=(low+high)>>1;if(runs[mid].end<=start)low=mid+1;else high=mid;}
 for(let i=low;i<runs.length&&runs[i].column<start+count;i++){
  const r=runs[i],a=Math.max(0,start-r.column),b=Math.min(r.n,start+count-r.column);
  for(let j=a;j<b;j++)out.push({q:r.op==='D'?'-':query[r.q+j],t:r.op==='I'?'-':target[r.t+j],qpos:r.op==='D'?null:r.q+j,tpos:r.op==='I'?null:r.t+j,op:r.op,column:r.column+j});
 }
 return out;
}
export function viewport(query,target,cigar,start=0,count=100){return indexedViewport(query,target,indexAlignment(cigar),start,count);}
export function alignmentLength(cigar){return indexAlignment(cigar).length;}
