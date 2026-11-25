import sys, json, numpy as np; sys.path.insert(0,'lib'); from fitlib import fit, project
# x along bundle (0 front .. back), y up, z across (near side +). pipe D=1. dims: f (dunnage h), a, sp (block spacing), zn
def model(d):
    f,a,sp,zn=d
    P=[[0,f+0.5,-1],[0,f+0.5,0],[0,f+0.5,1],[0,f+1.366,-0.5],[0,f+1.366,0.5]]
    P+=[[a+k*sp,0,zn] for k in range(6)]
    return np.array(P), np.array([2.5,0.8,0])
obs=[(246.9,425.3),(300.6,448.8),(360.9,470.6),(259.4,378.4),(320.3,397.2),
     (402,520),(512.5,420.6),(600,355),(690.6,292.5),(762.5,242.5),(821.9,198.8)]
wts=[1]*5+[0.5,1,1,1,1,1]
best=None
for zsign in (1,):
    o=list(obs)
    if zsign<0: o=[obs[2],obs[1],obs[0],obs[4],obs[3]]+obs[5:]
    r=fit(model,o,[0.3,0.2,1.0,1.3],([0.02,-0.5,0.3,1.2],[0.8,1.5,3.0,1.5]),np.radians(np.arange(0,360,45)),np.radians([20,35,50]),[6,12,24],(1021,824),wts)
    print(zsign,'rms',round(r['rms'],2),'dims',np.round(r['dims'],3),'az el',np.round(np.degrees(r['cam'][:2]),1),'d',round(r['cam'][2],2),'roll',round(np.degrees(r['cam'][3]),1),'s',round(r['cam'][4]))
    if best is None or r['rms']<best[0]['rms']: best=(r,zsign,o)
r,zs,o=best
for a,b in zip(o,r['uv']): print(a,np.round(b))
r['zsign']=zs; json.dump(r,open('pipes_fit.json','w'))
