import sys, json, numpy as np, cv2; sys.path.insert(0,'lib')
from seglib import *
r=json.load(open('plates_fit.json')); L,Hs,hs=r['dims']; cam=r['cam']; T=r['T']
img=cv2.imread('plates.png'); H,W=img.shape[:2]
stack=hull_mask(img.shape,[box_pts(0,L,hs,hs+Hs,-1,0)],T,cam)
sup=hull_mask(img.shape,[box_pts(0,L,0,hs+0.01,-1,0.02)],T,cam)
lab=cv2.cvtColor(cv2.medianBlur(img,3),cv2.COLOR_BGR2LAB).astype(np.float32); Lc,A,B=lab[...,0],lab[...,1]-128,lab[...,2]-128
sure=cv2.erode(stack,np.ones((7,7),np.uint8))
prob=cv2.dilate(cv2.bitwise_or(stack,sup),np.ones((9,9),np.uint8))
boardlike=(Lc>185)&(B>8)
bg=(prob==0)|(boardlike&(sure==0))
fg=grabcut(img,sure,prob,bg)
fg=keep_big(cv2.morphologyEx(fg,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),300,300)
cv2.imwrite('plates_mask.png',fg); cv2.imwrite('plates_maskviz.png',viz(img,fg))
cv2.imwrite('plates_shadow.png',(photo_shadow(img,fg,fade_px=30,hole_dil=21,scale=2)*255).astype(np.uint8))
supz=cv2.dilate(hull_mask(img.shape,[box_pts(-0.02,L+0.02,-0.01,hs+0.03,-1.02,0.03)],T,cam),np.ones((7,7),np.uint8))
supc=((Lc<160)&(supz>0)).astype(np.uint8)*255
supc=cv2.morphologyEx(supc,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
fg2=keep_big(cv2.morphologyEx(cv2.bitwise_or(fg,supc),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)),300,200)
cv2.imwrite('plates_mask.png',fg2); cv2.imwrite('plates_maskviz.png',viz(img,fg2))
cv2.imwrite('plates_shadow.png',(photo_shadow(img,fg2,fade_px=30,hole_dil=21,scale=2)*255).astype(np.uint8))
c=cv2.resize(viz(img,fg2)[180:360,150:900],None,fx=1.8,fy=1.8); cv2.imwrite('plz_sup2.png',c)
from fitlib import project
xs=np.linspace(-0.05,L+0.05,60)
bot,_=project(np.array([[x,0.0,0.0] for x in xs]),T,cam)
below=np.zeros_like(fg2); poly=np.vstack([bot,[[W+50,H+50],[-50,H+50]]]).astype(np.int32); cv2.fillPoly(below,[poly],255)
fg3=fg2.copy(); fg3[below>0]=0
band=cv2.subtract(supz,cv2.erode(stack,np.ones((3,3),np.uint8)))
fg3[(band>0)&(Lc>150)&(B>11)]=0
fg3=keep_big(cv2.morphologyEx(fg3,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),300,150)
cv2.imwrite('plates_mask.png',fg3); cv2.imwrite('plates_maskviz.png',viz(img,fg3))
cv2.imwrite('plates_shadow.png',(photo_shadow(img,fg3,fade_px=30,hole_dil=21,scale=2)*255).astype(np.uint8))
c=cv2.resize(viz(img,fg3)[180:360,150:900],None,fx=1.8,fy=1.8); cv2.imwrite('plz_sup2.png',c)
