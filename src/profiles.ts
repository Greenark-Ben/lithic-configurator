import { AFKC_SOURCE } from './afkc-source';
import type { Definition, Part, Configuration } from './engine';
export type ProfileSweep = {pointsMm:readonly (readonly number[])[]; originMm:[number,number,number]; inward:[number,number,number]; axis:[number,number,number]; lengthMm:number};
export const AFKC:Definition = {
 schemaVersion:'0.1',id:'elitfonster-afkc-profile-proof',revision:1,product:'Elitfönster AFKC · source profile proof',operation:'fixed',frameFace:53.5,frameDepth:105,glazingThickness:48,
 provenance:{frameFace:'Drawing 61-37-F221 rev A · sections A/B/C/D',frameDepth:'Prior DWG measurement · 105 mm; drawing section B',glazing:'Prior source definition · 48 mm assembly; pane build-up unresolved'},
 profile:{id:'afkc-polygon/0.1',source:AFKC_SOURCE,depthTransform:'view Z = -source depth; positive view Z is exterior. Source orientation prose conflicts with aluminium coordinates.',manufacturerApproved:false}
};
export function profileParts(d:Definition,c:Configuration):Part[]{
 const source=d.profile!.source,p=source.profiles,w=c.width,h=c.height,f=d.frameFace;
 const members=[
  {id:'left',origin:[-w/2,0,0],inward:[1,0,0],axis:[0,1,0],length:h,timber:p.timberJamb,alu:p.aluminiumHeadJamb},
  {id:'right',origin:[w/2,0,0],inward:[-1,0,0],axis:[0,1,0],length:h,timber:p.timberJamb,alu:p.aluminiumHeadJamb},
  {id:'head',origin:[-w/2+f,h,0],inward:[0,-1,0],axis:[1,0,0],length:w-2*f,timber:p.timberHead,alu:p.aluminiumHeadJamb},
  {id:'sill',origin:[-w/2+f,0,0],inward:[0,1,0],axis:[1,0,0],length:w-2*f,timber:p.timberSill,alu:p.aluminiumSill}
 ];
 const parts:Part[]=[];
 for(const m of members)for(const role of ['timber','aluminium'] as const){
  const points=(role==='timber'?m.timber:m.alu).pointsMm.map(([u,z])=>[u,-z]);
  const sweep:ProfileSweep={pointsMm:points,originMm:m.origin as [number,number,number],inward:m.inward as [number,number,number],axis:m.axis as [number,number,number],lengthMm:m.length};
  const bounds=[0,1,2].map(i=>{const values=points.flatMap(([u,z])=>[0,m.length].map(t=>m.origin[i]+m.inward[i]*u+m.axis[i]*t+(i===2?z:0)));return [Math.min(...values),Math.max(...values)]});
  parts.push({id:`${role}-${m.id}`,role,position:bounds.map(([a,b])=>(a+b)/2) as Part['position'],size:bounds.map(([a,b])=>b-a) as Part['size'],sweep});
 }
 const inset=f-source.fixedSectionDimensions.glazingSeatOverlapMm.value;
 parts.push({id:'glazing',role:'glazing',position:[0,h/2,-source.fixedSectionDimensions.glazingCenterOffsetFromTimberCenterMm.value],size:[w-2*inset,h-2*inset,d.glazingThickness]});
 return parts;
}
