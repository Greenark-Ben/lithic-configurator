import {describe,it,expect} from 'vitest';
import {SIDE_HUNG_DEFINITION as definition,SIDE_HUNG_INITIAL as config,SIDE_HUNG_PARTS as parts,SIDE_HUNG_PIVOT as pivot,rotateSashPoint,openingAngleIssues} from './sideHung';
import {calculateParts,configurationIssues,createBuildRequest,definitionIssues} from './engine';
import {prepareNativeHandoff} from './nativeHandoff';
import {partGeometry} from './profileGeometry';
import mesh from './sidehung-mesh.json';
import {validateRequest,revitRoute} from '../server/revit';
describe('side-hung browser snapshot',()=>{
 it('keeps the native source identity, parts and geometry distinct from fixed exports',async()=>{
  expect(definitionIssues(definition)).toEqual([]);expect(configurationIssues(config,definition)).toEqual([]);
  expect(definition.productId).toBe('lithic.window.side-hung-outward');expect(definition.sideHung?.source.model).toBe('AFSC');
  expect(mesh.activeProjectPreserved).toBe(true);expect(mesh.headAnalyticVolumeCheckPassed).toBe(false);
  expect(calculateParts(definition,config)).toHaveLength(29);expect(parts.filter(p=>p.mesh?.moving)).toHaveLength(21);
  expect(parts.filter(p=>p.role==='glazing')).toHaveLength(3);expect(parts.filter(p=>p.role==='spacer')).toHaveLength(8);
  expect(()=>createBuildRequest({definition,approvedAt:'2026-10-16'},config)).toThrow('preview only');
  await expect(prepareNativeHandoff({definition,approvedAt:'2026-10-16'},config)).rejects.toThrow('Fixed Window');
  expect(configurationIssues({...config,width:900},definition)[0]).toContain('snapshot only');
 });
 it('rotates every moving part rigidly outward about outside-left and returns to closed',()=>{
  for(const angle of [0,15,30,45,90]){
   expect(rotateSashPoint(pivot,angle)).toEqual(pivot);
   const p:[number,number,number]=[350,650,-40],q=rotateSashPoint(p,angle);
   expect(Math.hypot(q[0]-pivot[0],q[2]-pivot[2])).toBeCloseTo(Math.hypot(p[0]-pivot[0],p[2]-pivot[2]),8);
   expect(q[1]).toBe(p[1]);
   if(angle>0)expect(q[2]).toBeGreaterThan(p[2]);
  }
  expect(rotateSashPoint([350,650,-40],0)).toEqual([350,650,-40]);
  for(const a of [-1,91,NaN,Infinity])expect(openingAngleIssues(a)).toHaveLength(1);
 });
 it('rejects a forged side-hung request before any APS submission',async()=>{
  const forged={kind:'lithic-build-request',schemaVersion:'0.1',definition,configuration:config,approvedAt:'2026-10-16T10:00:00Z'};
  expect(()=>validateRequest(JSON.stringify(forged))).toThrow('differs from');
  let calls=0;const response=await revitRoute(new Request('https://lithic.test/api/revit/jobs',{method:'POST',headers:{origin:'https://lithic.test','content-type':'application/json','oai-authenticated-user-id':'owner'},body:JSON.stringify(forged)}),{}, {bundle:new Uint8Array(),template:new Uint8Array(),bundleSha256:''},async()=>{calls++;throw new Error('Must not call APS')});
  expect(response?.status).not.toBe(200);expect(calls).toBe(0);
 });
 it('renders complete nondegenerate native meshes with the native pane thicknesses',()=>{
  for(const part of parts){
   const g=partGeometry(part);g.computeBoundingBox();
   expect(g.attributes.position.count%3).toBe(0);expect(g.attributes.position.count).toBeGreaterThan(0);
   for(const n of g.attributes.position.array)expect(Number.isFinite(n)).toBe(true);
   if(part.role==='glazing')expect(g.boundingBox!.max.z-g.boundingBox!.min.z).toBeCloseTo(.004,6);
   g.dispose();
  }
 });
});
