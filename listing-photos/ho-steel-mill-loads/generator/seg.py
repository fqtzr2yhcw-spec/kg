import cv2, numpy as np
im=cv2.imread('p1.png'); H,W=im.shape[:2]
lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
L=lab[...,0]; A=lab[...,1]-128; B=lab[...,2]-128
poly=np.array([(148,68),(230,50),(275,38),(348,20),(1045,378),(1040,472),(1005,502),(912,562),(805,612),(770,602),(146,162)],np.int32)
hull=np.zeros((H,W),np.uint8); cv2.fillPoly(hull,[poly],1)
mask=np.full((H,W),cv2.GC_BGD,np.uint8)
mask[hull==1]=cv2.GC_PR_FGD
boardlike=(B-1.6*A>13)&(L>140)
fabriclike=(B<4)&(A<2)&(L>150)
mask[(hull==1)&(boardlike|fabriclike)]=cv2.GC_PR_BGD
brown=(A>3.5)&(B-1.6*A<8)
dark=(L<80)&(A>2)
er=cv2.erode(hull,np.ones((25,25),np.uint8))
mask[(er==1)&(brown|dark)]=cv2.GC_FGD
bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
cv2.grabCut(im,mask,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
fg=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype(np.uint8)
# keep largest component(s)
n,lbl,st,_=cv2.connectedComponentsWithStats(fg)
keep=np.zeros_like(fg)
for i in range(1,n):
    if st[i,cv2.CC_STAT_AREA]>150: keep[lbl==i]=255
cv2.imwrite('mask_raw.png',keep)
viz=im.copy(); viz[keep==0]=(viz[keep==0]*0.25+np.array([0,255,0])*0.75).astype(np.uint8)
cv2.imwrite('mask_viz.png',viz)
