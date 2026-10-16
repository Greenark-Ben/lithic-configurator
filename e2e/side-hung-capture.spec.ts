import {test,expect} from '@playwright/test';
import {unzipSync} from 'fflate';
import {mkdirSync} from 'node:fs';
import {join} from 'node:path';
test('exports a source-pinned side-hung package with the selected white finishes and angle',async({page},info)=>{
 test.setTimeout(90000);await page.goto('/');await page.getByRole('button',{name:'Review LITHIC Side-Hung Outward Window'}).click();await page.getByRole('button',{name:'Approve product definition'}).click();
 await page.getByRole('button',{name:'45°',exact:true}).click();await page.getByRole('button',{name:'White',exact:true}).first().click();await page.getByRole('button',{name:'White',exact:true}).last().click();
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Prepare Revit handoff'}).click();const download=await pending;
 const file=info.outputPath('sidehung-white45-handoff.zip');await download.saveAs(file);
 if(process.env.LITHIC_SIDEHUNG_EVIDENCE_DIR){mkdirSync(process.env.LITHIC_SIDEHUNG_EVIDENCE_DIR,{recursive:true});await download.saveAs(join(process.env.LITHIC_SIDEHUNG_EVIDENCE_DIR,'handoff.zip'));}
 const stream=await download.createReadStream(),chunks:Buffer[]=[];for await(const chunk of stream!)chunks.push(Buffer.from(chunk));const files=unzipSync(Buffer.concat(chunks));
 const decode=(name:string)=>new TextDecoder().decode(files[name]),request=JSON.parse(decode('request.json'));
 expect(request.configuration).toEqual({width:880,height:1180,interior:'white',exterior:'white',openingAngleDegrees:45});expect(request.definition.productId).toBe('lithic.window.side-hung-outward');
 expect(decode('build_native.py')).toContain('LITHIC-Window-SideHung-Outward-Moving-Sash.rfa');expect(decode('build_native.py')).not.toContain('LITHIC-AFSC-');expect(Object.keys(files).some(name=>name.endsWith('.rft'))).toBe(false);
});
