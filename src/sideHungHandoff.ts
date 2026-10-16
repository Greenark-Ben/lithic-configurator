import type {Approval,Configuration} from './engine';
export const SIDE_HUNG_BUILDER='lithic-window-sidehung-desktop/0.1.0';
export const SIDE_HUNG_FILES=['script.py','desktop_contract.py','fixed_contract.py','authoring.py','build_closed.py','corner_math.py','build_native.py','wrap_hosted.py','material_controls.py','export_builder.py','definition.json','source.json','hinge-reference.json','Install.ps1','bundle.yaml','README.txt'];
export function validateSideHungReport(r:any,a:Approval,c:Configuration,digest:string){
 const angle=c.openingAngleDegrees??0;
 if(r?.kind!=='lithic-sidehung-native-report'||r.schemaVersion!=='0.1'||r.builder!==SIDE_HUNG_BUILDER||r.requestSha256!==digest||r.revitVersion!=='2024'||r.geometryMode!=='fixed-size-snapshot'||r.nativeParameterFlex!==false||r.manufacturerApproved!==false||!['passed','failed'].includes(r.status))throw new Error('This side-hung report does not match the approved configuration.');
 const expected={width:c.width,height:c.height,interior:c.interior,exterior:c.exterior,openingAngleDegrees:angle};
 if(a.definition.productId!=='lithic.window.side-hung-outward'||!r.configuration||Object.keys(r.configuration).length!==5||Object.entries(expected).some(([k,v])=>r.configuration[k]!==v))throw new Error('This report uses different dimensions, finishes or opening angle.');
 if(r.status==='passed'){
  if(['headCornerCheckResolved','openingAngleControlVerified','familyPersistencePassed','wallCutPersisted','planViewsPersisted','requestedAnglePersisted','requestIdentityPersisted','activeProjectPreserved'].some(k=>r[k]!==true)||!Array.isArray(r.familyWarnings)||r.familyWarnings.length||r.familyFile!=='LITHIC-Window-SideHung-Outward-880x1180.rfa'||!/^[a-f0-9]{64}$/.test(r.familySha256))throw new Error('The side-hung pass lacks its native evidence.');
  const hosts=r.hostedCases;if(!Array.isArray(hosts)||hosts.length!==48||[100,200,300,500].some(w=>[0,50,100].some(s=>[0,15,45,90].some(a=>hosts.filter((h:any)=>h.wallMm===w&&h.setbackMm===s&&h.degrees===a&&h.passed===true&&h.geometryPassed===true&&h.openingPassed===true&&h.sillPassed===true&&h.hostPassed===true).length!==1))))throw new Error('The side-hung report lacks the hosted opening matrix.');
  const materials=r.materialCases,names=['Timber Material','Aluminium Material','Glazing Material','Glazing Spacer Material','Glazing Seal Material'],counts=[8,8,3,8,2];
  if(!Array.isArray(materials)||materials.length!==15||names.some((n,i)=>[0,45,90].some(a=>materials.filter((m:any)=>m.parameter===n&&m.degrees===a&&m.passed===true&&m.actualSolids===counts[i]&&m.affectedSolids===counts[i]).length!==1)))throw new Error('The side-hung report lacks nested material checks.');
  if(!Array.isArray(r.projectPersistenceChecks)||r.projectPersistenceChecks.length!==3||[0,45,90].some(a=>r.projectPersistenceChecks.filter((p:any)=>p.degrees===a&&p.passed===true).length!==1))throw new Error('The side-hung report lacks project persistence checks.');
 }
 return {kind:'lithic-native-report' as const,builder:r.builder,requestSha256:r.requestSha256,status:r.status as 'passed'|'failed',revitVersion:r.revitVersion,cases:[{sizeMm:[c.width,c.height] as [number,number],status:r.status as 'passed'|'failed',familyFile:r.familyFile,error:r.error}]};
}
