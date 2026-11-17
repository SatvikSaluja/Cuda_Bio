// Run against the actual locally running service, never mocked alignment responses.
// WARPALIGN_BASE_URL defaults to the loopback Studio server.
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.WARPALIGN_BASE_URL||'http://127.0.0.1:8000');
 await page.getByText('Local engine connected',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Try a real demo'}).click();
 await page.getByRole('heading',{name:'Measured demo performance'}).waitFor({timeout:30000});
 await page.getByRole('heading',{name:'demo-indel → target-indel'}).waitFor();
 await page.getByRole('img',{name:'Demo latency',exact:true}).waitFor();
 assert.equal(await page.getByRole('img',{name:'Demo latency',exact:true}).locator('circle').count(),3);
 if(process.env.WARPALIGN_SCREENSHOT_DIR){
  await mkdir(process.env.WARPALIGN_SCREENSHOT_DIR,{recursive:true});
  await page.screenshot({path:join(process.env.WARPALIGN_SCREENSHOT_DIR,'studio-demo.png'),fullPage:true});
 }
 await page.getByRole('button',{name:'Next difference →'}).click();
 await page.getByLabel('Column',{exact:true}).fill('2');
 await page.getByRole('button',{name:'Settings',exact:true}).click();
 await page.getByLabel('Color theme').selectOption('dark');
 assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
 assert.deepEqual(errors,[]);
 console.log('Actual browser demo, inspection, theme and mobile checks passed');
}finally{await browser.close()}
