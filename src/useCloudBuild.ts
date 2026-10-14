import {useEffect,useState,useRef} from 'react';
import {requestIdentity} from './nativeHandoff';
import type {Approval,Configuration} from './engine';
export type CloudJob={id:string;status:'preparing'|'queued'|'building'|'checking'|'ready'|'failed'|'needs-attention';sizeMm:number[];configuration:Configuration;createdAt:string;requestSha256:string;error?:string;nativeChecksPassed:boolean;visualReviewPassed:false;nativeParameterFlex:false;downloads?:{family:string;report:string;evidence:string}};
const STORAGE='lithic-cloud-job-v1';
const active=(j:CloudJob|null)=>!!j&&['preparing','queued','building','checking'].includes(j.status);
export function useCloudBuild(){
 const [available,setAvailable]=useState(false),[job,setJob]=useState<CloudJob|null>(null),[submitting,setSubmitting]=useState(false),[error,setError]=useState('');
 const mounted=useRef(true);useEffect(()=>{mounted.current=true;fetch('/api/revit/status').then(r=>r.json()).then(x=>{if(mounted.current)setAvailable(x.available===true)}).catch(()=>{});try{const id=localStorage.getItem(STORAGE);if(id&&/^[a-f0-9]{64}$/.test(id))fetch('/api/revit/jobs/'+id).then(async r=>r.ok?r.json():null).then(j=>{if(j&&mounted.current)setJob(j)}).catch(()=>{})}catch{}return()=>{mounted.current=false}},[]);
 useEffect(()=>{if(!active(job))return;let gone=false;const timer=setInterval(async()=>{try{const r=await fetch('/api/revit/jobs/'+job!.id);const body=await r.json();if(gone)return;if(!r.ok){setError(body.error||'Progress is temporarily unavailable.');if(body.job)setJob(body.job)}else{setJob(body);setError('')}}catch{if(!gone)setError('Connection interrupted. Your build has not been resubmitted.')}},10000);return()=>{gone=true;clearInterval(timer)}},[job?.id,job?.status]);
 async function start(a:Approval,c:Configuration){if(submitting||active(job))return;setSubmitting(true);setError('');let id='';try{const identity=await requestIdentity(a,c);id=identity.sha256;try{localStorage.setItem(STORAGE,id)}catch{}const r=await fetch('/api/revit/jobs',{method:'POST',headers:{'content-type':'application/json'},body:identity.text});const body=await r.json();if(body.id)setJob(body);else if(body.job)setJob(body.job);if(!r.ok)throw new Error(body.error||body.job?.error||'The cloud build could not start.');}catch(e){setError((e as Error).message||'Build submission could not be confirmed.');if(id){try{const r=await fetch('/api/revit/jobs/'+id);if(r.ok)setJob(await r.json())}catch{}}}finally{setSubmitting(false)}}
 return {available,job,error,start,busy:submitting||active(job),submitting};
}
