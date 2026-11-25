import numpy as np, json, itertools
from scipy.optimize import least_squares
# (x: 0 back..Lg front, z: 0 outer-left .. , y up). params dims: Lg,H,f,g
obs = [
 # (xsel, zsel, ysel, u, v)  xsel: 0 back / 1 front ; zsel: 'L0','L1','R0','R1'; ysel: 'top'/'bot'
 (0,'L0','top',158,75),(0,'L1','top',226,58),(1,'L0','top',808,490),(1,'L1','top',905,450),
 (1,'L0','bot',808,580),(1,'L1','bot',905,545),(0,'L0','bot',160,148),
 (1,'R1','top',1030,383),(1,'R1','bot',1025,458),(0,'R1','top',350,28),(0,'R0','top',277,45),(1,'R0','top',932,438),
]
def pts3(dims):
    Lg,H,f,g=dims
    zs={'L0':0,'L1':-1,'R0':-1-g,'R1':-2-g}
    out=[]
    for xs,zk,yk,u,v in obs:
        out.append([xs*Lg, f+H if yk=='top' else f, zs[zk]])
    return np.array(out)
def project(P, cam):
    az,el,d,roll,s,tx,ty,cx,cz = cam
    T=np.array([cx,0.5,cz])
    C=T+d*np.array([np.cos(el)*np.cos(az), np.sin(el), np.cos(el)*np.sin(az)])
    fw=(T-C)/np.linalg.norm(T-C); up=np.array([0,1,0.])
    rt=np.cross(fw,up); rt/=np.linalg.norm(rt); u2=np.cross(rt,fw)
    V=P-C; xc=V@rt; yc=V@u2; zc=V@fw
    u=xc/zc; w=-yc/zc
    cr,sr=np.cos(roll),np.sin(roll)
    return np.stack([s*(cr*u-sr*w)+tx, s*(sr*u+cr*w)+ty],1), zc
UV=np.array([[o[3],o[4]] for o in obs],float)
def resid(p):
    dims=p[:4]; cam=np.concatenate([p[4:11],[p[0]/2,-(2+p[3])/2]])
    uv,zc=project(pts3(dims),cam)
    r=(uv-UV).ravel()
    if np.any(zc<=0): r=r+1e4
    return r
best=None
for az0 in np.radians([-60,-30,0,30,60,120,150,180,-120,-150]):
  for el0 in np.radians([20,35,50]):
    for d0 in [8,15,30]:
      p0=[6,0.9,0.15,0.1, az0,el0,d0,0,800,600,300]
      try:
        r=least_squares(resid,p0,bounds=([2,0.3,0,0, -10,0.05,2,-1,50,-3000,-3000],[15,3,0.5,0.6, 10,1.5,200,1,20000,5000,5000]))
      except Exception as e: continue
      if best is None or r.cost<best.cost: best=r
p=best.x
print('cost',best.cost,'rms px',np.sqrt(2*best.cost/len(UV)/2))
print('dims Lg,H,f,g',p[:4]); print('az,el(deg)',np.degrees(p[4]),np.degrees(p[5]),'d',p[6],'roll',np.degrees(p[7]),'s',p[8])
uv,_=project(pts3(p[:4]),np.concatenate([p[4:11],[p[0]/2,-(2+p[3])/2]]))
print(np.round(np.hstack([UV,uv]),0))
json.dump({'p':p.tolist()},open('fit.json','w'))
