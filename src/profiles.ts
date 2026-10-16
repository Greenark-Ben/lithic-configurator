import { FIXED_WINDOW } from './productCatalogue';
import { AFKC_SOURCE } from './afkc-source';
import type { Definition, Part, Configuration } from './engine';
export type ProfileSweep = {pointsMm:readonly (readonly number[])[]; holesMm?:readonly (readonly (readonly number[])[])[]; originMm:[number,number,number]; inward:[number,number,number]; axis:[number,number,number]; lengthMm:number; mitred?:boolean};
export const FIXED_WINDOW_DEFINITION:Definition = {
 schemaVersion:'0.1',id:FIXED_WINDOW.constructionId,productId:FIXED_WINDOW.id,revision:4,product:FIXED_WINDOW.name,operation:'fixed',frameFace:53.5,frameDepth:105,glazingThickness:48,
 provenance:{frameFace:'Drawing 61-37-F221 rev A · sections A/B/C/D',frameDepth:'DWG measurement · 105 mm; drawing section B',glazing:'Reviewed source build-up: 4 / 18 / 4 / 18 / 4 mm'},
 profile:{id:'lithic-fixed-profile/0.3.0',source:AFKC_SOURCE,depthTransform:'View exterior depth = negative source depth.',manufacturerApproved:false}
};
// Legacy source-fixture alias; product identity is supplier-independent.
export const AFKC=FIXED_WINDOW_DEFINITION;
export function profileParts(d:Definition,c:Configuration):Part[]{
 const source=d.profile!.source,p=source.profiles,w=c.width,h=c.height,f=d.frameFace,parts:Part[]=[];
 const add=(id:string,role:Part['role'],points:readonly (readonly number[])[],origin:[number,number,number],inward:[number,number,number],axis:[number,number,number],length:number,mitred=false,holes?:number[][][])=>{
  const sweep:ProfileSweep={pointsMm:points,originMm:origin,inward,axis,lengthMm:length,...(mitred?{mitred:true}:{}),...(holes?{holesMm:holes}:{})};
  const bounds=[0,1,2].map(i=>{const values=points.flatMap(([u,z])=>[mitred?u:0,mitred?length-u:length].map(t=>origin[i]+inward[i]*u+axis[i]*t+(i===2?z:0)));return [Math.min(...values),Math.max(...values)]});
  parts.push({id,role,position:bounds.map(([a,b])=>(a+b)/2) as Part['position'],size:bounds.map(([a,b])=>b-a) as Part['size'],sweep});
 };
 const members=[
  {id:'left',origin:[-w/2,0,0],inward:[1,0,0],axis:[0,1,0],length:h},
  {id:'right',origin:[w/2,0,0],inward:[-1,0,0],axis:[0,1,0],length:h},
  {id:'head',origin:[-w/2,h,0],inward:[0,-1,0],axis:[1,0,0],length:w},
  {id:'sill',origin:[-w/2,0,0],inward:[0,1,0],axis:[1,0,0],length:w}
 ];
 for(const m of members){
  const inward=m.inward as [number,number,number],axis=m.axis as [number,number,number];
  const horizontal=m.id==='head'||m.id==='sill';
  const timber=m.id==='sill'?p.timberSill:m.id==='head'?p.timberHead:p.timberJamb;
  const bead=m.id==='sill'?p.beadSill:p.beadHeadJamb;
  const mapped=(profile:{pointsMm:readonly (readonly number[])[]})=>profile.pointsMm.map(([u,z])=>[u,-z]);
  add('timber-'+m.id,'timber',mapped(timber),[m.origin[0]+(horizontal?f:0),m.origin[1],0],inward,axis,m.length-(horizontal?2*f:0));
  add('bead-'+m.id,'timber',mapped(bead),[m.origin[0]+(horizontal?40:0),m.origin[1],0],inward,axis,m.length-(horizontal?80:0));
  add('aluminium-'+m.id,'aluminium',mapped(m.id==='sill'?p.aluminiumSill:p.aluminiumHeadJamb),m.origin as [number,number,number],inward,axis,m.length,true);
  if(m.id!=='sill')add('return-'+m.id,'aluminium',mapped(p.aluminiumCoverageReturn),m.origin as [number,number,number],inward,axis,m.length,true);
  add('seal-'+m.id,'seal',mapped(p.glazingSeal),m.origin as [number,number,number],inward,axis,m.length,true);
 }
 const inset=f-source.fixedSectionDimensions.glazingSeatOverlapMm.value;
 source.glazing.paneDepthRangesMm.forEach(([a,b],i)=>parts.push({id:'glass-pane-'+(i+1),role:'glazing',position:[0,h/2,(a+b)/2],size:[w-2*inset,h-2*inset,b-a]}));
 const {edgeInsetMm:edge,radialHeightMm:radial,skinMm:skin}=source.glazing.spacer;
 source.glazing.cavityDepthRangesMm.forEach(([a,b],i)=>{
  const points=[[0,a],[radial,a],[radial,b],[0,b]],holes=[[[skin,a+skin],[skin,b-skin],[radial-skin,b-skin],[radial-skin,a+skin]]];
  for(const side of ['left','right','sill','head']){
   const vertical=side==='left'||side==='right';
   const origin:[number,number,number]=vertical?[side==='left'?-w/2+inset+edge:w/2-inset-edge-radial,inset+edge,0]:[-w/2+inset+edge+radial,side==='sill'?inset+edge:h-inset-edge-radial,0];
   add('spacer-'+(i+1)+'-'+side,'spacer',points,origin,vertical?[1,0,0]:[0,1,0],vertical?[0,1,0]:[1,0,0],vertical?h-2*(inset+edge):w-2*(inset+edge+radial),false,holes);
  }
 });
 return parts;
}
