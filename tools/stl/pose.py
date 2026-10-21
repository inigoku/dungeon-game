"""Mueve piernas y brazos del modelo: pose.py <nombre> <cadera_izq> <cadera_der> <rodilla_izq> <rodilla_der> <brazo_izq> <brazo_der> (radianes, giro sobre el eje x)"""
import sys
import numpy as np
t=np.load('/tmp/claude-0/stl/tri.npy').astype(np.float64)  # N,3,3
label=np.load('/tmp/claude-0/stl/label_base.npy')
N=len(t); V=t.reshape(-1,3); x,y,z=V.T
tl=np.repeat(label,3)
def clamp01(a): return np.clip(a,0,1)
def smooth(a): a=clamp01(a); return a*a*(3-2*a)
AD=0.38
HIP_Z=21.0; KNEE_Z=10.8
W={}
for side,sg in (('L',-1),('R',1)):
    # la bota sobresale por delante: elipse más ancha a ras de suelo
    low=z<8.5
    d=np.sqrt(((np.abs(x)-5.2)/4.6)**2+((y-np.where(low,-2.5,-0.8))/np.where(low,7.0,4.4))**2)
    tube=smooth((1.0-d)/0.25)*(np.sign(x)==sg)
    wleg=tube*smooth((25.0-z)/6.0)
    wshin=smooth((12.6-z)/3.0)
    # brazo: cápsula del hombro a la mano
    S=np.array([sg*8.0,-0.8,32.0]); H=np.array([sg*15.5,-1.5,21.5])
    seg=H-S; L2=seg@seg
    tt=clamp01(((V-S)@seg)/L2)
    proj=S+tt[:,None]*seg
    dist=np.linalg.norm(V-proj,axis=1)
    warm=smooth((3.4-dist)/0.8)*smooth((tt-0.08)/0.25)*(np.sign(x)==sg)
    # hojas de las espadas (delante de la mano) y manos van con el brazo
    blade=(tl==4)&(np.sign(x)==sg)&(np.abs(x)>9)
    hand=(np.abs(x)>13.0)&(z>17.5)&(z<25.5)&(y>-5.5)&(y<4.0)&(np.sign(x)==sg)&(tl!=2)
    warm=np.maximum(warm,np.maximum(blade,hand).astype(float))
    warm=np.where(tl==2,0.0,warm)
    wleg=np.where(warm>0.5,0.0,wleg)
    wfoot=smooth((4.8-z)/1.6)
    wfore=np.where((blade|hand),1.0,smooth((tt-0.45)/0.2))*(warm>0)
    W[side]=(wleg,wshin,warm,wfoot,wfore)
def rot(P,Pivot,ang,w):
    dy=P[:,1]-Pivot[1]; dz=P[:,2]-Pivot[2]
    c,s=np.cos(ang*w),np.sin(ang*w)
    Q=P.copy()
    Q[:,1]=Pivot[1]+dy*c-dz*s
    Q[:,2]=Pivot[2]+dy*s+dz*c
    return Q
def pose(name,hipL,hipR,kneeL,kneeR,ankL,ankR,swL,swR,flL,flR):
    P=V.copy()
    for side,sg,hip,knee,ank,sw,fl in (('L',-1,hipL,kneeL,ankL,swL,flL),('R',1,hipR,kneeR,ankR,swR,flR)):
        wleg,wshin,warm,wfoot,wfore=W[side]
        sel=wleg>0
        P[sel]=rot(P[sel],np.array([sg*5.2,-1.4,3.0]),ank,(wfoot)[sel])
        P[sel]=rot(P[sel],np.array([sg*5.2,-1.2,KNEE_Z]),knee,(wshin)[sel])
        P[sel]=rot(P[sel],np.array([sg*5.2,-0.8,HIP_Z]),hip,wleg[sel])
        sel=warm>0
        P[sel]=rot(P[sel],np.array([sg*11.7,-1.1,26.7]),fl,wfore[sel])
        P[sel]=rot(P[sel],np.array([sg*8.0,-0.8,32.0]),sw,warm[sel])
        # los brazos pegados al cuerpo (en la T original parecen de muñeca)
        Q=P[sel]; w=warm[sel]; piv=np.array([sg*8.0,-0.8,32.0]); a=sg*AD*w
        dx=Q[:,0]-piv[0]; dz=Q[:,2]-piv[2]
        Q[:,0]=piv[0]+dx*np.cos(a)+dz*np.sin(a); Q[:,2]=piv[2]-dx*np.sin(a)+dz*np.cos(a)
        P[sel]=Q
    P.astype(np.float32).tofile(f'/tmp/claude-0/r3d/pos_{name}.bin')
def walk_params(phi,A=0.5,K=0.95,B=0.42):
    import math
    s,c=math.sin(phi),math.cos(phi)
    hipR,hipL=-A*s,A*s
    kneeR=K*max(0,c)+0.12; kneeL=K*max(0,-c)+0.12
    # pie plano en el suelo; al despegar la punta baja un poco
    ankR=-(hipR+kneeR)*0.85+0.25*max(0,hipR); ankL=-(hipL+kneeL)*0.85+0.25*max(0,hipL)
    swR,swL=B*s,-B*s
    flR=-0.35-0.3*max(0,-swR/B); flL=-0.35-0.3*max(0,-swL/B)
    return hipL,hipR,kneeL,kneeR,ankL,ankR,swL,swR,flL,flR
if __name__=='__main__':
    import math
    for i in range(8): pose(f'w{i}',*walk_params(i*math.pi/4))
    pose('idle',0.0,0.0,0.1,0.1,-0.09,-0.09,0.12,0.12,-0.55,-0.55)
