# Repeint les morceaux mal colores (gris jamais peints, taches claires ou sombres) d'un personnage deja rigge,
# sans toucher a sa forme. Chaque texel fautif prend la couleur de la surface peinte la plus proche sur le corps (en 3D, meme orientation),
# puis les marges de la texture sont prolongees depuis les bords peints. Seule l'image change dans le .glb.
# Usage : python3 combler_gris.py entree.glb sortie.glb regles.json [apercu.png]
#   regles.json : liste de {"h":[h0,h1], "faux":"expression", "zone":"expression facultative"}
#   variables des expressions (tableaux numpy par texel) : r,g,b (0-255), lum, sat, h (hauteur 0-1), x (lateral), p (profondeur, >0 devant)
#   "faux" designe les texels mal peints ; ils prennent la couleur des texels justes les plus proches sur le corps.
import sys, json, struct, io
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage

SRC, OUT = sys.argv[1], sys.argv[2]
REGLES = json.load(open(sys.argv[3]))
APERCU = sys.argv[4] if len(sys.argv) > 4 else None

b = open(SRC, "rb").read()
lj = struct.unpack("<I", b[12:16])[0]; J = json.loads(b[20:20+lj])
o = 20 + lj; lb = struct.unpack("<I", b[o:o+4])[0]; BIN = b[o+8:o+8+lb]

TYP = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NB = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
def acces(i):
    a = J["accessors"][i]; bv = J["bufferViews"][a["bufferView"]]
    dt = TYP[a["componentType"]]; n = NB[a["type"]]
    deb = bv.get("byteOffset", 0) + a.get("byteOffset", 0); pas = bv.get("byteStride", 0)
    if pas and pas != n*np.dtype(dt).itemsize:
        brut = np.frombuffer(BIN, np.uint8, count=a["count"]*pas, offset=deb).reshape(-1, pas)
        return brut[:, :n*np.dtype(dt).itemsize].copy().view(dt).reshape(a["count"], n)
    return np.frombuffer(BIN, dt, count=a["count"]*n, offset=deb).reshape(a["count"], n)

# image de base (une seule texture par personnage dans notre chaine)
img_i = J["textures"][J["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
im = J["images"][img_i]; bvi = im["bufferView"]; bv = J["bufferViews"][bvi]
data = BIN[bv.get("byteOffset", 0):bv.get("byteOffset", 0)+bv["byteLength"]]
tex = np.array(Image.open(io.BytesIO(data)).convert("RGB")).astype(np.float32)
Ht, Wt = tex.shape[:2]

# position 3D et normale de chaque texel couvert
pos_t = np.zeros((Ht, Wt, 3), np.float32); nor_t = np.zeros((Ht, Wt, 3), np.float32); couvert = np.zeros((Ht, Wt), bool)
for m in J["meshes"]:
    for p in m["primitives"]:
        A = p["attributes"]; P = acces(A["POSITION"]).astype(np.float64); UV = acces(A["TEXCOORD_0"]).astype(np.float64)
        Nn = acces(A["NORMAL"]).astype(np.float64) if "NORMAL" in A else None
        I = acces(p["indices"]).reshape(-1, 3).astype(np.int64)
        px = np.c_[UV[:, 0]*Wt - .5, UV[:, 1]*Ht - .5]          # glTF : v vers le bas de l'image
        for t in I:
            a_, b_, c_ = px[t[0]], px[t[1]], px[t[2]]
            x0 = max(int(np.floor(min(a_[0], b_[0], c_[0]))), 0); x1 = min(int(np.ceil(max(a_[0], b_[0], c_[0]))), Wt-1)
            y0 = max(int(np.floor(min(a_[1], b_[1], c_[1]))), 0); y1 = min(int(np.ceil(max(a_[1], b_[1], c_[1]))), Ht-1)
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1+1), np.arange(y0, y1+1))
            d = (b_[1]-c_[1])*(a_[0]-c_[0]) + (c_[0]-b_[0])*(a_[1]-c_[1])
            if abs(d) < 1e-12: continue
            l1 = ((b_[1]-c_[1])*(gx-c_[0]) + (c_[0]-b_[0])*(gy-c_[1]))/d
            l2 = ((c_[1]-a_[1])*(gx-c_[0]) + (a_[0]-c_[0])*(gy-c_[1]))/d; l3 = 1-l1-l2
            ins = (l1 >= -.01) & (l2 >= -.01) & (l3 >= -.01)
            if not ins.any(): continue
            yy, xx = gy[ins], gx[ins]; w = np.stack([l1[ins], l2[ins], l3[ins]], 1)
            pos_t[yy, xx] = w @ P[t]
            nn = w @ Nn[t] if Nn is not None else np.tile(np.cross(P[t[1]]-P[t[0]], P[t[2]]-P[t[0]]), (len(yy), 1))
            nor_t[yy, xx] = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-9)
            couvert[yy, xx] = True

# coordonnees normalisees du corps : h hauteur 0-1 (glTF : y vers le haut), x lateral, p profondeur (glTF +z)
Pc = pos_t[couvert]; y0_, y1_ = Pc[:, 1].min(), Pc[:, 1].max(); Hc = y1_ - y0_
cxz = np.median(Pc[:, [0, 2]], 0)
V = {"h": (pos_t[..., 1]-y0_)/Hc, "x": (pos_t[..., 0]-cxz[0])/Hc, "p": (pos_t[..., 2]-cxz[1])/Hc,
     "r": tex[..., 0], "g": tex[..., 1], "b": tex[..., 2]}
V["lum"] = .3*V["r"] + .59*V["g"] + .11*V["b"]; V["sat"] = tex.max(-1) - tex.min(-1)
gris = np.zeros_like(couvert)
for R in REGLES:
    zone = couvert & (V["h"] >= R["h"][0]) & (V["h"] <= R["h"][1])
    if "zone" in R: zone &= eval(R["zone"], {"np": np}, V)
    faux = zone & eval(R["faux"], {"np": np}, V)
    print("REGLE", R.get("nom", R["faux"]), "texels", int(faux.sum()), f"({faux.sum()/max(zone.sum(),1):.1%} de la zone)")
    gris |= faux
peint = couvert & ~gris
taille = np.ptp(pos_t[couvert], axis=0).max()
print("TEXELS couverts", int(couvert.sum()), "a repeindre", int(gris.sum()), f"({gris.sum()/max(couvert.sum(),1):.1%})")

# couleur de la surface peinte la plus proche (position + orientation), moyenne des 6 plus proches
k_or = .04 * taille
ep = np.argwhere(peint); pas = max(1, len(ep)//600000); ep = ep[::pas]
arbre = cKDTree(np.c_[pos_t[ep[:, 0], ep[:, 1]], nor_t[ep[:, 0], ep[:, 1]]*k_or])
eg = np.argwhere(gris)
dist, idx = arbre.query(np.c_[pos_t[eg[:, 0], eg[:, 1]], nor_t[eg[:, 0], eg[:, 1]]*k_or], k=6)
w = 1/np.maximum(dist, 1e-6); w /= w.sum(1, keepdims=True)
cols = tex[ep[idx][..., 0], ep[idx][..., 1]]
tex[eg[:, 0], eg[:, 1]] = (cols*w[..., None]).sum(1)

# marges : chaque texel hors du corps prend la couleur du texel couvert le plus proche (plus de fuite grise aux coutures)
_, (iy, ix) = ndimage.distance_transform_edt(~couvert, return_indices=True)
tex[~couvert] = tex[iy[~couvert], ix[~couvert]]

sortie = Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8))
tampon = io.BytesIO()
fmt = "JPEG" if im.get("mimeType", "image/jpeg") == "image/jpeg" else "PNG"
sortie.save(tampon, fmt, quality=92) if fmt == "JPEG" else sortie.save(tampon, fmt)
if APERCU:
    av = np.array(Image.open(io.BytesIO(data)).convert("RGB")); ap = np.array(sortie)
    Image.fromarray(np.concatenate([av, ap], 1)).resize((2048, 1024)).save(APERCU)

# reecriture du .glb : seule la vue de l'image change, les autres sont recalees
vues = []
for i, v in enumerate(J["bufferViews"]):
    vues.append(tampon.getvalue() if i == bvi else BIN[v.get("byteOffset", 0):v.get("byteOffset", 0)+v["byteLength"]])
neuf = bytearray()
for i, (v, d) in enumerate(zip(J["bufferViews"], vues)):
    while len(neuf) % 4: neuf += b"\0"
    v["byteOffset"] = len(neuf); v["byteLength"] = len(d); neuf += d
while len(neuf) % 4: neuf += b"\0"
J["buffers"][0]["byteLength"] = len(neuf)
js = json.dumps(J, separators=(",", ":")).encode()
while len(js) % 4: js += b" "
glb = struct.pack("<III", 0x46546C67, 2, 12+8+len(js)+8+len(neuf)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(neuf), 0x004E4942) + bytes(neuf)
open(OUT, "wb").write(glb)
print("COMBLE", OUT, len(glb)//1024, "Ko")
