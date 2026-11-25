import json, sys, urllib.parse, subprocess
P=sys.argv[1]; t=json.load(open(f'b2/text_{P}.json'))
def qs(hero,W=None,clean=False,extra=None):
    tt=dict(t); tt.update(extra or {})
    d={'t':json.dumps(tt),'hero':hero}
    if W: d['W']=str(W)
    if clean: d['clean']='1'
    return urllib.parse.urlencode(d)
jobs=[{'qs':qs(f'b2/hero_{P}_sq.png',extra=t.get('sq',{})),'out':f'b2/T_{P}_square.png'},
      {'qs':qs(f'b2/hero_{P}_wide.png',2667,extra=t.get('wide',{})),'out':f'b2/T_{P}_etsy.png','W':2667},
      {'qs':qs(f'b2/hero_{P}_clean.png',clean=True,extra=t.get('clean',{})),'out':f'b2/T_{P}_clean.png'}]
json.dump(jobs,open('b2/jobs.json','w'))
subprocess.run(['node','shot2.js','b2/jobs.json'],check=True)
from PIL import Image
for j in jobs:
    im=Image.open(j['out']); im.resize((im.size[0]//2,im.size[1]//2),Image.LANCZOS).save(j['out'].replace('T_','V_'))
