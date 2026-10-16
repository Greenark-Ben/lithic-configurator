import {sharedFixture} from '../src/sharedParameters.test-fixture';
import {NATIVE_BUILDER} from '../src/nativeHandoff';
import {describe,it,expect,vi} from 'vitest';
import {revitRoute,validateRequest,validateReport,sha256,type CloudStore,type CloudEnv} from './revit';
import {AFKC} from '../src/profiles';
import {createBuildRequest,INITIAL} from '../src/engine';
import {zipFiles} from '../src/nativeHandoff';
import evidence from './fixtures/afkc-cloud-report.json';

class MemoryStore implements CloudStore{
 data=new Map<string,{bytes:Uint8Array;etag:string}>();counter=0;
 async get(key:string){const item=this.data.get(key);if(!item)return null;return {etag:item.etag,body:new Blob([new Uint8Array(item.bytes).buffer]).stream(),json:async<T>()=>JSON.parse(new TextDecoder().decode(item.bytes)) as T,arrayBuffer:async()=>new Uint8Array(item.bytes).buffer};}
 async put(key:string,value:string|Uint8Array,options?:{onlyIf:{etagMatches?:string;etagDoesNotMatch?:string}}){const old=this.data.get(key),condition=options?.onlyIf;if(condition?.etagDoesNotMatch==='*'&&old||condition?.etagMatches&&condition.etagMatches!==old?.etag)return null;const etag=String(++this.counter);this.data.set(key,{bytes:typeof value==='string'?new TextEncoder().encode(value):value,etag});return {etag};}
 async delete(key:string){this.data.delete(key);}
 async list({prefix,limit,cursor}:{prefix:string;limit:number;cursor?:string}){const keys=[...this.data.keys()].filter(k=>k.startsWith(prefix)).sort(),start=Number(cursor||0),page=keys.slice(start,start+limit);return {objects:page.map(key=>({key})),truncated:start+limit<keys.length,cursor:start+limit<keys.length?String(start+limit):undefined};}
}
const approval={definition:AFKC,approvedAt:'2026-10-14T10:00:00.000Z'};
const requestText=JSON.stringify(createBuildRequest(approval,INITIAL),null,2);
const post=()=>new Request('https://lithic.test/api/revit/jobs',{method:'POST',headers:{origin:'https://lithic.test','content-type':'application/json','oai-authenticated-user-id':'owner'},body:requestText});
const get=(id:string,suffix='',user='owner')=>new Request(`https://lithic.test/api/revit/jobs/${id}${suffix}`,{headers:{'oai-authenticated-user-id':user}});
const assets={bundle:new Uint8Array([1,2,3]),template:new Uint8Array([4,5]),bundleSha256:'fixture'};
async function fixture(change?:(r:any)=>void){
 const report:any=structuredClone(evidence),id=await sha256(new TextEncoder().encode(requestText));report.adapter='lithic-window-fixed-aps-browser/0.3.0';report.requestSha256=id;report.sourceBuilder=NATIVE_BUILDER;Object.assign(report.cases[0],sharedFixture(id));report.cases[0].familyFile=report.cases[0].familyFile.replace('LITHIC-AFKC-','LITHIC-Window-Fixed-');report.cases[0].projectFile=report.cases[0].projectFile.replace('LITHIC-AFKC-','LITHIC-Window-Fixed-');
 const family=new TextEncoder().encode('TEST ONLY RFA BYTES'),project=new TextEncoder().encode('TEST ONLY RVT BYTES');report.cases[0].familySha256=await sha256(family);report.cases[0].projectSha256=await sha256(project);change?.(report);
 const zip=zipFiles([{name:'cloud-proof-report.json',data:new TextEncoder().encode(JSON.stringify(report))},{name:report.cases[0].familyFile,data:family},{name:report.cases[0].projectFile,data:project}]);
 let phase='pending',workItems=0;
 const upstream=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{const url=new URL(String(input)),p=url.pathname,method=init?.method||'GET';if(url.hostname.endsWith('.amazonaws.com')){expect(new Headers(init?.headers).has('authorization')).toBe(false);return new Response(method==='GET'?new Uint8Array(zip).buffer:'ok');}
  if(p.endsWith('/token')){const scopes=(init?.body as URLSearchParams).get('scope');expect(scopes).not.toContain('bucket:write');return Response.json({access_token:'fixture-token'});}
  if(p.endsWith('/appbundles'))return Response.json({version:1,uploadParameters:{endpointURL:'https://fixture.s3.amazonaws.com/upload',formData:{key:'test'}}});
  if(p.endsWith('/aliases')||p.endsWith('/activities')||p.endsWith('/buckets'))return Response.json({version:1});
  if(p.endsWith('/signeds3upload'))return Response.json(method==='POST'?{}:{uploadKey:'private-upload-key',urls:['https://fixture.s3.amazonaws.com/transfer']});
  if(p.endsWith('/signeds3download'))return Response.json({url:'https://fixture.s3.amazonaws.com/transfer'});
  if(p.endsWith('/workitems')&&method==='POST'){workItems++;return Response.json({id:'fixture-job',status:'pending'});}
  if(p.endsWith('/workitems/fixture-job'))return Response.json({status:phase});
  throw new Error('Unexpected fixture request: '+p);
 }) as unknown as typeof fetch;
 const store=new MemoryStore(),env:CloudEnv={APS_CLIENT_ID:'private-client',APS_CLIENT_SECRET:'private-secret',BUCKET:store};
 return {env,upstream,id,report,phase:(value:string)=>phase=value,workItems:()=>workItems};
}
describe('APS browser generation',()=>{
 it('reserves the last daily allowance atomically across separate visitor locks',async()=>{const f=await fixture();const key=`revit/usage/${new Date().toISOString().slice(0,10)}.json`;await f.env.BUCKET!.put(key,JSON.stringify({count:9}));const other=post();other.headers.set('oai-authenticated-user-id','second-visitor');await Promise.all([revitRoute(post(),f.env,assets,f.upstream),revitRoute(other,f.env,assets,f.upstream)]);expect(f.workItems()).toBe(1);expect(await(await f.env.BUCKET!.get(key))!.json()).toEqual({count:10})});
 it('lists only the current owner’s builds and keeps prior downloads available',async()=>{const f=await fixture();await revitRoute(post(),f.env,assets,f.upstream);f.phase('success');await revitRoute(get(f.id),f.env,assets,f.upstream);const history=new Request('https://lithic.test/api/revit/jobs',{headers:{'oai-authenticated-user-id':'owner'}});const body=await(await revitRoute(history,f.env,assets,f.upstream)).json() as any;expect(body.jobs).toHaveLength(1);expect(body.jobs[0]).toMatchObject({id:f.id,status:'ready'});expect(body.usage).toMatchObject({limit:10,used:1,remaining:9});expect(JSON.stringify(body)).not.toMatch(/private-secret|fixture-token|private-upload-key|amazonaws/);expect((await(await revitRoute(new Request('https://lithic.test/api/revit/jobs',{headers:{'oai-authenticated-user-id':'someone-else'}}),f.env,assets,f.upstream)).json() as any).jobs).toEqual([]);expect(f.workItems()).toBe(1)});
 it('enforces a shared UTC daily submission cap without charging for cached downloads',async()=>{const f=await fixture();await revitRoute(post(),f.env,assets,f.upstream);f.phase('success');await revitRoute(get(f.id),f.env,assets,f.upstream);await f.env.BUCKET!.put(`revit/usage/${new Date().toISOString().slice(0,10)}.json`,JSON.stringify({count:10}));const another=post();another.headers.set('oai-authenticated-user-id','another-owner');expect(await(await revitRoute(another,f.env,assets,f.upstream)).json()).toMatchObject({status:'failed',error:expect.stringContaining('limit')});expect(f.workItems()).toBe(1);expect((await revitRoute(get(f.id,'/family'),f.env,assets,f.upstream)).status).toBe(200);await revitRoute(post(),f.env,assets,f.upstream);expect(f.workItems()).toBe(1)});
 it('recovers completed results after a transient transfer failure without resubmission',async()=>{const f=await fixture();await revitRoute(post(),f.env,assets,f.upstream);f.phase('success');let broken=true;const upstream=(async(input:any,init:any)=>{if(String(input).includes('.amazonaws.com')&&(!init?.method||init.method==='GET')&&broken)throw new Error('Temporary transfer failure');return f.upstream(input,init)}) as typeof fetch;expect(await(await revitRoute(get(f.id),f.env,assets,upstream)).json()).toMatchObject({status:'needs-attention',canRecover:true});broken=false;const r=get(f.id,'/recover');r.headers.set('origin','https://lithic.test');const recover=new Request(r,{method:'POST'});expect(await(await revitRoute(recover,f.env,assets,upstream)).json()).toMatchObject({status:'ready',nativeChecksPassed:true});expect(f.workItems()).toBe(1);expect((await revitRoute(get(f.id,'/family'),f.env,assets,upstream)).status).toBe(200)});
 it('cannot recover an uncertain submission by launching another work item',async()=>{const f=await fixture();const upstream=(async(input:any,init:any)=>{if(String(input).endsWith('/workitems')&&init?.method==='POST')throw new Error('Lost response');return f.upstream(input,init)}) as typeof fetch;await revitRoute(post(),f.env,assets,upstream);const r=new Request(get(f.id,'/recover'),{method:'POST',headers:{origin:'https://lithic.test','oai-authenticated-user-id':'owner'}});expect((await revitRoute(r,f.env,assets,upstream)).status).toBe(409);expect(f.workItems()).toBe(0)});
 it('fails closed when secrets/storage are absent; rejects cross-origin writes',async()=>{const f=await fixture();expect((await revitRoute(new Request('https://lithic.test/api/revit/status'),{},assets)).status).toBe(200);expect(await(await revitRoute(new Request('https://lithic.test/api/revit/status'),{},assets)).json()).toMatchObject({available:false});const foreign=post();foreign.headers.set('origin','https://evil.test');expect((await revitRoute(foreign,f.env,assets,f.upstream)).status).toBe(403);expect(f.workItems()).toBe(0)});
 it('rejects changed source geometry and unsupported finishes',()=>{expect(validateRequest(requestText)).toEqual(INITIAL);for(const change of [(r:any)=>r.parts[0].size[0]++,(r:any)=>r.definition.profile.source.revision='changed',(r:any)=>r.configuration.interior='plastic']){const r=JSON.parse(requestText);change(r);expect(()=>validateRequest(JSON.stringify(r))).toThrow()}});
 it('submits only once, persists status, verifies native results and proxies downloads',async()=>{const f=await fixture();const first=await revitRoute(post(),f.env,assets,f.upstream);expect(first.status).toBe(202);expect(await first.json()).toMatchObject({id:f.id,status:'queued'});await revitRoute(post(),f.env,assets,f.upstream);expect(f.workItems()).toBe(1);f.phase('inprogress');expect(await(await revitRoute(get(f.id),f.env,assets,f.upstream)).json()).toMatchObject({status:'building'});f.phase('success');const result=await(await revitRoute(get(f.id),f.env,assets,f.upstream)).json() as any;expect(result).toMatchObject({status:'ready',nativeChecksPassed:true,visualReviewPassed:false,nativeParameterFlex:false});expect(JSON.stringify(result)).not.toMatch(/private-secret|fixture-token|private-upload-key|amazonaws/);const file=await revitRoute(get(f.id,'/family'),f.env,assets,f.upstream);expect(file.status).toBe(200);expect(file.headers.get('content-disposition')).toContain('.rfa');expect(await file.text()).toBe('TEST ONLY RFA BYTES');expect((await revitRoute(get(f.id,'','another-user'),f.env,assets,f.upstream)).status).toBe(404)});
 it('uses a conditional lock to prevent concurrent paid submissions',async()=>{const f=await fixture();await Promise.all([revitRoute(post(),f.env,assets,f.upstream),revitRoute(post(),f.env,assets,f.upstream)]);expect(f.workItems()).toBe(1)});
 it('does not let a delayed progress response overwrite a verified result',async()=>{const f=await fixture();await revitRoute(post(),f.env,assets,f.upstream);let release!:(r:Response)=>void,started!:()=>void;const waiting=new Promise<void>(r=>started=r);let polls=0;const upstream=(async(input:any,init:any)=>{if(String(input).endsWith('/workitems/fixture-job')){polls++;if(polls===1){started();return new Promise<Response>(r=>release=r)}return Response.json({status:'success'})}return f.upstream(input,init)}) as typeof fetch;const delayed=revitRoute(get(f.id),f.env,assets,upstream);await waiting;expect(await(await revitRoute(get(f.id),f.env,assets,upstream)).json()).toMatchObject({status:'ready'});release(Response.json({status:'inprogress'}));expect(await(await delayed).json()).toMatchObject({status:'ready'});});
 it('blocks download when a native host check or file hash fails',async()=>{for(const change of [(r:any)=>r.cases[0].hostThicknessCases[2].reopenedPlanSymbols.fine.passed=false,(r:any)=>r.cases[0].familySha256='0'.repeat(64)]){const f=await fixture(change);await revitRoute(post(),f.env,assets,f.upstream);f.phase('success');expect(await(await revitRoute(get(f.id),f.env,assets,f.upstream)).json()).toMatchObject({status:'needs-attention',nativeChecksPassed:false});expect((await revitRoute(get(f.id,'/family'),f.env,assets,f.upstream)).status).toBe(409)}});
 it('does not retry an uncertain work-item submission',async()=>{const f=await fixture(),normal=f.upstream;const upstream=vi.fn(async(input:any,init:any)=>{if(String(input).endsWith('/workitems')&&init?.method==='POST')throw new Error('Network lost after send');return normal(input,init)}) as unknown as typeof fetch;const response=await revitRoute(post(),f.env,assets,upstream);expect(await response.json()).toMatchObject({status:'needs-attention'});await revitRoute(post(),f.env,assets,upstream);expect((upstream as any).mock.calls.filter(([u]:any)=>String(u).endsWith('/workitems')).length).toBe(1)});
 it('calls fetch as a standalone function and permits an explicit retry before submission',async()=>{const f=await fixture();let reject=true;const upstream=(function(this:unknown,input:any,init:any){expect(this).toBeUndefined();if(String(input).endsWith('/token')&&reject)return Promise.resolve(new Response('',{status:401}));return f.upstream(input,init)}) as typeof fetch;expect(await(await revitRoute(post(),f.env,assets,upstream)).json()).toMatchObject({status:'failed'});expect(f.workItems()).toBe(0);reject=false;expect(await(await revitRoute(post(),f.env,assets,upstream)).json()).toMatchObject({status:'queued'});expect(f.workItems()).toBe(1);});
 it('rejects incomplete reports and old adapters',async()=>{const f=await fixture();expect(()=>validateReport(f.report,{requestSha256:f.id,sizeMm:[1200,1500]})).not.toThrow();for(const change of [(r:any)=>r.adapter='lithic-afkc-aps-proof/0.1',(r:any)=>r.cases[0].nativeFormCounts.freeForms=1,(r:any)=>r.cases[0].reopenedWarnings=['warning']]){const r=structuredClone(f.report);change(r);expect(()=>validateReport(r,{requestSha256:f.id,sizeMm:[1200,1500]})).toThrow()}});
});

describe('version-pinned naming migration',()=>{
 it('keeps authentic legacy evidence valid only for its original contract',()=>{
  const old=structuredClone(evidence);
  const job={requestSha256:old.requestSha256,sizeMm:old.cases[0].sizeMm,builderVersion:'lithic-afkc-desktop/0.2.2'};
  expect(validateReport(old,job).familyFile).toContain('LITHIC-AFKC-');
  expect(()=>validateReport(old,{...job,builderVersion:NATIVE_BUILDER})).toThrow('does not verify');
  expect(()=>validateReport(old,{...job,builderVersion:'unknown'})).toThrow('Unsupported build contract');
 });
 it('rejects supplier-named output from a new-contract job',async()=>{
  const f=await fixture();f.report.cases[0].familyFile='LITHIC-AFKC-1200x1500.rfa';
  expect(()=>validateReport(f.report,{requestSha256:f.id,sizeMm:[1200,1500],builderVersion:NATIVE_BUILDER})).toThrow('Native file evidence');
 });
 it('rejects legacy requests instead of silently relabelling their approval',()=>{
  const old=JSON.parse(requestText);old.definition.id='elitfonster-afkc-profile-proof';
  expect(()=>validateRequest(JSON.stringify(old))).toThrow('differs from');
 });
});

it('finishes a pre-migration pending cloud job without a new submission',async()=>{
 const legacy='lithic-afkc-desktop/0.2.2';
 const f=await fixture(r=>{
  const replace=(v:any):any=>typeof v==='string'?v.replaceAll(NATIVE_BUILDER,legacy).replaceAll('lithic-window-fixed-aps-browser/0.3.0','lithic-afkc-aps-browser/0.2').replaceAll('LITHIC-Window-Fixed-','LITHIC-AFKC-'):Array.isArray(v)?v.map(replace):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).map(([k,x])=>[k,replace(x)])):v;
  Object.assign(r,replace(r));
 });
 expect((await revitRoute(post(),f.env,assets,f.upstream)).status).toBe(202);
 const scope=(await sha256(new TextEncoder().encode('owner'))).slice(0,24),key=`revit/jobs/${scope}/${f.id}.json`;
 const old=await (await f.env.BUCKET!.get(key))!.json<any>();delete old.builderVersion;await f.env.BUCKET!.put(key,JSON.stringify(old));
 f.phase('success');const result=await revitRoute(get(f.id),f.env,assets,f.upstream);expect((await result.json() as any).status).toBe('ready');
 const download=await revitRoute(get(f.id,'/family'),f.env,assets,f.upstream);expect(download.headers.get('content-disposition')).toContain('LITHIC-AFKC-');expect(f.workItems()).toBe(1);
});
