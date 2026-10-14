import {test,expect} from '@playwright/test';
import {writeFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';

test('exports the reviewed 1200 x 1500 desktop package for native proof builds',async({page},testInfo)=>{
 await page.goto('/');await page.getByRole('button',{name:'Review AFKC source profiles'}).click();
 await expect(page.getByText('The 48 mm assembly contains three 4 mm panes and two 18 mm air cavities, with separate hollow aluminium spacers.')).toBeVisible();
 await page.getByRole('button',{name:'Approve product definition'}).click();
 const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Prepare Revit handoff'}).click();
 const download=await downloadEvent,stream=await download.createReadStream(),chunks:Buffer[]=[];
 for await(const chunk of stream!)chunks.push(Buffer.from(chunk));
 const bytes=Buffer.concat(chunks);
 const proof=JSON.parse(execFileSync('python3',['-X','utf8','-c',"import io,sys,zipfile,json,hashlib;z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));assert z.testzip() is None;r=z.read('request.json');m=json.loads(z.read('manifest.json'));assert hashlib.sha256(r).hexdigest()==m['requestSha256'];print(json.dumps({'request':json.loads(r),'manifest':m,'files':z.namelist()}))"],{input:bytes,encoding:'utf8'}));
 expect(proof.manifest.builder).toBe('lithic-afkc-desktop/0.2.1');expect(proof.request.parts).toHaveLength(30);
 expect(proof.files).toEqual(expect.arrayContaining(['authoring.py','drawings.py','script.py','contract.py','afkc-source.json','Install.ps1','bundle.yaml','README.txt','request.json','manifest.json']));
 expect(proof.request.configuration).toEqual({width:1200,height:1500,interior:'timber',exterior:'graphite'});
 writeFileSync(testInfo.outputPath('browser-native-handoff.zip'),bytes);
 if(process.env.LITHIC_EVIDENCE_DIR){mkdirSync(process.env.LITHIC_EVIDENCE_DIR,{recursive:true});writeFileSync(join(process.env.LITHIC_EVIDENCE_DIR,'browser-native-handoff.zip'),bytes)}
 await page.getByRole('button',{name:'Section',exact:true}).click();await page.screenshot({path:testInfo.outputPath('reviewed-afkc-section.png')});
});
