import sys, json, numpy as np; sys.path.insert(0,'lib'); from fitlib import fit
# x along length (left end 0), z: front 0, back -1 (width=1), y up (support bottom 0). dims: L, Hs, hs
def model(d):
    L,Hs,hs=d; t=hs+Hs
    P=[[0,t,-1],[0,t,0],[L,t,0],[0,hs,0],[L,hs,0],[0,0,0],[0,0,-1],[0,hs,-1]]
    return np.array(P), np.array([L/2,hs+Hs/2,-0.5])
obs=[(37,179),(193,265),(1200,38.5),(195,316.5),(1198,65),(208,341.5),(37,243),(35.4,218.5)]
wts=[1,1,1,1,0.8,0.6,0.5,0.7]
r=fit(model,obs,[6,0.3,0.1],([2,0.05,0.0],[20,1.5,0.6]),np.radians(np.arange(0,360,30)),np.radians([5,12,25]),[5,10,20,40],(1220,366),wts)
print('rms',round(r['rms'],2),'dims',np.round(r['dims'],3),'az el',np.round(np.degrees(r['cam'][:2]),1),'d',round(r['cam'][2],2),'roll',round(np.degrees(r['cam'][3]),1),'s',round(r['cam'][4]))
for o,u in zip(obs,r['uv']): print(o,np.round(u))
json.dump(r,open('plates_fit.json','w'))
