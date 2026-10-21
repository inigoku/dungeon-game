"""Genera las poses (pos_*.bin) y la lista de trabajos (jobs.json + atlas.json) de la Duelista."""
import json, math, sys
sys.path.insert(0,'/tmp/claude-0/r3d')
import pose as P
jobs={}; atlas={}
cell=dict(size=512,half=29.09,zc=26.36)
def job(name,view,posename,col='guardia',**kw):
    jobs[name]=dict(cell,view=view,pose=posename,col=f'col_{col}.bin',**kw)
def walk_params(phi,A=0.5,K=0.95,B=0.42):
    s,c=math.sin(phi),math.cos(phi)
    hipR,hipL=-A*s,A*s
    kneeR=K*max(0,c)+0.12; kneeL=K*max(0,-c)+0.12
    ankR=-(hipR+kneeR)*0.85+0.25*max(0,hipR); ankL=-(hipL+kneeL)*0.85+0.25*max(0,hipL)
    swR,swL=B*s,-B*s
    return dict(hipL=hipL,hipR=hipR,kneeL=kneeL,kneeR=kneeR,ankL=ankL,ankR=ankR,swL=swL,swR=swR,
                flR=-0.35-0.3*max(0,-swR/B),flL=-0.35-0.3*max(0,-swL/B),lean=0.05,hx=0.12*math.cos(2*phi+0.5),hy=0.07*math.sin(phi))
WALK={'S':(list(range(26,34)),'frente'),'N':(list(range(34,42)),'atras'),'E':(list(range(3,11)),'izq'),'O':([42,43,44,45,46,47,52,53],'der')}
for d,(idx,view) in WALK.items():
    for k,i in enumerate(idx):
        P.pose(f'w{k}',**walk_params(k*math.pi/4))
        job(f'w{d}{k}',view,f'w{k}',ground=True,rot=[0.05,0,0]); atlas[i]=f'w{d}{k}'
# reposo / guardia: respira y se balancea
def idle(th):
    s=math.sin(th); c=math.cos(th)
    kn=0.10
    return dict(kneeL=kn+0.04*s,kneeR=kn-0.04*s,ankL=-(kn+0.04*s)*0.85,ankR=-(kn-0.04*s)*0.85,swL=0.12+0.03*s,swR=0.12-0.03*s,flL=-0.55-0.05*c,flR=-0.55+0.05*c,lean=0.02+0.015*s,hx=0.08*math.sin(th+0.8),hy=0.05*c)
for k in range(4):
    P.pose(f'q{k}',**idle(k*math.pi/2)); job(f'q{k}','frente',f'q{k}',ground=True); atlas[13+k]=f'q{k}'
P.pose('q0',**idle(0))
for i,view in ((0,'frente'),(1,'frente'),(2,'frente'),(12,'atras'),(17,'izq'),(20,'der')):
    job(f'i{i}',view,'q0',ground=True); atlas[i]=f'i{i}'
# herida (se queda así mientras le falte vida): encorvada, respirando fuerte, con las espadas más bajas
P.pose('h0',lean=0.16,kneeL=0.28,kneeR=0.22,ankL=-0.24,ankR=-0.19,hipL=0.05,hipR=-0.05,swL=0.2,swR=0.15,flL=-0.8,flR=-0.7,hx=0.15)
P.pose('h1',lean=0.24,kneeL=0.32,kneeR=0.32,ankL=-0.27,ankR=-0.27,swL=0.05,swR=0.0,flL=-0.35,flR=-0.3,adL=0.2,adR=0.2,hx=0.2,hy=0.1)
job('h0','frente','h0',ground=True); atlas[24]='h0'
job('h1','frente','h1',ground=True); atlas[25]='h1'
# muerte (de perfil, cae hacia atrás)
P.pose('d0',lean=-0.45,swL=1.2,swR=1.0,flL=-0.3,flR=-0.3,adL=0.1,adR=0.1,kneeL=0.5,kneeR=0.4,hipL=-0.2,hipR=0.25,ankL=-0.3,ankR=-0.3,hx=0.5)
P.pose('d1',lean=-0.2,swL=-1.6,swR=-1.3,adL=0.2,adR=0.2,flL=-0.4,flR=-0.4,kneeL=0.7,kneeR=0.5,hipL=-0.5,hipR=-0.2,hx=0.6)
P.pose('d2',swL=-0.8,swR=-0.5,kneeL=0.5,kneeR=0.2,hipL=-0.3,hx=0.3)
P.pose('d3',swL=0.3,swR=-0.4,flL=-0.2,flR=-0.4,kneeL=0.2,kneeR=0.5,hipR=-0.35,hx=0.2)
job('d0','izq','d0',col='dolor',rot=[-0.4,0,0],ground=False,center=True); atlas[48]='d0'
job('d1','izq','d1',col='dolor',rot=[-0.95,0,0],ground=True,center=True); atlas[49]='d1'
job('d2','izq','d2',col='muerta',rot=[-1.35,0,0],ground=True,center=True); atlas[50]='d2'
job('d3','izq','d3',col='muerta',rot=[-1.5708,0,0],ground=True,center=True); atlas[51]='d3'
# tropiezo y caída
P.pose('s0',lean=0.35,swL=-1.0,swR=0.8,flL=-0.3,flR=-0.3,adL=-0.3,adR=-0.3,hipL=-0.6,kneeL=0.6,hipR=0.35,kneeR=0.2,ankL=-0.2,ankR=-0.3,hx=-0.3)
P.pose('s1',lean=0.2,swL=-2.4,swR=-1.6,adL=-0.2,adR=-0.2,flL=-0.4,flR=-0.4,hipL=-1.0,hipR=-0.4,kneeL=0.8,kneeR=0.6,hx=-0.5)
job('s0','izq','s0',col='susto',rot=[0.4,0,0]); atlas[56]='s0'
job('s1','izq','s1',col='susto',rot=[1.05,0,0],center=True); atlas[57]='s1'
json.dump(jobs,open('/tmp/claude-0/r3d/jobs.json','w'))
json.dump({str(k):v for k,v in atlas.items()},open('/tmp/claude-0/r3d/atlas.json','w'))
print(len(jobs),'trabajos')
