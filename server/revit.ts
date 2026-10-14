import {validateSharedParameters} from '../src/sharedParameters';
import {unzipSync} from 'fflate';
import {AFKC} from '../src/profiles';
import {createBuildRequest,configurationIssues,type Approval,type Configuration} from '../src/engine';
import {zipFiles,NATIVE_BUILDER} from '../src/nativeHandoff';

export type StoreObject={etag:string;body:ReadableStream;json<T>():Promise<T>;arrayBuffer():Promise<ArrayBuffer>};
export type CloudStore={get(key:string):Promise<StoreObject|null>;list(options:{prefix:string;limit:number;cursor?:string}):Promise<{objects:{key:string}[];truncated:boolean;cursor?:string}>;put(key:string,value:string|Uint8Array,options?:{onlyIf:{etagMatches?:string;etagDoesNotMatch?:string}}):Promise<{etag:string}|null>;delete(key:string):Promise<void>};
export type CloudEnv={APS_CLIENT_ID?:string;APS_CLIENT_SECRET?:string;BUCKET?:CloudStore};
export type CloudAssets={bundle:Uint8Array;template:Uint8Array;bundleSha256:string};
type State='preparing'|'queued'|'building'|'checking'|'ready'|'failed'|'needs-attention';
type Job={id:string;scope:string;status:State;sizeMm:number[];configuration:Configuration;createdAt:string;requestSha256:string;workItemId?:string;submissionAttempted?:boolean;checkingAt?:string;resultFinalized?:boolean;resultObject?:string;uploadKey?:string;bucket?:string;error?:string;familyFile?:string;familySha256?:string;resultSha256?:string};
const HOST='https://developer.api.autodesk.com',DA=HOST+'/da/us-east/v3',ADAPTER='lithic-afkc-aps-browser/0.2';
const bundleName='LithicAfkcBrowser',activityName='LithicAfkcBrowserActivity',alias='browser';
const json=(value:unknown,status=200)=>Response.json(value,{status,headers:{'cache-control':'no-store'}});
export async function sha256(bytes:Uint8Array){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new Uint8Array(bytes).buffer))].map(n=>n.toString(16).padStart(2,'0')).join('')}
const decode=(value:string)=>new TextEncoder().encode(value);
const jobKey=(scope:string,id:string)=>`revit/jobs/${scope}/${id}.json`;
const lockKey=(scope:string)=>`revit/locks/${scope}`;
const fileKey=(j:Job,name:string)=>`revit/results/${j.scope}/${j.id}/${name}`;
const publicJob=(j:Job)=>({id:j.id,status:j.status,sizeMm:j.sizeMm,configuration:j.configuration,createdAt:j.createdAt,requestSha256:j.requestSha256,error:j.error,canRecover:!!j.workItemId&&j.status!=='ready'&&j.status!=='failed',nativeChecksPassed:j.status==='ready',visualReviewPassed:false,nativeParameterFlex:false,downloads:j.status==='ready'?{family:`/api/revit/jobs/${j.id}/family`,report:`/api/revit/jobs/${j.id}/report`,evidence:`/api/revit/jobs/${j.id}/evidence`}:undefined});
const DAILY_LIMIT=10;
async function reserveSubmission(store:CloudStore){
 const key=`revit/usage/${new Date().toISOString().slice(0,10)}.json`;
 for(let attempt=0;attempt<8;attempt++){const old=await store.get(key),count=old?(await old.json<{count:number}>()).count:0;if(count>=DAILY_LIMIT)throw new Error('Today’s cloud build limit has been reached. Existing downloads remain available. The limit resets at 00:00 UTC.');if(await store.put(key,JSON.stringify({count:count+1}),{onlyIf:old?{etagMatches:old.etag}:{etagDoesNotMatch:'*'}}))return;}
 throw new Error('Cloud usage is busy. Check progress and try again shortly.');
}

export function validateRequest(text:string){
 let input:any;try{input=JSON.parse(text)}catch{throw new Error('Invalid build request.');}
 const c=input.configuration as Configuration;
 if(!c||configurationIssues(c,AFKC).length||!['timber','white'].includes(c.interior)||!['graphite','white'].includes(c.exterior))throw new Error('Choose supported AFKC dimensions and finishes.');
 if(typeof input.approvedAt!=='string'||!Number.isFinite(Date.parse(input.approvedAt)))throw new Error('Approve the AFKC definition before building.');
 const expected=createBuildRequest({definition:AFKC,approvedAt:input.approvedAt},c);
 if(JSON.stringify(input)!==JSON.stringify(expected))throw new Error('The build request differs from the reviewed AFKC definition. Refresh and approve it again.');
 return c;
}
export function validateReport(report:any,j:Pick<Job,'requestSha256'|'sizeMm'>){
 if(report?.kind!=='lithic-cloud-proof-report'||report.adapter!==ADAPTER||report.sourceBuilder!==NATIVE_BUILDER||report.revitVersion!=='2024'||report.requestSha256!==j.requestSha256||report.geometryChecksPassed!==true||report.nativeParameterFlex!==false||report.manufacturerApproved!==false||report.visualReviewPassed!==false||report.status!=='geometry-passed-awaiting-visual-review'||report.cases?.length!==1)throw new Error('The returned report does not verify this configuration.');
 const c=report.cases[0],required=['scheduleDimensionsPassed','provenancePassed','hostPassed','openingPassed','exteriorPassed','familyReopened','projectReopened','persistenceGeometryPassed','hostPersisted','openingPersisted','nativeAuthoringPassed','materialsBoundPassed','cornerChecksPassed','cavitiesEmptyPassed','planVisibilityPassed','drawingViewsPersisted','hostedGeometryStablePassed'];
 if(c.status!=='passed'||JSON.stringify(c.sizeMm)!==JSON.stringify(j.sizeMm)||required.some(k=>c[k]!==true)||['familyWarnings','projectWarnings','reopenedWarnings'].some(k=>!Array.isArray(c[k])||c[k].length))throw new Error('Native checks failed or are incomplete.');
 if(c.parts?.length!==22||c.reopenedParts?.length!==22||[...c.parts,...c.reopenedParts].some((p:any)=>p.passed!==true))throw new Error('Native geometry checks are incomplete.');
 const n=c.nativeFormCounts;if(!n||n.sweeps!==4||n.solidExtrusions!==19||n.voidExtrusions!==4||n.freeForms!==0||n.directShapes!==0||c.sweepInputChecks?.length!==4||c.sweepInputChecks.some((p:any)=>p.passed!==true||p.nativeType!=='Sweep')||c.materialBindings?.length!==23||c.materialBindings.some((p:any)=>p.passed!==true))throw new Error('Native authoring or material evidence is incomplete.');
 if(c.hostThicknessCases?.length!==4||JSON.stringify(c.hostThicknessCases.map((h:any)=>h.wallThicknessMm).sort((a:number,b:number)=>a-b))!=='[100,200,300,500]')throw new Error('Hosted-wall evidence is incomplete.');
 for(const h of c.hostThicknessCases){if(h.passed!==true||h.savedReopenedPassed!==true||h.geometry?.passed!==true||h.reopenedGeometry?.passed!==true||h.openingPassed!==true||h.reopenedOpeningPassed!==true)throw new Error('Hosted-wall checks failed.');for(const k of ['planSymbols','reopenedPlanSymbols'])for(const [lod,count] of [['coarse',10],['medium',14],['fine',144]] as const){const p=h[k]?.[lod];if(p?.passed!==true||p.curveCount!==count||p.expectedCount!==count||!/^[a-f0-9]{64}$/.test(p.sha256)||p.sha256!==p.expectedSha256)throw new Error('Plan graphics checks failed.');}}
 if(!/^LITHIC-AFKC-[0-9_]+x[0-9_]+\.rfa$/.test(c.familyFile)||!/^LITHIC-AFKC-[0-9_]+x[0-9_]+-verification\.rvt$/.test(c.projectFile)||!/^[a-f0-9]{64}$/.test(c.familySha256)||!/^[a-f0-9]{64}$/.test(c.projectSha256))throw new Error('Native file evidence is incomplete.');
 validateSharedParameters(c,j.requestSha256,NATIVE_BUILDER);
 return c;
}

class Aps {
 token='';private upstream:typeof fetch;constructor(private env:CloudEnv,upstream:typeof fetch){this.upstream=(input,init)=>upstream(input,init);}
 async authenticate(){const r=await this.upstream(HOST+'/authentication/v2/token',{method:'POST',headers:{authorization:'Basic '+btoa(this.env.APS_CLIENT_ID+':'+this.env.APS_CLIENT_SECRET),'content-type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'client_credentials',scope:'code:all bucket:create bucket:read data:read data:write data:create'}),signal:AbortSignal.timeout(30000)});if(!r.ok)throw new Error('APS connection could not authenticate.');this.token=(await r.json() as any).access_token;if(!this.token)throw new Error('APS connection returned no token.');}
 async api(path:string,method='GET',body?:unknown,allow:number[]=[]):Promise<any>{const r=await this.upstream(path.startsWith('https://')?path:DA+path,{method,headers:{authorization:'Bearer '+this.token,...(body?{'content-type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(30000)});if(allow.includes(r.status))return {allowedStatus:r.status};if(!r.ok)throw new Error('APS could not complete '+method+' '+new URL(r.url||(path.startsWith('https://')?path:DA+path)).pathname+' (HTTP '+r.status+').');return r.status===204?{}:r.json();}
 async transfer(url:string,init:RequestInit={}){const u=new URL(url);if(u.protocol!=='https:'||!u.hostname.endsWith('.amazonaws.com'))throw new Error('APS returned an unsupported transfer address.');const r=await this.upstream(url,{...init,signal:AbortSignal.timeout(60000)});if(!r.ok)throw new Error('APS file transfer failed (HTTP '+r.status+').');return r;}
 object(bucket:string,name:string){return `${HOST}/oss/v2/buckets/${bucket}/objects/${encodeURIComponent(name)}`;}
 async upload(bucket:string,name:string,data:Uint8Array){const url=this.object(bucket,name),s=await this.api(url+'/signeds3upload?minutesExpiration=60');await this.transfer(s.urls[0],{method:'PUT',body:new Uint8Array(data).buffer});await this.api(url+'/signeds3upload','POST',{uploadKey:s.uploadKey});return (await this.api(url+'/signeds3download?minutesExpiration=60')).url;}
 async version(kind:string,name:string,spec:unknown){let r=await this.api('/'+kind,'POST',{id:name,...spec as object},[409]);if(r.allowedStatus===409)r=await this.api(`/${kind}/${name}/versions`,'POST',spec);return r;}
 async alias(kind:string,name:string,version:number){const r=await this.api(`/${kind}/${name}/aliases`,'POST',{id:alias,version},[409]);if(r.allowedStatus===409)await this.api(`/${kind}/${name}/aliases/${alias}`,'PATCH',{version});}
}

async function prepareRuntime(api:Aps,env:CloudEnv,assets:CloudAssets){
 const store=env.BUCKET!,fingerprint=await sha256(decode(env.APS_CLIENT_ID!)),key=`revit/runtime/${fingerprint}/${assets.bundleSha256}.json`,saved=await store.get(key);
 if(saved)return saved.json<{activityId:string;bucket:string}>();
 const b=await api.version('appbundles',bundleName,{engine:'Autodesk.Revit+2024',description:'LITHIC AFKC browser generation'}),form=new FormData();for(const [k,v] of Object.entries(b.uploadParameters.formData))form.append(k,String(v));form.append('file',new Blob([new Uint8Array(assets.bundle).buffer],{type:'application/zip'}),'appbundle.zip');await api.transfer(b.uploadParameters.endpointURL,{method:'POST',body:form});await api.alias('appbundles',bundleName,b.version);
 const owner=env.APS_CLIENT_ID!,a=await api.version('activities',activityName,{engine:'Autodesk.Revit+2024',appbundles:[`${owner}.${bundleName}+${alias}`],commandLine:[`"$(engine.path)\\revitcoreconsole.exe" /al "$(appbundles[${bundleName}].path)"`],parameters:{input:{verb:'get',required:true,zip:true,localName:'input'},result:{verb:'put',required:true,localName:'results.zip'}},description:'Fixed-size AFKC snapshots; native checks required, visual review pending'});await api.alias('activities',activityName,a.version);
 const bucket='lithic-afkc-browser-'+fingerprint.slice(0,20);await api.api(HOST+'/oss/v2/buckets','POST',{bucketKey:bucket,policyKey:'transient'},[409]);const runtime={activityId:`${owner}.${activityName}+${alias}`,bucket};await store.put(key,JSON.stringify(runtime));return runtime;
}
async function releaseLock(store:CloudStore,j:Job){const l=await store.get(lockKey(j.scope));if(l&&(await l.json<{id:string}>()).id===j.id)await store.delete(lockKey(j.scope));}
async function persist(store:CloudStore,j:Job){await store.put(jobKey(j.scope,j.id),JSON.stringify(j));}
async function inspectResult(api:Aps,store:CloudStore,j:Job){
 const base=api.object(j.bucket!,j.resultObject!);let finalizationError:unknown;
 if(!j.resultFinalized){try{await api.api(base+'/signeds3upload','POST',{uploadKey:j.uploadKey});j.resultFinalized=true;await persist(store,j)}catch(e){finalizationError=e}}
 // Completion can succeed before its response or storage write is lost. In that
 // case read the existing object; native report and hashes still gate release.
 let url:string;try{url=(await api.api(base+'/signeds3download?minutesExpiration=10')).url}catch(e){throw finalizationError||e}const r=await api.transfer(url);
 if(!j.resultFinalized){j.resultFinalized=true;await persist(store,j)}
 const bytes=new Uint8Array(await r.arrayBuffer());if(bytes.byteLength>20*1024*1024)throw new Error('Native result exceeds the supported download limit.');let total=0,entries=0;
 const files=unzipSync(bytes,{filter:file=>{entries++;total+=file.originalSize;if(entries>12||total>64*1024*1024||file.originalSize>32*1024*1024||file.name.includes('..')||/[\\/]/.test(file.name))throw new Error('Unexpected native result archive.');return true;}});
 if(!files['cloud-proof-report.json'])throw new Error('Native result lacks its report.');const report=JSON.parse(new TextDecoder().decode(files['cloud-proof-report.json'])),c=validateReport(report,j);
 if(!files[c.familyFile]||!files[c.projectFile]||await sha256(files[c.familyFile])!==c.familySha256||await sha256(files[c.projectFile])!==c.projectSha256)throw new Error('Native file hashes do not match the checked report.');
 await store.put(fileKey(j,'family'),files[c.familyFile]);await store.put(fileKey(j,'report'),files['cloud-proof-report.json']);await store.put(fileKey(j,'evidence'),bytes);
 j.familyFile=c.familyFile;j.familySha256=c.familySha256;j.resultSha256=await sha256(bytes);j.status='ready';delete j.error;delete j.uploadKey;await persist(store,j);await releaseLock(store,j);
}

export async function revitRoute(request:Request,env:CloudEnv,assets:CloudAssets,upstream:typeof fetch=fetch){
 const url=new URL(request.url),path=url.pathname,store=env.BUCKET;
 if(path==='/api/revit/status'&&request.method==='GET')return json({available:!!(env.APS_CLIENT_ID&&env.APS_CLIENT_SECRET&&store&&assets.bundle.length&&assets.template.length),engine:'Revit 2024',geometryMode:'fixed-size-snapshot'});
 // The published Site remains owner-private behind Sites dispatch. Scope every record
 // to the trusted visitor identity; service-access QA has a separate namespace.
 if(request.headers.get('sec-fetch-site')==='cross-site'||(request.method==='POST'&&request.headers.get('origin')!==url.origin))return json({error:'Use LITHIC to start a build.'},403);
 if(!env.APS_CLIENT_ID||!env.APS_CLIENT_SECRET||!store||!assets.bundle.length||!assets.template.length)return json({error:'Cloud generation is awaiting its secure connection.'},503);
 const scope=(await sha256(decode(request.headers.get('oai-authenticated-user-id')||'owner-private-service'))).slice(0,24);
 if(path==='/api/revit/jobs'&&request.method==='GET'){
  const page=await store.list({prefix:`revit/jobs/${scope}/`,limit:100,cursor:url.searchParams.get('cursor')||undefined});
  const jobs=await Promise.all(page.objects.map(async x=>{const item=await store.get(x.key);return item?publicJob(await item.json<Job>()):null}));
  const usage=await store.get(`revit/usage/${new Date().toISOString().slice(0,10)}.json`),used=usage?(await usage.json<{count:number}>()).count:0;
  return json({jobs:jobs.filter(Boolean).sort((a,b)=>b!.createdAt.localeCompare(a!.createdAt)),cursor:page.truncated?page.cursor:undefined,usage:{limit:DAILY_LIMIT,used,remaining:Math.max(0,DAILY_LIMIT-used),resetsAt:new Date(new Date().setUTCHours(24,0,0,0)).toISOString()}});
 }
 if(path==='/api/revit/jobs'&&request.method==='POST'){
  if(!request.headers.get('content-type')?.includes('application/json'))return json({error:'Use a JSON build request.'},400);
  const reader=request.body?.getReader();if(!reader)return json({error:'Missing build request.'},400);let length=0;const chunks:Uint8Array[]=[];while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>150000){await reader.cancel();return json({error:'Build request is too large.'},413)}chunks.push(value)}const raw=new Uint8Array(length);let pos=0;for(const c of chunks){raw.set(c,pos);pos+=c.length}const text=new TextDecoder().decode(raw);
  let config:Configuration;try{config=validateRequest(text)}catch(e){return json({error:(e as Error).message},400)}
  const id=await sha256(raw),previous=await store.get(jobKey(scope,id));if(previous){const old=await previous.json<Job>();if(old.status==='failed'&&!old.submissionAttempted)await store.put(`revit/history/${scope}/${id}/${Date.now()}.json`,JSON.stringify(old));else return json(publicJob(old));}
  const j:Job={id,scope,status:'preparing',sizeMm:[config.width,config.height],configuration:config,createdAt:new Date().toISOString(),requestSha256:id};
  const locked=await store.put(lockKey(scope),JSON.stringify({id,createdAt:j.createdAt}),{onlyIf:{etagDoesNotMatch:'*'}});if(!locked){const l=await store.get(lockKey(scope)),existing=l?await store.get(jobKey(scope,(await l.json<{id:string}>()).id)):null;return existing?json({error:'A build is already active. Check its progress before starting another.',job:publicJob(await existing.json<Job>())},409):json({error:'A build is being prepared. Retry the status check shortly.'},409)}
  await persist(store,j);
  try{
   const api=new Aps(env,upstream);await api.authenticate();const runtime=await prepareRuntime(api,env,assets);
   const manifest=decode(JSON.stringify({builder:NATIVE_BUILDER,requestSha256:id,geometryMode:'fixed-size-snapshot',nativeParameterFlex:false}));const input=zipFiles([{name:'request.json',data:raw},{name:'manifest.json',data:manifest},{name:'window.rft',data:assets.template}]);
   const inputUrl=await api.upload(runtime.bucket,`input-${scope}-${id}.zip`,input),resultObject=`result-${scope}-${id}.zip`,upload=await api.api(api.object(runtime.bucket,resultObject)+'/signeds3upload?minutesExpiration=60');j.bucket=runtime.bucket;j.resultObject=resultObject;j.uploadKey=upload.uploadKey;await reserveSubmission(store);j.submissionAttempted=true;await persist(store,j);
   const work=await api.api('/workitems','POST',{activityId:runtime.activityId,arguments:{input:{url:inputUrl,verb:'get'},result:{url:upload.urls[0],verb:'put'}}});if(!work.id)throw new Error('APS did not return a build identifier.');j.workItemId=work.id;j.status='queued';await persist(store,j);return json(publicJob(j),202);
  }catch(e){j.status=j.submissionAttempted?'needs-attention':'failed';j.error=j.submissionAttempted?'Build submission could not be confirmed. Do not start it again; retain this build for support.':(e as Error).message;await persist(store,j);if(!j.submissionAttempted)await releaseLock(store,j);return json(publicJob(j),j.submissionAttempted?202:502);}
 }
 const match=path.match(/^\/api\/revit\/jobs\/([a-f0-9]{64})(?:\/(family|report|evidence|recover))?$/),recover=match?.[2]==='recover';if(!match||request.method!==(recover?'POST':'GET'))return json({error:'Not found.'},404);
 const object=await store.get(jobKey(scope,match[1]));if(!object)return json({error:'Build not found.'},404);const j=await object.json<Job>();
 if(match[2]&&!recover){if(j.status!=='ready')return json({error:'The checked family is not ready.'},409);const file=await store.get(fileKey(j,match[2]));if(!file)return json({error:'The build file is unavailable.'},404);const name=match[2]==='family'?j.familyFile:match[2]==='report'?'LITHIC-cloud-report.json':'LITHIC-native-evidence.zip';return new Response(file.body,{headers:{'content-type':match[2]==='report'?'application/json':match[2]==='evidence'?'application/zip':'application/octet-stream','content-disposition':`attachment; filename="${name}"`,'cache-control':'private,no-store','x-content-type-options':'nosniff'}});}
 if(recover&&!j.workItemId)return json({error:'This submission has no confirmed APS identifier. Retain its build ID for support; it cannot be safely resubmitted.',job:publicJob(j)},409);
 if(j.status==='preparing'&&!j.workItemId&&Date.now()-Date.parse(j.createdAt)>120000)return json({...publicJob(j),status:'needs-attention',error:'Build preparation has not been confirmed. Do not resubmit; retain this build for support.'});
 if(j.workItemId&&(['queued','building'].includes(j.status)||(recover&&['needs-attention','checking'].includes(j.status)))){
  if(j.status==='checking'&&Date.now()-Date.parse(j.checkingAt||j.createdAt)<120000)return json(publicJob(j));
  try{const api=new Aps(env,upstream);await api.authenticate();const state=await api.api('/workitems/'+j.workItemId);if(['pending','inprogress'].includes(state.status)){j.status=state.status==='pending'?'queued':'building';const updated=await store.put(jobKey(scope,j.id),JSON.stringify(j),{onlyIf:{etagMatches:object.etag}});if(!updated){const fresh=await store.get(jobKey(scope,j.id));return json(publicJob(await fresh!.json<Job>()));}}else if(state.status==='success'){
    j.status='checking';j.checkingAt=new Date().toISOString();const claimed=await store.put(jobKey(scope,j.id),JSON.stringify(j),{onlyIf:{etagMatches:object.etag}});if(!claimed){const fresh=await store.get(jobKey(scope,j.id));return json(publicJob(await fresh!.json<Job>()));}
    try{await inspectResult(api,store,j)}catch(e){j.status='needs-attention';j.error='The cloud build finished, but its native results could not be verified. '+(e as Error).message;await persist(store,j);}
   }else{j.status='failed';j.error='Revit could not complete this build ('+String(state.status).replace(/[^a-zA-Z]/g,'')+').';const updated=await store.put(jobKey(scope,j.id),JSON.stringify(j),{onlyIf:{etagMatches:object.etag}});if(updated)await releaseLock(store,j);else{const fresh=await store.get(jobKey(scope,j.id));return json(publicJob(await fresh!.json<Job>()));}}}
  catch{return json({error:'Build progress is temporarily unavailable. Your build has not been resubmitted.',job:publicJob(j)},503)}
 }
 return json(publicJob(j));
}
