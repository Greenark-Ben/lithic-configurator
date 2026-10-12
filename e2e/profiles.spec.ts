import {test,expect} from '@playwright/test';
test('source profile review, section view and dynamic sweep export',async({page},testInfo)=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewportSize({width:1672,height:941});await page.goto('/');
 await page.getByRole('button',{name:'Review AFKC source profiles'}).click();await expect(page.locator('canvas')).toHaveCount(0);await expect(page.getByRole('link',{name:'View head / sill drawing'})).toHaveAttribute('href','/evidence/afkc-head-sill.png');
 await page.getByRole('button',{name:'Approve product definition'}).click();await expect(page.locator('canvas')).toBeVisible();await page.waitForTimeout(1000);await page.screenshot({path:testInfo.outputPath('afkc-profile.png')});
 await page.getByRole('button',{name:'Section',exact:true}).click();await page.getByLabel('Width',{exact:true}).fill('1275');await page.getByLabel('Height',{exact:true}).fill('1625');await page.screenshot({path:testInfo.outputPath('afkc-profile-section.png')});
 const event=page.waitForEvent('download');await page.getByRole('button',{name:'Download build request'}).click();const download=await event;const stream=await download.createReadStream();let text='';for await(const chunk of stream!)text+=chunk.toString();const request=JSON.parse(text);
 expect(request.parts.filter((p:any)=>p.sweep)).toHaveLength(8);expect(request.parts.find((p:any)=>p.id==='glazing').size).toEqual([1194,1544,48]);expect(request.parts.find((p:any)=>p.id==='timber-head').sweep.lengthMm).toBe(1168);expect(request.definition.profile.manufacturerApproved).toBe(false);expect(request.nativeStatus).toBe('not-built');expect(errors).toEqual([]);
});
