export async function api(path:string,init?:RequestInit){
 const response=await fetch('/api'+path,init);
 const data=await response.json().catch(()=>({detail:'The local service returned an invalid response.'}));
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));
 return data;
}
export function downloadJson(value:unknown,name:string){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
