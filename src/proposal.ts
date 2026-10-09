import { type Definition, type Configuration, INITIAL } from './engine';

export const FIELD_KEYS = ['width','height','frameFace','frameDepth','glazingThickness'] as const;
export type FieldKey = typeof FIELD_KEYS[number];
export type Evidence = { value:number|null; sourceId:string|null; evidence:string; status:'stated'|'unknown'|'conflict' };
export type Extraction = { product:string; supported:boolean; reason:string; fields:Record<FieldKey,Evidence>; questions:string[] };
export type Source = {id:string;name:string;type:string;sha256:string};
export type Proposal = Extraction & {id:string;revision:number;createdAt:string;model:string;sources:Source[];description:string};
const evidenceSchema={type:'object',additionalProperties:false,properties:{value:{type:['number','null']},sourceId:{type:['string','null']},evidence:{type:'string'},status:{type:'string',enum:['stated','unknown','conflict']}},required:['value','sourceId','evidence','status']};
export const EXTRACTION_SCHEMA={type:'object',additionalProperties:false,properties:{product:{type:'string'},supported:{type:'boolean'},reason:{type:'string'},fields:{type:'object',additionalProperties:false,properties:Object.fromEntries(FIELD_KEYS.map(k=>[k,evidenceSchema])),required:[...FIELD_KEYS]},questions:{type:'array',items:{type:'string'}}},required:['product','supported','reason','fields','questions']};

// Runtime validation remains required even when an upstream service promises a schema.
export function validateExtraction(value:unknown,sourceIds:string[]):Extraction {
 if(!value||typeof value!=='object')throw new Error('Invalid proposal.');
 const x=value as Extraction;
 if(typeof x.product!=='string'||!x.product.trim()||x.product.length>200||typeof x.supported!=='boolean'||typeof x.reason!=='string'||x.reason.length>2000||!Array.isArray(x.questions)||x.questions.length>20||x.questions.some(q=>typeof q!=='string'||q.length>2000)||!x.fields)throw new Error('Invalid proposal.');
 for(const key of FIELD_KEYS){const f=x.fields[key];if(!f||!['stated','unknown','conflict'].includes(f.status)||typeof f.evidence!=='string'||f.evidence.length>2000||(f.value!==null&&(!Number.isFinite(f.value)||f.value<=0))||(f.sourceId!==null&&!sourceIds.includes(f.sourceId)))throw new Error('Invalid proposal evidence.');if(f.status==='stated'&&(f.value===null||f.sourceId===null||!f.evidence.trim()))throw new Error('Stated dimensions require source evidence.');if(f.status!=='stated'&&f.value!==null)throw new Error('Uncertain dimensions must remain unknown.');}
 return {product:x.product,supported:x.supported,reason:x.reason,fields:Object.fromEntries(FIELD_KEYS.map(k=>[k,{...x.fields[k]}])) as Extraction['fields'],questions:[...x.questions]};
}
export function proposalIssues(p:Proposal){
 const issues:string[]=[];
 if(!p.supported)issues.push(p.reason||'This product is outside the fixed timber window engine.');
 for(const k of FIELD_KEYS){const f=p.fields[k];if(f.status!=='stated'||f.value===null||!Number.isFinite(f.value)||!f.sourceId||!f.evidence.trim())issues.push(`Confirm ${k} and its source.`);}
 const f=p.fields;
 for(const k of ['width','height'] as const)if(f[k].value!==null&&(f[k].value!<300||f[k].value!>3000))issues.push('Overall dimensions must be 300–3000 mm for this engine.');
 if(f.frameFace.value!==null&&(f.frameFace.value<20||f.frameFace.value>150))issues.push('Frame face must be 20–150 mm.');
 if(f.frameDepth.value!==null&&(f.frameDepth.value<70||f.frameDepth.value>200))issues.push('Frame depth must be 70–200 mm.');
 if(f.glazingThickness.value!==null&&(f.glazingThickness.value<12||f.glazingThickness.value>80))issues.push('Glazing thickness must be 12–80 mm.');
 if(f.frameFace.value!==null&&f.width.value!==null&&f.height.value!==null&&2*f.frameFace.value>=Math.min(f.width.value,f.height.value))issues.push('Frame face leaves no glazing opening.');
 if(f.frameDepth.value!==null&&f.glazingThickness.value!==null&&f.glazingThickness.value>f.frameDepth.value)issues.push('Glazing thickness exceeds frame depth.');
 return issues;
}
export function proposalDefinition(p:Proposal):{definition:Definition;configuration:Configuration}{
 const issues=proposalIssues(p);if(issues.length)throw new Error(issues.join(' '));
 const f=p.fields;const evidence=(k:FieldKey)=>`${f[k].sourceId}: ${f[k].evidence}`;
 return {definition:{schemaVersion:'0.1',id:p.id,revision:p.revision,product:p.product,operation:'fixed',frameFace:f.frameFace.value!,frameDepth:f.frameDepth.value!,glazingThickness:f.glazingThickness.value!,provenance:{frameFace:evidence('frameFace'),frameDepth:evidence('frameDepth'),glazing:evidence('glazingThickness')},allowedSizes:[[f.width.value!,f.height.value!]],proposal:p},configuration:{...INITIAL,width:f.width.value!,height:f.height.value!}};
}
