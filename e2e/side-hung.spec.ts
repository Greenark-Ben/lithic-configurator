import {mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {test,expect} from '@playwright/test';
test('side-hung review, outward opening, finishes and fixed-product isolation',async({page},testInfo)=>{
 test.setTimeout(150000);const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 let submissions=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/api/revit/'))submissions++});
 await page.setViewportSize({width:1672,height:1000});await page.goto('/');
 await page.getByRole('button',{name:'Review LITHIC Side-Hung Outward Window'}).click();
 await expect(page.getByRole('link',{name:'View side-hung source sections'})).toHaveAttribute('href','/evidence/side-hung-sections.png');
 await expect(page.locator('canvas')).toHaveCount(0);await page.getByRole('button',{name:'Approve product definition'}).click();
 await expect(page.locator('canvas')).toBeVisible();await expect(page.getByLabel('Width',{exact:true})).toHaveValue('880');await expect(page.getByLabel('Width',{exact:true})).toBeDisabled();
 await expect(page.getByLabel('Height',{exact:true})).toHaveValue('1180');await expect(page.getByLabel('Height',{exact:true})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Side-hung cloud generation pending'})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Download build request'})).toBeEnabled();await expect(page.getByRole('button',{name:'Prepare Revit handoff'})).toBeEnabled();
 await page.waitForTimeout(1500);const closed=await page.locator('canvas').screenshot();await page.screenshot({path:testInfo.outputPath('sidehung-closed.png')});
 await page.getByRole('button',{name:'45°',exact:true}).click();await expect(page.getByLabel('Opening angle')).toHaveValue('45');
 await page.waitForTimeout(500);const opened=await page.locator('canvas').screenshot();expect(opened.equals(closed)).toBe(false);await page.screenshot({path:testInfo.outputPath('sidehung-open45.png')});
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Prepare Revit handoff'}).click();const download=await pending;expect(download.suggestedFilename()).toBe('lithic-sidehung-window-revit-handoff.zip');if(process.env.LITHIC_SIDEHUNG_EVIDENCE_DIR){mkdirSync(process.env.LITHIC_SIDEHUNG_EVIDENCE_DIR,{recursive:true});await download.saveAs(join(process.env.LITHIC_SIDEHUNG_EVIDENCE_DIR,'handoff.zip'));}
 await page.getByLabel('Opening angle').focus();await page.keyboard.press('ArrowRight');await expect(page.getByLabel('Opening angle')).toHaveValue('46');
 await page.getByRole('button',{name:'90°',exact:true}).click();await page.waitForTimeout(300);await page.screenshot({path:testInfo.outputPath('sidehung-open90.png')});
 await page.getByRole('button',{name:'White',exact:true}).first().click();await page.getByRole('button',{name:'White',exact:true}).last().click();
 await page.getByRole('button',{name:'Closed',exact:true}).click();await expect(page.getByLabel('Opening angle')).toHaveValue('0');
 await page.getByRole('button',{name:'View approved definition'}).click();await expect(page.getByRole('dialog')).toContainText('lithic.window.side-hung-outward');await page.keyboard.press('Escape');
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:testInfo.outputPath('sidehung-mobile.png'),fullPage:true});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.setViewportSize({width:1672,height:1000});await page.getByRole('button',{name:'References',exact:true}).click();await page.getByRole('button',{name:'Review LITHIC Fixed Window'}).click();await page.getByRole('button',{name:'Approve product definition'}).click();
 await expect(page.getByLabel('Width',{exact:true})).toHaveValue('1200');await expect(page.getByLabel('Width',{exact:true})).toBeEnabled();await expect(page.getByLabel('Opening angle')).toHaveCount(0);await expect(page.getByRole('button',{name:'Prepare Revit handoff'})).toBeEnabled();
 expect(submissions).toBe(0);expect(errors).toEqual([]);
});
