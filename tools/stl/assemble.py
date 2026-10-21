import math
from PIL import Image, ImageDraw
O='/tmp/claude-0/stl/out/'
def load(n): return Image.open(O+n+'.png').convert('RGBA')
atlas=Image.new('RGBA',(1024,1024),(0,0,0,0))
for i in [0,1,2,12,17,20,24,25,48,49,50,51,56,57]:
    f=load(f'a{i}').resize((128,128),Image.LANCZOS)
    r,c=divmod(i,8); atlas.alpha_composite(f,(c*128,r*128))
atlas.save('/tmp/claude-0/stl/atlas_duelista.png')
strip=Image.new('RGBA',(2048,256),(0,0,0,0))
for i in range(8):
    f=load(f'c{i}').resize((256,256),Image.LANCZOS)
    if i==4:
        d=ImageDraw.Draw(f)
        for cx,cy,r in [(58,70,22),(200,40,16),(214,110,12),(40,150,12)]:
            pts=[(cx,cy-r),(cx+r*.22,cy-r*.22),(cx+r,cy),(cx+r*.22,cy+r*.22),(cx,cy+r),(cx-r*.22,cy+r*.22),(cx-r,cy),(cx-r*.22,cy-r*.22)]
            d.polygon(pts,fill=(255,236,140,255))
    strip.alpha_composite(f,(i*256,0))
strip.save('/tmp/claude-0/stl/caras_duelista.png')
p=load('retrato'); w=round(640*97/134)
p=p.crop(((640-w)//2,0,(640-w)//2+w,640)) if False else p
# recorte 97:134 centrado en la cara
h=640; w=round(h*97/134); x0=(640-w)//2
p=p.crop((x0,0,x0+w,h)).resize((97,134),Image.LANCZOS)
p.save('/tmp/claude-0/stl/retrato_duelista.png')
# hoja de contacto
sheet=Image.new('RGB',(1024+2048//2+0,1024),(90,90,100))
sheet.paste(atlas,(0,0),atlas)
sheet.paste(strip.resize((1024,128)),(0,0),strip.resize((1024,128))) if False else None
sheet.save('/tmp/claude-0/stl/contact.png')
cs=Image.new('RGB',(2048,256+134),(90,90,100)); cs.paste(strip,(0,0),strip); cs.paste(p,(0,260),p); cs.save('/tmp/claude-0/stl/contact2.png')
