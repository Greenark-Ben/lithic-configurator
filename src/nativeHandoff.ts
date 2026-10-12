import {createBuildRequest,PRESETS,type Approval,type Configuration} from './engine';
export const NATIVE_BUILDER='lithic-afkc-desktop/0.1';
export async function requestIdentity(a:Approval,c:Configuration){
 const text=JSON.stringify(createBuildRequest(a,c),null,2);
 const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
 return {text,sha256:Array.from(new Uint8Array(digest)).map(n=>n.toString(16).padStart(2,'0')).join('')};
}
function crc32(data:Uint8Array){let crc=0xffffffff;for(const b of data){crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0)}return (crc^0xffffffff)>>>0}
// Small, dependency-free ZIP writer: stored entries, UTF-8 filenames and matching CRCs.
export function zipFiles(files:{name:string;data:Uint8Array}[]):Uint8Array{
 const encoder=new TextEncoder(),chunks:Uint8Array[]=[],directory:Uint8Array[]=[];let offset=0;
 for(const f of files){const name=encoder.encode(f.name),crc=crc32(f.data),local=new Uint8Array(30+name.length),v=new DataView(local.buffer);
  v.setUint32(0,0x04034b50,true);v.setUint16(4,20,true);v.setUint16(6,0x800,true);v.setUint16(12,33,true);v.setUint32(14,crc,true);v.setUint32(18,f.data.length,true);v.setUint32(22,f.data.length,true);v.setUint16(26,name.length,true);local.set(name,30);
  const central=new Uint8Array(46+name.length),d=new DataView(central.buffer);d.setUint32(0,0x02014b50,true);d.setUint16(4,20,true);d.setUint16(6,20,true);d.setUint16(8,0x800,true);d.setUint16(14,33,true);d.setUint32(16,crc,true);d.setUint32(20,f.data.length,true);d.setUint32(24,f.data.length,true);d.setUint16(28,name.length,true);d.setUint32(42,offset,true);central.set(name,46);directory.push(central);chunks.push(local,f.data);offset+=local.length+f.data.length;
 }
 const size=directory.reduce((n,d)=>n+d.length,0),end=new Uint8Array(22),e=new DataView(end.buffer);e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,size,true);e.setUint32(16,offset,true);chunks.push(...directory,end);
 const result=new Uint8Array(offset+size+22);let position=0;for(const chunk of chunks){result.set(chunk,position);position+=chunk.length}return result;
}
export async function prepareNativeHandoff(a:Approval,c:Configuration){
 if(!a.definition.profile)throw new Error('The desktop builder currently supports the AFKC source profile proof.');
 const identity=await requestIdentity(a,c),names=['script.py','contract.py','afkc-source.json','Install.ps1','bundle.yaml','README.txt'];
 const files=await Promise.all(names.map(async name=>{const response=await fetch('/native/'+name);if(!response.ok)throw new Error('The Revit handoff files are unavailable. Please retry.');return {name,data:new Uint8Array(await response.arrayBuffer())}}));
 const encoder=new TextEncoder();files.push({name:'request.json',data:encoder.encode(identity.text)},{name:'manifest.json',data:encoder.encode(JSON.stringify({builder:NATIVE_BUILDER,requestSha256:identity.sha256,geometryMode:'fixed-size-snapshot',nativeParameterFlex:false},null,2))});
 return zipFiles(files);
}
export type NativeReport={kind:'lithic-native-report';builder:string;requestSha256:string;status:'passed'|'failed';revitVersion:string;cases:{sizeMm:[number,number];status:'passed'|'failed';familyFile?:string;error?:string}[]};
export async function readNativeReport(value:unknown,a:Approval,c:Configuration):Promise<NativeReport>{
 const r=value as Record<string,any>,identity=await requestIdentity(a,c);
 if(!r||r.kind!=='lithic-native-report'||r.schemaVersion!=='0.1'||r.builder!==NATIVE_BUILDER||r.requestSha256!==identity.sha256)throw new Error('This report does not match the current approved configuration. Return to the exported size and finishes, or prepare a fresh handoff.');
 if(r.nativeParameterFlex!==false||r.manufacturerApproved!==false||r.geometryMode!=='fixed-size-snapshot'||!/^20\d\d$/.test(r.revitVersion)||Number(r.revitVersion)<2024||!['passed','failed'].includes(r.status)||!Array.isArray(r.cases))throw new Error('Unsupported or incomplete native report.');
 const sizes=[[c.width,c.height],...PRESETS.filter(([w,h])=>w!==c.width||h!==c.height)];
 if(r.cases.length!==sizes.length||sizes.some(([w,h])=>r.cases.filter((x:any)=>Array.isArray(x.sizeMm)&&x.sizeMm[0]===w&&x.sizeMm[1]===h).length!==1))throw new Error('The native report is missing required size checks.');
 for(const result of r.cases){
  if(!Array.isArray(result.sizeMm)||result.sizeMm.length!==2||result.error!==undefined&&typeof result.error!=='string')throw new Error('The native report contains malformed case details.');
  if(!['passed','failed'].includes(result.status))throw new Error('A native check has no valid result.');
  if(result.status==='passed'){
   const required=['scheduleDimensionsPassed','provenancePassed','hostPassed','openingPassed','exteriorPassed','familyReopened','projectReopened','persistenceGeometryPassed','hostPersisted','openingPersisted'];
   if(required.some(k=>result[k]!==true)||['familyWarnings','projectWarnings','reopenedWarnings'].some(k=>!Array.isArray(result[k])||result[k].length)||!Array.isArray(result.parts)||result.parts.length!==9||result.parts.some((p:any)=>p.passed!==true)||typeof result.familyFile!=='string'||!/^LITHIC-AFKC-[\d_x]+\.rfa$/.test(result.familyFile)||!/^[a-f0-9]{64}$/.test(result.familySha256))throw new Error('The claimed pass lacks its native check evidence.');
  }
 }
 if((r.cases.every((x:any)=>x.status==='passed')?'passed':'failed')!==r.status)throw new Error('The report summary conflicts with its case results.');
 return r as NativeReport;
}
