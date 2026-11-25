import sys, json, numpy as np, cv2; sys.path.insert(0,'lib')
from seglib import *
r=json.load(open('props_fit.json')); dx,dz,yaw=r['dims']; cam=r['cam']; T=r['T']
img=cv2.imread('props.png'); H,W=img.shape[:2]
def palpts(cx,cz,yw,e,y0,y1):
    c,s=np.cos(yw),np.sin(yw); out=[]
    for (u,v) in [(-0.5-e,-0.5-e),(0.5+e,-0.5-e),(-0.5-e,0.5+e),(0.5+e,0.5+e)]:
        for y in (y0,y1): out.append([cx+c*u-s*v,y,cz+s*u+c*v])
    return out
pal=[(-0.52,0,0),(-0.52+dx,dz,yaw)]
sure=np.zeros((H,W),np.uint8); prob=np.zeros_like(sure)
for p in pal:
    sure|=hull_mask(img.shape,[palpts(*p,-0.04,0,0.01)],T,cam)
    prob|=hull_mask(img.shape,[palpts(*p,0.16,0,0.35)],T,cam)
sure=cv2.erode(sure,np.ones((15,15),np.uint8))
lab=cv2.cvtColor(cv2.medianBlur(img,5),cv2.COLOR_BGR2LAB).astype(np.float32); Lc,A,B=lab[...,0],lab[...,1]-128,lab[...,2]-128
plylike=(B>17)&(Lc>170)
bg=(prob==0)|(plylike&(sure==0))
fg=grabcut(img,sure,prob,bg,iters=6)
fg=keep_big(cv2.morphologyEx(fg,cv2.MORPH_OPEN,np.ones((5,5),np.uint8)),3000,2000)
cv2.imwrite('props_mask.png',fg); v=viz(img,fg); cv2.imwrite('props_maskviz.png',cv2.resize(v[1150:1950,450:1550],None,fx=0.9,fy=0.9))
cv2.imwrite('props_shadow.png',(photo_shadow(img,fg,fade_px=60,hole_dil=41)*255).astype(np.uint8))
from fitlib import project
SS=4; big=np.zeros((H*SS,W*SS),np.uint8)
for p in pal:
    uv,_=project(np.array(palpts(*p,0.0,-0.02,0.0)),T,cam)
    hull=cv2.convexHull((uv*SS).astype(np.float32)).astype(np.int32); cv2.fillPoly(big,[hull],255,lineType=cv2.LINE_AA)
soft=cv2.resize(big,(W,H),interpolation=cv2.INTER_AREA)
cv2.imwrite('props_mask.png',soft)
hard=(soft>127).astype(np.uint8)*255
cv2.imwrite('props_shadow.png',(photo_shadow(img,hard,fade_px=70,hole_dil=41)*255).astype(np.uint8))
cv2.imwrite('props_maskviz.png',viz(img,hard)[900:1500,500:1550])
