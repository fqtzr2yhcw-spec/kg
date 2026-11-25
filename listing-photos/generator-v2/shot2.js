const { chromium } = require('playwright');
(async()=>{
  const [,,jsonPath]=process.argv;           // list of jobs: [{qs, out, W}]
  const jobs=require(require('path').resolve(jsonPath));
  const b = await chromium.launch();
  for (const j of jobs){
    const p = await b.newPage({viewport:{width:j.W||2000,height:2000},deviceScaleFactor:1});
    p.on('pageerror',e=>console.log('[err]',e.message));
    await p.goto('http://127.0.0.1:8765/thumb2.html?'+j.qs);
    await p.waitForFunction(()=>window.__ready,null,{timeout:20000});
    await p.waitForTimeout(250);
    await p.screenshot({path:j.out,type:'png'}); await p.close();
  }
  await b.close();
})();
