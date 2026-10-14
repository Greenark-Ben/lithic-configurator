import {interpretRoute} from './interpret';
import {revitRoute,type CloudEnv} from './revit';
// @ts-expect-error Build-only private payload, never served as a browser asset.
import cloudPayload from 'virtual:lithic-cloud';
// @ts-expect-error Build-only virtual module embeds the exact Vite asset output.
import assets from 'virtual:lithic-assets';
export default {async fetch(request:Request,env:CloudEnv&{OPENAI_API_KEY?:string;OPENAI_MODEL?:string}){
 const path=new URL(request.url).pathname;
 if(path.startsWith('/api/revit/')){
  const bytes=(value:string)=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
  return revitRoute(request,env,{bundle:bytes(cloudPayload.bundle),template:bytes(cloudPayload.template),bundleSha256:cloudPayload.bundleSha256});
 }
 if(path.startsWith('/api/'))return interpretRoute(request,env);
 if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405});
 const asset=assets[path]||(path==='/'?assets['/index.html']:undefined);
 if(!asset)return new Response('Not found',{status:404});
 const data=Uint8Array.from(atob(asset.data),(c:string)=>c.charCodeAt(0));
 return new Response(request.method==='HEAD'?null:data,{headers:{'content-type':asset.type,'cache-control':path.startsWith('/assets/')?'public,max-age=31536000,immutable':'no-cache','x-content-type-options':'nosniff'}});
}};
