import numpy as np
t=np.load('/tmp/claude-0/stl/tri.npy'); c=t.mean(1)
e1=t[:,1]-t[:,0]; e2=t[:,2]-t[:,0]
n=np.cross(e1,e2); n/= (np.linalg.norm(n,axis=1,keepdims=True)+1e-9)
x,y,z=c[:,0],c[:,1],c[:,2]
N=len(t)
RED=(196,32,38); SKIN=(244,206,178); HAIR=(22,20,26); STEEL=(190,196,208); BROWN=(104,58,26); LIPS=(206,112,116)
L={'armadura':6,'ropa':0,'piel':1,'pelo':2,'ojo':3,'acero':4,'labio':5}
label=np.zeros(N,int)
helmet=(z>=40.2)&(np.abs(x)<9.5)&(y>-9.5)&(y<10)
# pelo: la masa de detrás y los mechones que enmarcan la cara
hair=(z>22)&(z<46)&(y>3.2)&~helmet
hair|=(z>29.0)&(z<40.2)&(np.abs(x)>3.7)&(np.abs(x)<15)&(y>-14)&(y<=3.2)
# los brazos (hombro-mano) no son pelo
arm=(z<34.5)&(np.abs(x)>9.0)&(y>-4.5)&(y<3.5)&(z>17)
hair&=~arm
label[hair]=L['pelo']
# acero: hojas de las espadas (delante de las manos)
blade=(np.abs(x)>13.5)&(z>17)&(z<25)&(y<-4.0)
label[blade]=L['acero']
# piel: cara, cuello y manos
face=(z>35.6)&(z<41.8)&(np.abs(x)<3.8)&(y<-5.3)&(n[:,1]<-0.1)
neck=(z>33.4)&(z<36.0)&(np.abs(x)<3.0)&(y<-1.0)&(y>-6.5)
hands=(np.abs(x)>14.0)&(z>18.5)&(z<24.5)&(y>-4.0)&(y<3.5)
label[face|neck|hands]=L['piel']
# mechones que caen junto a la mandíbula: lo que quede sin pintar ahí es pelo
lock=(label==L['ropa'])&(z>33.0)&(z<40.2)&(np.abs(x)<6.0)&(y<-1.0)
label[lock]=L['pelo']
# armadura oscura con adornos rojos: plumas y banda del casco, y la tela (faldón y capa)
base=label==L['ropa']
label[base]=L['armadura']
deco=np.zeros(N,bool)
deco|=((z>=40.2)&(z<43.0)&helmet)|((z>46.0)&((y>3.0)|(np.abs(x)>7.0)|(z>49.0)))
leg=((np.abs(x)-5.2)/4.3)**2+((y+0.8)/4.2)**2<1.0
arm=(np.abs(x)>5.8)&(z>22)&(z<31)&(y>-4.5)&(y<3.5)
deco|=(z>9.0)&(z<24.0)&~leg&~arm
deco|=(z>=24.0)&(z<28.5)&~arm
label[base&deco]=L['ropa']
np.save('/tmp/claude-0/stl/label.npy',label)
np.save('/tmp/claude-0/stl/label_base.npy',label)
np.save('/tmp/claude-0/stl/normals.npy',n)
print({k:int((label==v).sum()) for k,v in L.items()})
