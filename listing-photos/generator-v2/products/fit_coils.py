import sys, json, numpy as np; sys.path.insert(0,'lib'); from fitlib import fit, project
# x right, y up, z toward camera. pallets side=1. dims: gp (gap), tp (pallet thk), R, Hc
def model(d):
    gp,tp,R,Hc=d
    P=[]
    for sx in (-1,1):
        x0 = -gp/2-1 if sx<0 else gp/2; x1=x0+1
        P += [[x0,tp,0.5],[x1,tp,0.5],[x0,tp,-0.5],[x1,tp,-0.5],[x0,0,0.5],[x1,0,0.5]]
    for cx in (-(gp/2+0.5), gp/2+0.5):
        yt=tp+Hc
        P += [[cx-R,yt,0],[cx+R,yt,0],[cx,yt,-R],[cx,yt,R]]
    return np.array(P), np.array([0, tp+Hc/2, 0])
obs=[ (188,551),(580,551),(229,264),(592,264),(190,563),(581,564),
      (612,552),(1004,552),(609,262),(952,262),(613,564),(1003,564),
      (188,212),(560,212),(375,75),(373,335),
      (625,214),(1000,214),(812,78),(812,336)]
wts=[1,1,0.4,1,1,1, 1,1,1,0.4,1,1, 0.7,0.7,0.7,0.5, 0.7,0.7,0.7,0.5]
r=fit(model,obs,[0.08,0.03,0.45,0.9],([0,0.005,0.2,0.3],[0.5,0.2,0.7,2.0]),np.radians([80,90,100]),np.radians([30,45,60]),[4,8,16],(1220,796),wts)
print('rms',round(r['rms'],2),'dims',np.round(r['dims'],3),'az el',np.round(np.degrees(r['cam'][:2]),2),'d',round(r['cam'][2],2),'roll',round(np.degrees(r['cam'][3]),2),'s',round(r['cam'][4]))
for o,u in zip(obs,r['uv']): print(o, np.round(u))
json.dump(r,open('coils_fit.json','w'))
