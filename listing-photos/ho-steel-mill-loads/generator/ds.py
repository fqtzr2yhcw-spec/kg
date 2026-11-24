import cv2, numpy as np, json, sys
src, name = sys.argv[1], sys.argv[2]   # e.g. r_wide4k  -> r_wide
r=cv2.imread(src+'.png',cv2.IMREAD_UNCHANGED).astype(np.float32); H,W=r.shape[:2]
a=r[...,3:4]/255; prem=np.dstack([r[...,:3]*a,a*255])
s=cv2.resize(prem,(W//2,H//2),interpolation=cv2.INTER_AREA)
aa=np.clip(s[...,3:4]/255,1e-4,1); cv2.imwrite(name+'.png',np.dstack([np.clip(s[...,:3]/aa,0,255),s[...,3]]).astype(np.uint8))
d=cv2.imread(src.replace('r_','d_')+'.png',cv2.IMREAD_UNCHANGED); cv2.imwrite(name.replace('r_','d_')+'.png',cv2.resize(d,(W//2,H//2),interpolation=cv2.INTER_NEAREST))
json.dump(json.load(open(src+'.json')),open(name+'.json','w'))
