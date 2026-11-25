import sys, json, numpy as np, cv2; sys.path.insert(0,'lib')
from seglib import *
r=json.load(open('pipes_fit.json')); f,a,sp,zn=r['dims']; cam=r['cam']; T=r['T']; L=11.5
img=cv2.imread('pipes.png'); H,W=img.shape[:2]
lab=cv2.cvtColor(cv2.medianBlur(img,3),cv2.COLOR_BGR2LAB).astype(np.float32); Lc,A,B=lab[...,0],lab[...,1]-128,lab[...,2]-128
green=((A<-14)&(Lc>60)).astype(np.uint8)*255
green=keep_big(cv2.morphologyEx(green,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)),2000,3000)
# dunnage zone: footprint band from ground to bundle bottom
dz=hull_mask(img.shape,[box_pts(-0.3,L+0.3,0,f+0.35,-1.7,1.7)],T,cam,dil=6)
dark=((Lc<105)&(dz>0)&(B<30)).astype(np.uint8)*255
m=cv2.bitwise_or(green,dark)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
m=keep_big(m,150,2500)
# hole fill for gaps between pipes at the front face
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); ff_=np.zeros_like(m); cv2.drawContours(ff_,cnts,-1,255,-1)
holes=cv2.subtract(ff_,m); n,lbl,st,_=cv2.connectedComponentsWithStats(holes)
for i in range(1,n):
    if st[i,cv2.CC_STAT_AREA]<1500: m[lbl==i]=255
cv2.imwrite('pipes_mask.png',m); cv2.imwrite('pipes_maskviz.png',viz(img,m))
cv2.imwrite('pipes_shadow.png',(photo_shadow(img,m,fade_px=40)*255).astype(np.uint8))
