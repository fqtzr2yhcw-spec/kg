import json, numpy as np, sys
r=json.load(open('pipes_fit.json')); f,a,sp,zn=r['dims']; az,el,d=r['cam'][:3]; L=11.5
cs=[(-1,f+0.5),(0,f+0.5),(1,f+0.5),(-0.5,f+1.366),(0.5,f+1.366)]
pts=[[0,y,z] for z,y in cs]+[[L,y,z] for z,y in cs]+[[a+k*sp,0,zn] for k in range(6)]+[[L/2,f+1.866,0],[L/2,0,1.5],[L/2,0,-1.5]]
cdx=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
cfg={'cam':{'T':r['T'],'az':az,'el':el,'d':d},
     'car':{'cx':L/2+cdx,'cz':0.0,'yaw':0.0,'yd':0.0,'scale':1.48},
     'proxies':[{'type':'cyl','c':[L/2,y,z],'r':0.5,'h':L,'axis':'x'} for z,y in cs]+
               [{'type':'box','c':[a+k*sp,f/2,0],'s':[0.3,f,3.2]} for k in range(6)],
     'pts':pts,'light':{'daz':-30,'el':55},'trackL':26}
json.dump(cfg,open('rcfg_pipes.json','w'),indent=1)
json.dump({'photo':'pipes.png','mask':'pipes_mask.png','shadow':'pipes_shadow.png','fit':'pipes_fit.json','rcfg':'rcfg_pipes.json',
  'shadow_k':0.75,'contrast':1.04,'dof':{'focus':[4,1,0],'pt':[L+4,0,0],'px':3.0,'max':7}},open('prod_pipes.json','w'),indent=1)
