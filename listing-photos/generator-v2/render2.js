const { chromium } = require('playwright');
const fs=require('fs');
(async()=>{
  const [,,qs,out]=process.argv;
  const b = await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const q=new URLSearchParams(qs); const w=+q.get('w'), h=+q.get('h');
  const p = await b.newPage({viewport:{width:w,height:h}});
  p.on('console',m=>console.log('[page]',m.text())); p.on('pageerror',e=>console.log('[err]',e.message));
  await p.goto('http://127.0.0.1:8765/scene2.html?'+qs);
  await p.waitForFunction(()=>window.__done,null,{timeout:300000});
  const o=await p.evaluate(()=>window.__out);
  fs.writeFileSync(out.replace('.png','.json'),JSON.stringify(o));
  const data=await p.evaluate(()=>document.querySelector('canvas').toDataURL('image/png'));
  fs.writeFileSync(out,Buffer.from(data.split(',')[1],'base64'));
  await b.close();
})();
