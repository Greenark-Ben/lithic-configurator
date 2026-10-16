import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildSync} from 'esbuild';
import {runInNewContext} from 'node:vm';
const root=resolve(fileURLToPath(new URL('..',import.meta.url))),out=join(root,'public/native/sidehung');mkdirSync(out,{recursive:true});
const compiled=buildSync({stdin:{contents:"export {SIDE_HUNG_DEFINITION as default} from './src/sideHung';",resolveDir:root,loader:'ts'},bundle:true,platform:'node',format:'cjs',write:false});
const module={exports:{}};runInNewContext(compiled.outputFiles[0].text,{module,exports:module.exports});
writeFileSync(join(out,'definition.json'),JSON.stringify(module.exports.default,null,2)+'\n');
for(const [src,dst] of [
 ['native/afsc/build_closed.py','build_closed.py'],['native/afsc/corner_math.py','corner_math.py'],['native/afsc/hinge-reference.json','hinge-reference.json'],
 ['native/afsc-opening/source-study.json','source.json'],['native/afsc-opening/build_native.py','build_native.py'],['native/afsc-opening/wrap_hosted.py','wrap_hosted.py'],
 ['native/afsc-opening/material_controls.py','material_controls.py'],['native/afsc-opening/export_builder.py','export_builder.py'],['native/afsc-opening/desktop_contract.py','desktop_contract.py'],
 ['public/native/contract.py','fixed_contract.py']])copyFileSync(join(root,src),join(out,dst));
writeFileSync(join(out,'authoring.py'),readFileSync(join(root,'public/native/authoring.py'),'utf8').replace('from contract import','from fixed_contract import'));
console.log('Side-hung native assets synchronized; no licensed templates included.');
