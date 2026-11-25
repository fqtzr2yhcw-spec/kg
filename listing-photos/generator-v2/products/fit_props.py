import sys, json, numpy as np; sys.path.insert(0,'lib'); from fitlib import fit
# x right, y up, z toward camera (front). left pallet centred at (-0.52,0,0), yaw 0. dims: dx,dz,yaw of right pallet
def sq(cx,cz,yaw):
    c,s=np.cos(yaw),np.sin(yaw); out=[]
    for (u,v) in [(-0.5,-0.5),(0.5,-0.5),(-0.5,0.5),(0.5,0.5)]:   # TL(back-left),TR,BL(front-left),BR
        out.append([cx+c*u-s*v,0,cz+s*u+c*v])
    return out
def model(d):
    dx,dz,yaw=d
    P=sq(-0.52,0,0)+sq(-0.52+dx,dz,yaw)
    return np.array(P), np.array([0.0,0.0,0.0])
obs=[(636.7,1019),(1007,1028.3),(613.7,1368.7),(1002,1375),(1022.5,1022.2),(1389.3,1018.7),(1029,1370),(1417,1366.3)]
r=fit(model,obs,[1.04,0,0],([0.95,-0.2,-0.2],[1.2,0.2,0.2]),np.radians([60,90,120]),np.radians([50,65,80]),[3,6,12],(1932,2576))
print('rms',round(r['rms'],2),'dims',np.round(r['dims'],3),'az el',np.round(np.degrees(r['cam'][:2]),1),'d',round(r['cam'][2],2),'roll',round(np.degrees(r['cam'][3]),1),'s',round(r['cam'][4]))
for o,u in zip(obs,r['uv']): print(o,np.round(u))
json.dump(r,open('props_fit.json','w'))
