import {createHash} from 'node:crypto';
import {test,expect} from '@playwright/test';
test('cloud build keeps the viewer, shows progress and downloads the checked family',async({page})=>{
 let submissions=0,job:any;
 await page.route('**/api/revit/status',r=>r.fulfill({json:{available:true}}));
 await page.route('**/api/revit/jobs',async r=>{submissions++;const input=r.request().postDataJSON();expect(input.configuration).toEqual({width:1200,height:1500,interior:'timber',exterior:'graphite'});const digest=createHash('sha256').update(r.request().postData()!).digest('hex');job={id:digest,status:'queued',sizeMm:[1200,1500],requestSha256:digest,configuration:input.configuration,nativeChecksPassed:false,visualReviewPassed:false,nativeParameterFlex:false};await r.fulfill({status:202,json:job})});
 await page.route('**/api/revit/jobs/*',async r=>{await r.fulfill({json:{...job,status:'ready',nativeChecksPassed:true,downloads:{family:'/api/revit/files/test.rfa',evidence:'/api/revit/files/test.zip'}}})});
 await page.route('**/api/revit/files/test.rfa',r=>r.fulfill({headers:{'content-disposition':'attachment; filename="LITHIC-AFKC-1200x1500.rfa"','content-type':'application/octet-stream'},body:'OFFLINE TEST FILE'}));
 await page.goto('/');await page.getByRole('button',{name:'Review AFKC source profiles'}).click();await page.getByRole('button',{name:'Approve product definition'}).click();
 await expect(page.locator('canvas')).toBeVisible();await page.getByRole('button',{name:'Build Revit family',exact:true}).click();await expect(page.getByText('Queued for Revit',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Building Revit family…',exact:true})).toBeDisabled();
 await expect(page.getByText('Your Revit family is ready',{exact:true})).toBeVisible({timeout:20000});await expect(page.locator('canvas')).toBeVisible();expect(submissions).toBe(1);
 const pending=page.waitForEvent('download');await page.getByRole('link',{name:'Download Revit family',exact:true}).click();expect((await pending).suggestedFilename()).toBe('LITHIC-AFKC-1200x1500.rfa');await page.getByRole('button',{name:'View approved definition'}).click();await expect(page.getByRole('dialog')).toContainText('native checks passed for this configuration');
});
