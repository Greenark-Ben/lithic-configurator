export const PRESETS = [[900,1200],[1200,1500],[1500,1800]] as const;
export type Configuration = { width: number; height: number; interior: 'timber'|'white'; exterior: 'graphite'|'white' };
export type Definition = { schemaVersion: '0.1'; id: string; revision: number; product: string; operation: 'fixed'; frameFace: number; frameDepth: number|null; glazingThickness: number; provenance: { frameFace:string; frameDepth:string|null; glazing:string }; allowedSizes?:number[][]; proposal?:import('./proposal').Proposal };
export type Approval = { definition: Definition; approvedAt: string };
export const SAMPLE: Definition = { schemaVersion:'0.1', id:'lithic-fixed-window-demo', revision:1, product:'Fixed-frame window', operation:'fixed', frameFace:70, frameDepth:null, glazingThickness:36, provenance:{frameFace:'Illustrative fixture, not manufacturer geometry',frameDepth:null,glazing:'Illustrative fixture, not a verified glazing specification'} };
export const INITIAL: Configuration = {width:1200,height:1500,interior:'timber',exterior:'graphite'};
export function definitionIssues(d:Definition) {
 const issues:string[]=[];
 if (d.frameDepth===null || !Number.isFinite(d.frameDepth) || d.frameDepth<70 || d.frameDepth>200) issues.push('Confirm a frame depth between 70 and 200 mm for this prototype.');
 if (!d.provenance.frameDepth) issues.push('Record the source of the confirmed frame depth.');
 if(!Number.isFinite(d.frameFace)||d.frameFace<20||d.frameFace>150||!d.provenance.frameFace?.trim())issues.push('Confirm a frame face between 20 and 150 mm with its source.');
 if(!Number.isFinite(d.glazingThickness)||d.glazingThickness<12||d.glazingThickness>80||!d.provenance.glazing?.trim()||d.frameDepth!==null&&d.glazingThickness>d.frameDepth)issues.push('Confirm a glazing thickness between 12 and 80 mm that fits the frame.');
 return issues;
}
export function configurationIssues(c:Configuration,d?:Definition) {
 return (d?.allowedSizes||PRESETS).some(([w,h])=>w===c.width&&h===c.height)&&Number.isFinite(c.width)&&Number.isFinite(c.height)&&c.width>=300&&c.height>=300&&c.width<=3000&&c.height<=3000 ? [] : [d?.allowedSizes?'Use the reviewed size. Additional sizes need a new approved proposal.':'Choose one of the three supported prototype sizes.'];
}
export type Part = { id:string; role:'timber'|'aluminium'|'glazing'; position:[number,number,number]; size:[number,number,number] };
// Millimetres throughout the definition. Preview adapter alone converts to metres.
export function calculateParts(d:Definition,c:Configuration):Part[] {
 const issues=[...definitionIssues(d),...configurationIssues(c,d)];
 if(issues.length) throw new Error(issues.join(' '));
 const w=c.width,h=c.height,f=d.frameFace,depth=d.frameDepth!;
 if(2*f>=Math.min(w,h))throw new Error('Frame face leaves no glazing opening.');
 const members = [{id:'left',p:[-w/2+f/2,h/2,0],s:[f,h,depth]},{id:'right',p:[w/2-f/2,h/2,0],s:[f,h,depth]},{id:'head',p:[0,h-f/2,0],s:[w-2*f,f,depth]},{id:'sill',p:[0,f/2,0],s:[w-2*f,f,depth]}];
 const parts:Part[]=members.map(m=>({id:`timber-${m.id}`,role:'timber',position:m.p as Part['position'],size:m.s as Part['size']}));
 for(const m of members) parts.push({id:`aluminium-${m.id}`,role:'aluminium',position:[m.p[0],m.p[1],depth/2+3],size:[m.s[0],m.s[1],6]});
 parts.push({id:'glazing',role:'glazing',position:[0,h/2,0],size:[w-2*f,h-2*f,d.glazingThickness]});
 return parts;
}
export function createBuildRequest(a:Approval,c:Configuration) {
 const parts=calculateParts(a.definition,c);
 return {kind:'lithic-build-request',schemaVersion:'0.1',definition:a.definition,approvedAt:a.approvedAt,configuration:c,geometryEngine:'fixed-window-boxes/0.1',units:'mm',parts,nativeStatus:'not-built',limitations:['Illustrative rectangular profiles; not manufacturer-approved','No connected Revit worker','No native hosting, flexing or 2D verification yet']};
}
