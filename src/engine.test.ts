import { describe,it,expect } from 'vitest';
import { SAMPLE,INITIAL,PRESETS,calculateParts,configurationIssues,definitionIssues,createBuildRequest } from './engine';
const approved={...SAMPLE,frameDepth:120,provenance:{...SAMPLE.provenance,frameDepth:'User confirmation'}};
describe('governed prototype',()=>{
 it('blocks unconfirmed depth and missing evidence',()=>{expect(definitionIssues(SAMPLE).length).toBe(2);expect(()=>calculateParts(SAMPLE,INITIAL)).toThrow();expect(definitionIssues({...approved,provenance:{...approved.provenance,frameDepth:null}})).toHaveLength(1)});
 it('rejects unsupported dimensions and nonfinite values',()=>{expect(configurationIssues({...INITIAL,width:1000})).toHaveLength(1);expect(definitionIssues({...approved,frameDepth:NaN})).not.toHaveLength(0)});
 it.each(PRESETS)('preserves outer bounds at %s by %s', (width,height)=>{const p=calculateParts(approved,{...INITIAL,width,height});expect(p).toHaveLength(9);expect(Math.min(...p.map(x=>x.position[0]-x.size[0]/2))).toBe(-width/2);expect(Math.max(...p.map(x=>x.position[0]+x.size[0]/2))).toBe(width/2);expect(Math.min(...p.map(x=>x.position[1]-x.size[1]/2))).toBe(0);expect(Math.max(...p.map(x=>x.position[1]+x.size[1]/2))).toBe(height);expect(p.find(x=>x.role==='glazing')?.size).toEqual([width-140,height-140,36]);});
 it('replays geometry without claiming native verification',()=>{const a={definition:approved,approvedAt:'2026-10-08T09:30:00Z'};expect(createBuildRequest(a,INITIAL)).toEqual(createBuildRequest(a,INITIAL));expect(createBuildRequest(a,INITIAL).nativeStatus).toBe('not-built')});
});
