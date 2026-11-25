const { chromium } = require('playwright');
(async()=>{
  const [,,qs,out]=process.argv;
  const b = await chromium.launch();
  const p = await b.newPage({viewport:{width:+(new URLSearchParams(qs||'').get('W')||2000),height:2000},deviceScaleFactor:1});
  p.on('pageerror',e=>console.log('[err]',e.message));
  await p.goto('http://127.0.0.1:8765/thumb.html?'+(qs||''));
  await p.evaluate(()=>document.fonts.ready);
  await p.waitForTimeout(300);
  await p.screenshot({path:out,type:'png'});
  await b.close();
})();
