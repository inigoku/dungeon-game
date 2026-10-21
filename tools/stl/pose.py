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
def roty(P,Pivot,ang,w):
    dx=P[:,0]-Pivot[0]; dz=P[:,2]-Pivot[2]
    c,s=np.cos(ang*w),np.sin(ang*w)
    Q=P.copy()
    Q[:,0]=Pivot[0]+dx*c+dz*s
    Q[:,2]=Pivot[2]-dx*s+dz*c
    return Q
# tela del faldón (adorno rojo bajo la cintura), pelo y cuerpo superior
cloth_mask=(label.repeat(3)==0)&(z>8.0)&(z<28.5)
cloth_w=smooth((27.0-z)/12.0)*cloth_mask
hair_w=(tl==2)*smooth((37.0-z)/14.0)*smooth((y+4.0)/6.0)
upper_w=smooth((z-23.0)/4.0)
DEF=dict(hipL=0,hipR=0,kneeL=0,kneeR=0,ankL=0,ankR=0,swL=0,swR=0,flL=0,flR=0,adL=AD,adR=AD,lean=0.0,hx=0.0,hy=0.0)
def pose(name,**kw):
    p=dict(DEF); p.update(kw)
    P=V.copy()
    hips={'L':p['hipL'],'R':p['hipR']}
    cw=np.zeros(len(V))
    for side,sg in (('L',-1),('R',1)):
        wleg,wshin,warm,wfoot,wfore=W[side]
        sel=wleg>0
        P[sel]=rot(P[sel],np.array([sg*5.2,-1.4,3.0]),p['ank'+side],wfoot[sel])
        P[sel]=rot(P[sel],np.array([sg*5.2,-1.2,KNEE_Z]),p['knee'+side],wshin[sel])
        P[sel]=rot(P[sel],np.array([sg*5.2,-0.8,HIP_Z]),p['hip'+side],wleg[sel])
        sel=warm>0
        P[sel]=rot(P[sel],np.array([sg*11.7,-1.1,26.7]),p['fl'+side],wfore[sel])
        P[sel]=rot(P[sel],np.array([sg*8.0,-0.8,32.0]),p['sw'+side],warm[sel])
        P[sel]=roty(P[sel],np.array([sg*8.0,-0.8,32.0]),sg*p['ad'+side],warm[sel])
    # faldón: sigue a la pierna de su lado (la mitad), el centro al promedio
    mean=(hips['L']+hips['R'])/2
    b=smooth((np.abs(x)-1.0)/4.0)
    ang=0.5*(b*np.where(x<0,hips['L'],hips['R'])+(1-b)*mean)
    wl=(wleg_all:=np.maximum(W['L'][0],W['R'][0]))
    wc=cloth_w*(1-np.clip(wl,0,1))*(np.maximum(W['L'][2],W['R'][2])<0.5)
    sel=wc>0
    P[sel]=rot(P[sel],np.array([0,-0.8,HIP_Z+3]),1.0,(wc*ang)[sel])
    # pelo: se balancea desde la nuca
    sel=hair_w>0
    P[sel]=rot(P[sel],np.array([0,3.0,37.0]),p['hx'],hair_w[sel])
    P[sel]=roty(P[sel],np.array([0,3.0,37.0]),p['hy'],hair_w[sel])
    # cuerpo superior: se inclina desde la cintura (negativo = hacia atrás)
    wu=upper_w*(1-np.clip(np.maximum(W['L'][0],W['R'][0]),0,1))
    sel=wu>0
    P[sel]=rot(P[sel],np.array([0,-0.5,24.0]),p['lean'],wu[sel])
    P.astype(np.float32).tofile(f'/tmp/claude-0/r3d/pos_{name}.bin')
