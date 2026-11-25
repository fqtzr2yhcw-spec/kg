import json, numpy as np, cv2
exec(open('composite.py').read().split('photo = cv2.imread')[0].split("render_png =")[0])  # imports + nothing
p = json.load(open('fit.json'))['p']; Lg,Hh,ff,g = p[:4]; cam=list(p[4:11])+[Lg/2,-(2+g)/2]
def project(P, cam):
    az, el, d, roll, s, tx, ty, cx, cz = cam
    T = np.array([cx, 0.5, cz]); C = T + d*np.array([np.cos(el)*np.cos(az), np.sin(el), np.cos(el)*np.sin(az)])
    fw=(T-C)/np.linalg.norm(T-C); up=np.array([0,1,0.]); rt=np.cross(fw,up); rt/=np.linalg.norm(rt); u2=np.cross(rt,fw)
    V=P-C; xc=V@rt; yc=V@u2; zc=V@fw; u=xc/zc; w=-yc/zc; cr,sr=np.cos(roll),np.sin(roll)
    return np.stack([s*(cr*u-sr*w)+tx, s*(sr*u+cr*w)+ty],1)
im=cv2.imread('p1.png')
gray=cv2.GaussianBlur(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32),(0,0),1.2)
gx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
def hexagon(z0,z1):
    pts={}
    for nm,(x,y,z) in {'bbn':(0,ff,z0),'btn':(0,ff+Hh,z0),'btf':(0,ff+Hh,z1),'ftf':(Lg,ff+Hh,z1),'fbf':(Lg,ff,z1),'fbn':(Lg,ff,z0),'ftn':(Lg,ff+Hh,z0)}.items():
        pts[nm]=project(np.array([[x,y,z]],float),cam)[0]
    return pts
def refine_edge(a,b,search=14):
    a=np.array(a,float); b=np.array(b,float); d=b-a; Lp=np.linalg.norm(d); t=d/Lp; n=np.array([-t[1],t[0]])
    samples=[]
    for s in np.linspace(0.08,0.92,60):
        c=a+d*s; best=None
        for o in np.arange(-search,search+0.5,0.5):
            q=c+n*o; x,y=q
            if not(1<x<im.shape[1]-2 and 1<y<im.shape[0]-2): continue
            G=abs(cv2.getRectSubPix(gx,(1,1),(x,y))[0,0]*n[0]+cv2.getRectSubPix(gy,(1,1),(x,y))[0,0]*n[1])
            if best is None or G>best[0]: best=(G,o)
        if best: samples.append((s,best[1],best[0]))
    S=np.array(samples); w=S[:,2]
    # robust line fit offset(s) = k*s + m
    k,m=0,np.median(S[:,1])
    for _ in range(5):
        r=S[:,1]-(k*S[:,0]+m); inl=np.abs(r)<2.5
        if inl.sum()<6: break
        A=np.vstack([S[inl,0],np.ones(inl.sum())]).T; k,m=np.linalg.lstsq(A*w[inl,None],S[inl,1]*w[inl],rcond=None)[0]
    return a+n*m, b+n*(k+m), inl.mean()
def inter(p1,p2,p3,p4):
    A=np.array([p2-p1,p3-p4]).T; t=np.linalg.solve(A,p3-p1); return p1+(p2-p1)*t[0]
out={}
for name,(z0,z1) in {'L':(0,-1),'R':(-1-g,-2-g)}.items():
    P=hexagon(z0,z1)
    order=['bbn','btn','btf','ftf','fbf','fbn'] if name=='L' else ['btn','btf','ftf','fbf']
    edges=[]
    for i in range(len(order)-(0 if name=='L' else 1)):
        a,b=P[order[i]],P[order[(i+1)%len(order)]]
        a2,b2,q=refine_edge(a,b); edges.append((a2,b2)); print(name,order[i],'->',order[(i+1)%len(order)],'inliers %.2f'%q, 'shift', np.round(a2-a,1), np.round(b2-b,1))
    verts=[]
    if name=='L':
        for i in range(len(edges)): verts.append(inter(*edges[i-1],*edges[i]))
    else:
        verts=[edges[0][0]]+[inter(*edges[i-1],*edges[i]) for i in range(1,len(edges))]+[edges[-1][1]]
    out[name]={'verts':[v.tolist() for v in verts],'fit':{k:v.tolist() for k,v in P.items()}}
json.dump(out,open('sil.json','w'),indent=1)
v=im.copy()
for name in out:
    pts=np.array(out[name]['verts'],np.int32); cv2.polylines(v,[pts],name=='L',(0,255,0),1,cv2.LINE_AA)
    f=out[name]['fit']; 
    for k in f: cv2.circle(v,tuple(np.int32(f[k])),3,(0,0,255),-1)
big=cv2.resize(v,None,fx=1.6,fy=1.6,interpolation=cv2.INTER_CUBIC)
cv2.imwrite('sil_viz.png',big[0:1100,150:1750])
