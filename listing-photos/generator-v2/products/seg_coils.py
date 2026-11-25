import sys, json, numpy as np, cv2; sys.path.insert(0,'lib')
from seglib import *
r=json.load(open('coils_fit.json')); gp,tp,R,Hc=r['dims']; cam=r['cam']; T=r['T']
img=cv2.imread('coils.png')
parts=[]
for sx in (-1,1):
    x0=-gp/2-1 if sx<0 else gp/2
    parts.append(box_pts(x0,x0+1,0,tp,-0.5,0.5))
    parts.append(cyl_pts([x0+0.5,tp,0],R,Hc))
sil=np.zeros(img.shape[:2],np.uint8)
for p in parts: sil|=hull_mask(img.shape,[p],T,cam)
sure=cv2.erode(sil,np.ones((25,25),np.uint8)); prob=cv2.dilate(sil,np.ones((31,31),np.uint8))
lab=cv2.cvtColor(cv2.medianBlur(img,5),cv2.COLOR_BGR2LAB).astype(np.float32); L,A,B=lab[...,0],lab[...,1]-128,lab[...,2]-128
woodlike=(B>14)&(L>150)&(A<12)
bg=(prob==0)|(woodlike & (sure==0))
fg=grabcut(img,sure,prob,bg)
fg=keep_big(cv2.morphologyEx(fg,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),500,600)
cv2.imwrite('coils_mask.png',fg)
cv2.imwrite('coils_maskviz.png',viz(img,fg))
# remove the wood gap between the pallets (outside coil hulls)
gapm=hull_mask(img.shape,[box_pts(-gp/2+0.012,gp/2-0.012,0,tp,-0.5,0.5)],T,cam)
coilh=np.zeros_like(gapm)
for sx in (-1,1):
    x0=-gp/2-1 if sx<0 else gp/2; coilh|=hull_mask(img.shape,[cyl_pts([x0+0.5,tp,0],R,Hc)],T,cam)
gapm[coilh>0]=0
fg[(gapm>0)&(~((A>4)&(L<120)))]=0
fg=keep_big(cv2.morphologyEx(fg,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)),500,0)
cv2.imwrite('coils_mask.png',fg); cv2.imwrite('coils_maskviz.png',viz(img,fg))
cv2.imwrite('coils_shadow.png',(photo_shadow(img,fg,fade_px=40)*255).astype(np.uint8))
gz=cv2.dilate(gapm,np.ones((9,9),np.uint8))
med=cv2.medianBlur(fg,9); med=cv2.morphologyEx(med,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
fg[gz>0]=med[gz>0]
cv2.imwrite('coils_mask.png',fg); cv2.imwrite('coils_maskviz.png',viz(img,fg))
