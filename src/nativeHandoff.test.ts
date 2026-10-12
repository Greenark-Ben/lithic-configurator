import {describe,it,expect} from 'vitest';
import {execFileSync} from 'node:child_process';
import {createBuildRequest,INITIAL} from './engine';
import {AFKC} from './profiles';
import {requestIdentity,readNativeReport,zipFiles,NATIVE_BUILDER} from './nativeHandoff';
const approval={definition:AFKC,approvedAt:'2026-10-12T11:00:00Z'};
describe('native desktop boundary',()=>{
 it.each([[900,1200],[1200,1500],[1500,1800],[1275,1625],[300,300],[3000,3000]])('replays browser parts in the independent Python contract at %s × %s',async(width,height)=>{
  const config={...INITIAL,width,height},identity=await requestIdentity(approval,config);
  const check="import sys,json;sys.path.insert(0,'public/native');from contract import validate,BUILDER;payload=json.load(sys.stdin);source=json.load(open('public/native/afkc-source.json'));request,digest=validate(payload['raw'].encode('utf-8'),{'builder':BUILDER,'requestSha256':payload['sha256']},source);print(digest)";
  expect(execFileSync('python3',['-B','-c',check],{input:JSON.stringify({raw:identity.text,sha256:identity.sha256}),encoding:'utf8'}).trim()).toBe(identity.sha256);
 });
 it('writes a ZIP that Python can read and verify, including UTF-8 names',()=>{
  const zip=zipFiles([{name:'request.json',data:new TextEncoder().encode('{"value":53.5}')},{name:'Räcke.txt',data:new TextEncoder().encode('åäö')}]);
  const result=execFileSync('python3',['-B','-c',"import sys,io,zipfile,json;z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));assert z.testzip() is None;print(json.dumps(z.namelist(),ensure_ascii=False));assert z.read('Räcke.txt').decode()=='åäö'"],{input:zip,encoding:'utf8'});
  expect(JSON.parse(result)).toEqual(['request.json','Räcke.txt']);
 });
 it('accepts a failed desktop report for the exact request and rejects size changes',async()=>{
  const identity=await requestIdentity(approval,INITIAL),report={kind:'lithic-native-report',schemaVersion:'0.1',builder:NATIVE_BUILDER,requestSha256:identity.sha256,geometryMode:'fixed-size-snapshot',nativeParameterFlex:false,manufacturerApproved:false,revitVersion:'2026',status:'failed',cases:[[1200,1500],[900,1200],[1500,1800]].map(sizeMm=>({sizeMm,status:'failed',error:'Test report: no native runtime'}))};
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
});
