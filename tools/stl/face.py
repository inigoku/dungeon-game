"""Pinta la cara según la expresión: ojos blancos con iris marrón, boca y cejas. Uso: face.py <nombre> <ojos> <iris_dx> <iris_dz> <boca>"""
import sys
import numpy as np
t=np.load('/tmp/claude-0/stl/tri.npy'); c=t.mean(1); x,y,z=c.T
n=np.load('/tmp/claude-0/stl/normals.npy')
label=np.load('/tmp/claude-0/stl/label_base.npy')
PAL={6:(46,48,62),0:(196,32,38),1:(244,206,178),2:(22,20,26),4:(190,196,208)}
col=np.zeros((len(t),3),np.uint8)
for k,v in PAL.items(): col[label==k]=v
def paint(name,eyes,dx,dz,mouth):
    out=col.copy()
    front=(y<-5.3)&(n[:,1]<-0.1)
    for s in (-1,1):
        ex,ez=s*2.0,39.75
        if eyes=='cerrados':
            m=((x-ex)/1.1)**2+((z-ez)/0.16)**2<1
            out[m&front]=(60,34,22)
            continue
        k=1.0 if eyes=='normal' else 1.35
        white=((x-ex)/(1.25*k))**2+((z-ez)/(0.86*k))**2<1
        out[white&front]=(252,252,252)
        iris=((x-ex-dx)**2+(z-ez-dz)**2)<(0.62*k)**2
        out[iris&white&front]=(112,62,26)
        pupil=((x-ex-dx)**2+(z-ez-dz)**2)<(0.28*k)**2
        out[pupil&white&front]=(18,10,8)
        brow=((x-ex)/1.35)**2+((z-(ez+(1.35 if eyes!='cerrados' else 1.0)*k))/0.13)**2<1
        out[brow&front]=(34,20,14)
    zm=37.35
    if mouth=='cerrada': m=((x/1.35)**2+((z-zm)/0.38)**2<1); colr=(206,112,116)
    elif mouth=='sonrisa': m=((x/1.7)**2+((z-zm-0.25*(1-(x/1.7)**2))/0.5)**2<1); colr=(206,112,116)
    elif mouth=='abierta': m=((x/1.2)**2+((z-zm+0.2)/1.05)**2<1); colr=(92,20,32)
    elif mouth=='o': m=((x/0.7)**2+((z-zm)/0.7)**2<1); colr=(92,20,32)
    else: m=np.zeros(len(t),bool); colr=(0,0,0)
    out[m&front]=colr
    out.tofile(f'/tmp/claude-0/r3d/col_{name}.bin')
if __name__=='__main__':
    nm,e,dx,dz,mo=sys.argv[1:6]; paint(nm,e,float(dx),float(dz),mo)
