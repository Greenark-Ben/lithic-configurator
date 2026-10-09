import { describe,it,expect } from 'vitest';
import { SAMPLE,INITIAL,PRESETS,calculateParts,configurationIssues,definitionIssues,createBuildRequest } from './engine';
import { AFKC } from './profiles';
import { partGeometry } from './profileGeometry';
const approved={...SAMPLE,frameDepth:120,provenance:{...SAMPLE.provenance,frameDepth:'User confirmation'}};
describe('governed prototype',()=>{
 it('blocks unconfirmed depth and missing evidence',()=>{expect(definitionIssues(SAMPLE).length).toBe(2);expect(()=>calculateParts(SAMPLE,INITIAL)).toThrow();expect(definitionIssues({...approved,provenance:{...approved.provenance,frameDepth:null}})).toHaveLength(1)});
 it('rejects unsupported dimensions and nonfinite values',()=>{expect(configurationIssues({...INITIAL,width:299},approved)).toHaveLength(1);expect(definitionIssues({...approved,frameDepth:NaN})).not.toHaveLength(0)});
 it('blocks nonfinite sizes and an opening consumed by the frame',()=>{expect(configurationIssues({...INITIAL,width:NaN},approved)).not.toHaveLength(0);expect(configurationIssues({...INITIAL,height:3001},approved)).not.toHaveLength(0);expect(()=>calculateParts({...approved,frameFace:150},{...INITIAL,width:300})).toThrow('no glazing opening')});
 it.each([...PRESETS,[1000,1375] as const,[300,300] as const,[3000,3000] as const])('preserves outer bounds at %s by %s', (width,height)=>{const p=calculateParts(approved,{...INITIAL,width,height});expect(p).toHaveLength(9);expect(Math.min(...p.map(x=>x.position[0]-x.size[0]/2))).toBe(-width/2);expect(Math.max(...p.map(x=>x.position[0]+x.size[0]/2))).toBe(width/2);expect(Math.min(...p.map(x=>x.position[1]-x.size[1]/2))).toBe(0);expect(Math.max(...p.map(x=>x.position[1]+x.size[1]/2))).toBe(height);expect(p.find(x=>x.role==='glazing')?.size).toEqual([width-140,height-140,36]);});
 it('replays geometry without claiming native verification',()=>{const a={definition:approved,approvedAt:'2026-10-08T09:30:00Z'};expect(createBuildRequest(a,INITIAL)).toEqual(createBuildRequest(a,INITIAL));expect(createBuildRequest(a,INITIAL).nativeStatus).toBe('not-built')});
});
describe('source-derived AFKC profiles',()=>{
 it.each([[900,1200],[1200,1500],[1500,1800],[300,300],[3000,3000]])('keeps fixed sections and seated glazing at %s × %s',(width,height)=>{
  const parts=calculateParts(AFKC,{...INITIAL,width,height});
  expect(parts).toHaveLength(9);expect(parts.filter(p=>p.sweep)).toHaveLength(8);
  const glass=parts.find(p=>p.role==='glazing')!;expect(glass.size).toEqual([width-81,height-81,48]);expect(glass.position[2]).toBe(13.5);
  for(const p of parts){const geometry=partGeometry(p);geometry.computeBoundingBox();const box=geometry.boundingBox!;for(let i=0;i<3;i++){expect(box.min.getComponent(i)*1000+p.position[i]).toBeCloseTo(p.position[i]-p.size[i]/2,3);expect(box.max.getComponent(i)*1000+p.position[i]).toBeCloseTo(p.position[i]+p.size[i]/2,3)}
   if(p.role==='aluminium')expect(p.position[2]+p.size[2]/2).toBe(62.5);
   if(p.role==='timber')expect(p.size[2]).toBe(105);
   const a=geometry.getAttribute('position');let volume=0;for(let i=0;i<a.count;i+=3){const [x,y,z]=[i,i+1,i+2].map(k=>[a.getX(k),a.getY(k),a.getZ(k)]);volume+=(x[0]*(y[1]*z[2]-y[2]*z[1])+x[1]*(y[2]*z[0]-y[0]*z[2])+x[2]*(y[0]*z[1]-y[1]*z[0]))/6}expect(volume).toBeGreaterThan(0);geometry.dispose();
  }
 });
 it('blocks changed fixed sections and exports traceable sweeps without native claims',()=>{
  expect(()=>calculateParts({...AFKC,frameDepth:120},INITIAL)).toThrow('Source profiles require');
  const request=createBuildRequest({definition:AFKC,approvedAt:'2026-10-09'},INITIAL);expect(request.geometryEngine).toBe('fixed-window-profile-sweeps/0.1');expect(request.definition.profile?.manufacturerApproved).toBe(false);expect(request.nativeStatus).toBe('not-built');expect(request.limitations).toContain(AFKC.profile!.source.junctionAssumption);
 });
});
