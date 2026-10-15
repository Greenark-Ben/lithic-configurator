import {AFKC_SOURCE} from './afkc-source';
// Require the complete persisted schedule, not a summary boolean alone.
export function validateSharedParameters(c:any,requestSha256:string,builder:string){
 const schema=AFKC_SOURCE.authoringRules.sharedParameterSchema,entries=schema.parameters;
 const matching=(actual:any[])=>Array.isArray(actual)&&actual.length===entries.length&&entries.every(e=>actual.filter(p=>p.name===e.name&&p.guid===e.guid&&p.passed===true).length===1);
 if(c.sharedParametersPassed!==true||!matching(c.sharedFamilyParameters))throw new Error('Shared family parameter identities are incomplete.');
 const provenance:Record<string,string>={'LITHIC Request SHA256':requestSha256,'LITHIC Source Drawing':'61-37-F221 rev A','LITHIC Builder':builder,'LITHIC Evidence Status':'UNAPPROVED_MANUFACTURER_SOURCE_PROTOTYPE','LITHIC Geometry Mode':'fixed-size-snapshot'};
 for(const report of [c.sharedParameters,c.reopenedSharedParameters]){
  if(report?.schema!==schema.version||report.passed!==true||!matching(report.parameters)||report.matchingRows!==5)throw new Error('Shared parameter schedule evidence is incomplete.');
  const values=entries.map(e=>report.parameters.find((p:any)=>p.guid===e.guid).value);
  if(values.some((v:any)=>typeof v!=='string'||!v)||entries.some((e,i)=>e.dataType==='text'&&values[i]!==provenance[e.name])||JSON.stringify(values)!==JSON.stringify(report.expectedValues)||!Array.isArray(report.scheduleCells)||report.scheduleCells.filter((row:any)=>JSON.stringify(row)===JSON.stringify(values)).length!==5)throw new Error('Shared parameter schedule values do not match the configuration.');
 }
 if(JSON.stringify(c.sharedParameters.expectedValues)!==JSON.stringify(c.reopenedSharedParameters.expectedValues))throw new Error('Shared parameter values changed after reopening.');
}
