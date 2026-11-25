import json, numpy as np, sys
r=json.load(open('coils_fit.json')); gp,tp,R,Hc=r['dims']; az,el,d=r['cam'][:3]
pts=[]
for sx in (-1,1):
    x0=-gp/2-1 if sx<0 else gp/2
    pts += [[x0,tp,0.5],[x0+1,tp,0.5],[x0,tp,-0.5],[x0+1,tp,-0.5],[x0,0,0.5],[x0+1,0,0.5]]
    cx=x0+0.5; pts += [[cx-R,tp+Hc,0],[cx+R,tp+Hc,0],[cx,tp+Hc,-R],[cx,tp+Hc,R],[cx,tp+Hc/2,R]]
cfg={'cam':{'T':r['T'],'az':az,'el':el,'d':d},
     'car':{'cx':float(sys.argv[1]) if len(sys.argv)>1 else 0.0,'cz':0.0,'yaw':0.0,'yd':0.0,'scale':0.56},
     'proxies':[{'type':'box','c':[sx*(gp/2+0.5),tp/2,0],'s':[1,tp,1]} for sx in (-1,1)]+
               [{'type':'cyl','c':[sx*(gp/2+0.5),tp+Hc/2,0],'r':R,'h':Hc,'axis':'y'} for sx in (-1,1)],
     'pts':pts,'light':{'daz':80,'el':50},'trackL':24}
json.dump(cfg,open('rcfg_coils.json','w'),indent=1)
json.dump({'photo':'coils.png','mask':'coils_mask.png','shadow':'coils_shadow.png','fit':'coils_fit.json','rcfg':'rcfg_coils.json',
  'shadow_k':0.7,'contrast':1.05,
  'dof':{'focus':[0,tp+Hc/2,0.3],'pt':[3.0,0,-0.6],'px':2.5,'max':7}},open('prod_coils.json','w'),indent=1)
