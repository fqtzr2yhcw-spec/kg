import json, numpy as np, sys
r=json.load(open('props_fit.json')); dx,dz,yaw=r['dims']; az,el,d=r['cam'][:3]
cdx=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
pal=[(-0.52,0,0),(-0.52+dx,dz,yaw)]
pts=[]
for cx,cz,yw in pal:
    c,s=np.cos(yw),np.sin(yw)
    for (u,v) in [(-0.5,-0.5),(0.5,-0.5),(-0.5,0.5),(0.5,0.5),(0,0)]:
        for y in (0.0,0.15): pts.append([cx+c*u-s*v,y,cz+s*u+c*v])
cfg={'cam':{'T':r['T'],'az':az,'el':el,'d':d},
     'car':{'cx':(pal[0][0]+pal[1][0])/2+cdx,'cz':dz/2,'yaw':0.0,'yd':-0.02,'scale':0.41},
     'proxies':[{'type':'box','c':[cx,-0.01,cz],'s':[1,0.02,1],'yaw':-yw} for cx,cz,yw in pal]+
               [{'type':'cyl','c':[cx,0.07,cz],'r':0.4,'h':0.14,'axis':'y'} for cx,cz,yw in pal],
     'pts':pts,'light':{'daz':133,'el':55},'trackL':26}
json.dump(cfg,open('rcfg_props.json','w'),indent=1)
json.dump({'photo':'props.png','mask':'props_mask.png','shadow':'props_shadow.png','fit':'props_fit.json','rcfg':'rcfg_props.json',
  'shadow_k':0.7,'contrast':1.05,'feather':0.6,'dof':{'focus':[0,0,0],'pt':[3.5,0,0],'px':1.6,'max':5}},open('prod_props.json','w'),indent=1)
