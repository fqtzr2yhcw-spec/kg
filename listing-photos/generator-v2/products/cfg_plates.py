import json, numpy as np, sys
r=json.load(open('plates_fit.json')); L,Hs,hs=r['dims']; az,el,d=r['cam'][:3]; t=hs+Hs
cdx=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
pts=[[x,y,z] for x in (0,L/2,L) for y in (0,hs,t) for z in (0,-1)]
cfg={'cam':{'T':r['T'],'az':az,'el':el,'d':d},
     'car':{'cx':L/2+cdx,'cz':-0.5,'yaw':0.0,'yd':0.0,'scale':0.46},
     'proxies':[{'type':'box','c':[L/2,hs+Hs/2,-0.5],'s':[L,Hs,1]},{'type':'box','c':[L/2,hs/2,-0.5],'s':[L*0.98,hs,0.9]}],
     'pts':pts,'light':{'daz':120,'el':58},'trackL':26}
json.dump(cfg,open('rcfg_plates.json','w'),indent=1)
json.dump({'photo':'plates.png','mask':'plates_mask.png','shadow':'plates_shadow.png','fit':'plates_fit.json','rcfg':'rcfg_plates.json',
  'shadow_k':0.6,'contrast':1.08,'lift':0.02,'dof':{'focus':[L*0.35,t,0],'pt':[L+1.5,0,-0.5],'px':3.0,'max':7}},open('prod_plates.json','w'),indent=1)
