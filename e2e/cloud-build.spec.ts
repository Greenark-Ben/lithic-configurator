import {createHash} from 'node:crypto';
import {test,expect} from '@playwright/test';
test('cloud build keeps the viewer, shows progress and downloads the checked family',async({page})=>{
 let submissions=0,job:any;
 await page.route('**/api/revit/status',r=>r.fulfill({json:{available:true}}));
 await page.route('**/api/revit/jobs',async r=>{if(r.request().method()==='GET'){await r.fulfill({json:{jobs:job?[job]:[],usage:{limit:10,used:submissions,remaining:10-submissions}}});return}submissions++;const input=r.request().postDataJSON();expect(input.configuration).toEqual({width:1200,height:1500,interior:'timber',exterior:'graphite'});const digest=createHash('sha256').update(r.request().postData()!).digest('hex');job={id:digest,status:'queued',createdAt:'2026-10-14T10:00:00Z',sizeMm:[1200,1500],requestSha256:digest,configuration:input.configuration,nativeChecksPassed:false,visualReviewPassed:false,nativeParameterFlex:false};await r.fulfill({status:202,json:job})});
 await page.route('**/api/revit/jobs/*',async r=>{await r.fulfill({json:{...job,status:'ready',nativeChecksPassed:true,downloads:{family:'/api/revit/files/test.rfa',evidence:'/api/revit/files/test.zip'}}})});
 await page.route('**/api/revit/files/test.rfa',r=>r.fulfill({headers:{'content-disposition':'attachment; filename="LITHIC-AFKC-1200x1500.rfa"','content-type':'application/octet-stream'},body:'OFFLINE TEST FILE'}));
 await page.goto('/');await page.getByRole('button',{name:'Review AFKC source profiles'}).click();await page.getByRole('button',{name:'Approve product definition'}).click();
 await expect(page.locator('canvas')).toBeVisible();await page.getByRole('button',{name:'Build Revit family',exact:true}).click();await expect(page.getByText('Queued for Revit',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Building Revit family…',exact:true})).toBeDisabled();
 await expect(page.getByText('Your Revit family is ready',{exact:true})).toBeVisible({timeout:20000});await expect(page.locator('canvas')).toBeVisible();expect(submissions).toBe(1);
 const pending=page.waitForEvent('download');await page.getByRole('link',{name:'Download Revit family',exact:true}).click();expect((await pending).suggestedFilename()).toBe('LITHIC-AFKC-1200x1500.rfa');await page.getByRole('button',{name:'View approved definition'}).click();await expect(page.getByRole('dialog')).toContainText('native checks passed for this configuration');
});

test('restores build history and recovers an existing job without a paid submission',async({page})=>{
 const id='a'.repeat(64),older='b'.repeat(64);let submissions=0,recoveries=0;
 const completed={id:older,status:'ready',createdAt:'2026-10-13T10:00:00Z',sizeMm:[900,1200],configuration:{width:900,height:1200,interior:'timber',exterior:'graphite'},requestSha256:older,nativeChecksPassed:true,visualReviewPassed:false,nativeParameterFlex:false,downloads:{family:'/api/revit/files/old.rfa',report:'/api/revit/files/report.json',evidence:'/api/revit/files/evidence.zip'}};
 let current={...completed,id,requestSha256:id,createdAt:'2026-10-14T10:00:00Z',sizeMm:[1200,1500],configuration:{...completed.configuration,width:1200,height:1500},status:'needs-attention',canRecover:true,nativeChecksPassed:false,error:'Temporary result transfer failure'};
 await page.route('**/api/revit/status',r=>r.fulfill({json:{available:true}}));
 await page.route('**/api/revit/jobs',r=>{if(r.request().method()==='POST')submissions++;return r.fulfill({json:{jobs:[current,completed],usage:{limit:10,used:10,remaining:0}}})});
 await page.route('**/api/revit/jobs/*/recover',async r=>{recoveries++;current={...current,status:'ready',nativeChecksPassed:true,canRecover:false,error:''};await r.fulfill({json:current})});
 await page.route('**/api/revit/jobs/'+id,r=>r.fulfill({json:current}));
 await page.route('**/api/revit/files/old.rfa',r=>r.fulfill({headers:{'content-disposition':'attachment; filename="LITHIC-AFKC-900x1200.rfa"'},body:'OFFLINE HISTORY FILE'}));
 await page.goto('/');await page.getByRole('button',{name:'Review AFKC source profiles'}).click();await page.getByRole('button',{name:'Approve product definition'}).click();
 await expect(page.getByText('Build needs attention',{exact:true})).toBeVisible();await expect(page.getByText('0 of 10 cloud submissions remaining today', {exact:false})).toBeVisible();
 await page.getByRole('button',{name:'Check existing build',exact:true}).click();await expect(page.getByText('Your Revit family is ready',{exact:true})).toBeVisible();
 await page.getByText('Build history (2)',{exact:true}).click();await page.getByRole('button',{name:/900 × 1200 mm/}).click();await expect(page.locator('.clarification').filter({hasText:'Your Revit family is ready'})).toContainText('900 × 1200');
 const pending=page.waitForEvent('download');await page.getByRole('link',{name:'Download this build',exact:true}).click();expect((await pending).suggestedFilename()).toBe('LITHIC-AFKC-900x1200.rfa');
 await page.reload();await page.getByRole('button',{name:'Review AFKC source profiles'}).click();await page.getByRole('button',{name:'Approve product definition'}).click();await expect(page.getByText('Your Revit family is ready',{exact:true})).toBeVisible();await expect(page.locator('canvas')).toBeVisible();expect(submissions).toBe(0);expect(recoveries).toBe(1);
});
