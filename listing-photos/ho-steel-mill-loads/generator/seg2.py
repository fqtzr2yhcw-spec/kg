import cv2, numpy as np
im=cv2.imread('p1.png'); H,W=im.shape[:2]
fg=cv2.imread('mask_raw.png',0)
lab=cv2.cvtColor(cv2.medianBlur(im,5),cv2.COLOR_BGR2LAB).astype(np.float32)
L=lab[...,0]; A=lab[...,1]-128; B=lab[...,2]-128
yellow=(B-1.6*A>8.0)&(L>70)
fg2=fg.copy(); fg2[yellow]=0
fg2=cv2.morphologyEx(fg2,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lbl,st,_=cv2.connectedComponentsWithStats(fg2)
keep=np.zeros_like(fg2)
for i in range(1,n):
    if st[i,cv2.CC_STAT_AREA]>120: keep[lbl==i]=255
# fill small holes
inv=255-keep; n,lbl,st,_=cv2.connectedComponentsWithStats(inv)
for i in range(1,n):
    if st[i,cv2.CC_STAT_AREA]<400: keep[lbl==i]=255
cv2.imwrite('mask2.png',keep)
viz=im.copy(); viz[keep==0]=(viz[keep==0]*0.25+np.array([0,255,0])*0.75).astype(np.uint8)
cv2.imwrite('mask2_viz.png',viz)
crop=viz[340:620,620:1060]; crop2=viz[40:420,130:560]
cv2.imwrite('zoom2.png',cv2.resize(np.hstack([crop,cv2.resize(crop2,(int(430*280/380),280))]),None,fx=1.4,fy=1.4))
