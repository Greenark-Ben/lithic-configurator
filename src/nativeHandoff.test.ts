import {validateSharedParameters} from './sharedParameters';
import {sharedFixture} from './sharedParameters.test-fixture';
import {describe,it,expect} from 'vitest';
import {execFileSync} from 'node:child_process';
import {createBuildRequest,INITIAL} from './engine';
import {AFKC} from './profiles';
import {requestIdentity,readNativeReport,zipFiles,NATIVE_BUILDER} from './nativeHandoff';
import {partGeometry} from './profileGeometry';
const approval={definition:AFKC,approvedAt:'2026-10-12T11:00:00Z'};
describe('native desktop boundary',()=>{
 it.each([[900,1200],[1200,1500],[1500,1800],[1275,1625],[300,300],[3000,3000]])('replays browser parts in the independent Python contract at %s × %s',async(width,height)=>{
  const config={...INITIAL,width,height},identity=await requestIdentity(approval,config);
  const check="import sys,json;sys.path.insert(0,'public/native');from contract import validate,BUILDER;payload=json.load(sys.stdin);source=json.load(open('public/native/afkc-source.json'));request,digest=validate(payload['raw'].encode('utf-8'),{'builder':BUILDER,'requestSha256':payload['sha256']},source);print(digest)";
  expect(execFileSync('python3',['-B','-X','utf8','-c',check],{input:JSON.stringify({raw:identity.text,sha256:identity.sha256}),encoding:'utf8'}).trim()).toBe(identity.sha256);
 });
 it('writes a ZIP that Python can read and verify, including UTF-8 names',()=>{
  const zip=zipFiles([{name:'request.json',data:new TextEncoder().encode('{"value":53.5}')},{name:'Räcke.txt',data:new TextEncoder().encode('åäö')}]);
  const result=execFileSync('python3',['-B','-X','utf8','-c',"import sys,io,zipfile,json;z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));assert z.testzip() is None;print(json.dumps(z.namelist(),ensure_ascii=False));assert z.read('Räcke.txt').decode()=='åäö'"],{input:zip,encoding:'utf8'});
  expect(JSON.parse(result)).toEqual(['request.json','Räcke.txt']);
 });
 it('accepts a failed desktop report for the exact request and rejects size changes',async()=>{
  const identity=await requestIdentity(approval,INITIAL),report={kind:'lithic-native-report',schemaVersion:'0.2',builder:NATIVE_BUILDER,requestSha256:identity.sha256,geometryMode:'fixed-size-snapshot',nativeParameterFlex:false,manufacturerApproved:false,revitVersion:'2026',status:'failed',cases:[[1200,1500],[900,1200],[1500,1800]].map(sizeMm=>({sizeMm,status:'failed',error:'Test report: no native runtime'}))};
  expect((await readNativeReport(report,approval,INITIAL)).status).toBe('failed');await expect(readNativeReport(report,approval,{...INITIAL,width:1300})).rejects.toThrow('does not match');
  await expect(readNativeReport({...report,cases:report.cases.map(c=>({...c,error:{message:'invalid'}}))},approval,INITIAL)).rejects.toThrow('malformed');
  await expect(readNativeReport({...report,status:'passed'},approval,INITIAL)).rejects.toThrow('summary conflicts');
  await expect(readNativeReport({...report,cases:report.cases.slice(0,1)},approval,INITIAL)).rejects.toThrow('missing required');
  await expect(readNativeReport({...report,status:'passed',cases:report.cases.map(c=>({...c,status:'passed'}))},approval,INITIAL)).rejects.toThrow('lacks its native check evidence');
 });
 it('pins selected finishes as well as geometry in the handoff identity',async()=>{
  expect((await requestIdentity(approval,INITIAL)).sha256).not.toBe((await requestIdentity(approval,{...INITIAL,exterior:'white'})).sha256);
  expect(createBuildRequest(approval,INITIAL).nativeStatus).toBe('not-built');
 });
 it('renders hollow spacers and mitred profiles with independent analytic volumes',()=>{
  const request=createBuildRequest(approval,INITIAL);
  const expected=JSON.parse(execFileSync('python3',['-B','-X','utf8','-c',"import sys,json;sys.path.insert(0,'public/native');from contract import volume_mm3;p=json.load(sys.stdin);print(json.dumps([volume_mm3(x) for x in p]))"],{input:JSON.stringify(request.parts),encoding:'utf8'}));
  request.parts.forEach((part,index)=>{
   const geometry=partGeometry(part),triangles=geometry.index?geometry.toNonIndexed():geometry,p=triangles.getAttribute('position');let volume=0;
   for(let i=0;i<p.count;i+=3){const [a,b,c]=[i,i+1,i+2].map(k=>[p.getX(k),p.getY(k),p.getZ(k)]);volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6}
   expect(Math.abs(volume*1e9-expected[index])).toBeLessThan(Math.max(1,expected[index]*.001));
   if(triangles!==geometry)triangles.dispose();geometry.dispose();
  });
 });
 it('accepts complete v0.2 evidence and rejects old or duplicated native authoring records',async()=>{
  const identity=await requestIdentity(approval,INITIAL);
  const required=['scheduleDimensionsPassed','provenancePassed','hostPassed','openingPassed','exteriorPassed','familyReopened','projectReopened','persistenceGeometryPassed','hostPersisted','openingPersisted','nativeAuthoringPassed','materialsBoundPassed','cornerChecksPassed','cavitiesEmptyPassed','planVisibilityPassed','drawingViewsPersisted','hostedGeometryStablePassed'];
  const cases=([[1200,1500],[900,1200],[1500,1800]] as [number,number][]).map(sizeMm=>{
   const ids=[...createBuildRequest(approval,{...INITIAL,width:sizeMm[0],height:sizeMm[1]}).parts.filter(p=>p.role!=='aluminium'&&p.role!=='seal').map(p=>p.id),'aluminium-head-jamb-return','aluminium-sill','seal-perimeter'];
   return {...sharedFixture(identity.sha256),sizeMm,status:'passed',...Object.fromEntries(required.map(k=>[k,true])),familyWarnings:[],projectWarnings:[],reopenedWarnings:[],familyFile:`LITHIC-AFKC-${sizeMm.join('x')}.rfa`,familySha256:'a'.repeat(64),parts:ids.map(id=>({id,passed:true,nativeType:id==='seal-perimeter'?'Sweep':id.startsWith('aluminium-')?'GeomCombination':'Extrusion'})),reopenedParts:ids.map(id=>({id,passed:true,nativeType:id==='seal-perimeter'?'Sweep':id.startsWith('aluminium-')?'GeomCombination':'Extrusion'})),hostThicknessCases:[100,200,300,500].map(wallThicknessMm=>({wallThicknessMm,passed:true,savedReopenedPassed:true,geometry:{solidCount:22,parts:ids.map(id=>({id,passed:true})),passed:true},reopenedGeometry:{solidCount:22,parts:ids.map(id=>({id,passed:true})),passed:true},openingPassed:true,reopenedOpeningPassed:true,planSymbols:Object.fromEntries([['coarse',10],['medium',14],['fine',144]].map(([lod,count])=>[lod,{curveCount:count,expectedCount:count,sha256:'b'.repeat(64),expectedSha256:'b'.repeat(64),passed:true}])),reopenedPlanSymbols:Object.fromEntries([['coarse',10],['medium',14],['fine',144]].map(([lod,count])=>[lod,{curveCount:count,expectedCount:count,sha256:'b'.repeat(64),expectedSha256:'b'.repeat(64),passed:true}]))})),materialBindings:Array.from({length:23},()=>({passed:true})),planSymbolCounts:{coarse:10,medium:14,fine:144},nativeFormCounts:{sweeps:4,solidExtrusions:19,voidExtrusions:4,freeForms:0,directShapes:0},sweepInputChecks:Array.from({length:4},()=>({nativeType:'Sweep',passed:true})),drawingEvidence:Array.from({length:9},(_,i)=>({file:`view-${i}.png`}))};
  });
  const report={kind:'lithic-native-report',schemaVersion:'0.2',builder:NATIVE_BUILDER,requestSha256:identity.sha256,geometryMode:'fixed-size-snapshot',nativeParameterFlex:false,manufacturerApproved:false,revitVersion:'2024',status:'passed',cases};
  expect((await readNativeReport(report,approval,INITIAL)).status).toBe('passed');
  await expect(readNativeReport({...report,builder:'lithic-afkc-desktop/0.1'},approval,INITIAL)).rejects.toThrow('does not match');
  const deformed=structuredClone(report);deformed.cases[0].hostThicknessCases[2].reopenedGeometry.parts[0].passed=false;await expect(readNativeReport(deformed,approval,INITIAL)).rejects.toThrow('host');
  const stretched=structuredClone(report);stretched.cases[0].hostThicknessCases[2].planSymbols.fine.passed=false;await expect(readNativeReport(stretched,approval,INITIAL)).rejects.toThrow('plan symbols');
  const duplicate=structuredClone(report);duplicate.cases[0].parts[1]=duplicate.cases[0].parts[0];await expect(readNativeReport(duplicate,approval,INITIAL)).rejects.toThrow();
  const freeform=structuredClone(report);freeform.cases[0].nativeFormCounts.freeForms=1;await expect(readNativeReport(freeform,approval,INITIAL)).rejects.toThrow('authoring');
 });
});

describe('shared parameter evidence',()=>{
 it('requires permanent GUIDs and persisted schedule values',()=>{
  const digest='f'.repeat(64),c=sharedFixture(digest);
  expect(()=>validateSharedParameters(c,digest,NATIVE_BUILDER)).not.toThrow();
  const wrong=structuredClone(c);wrong.sharedFamilyParameters[0].guid='0'.repeat(36);expect(()=>validateSharedParameters(wrong,digest,NATIVE_BUILDER)).toThrow('identities');
  const lost=structuredClone(c);lost.reopenedSharedParameters.scheduleCells.pop();expect(()=>validateSharedParameters(lost,digest,NATIVE_BUILDER)).toThrow('values');
  const stale=structuredClone(c);stale.reopenedSharedParameters.parameters.find(p=>p.name==='LITHIC Builder')!.value='old';expect(()=>validateSharedParameters(stale,digest,NATIVE_BUILDER)).toThrow('values');
  const duplicate=structuredClone(c);duplicate.sharedParameters.parameters[1]=duplicate.sharedParameters.parameters[0];expect(()=>validateSharedParameters(duplicate,digest,NATIVE_BUILDER)).toThrow('incomplete');
 });
});
