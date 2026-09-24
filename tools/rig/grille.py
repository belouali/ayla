# Ajoute une grille graduee : ortho_scale 1.1 centre sur (0, 0.5) -> pixel = (x+0.55)*1000/1.1
import sys
from PIL import Image, ImageDraw
for f in sys.argv[1:]:
    im=Image.open(f).convert("RGB"); d=ImageDraw.Draw(im)
    for k in range(0,101,5):
        v=k/100
        yp=int((0.55-(v-0.5))*1000/1.1); xp=int((v-0.5+0.55)*1000/1.1)
        col=(220,60,60) if k%10==0 else (120,120,200)
        d.line([(0,yp),(1000,yp)],fill=col,width=1)
        d.text((4,yp-11),f"z{v:.2f}",fill=col)
        if k<=100:
            xv=v-0.5; xp=int((xv+0.55)*1000/1.1)
            d.line([(xp,0),(xp,1000)],fill=col,width=1)
            d.text((xp+2,2),f"{xv:+.2f}",fill=col)
    im.save(f.replace(".png","_g.png"))
