// CIGAR-indexed viewport: O(number of runs + visible bases), never one DOM node/base.
export function viewport(query,target,cigar,start=0,count=100) {
 let q=0,t=0,column=0; const output=[];
 for(const match of cigar.matchAll(/(\d+)([=XID])/g)) {
  const n=Number(match[1]),op=match[2],end=column+n;
  const a=Math.max(0,start-column),b=Math.min(n,start+count-column);
  for(let j=a;j<b;j++) output.push({q:op==='D'?'-':query[q+j],t:op==='I'?'-':target[t+j],op,column:column+j});
  if(op!=='D')q+=n;if(op!=='I')t+=n;column=end;
  if(column>=start+count)break;
 }
 return output;
}
export function alignmentLength(cigar){return [...cigar.matchAll(/(\d+)[=XID]/g)].reduce((n,m)=>n+Number(m[1]),0);}
