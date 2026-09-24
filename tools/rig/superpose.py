# Dessine le squelette detecte sur la vue de face.
import sys, json
from PIL import Image, ImageDraw
def px(x, z): return ((x+0.55)*1000/1.1, (0.55-(z-0.5))*1000/1.1)
for base in sys.argv[1:]:
    R = json.load(open(base+".json")); im = Image.open(base+"_face.png").convert("RGB"); d = ImageDraw.Draw(im)
    def seg(a, b, c): d.line([px(a[0], a[-1]), px(b[0], b[-1])], fill=c, width=5)
    def pt(a, c): x, y = px(a[0], a[-1]); d.ellipse([x-8, y-8, x+8, y+8], fill=c)
    cou = [0, R["cou_z"]]; bassin = [0, R["entrejambe"]+0.05]
    seg(bassin, cou, (255, 200, 0)); seg(cou, [0, 0.99], (255, 200, 0))
    for n in ("R", "L"):
        b = R["bras"][n]; j = R["jambes"][n]
        seg(cou, b["epaule"], (0, 200, 255)); seg(b["epaule"], b["coude"], (0, 200, 255))
        seg(b["coude"], b["poignet"], (0, 120, 255)); seg(b["poignet"], b["main"], (0, 60, 255))
        seg(bassin, j["hanche"], (255, 0, 120)); seg(j["hanche"], j["genou"], (255, 0, 120)); seg(j["genou"], j["cheville"], (200, 0, 200))
        for k in b.values():
            if isinstance(k[0], (int, float)): pt(k, (255, 255, 255))
        for k in j.values(): pt(k, (255, 255, 255))
        for t in b["trace"]: x, y = px(t[1], t[0]); d.ellipse([x-3, y-3, x+3, y+3], fill=(0, 255, 0))
    im = im.resize((600, 600)); im.save(base+"_sq.png")
