// Synthetic evidence for validation tests; no native execution is claimed.
import {AFKC_SOURCE} from './afkc-source';
import {NATIVE_BUILDER} from './nativeHandoff';
export function sharedFixture(digest:string){
 const parameters:{name:string;guid:string;value:string;passed:boolean}[]=AFKC_SOURCE.authoringRules.sharedParameterSchema.parameters.map(e=>({name:e.name,guid:e.guid,value:e.dataType==='material'?'TEST material':({'LITHIC Request SHA256':digest,'LITHIC Source Drawing':'61-37-F221 rev A','LITHIC Builder':NATIVE_BUILDER,'LITHIC Evidence Status':'UNAPPROVED_MANUFACTURER_SOURCE_PROTOTYPE','LITHIC Geometry Mode':'fixed-size-snapshot'} as Record<string,string>)[e.name],passed:true}));
 const values=parameters.map(p=>p.value),proof={schema:AFKC_SOURCE.authoringRules.sharedParameterSchema.version,parameters,expectedValues:values,scheduleCells:Array.from({length:5},()=>[...values]),matchingRows:5,passed:true};
 return {sharedParametersPassed:true,sharedFamilyParameters:parameters.map(({name,guid})=>({name,guid,passed:true})),sharedParameters:structuredClone(proof),reopenedSharedParameters:structuredClone(proof)};
}
