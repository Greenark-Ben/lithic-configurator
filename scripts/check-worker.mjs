import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import worker from '../dist/server/index.js';

const get=async path=>worker.fetch(new Request('https://lithic.invalid'+path),{});
const index=await get('/');assert.equal(index.status,200);
const html=await index.text();
const assets=[...html.matchAll(/(?:src|href)="(\/assets\/[^\"]+)"/g)].map(m=>m[1]);
assert.ok(assets.length>=2,'Built index must reference its JS and CSS');
for(const path of assets){
 const response=await get(path);assert.equal(response.status,200,path);
 assert.ok((await response.arrayBuffer()).byteLength>0,path);
}
for(const name of ['script.py','contract.py','authoring.py','drawings.py','afkc-source.json','Install.ps1','bundle.yaml','README.txt']){
 const response=await get('/native/'+name);assert.equal(response.status,200,name);
 assert.deepEqual(Buffer.from(await response.arrayBuffer()),readFileSync(new URL('../public/native/'+name,import.meta.url)),name);
}
console.log('Built Worker serves its JS, CSS and exact native handoff files.');
for(const name of ['script.py','desktop_contract.py','build_closed.py','build_native.py','wrap_hosted.py','material_controls.py','export_builder.py','definition.json','source.json','Install.ps1','README.txt']){
 const response=await get('/native/sidehung/'+name);assert.equal(response.status,200,'sidehung/'+name);
 assert.deepEqual(Buffer.from(await response.arrayBuffer()),readFileSync(new URL('../public/native/sidehung/'+name,import.meta.url)),name);
}
assert.equal((await get('/cloud/artifacts/window.rft')).status,404);
console.log('Built Worker serves the exact side-hung handoff and keeps licensed templates private.');
