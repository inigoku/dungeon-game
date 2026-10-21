"""Mueve piernas y brazos del modelo: pose.py <nombre> <cadera_izq> <cadera_der> <rodilla_izq> <rodilla_der> <brazo_izq> <brazo_der> (radianes, giro sobre el eje x)"""
import sys
import numpy as np
t=np.load('/tmp/claude-0/stl/tri.npy').astype(np.float64)  # N,3,3
label=np.load('/tmp/claude-0/stl/label_base.npy')
N=len(t); V=t.reshape(-1,3); x,y,z=V.T
tl=np.repeat(label,3)
def clamp01(a): return np.clip(a,0,1)
def smooth(a): a=clamp01(a); return a*a*(3-2*a)
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
    W[side]=(wleg,wshin,warm)
def rot(P,Pivot,ang,w):
    dy=P[:,1]-Pivot[1]; dz=P[:,2]-Pivot[2]
    c,s=np.cos(ang*w),np.sin(ang*w)
    Q=P.copy()
    Q[:,1]=Pivot[1]+dy*c-dz*s
    Q[:,2]=Pivot[2]+dy*s+dz*c
    return Q
def pose(name,legL,legR,kneeL,kneeR,armL,armR):
    P=V.copy()
    for side,sg,hip,knee,arm in (('L',-1,legL,kneeL,armL),('R',1,legR,kneeR,armR)):
        wleg,wshin,warm=W[side]
        # la rodilla gira solo la parte baja de la pierna; luego toda la pierna gira en la cadera
        sel=wleg>0
        P[sel]=rot(P[sel],np.array([sg*5.2,-1.2,KNEE_Z]),knee,(wshin*np.ones_like(wleg))[sel])
        P[sel]=rot(P[sel],np.array([sg*5.2,-0.8,HIP_Z]),hip,wleg[sel])
        sel=warm>0
        P[sel]=rot(P[sel],np.array([sg*8.0,-0.8,32.0]),arm,warm[sel])
    P.astype(np.float32).tofile(f'/tmp/claude-0/r3d/pos_{name}.bin')
if __name__=='__main__':
    a=sys.argv; pose(a[1],*[float(v) for v in a[2:8]])
