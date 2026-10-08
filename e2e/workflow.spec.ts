import {test,expect} from '@playwright/test';
test('sample approval gates configurations and JSON handoff',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Explore sample definition'}).click();
 await expect(page.getByRole('button',{name:'Approve sample definition'})).toBeDisabled();
 await page.getByLabel('Frame depth',{exact:true}).fill('120');await page.getByLabel('Source of this dimension').fill('User confirmation for prototype');
 await page.getByRole('button',{name:'Approve sample definition'}).click();
 await expect(page.getByRole('button',{name:'Build Revit family'})).toBeDisabled();
 await page.getByLabel('Width',{exact:true}).fill('1000');await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('button',{name:'Download build request'})).toBeDisabled();
 await page.getByRole('button',{name:'1500 × 1800'}).click();const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Download build request'}).click();expect((await pending).suggestedFilename()).toBe('lithic-window-build-request.json');
 await page.getByRole('button',{name:'View approved definition'}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
});
