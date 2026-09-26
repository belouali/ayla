# Repeint les morceaux mal colores (gris jamais peints, taches claires ou sombres) d'un personnage deja rigge,
# sans toucher a sa forme. Chaque texel fautif prend la couleur de la surface peinte la plus proche sur le corps (en 3D, meme orientation),
# puis les marges de la texture sont prolongees depuis les bords peints. Seule l'image change dans le .glb.
# Usage : python3 combler_gris.py entree.glb sortie.glb regles.json [apercu.png]
#   regles.json : liste de {"h":[h0,h1], "faux":"expression", "zone":"expression facultative"}
#   variables des expressions (tableaux numpy par texel) : r,g,b (0-255), lum, sat, h (hauteur 0-1), x (lateral), p (profondeur, >0 devant),
#   nx, ny, nz (normale de la surface),
#   cache (texel enfoui sous une autre couche du corps : en avancant le long de sa normale on retombe sur la surface)
#   "faux" designe les texels mal peints ; ils prennent la couleur des texels justes les plus proches sur le corps.
#   "ilot": [[colonne, ligne], ...] designe en bloc la piece de texture (faces reliees) qui contient ce pixel,
#   pour une piece mal projetee (couleurs etirees) reperee a l'oeil ; "faux" vaut alors vrai par defaut.
#   "masque": fichier .npy (booleens, taille de la texture) : texels choisis a la main depuis une vue rendue.
#   "source": expression facultative : ces texels ne prennent leur couleur que parmi les texels justes qui la verifient
#   (utile quand une couche du dessous perce : la peau du bras sous la manche doit prendre la couleur de la veste).
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
tri_t = np.full((Ht, Wt), -1, np.int64); TRI_V = []; nb_tri = 0
pos_t = np.zeros((Ht, Wt, 3), np.float32); nor_t = np.zeros((Ht, Wt, 3), np.float32); couvert = np.zeros((Ht, Wt), bool)
for m in J["meshes"]:
    for p in m["primitives"]:
        A = p["attributes"]; P = acces(A["POSITION"]).astype(np.float64); UV = acces(A["TEXCOORD_0"]).astype(np.float64)
        Nn = acces(A["NORMAL"]).astype(np.float64) if "NORMAL" in A else None
        I = acces(p["indices"]).reshape(-1, 3).astype(np.int64)
        TRI_V.append(I + (sum(len(x) for x in TRI_V) and 0)); base_tri = nb_tri; nb_tri += len(I)
        px = np.c_[UV[:, 0]*Wt - .5, UV[:, 1]*Ht - .5]          # glTF : v vers le bas de l'image
        for it, t in enumerate(I):
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
            couvert[yy, xx] = True; tri_t[yy, xx] = base_tri + it

# coordonnees normalisees du corps : h hauteur 0-1 (glTF : y vers le haut), x lateral, p profondeur (glTF +z)
Pc = pos_t[couvert]; y0_, y1_ = Pc[:, 1].min(), Pc[:, 1].max(); Hc = y1_ - y0_
cxz = np.median(Pc[:, [0, 2]], 0)
V = {"h": (pos_t[..., 1]-y0_)/Hc, "x": (pos_t[..., 0]-cxz[0])/Hc, "p": (pos_t[..., 2]-cxz[1])/Hc,
     "r": tex[..., 0], "g": tex[..., 1], "b": tex[..., 2]}
V["lum"] = .3*V["r"] + .59*V["g"] + .11*V["b"]; V["sat"] = tex.max(-1) - tex.min(-1)
V["nx"] = nor_t[..., 0]; V["nz"] = nor_t[..., 2]; V["ny"] = nor_t[..., 1]
gris = np.zeros_like(couvert); ciblees = []
for R in REGLES:
    zone = couvert & (V["h"] >= R["h"][0]) & (V["h"] <= R["h"][1])
    if "zone" in R: zone &= eval(R["zone"], {"np": np}, V)
    if "cache" in R.get("faux", ""):
        # on avance le long de la normale : si une autre surface du corps occupe ces points, le texel est enfoui
        if "_surf" not in V:
            ec = np.argwhere(couvert); V["_surf"] = cKDTree(pos_t[ec[:, 0], ec[:, 1]])
        ez = np.argwhere(zone); o_ = pos_t[ez[:, 0], ez[:, 1]]; d_ = nor_t[ez[:, 0], ez[:, 1]]
        portee = R.get("portee", .03)*Hc; rayon = .0045*Hc
        # cinq directions (la normale et quatre inclinees de 35 degres) : sous une fente etroite, le rayon droit
        # s'echappe mais les rayons inclines retombent sur le tissu ; enfoui si au moins trois directions touchent
        t1 = np.cross(d_, np.where(np.abs(d_[:, 1:2]) < .9, [[0, 1, 0]], [[1, 0, 0]]))
        t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9); t2 = np.cross(d_, t1)
        ca, sa = np.cos(np.radians(35)), np.sin(np.radians(35))
        dirs = [d_] + [d_*ca + t*sa*sg for t in (t1, t2) for sg in (1, -1)]
        hits = np.zeros(len(ez), np.int8)
        for dv in dirs:
            h1 = np.zeros(len(ez), bool)
            for k in np.linspace(.006*Hc, portee, 8):
                dd, _ = V["_surf"].query(o_ + dv*k, k=1, distance_upper_bound=rayon)
                h1 |= np.isfinite(dd)
            hits += h1
        touche = hits >= R.get("directions", 3)
        V["cache"] = np.zeros_like(couvert); V["cache"][ez[touche, 0], ez[touche, 1]] = True
    if "ilot" in R:
        # faces reliees par leurs sommets (dans glTF, une couture de texture separe les sommets) : une piece de texture
        TV = np.concatenate(TRI_V); par_sommet = {}
        for i_, t_ in enumerate(TV):
            for v_ in t_: par_sommet.setdefault(int(v_), []).append(i_)
        piece = set()
        for col, lig in R["ilot"]:
            t0 = int(tri_t[lig, col])
            if t0 < 0: print("ILOT pixel hors du corps", col, lig); continue
            pile = [t0]; piece.add(t0)
            while pile:
                u_ = pile.pop()
                for v_ in TV[u_]:
                    for w_ in par_sommet[int(v_)]:
                        if w_ not in piece: piece.add(w_); pile.append(w_)
        V["ilot"] = np.isin(tri_t, np.fromiter(piece, np.int64)) & couvert
        print("ILOT faces", len(piece))
    if "masque" in R:
        import os
        V["masque"] = np.load(os.path.join(os.path.dirname(os.path.abspath(sys.argv[3])), R["masque"])) & couvert
    faux = zone & (eval(R["faux"], {"np": np}, V) if "faux" in R else (V["ilot"] if "ilot" in R else V["masque"]))
    print("REGLE", R.get("nom", R.get("faux")), "texels", int(faux.sum()), f"({faux.sum()/max(zone.sum(),1):.1%} de la zone)")
    gris |= faux
    if "source" in R: ciblees.append((faux, R["source"]))
peint = couvert & ~gris
taille = np.ptp(pos_t[couvert], axis=0).max()
print("TEXELS couverts", int(couvert.sum()), "a repeindre", int(gris.sum()), f"({gris.sum()/max(couvert.sum(),1):.1%})")

import os
if os.environ.get("MARQUER"):   # diagnostic : les texels fautifs en magenta, sans repeindre
    tex[gris] = [255, 0, 255]; gris = np.zeros_like(gris); peint = couvert.copy()
# couleur de la surface peinte la plus proche (position + orientation), moyenne des 6 plus proches
k_or = .04 * taille
ep = np.argwhere(peint); pas = max(1, len(ep)//600000); ep = ep[::pas]
arbre = cKDTree(np.c_[pos_t[ep[:, 0], ep[:, 1]], nor_t[ep[:, 0], ep[:, 1]]*k_or])
eg = np.argwhere(gris)
dist, idx = arbre.query(np.c_[pos_t[eg[:, 0], eg[:, 1]], nor_t[eg[:, 0], eg[:, 1]]*k_or], k=6)
w = 1/np.maximum(dist, 1e-6); w /= w.sum(1, keepdims=True)
cols = tex[ep[idx][..., 0], ep[idx][..., 1]]
tex[eg[:, 0], eg[:, 1]] = (cols*w[..., None]).sum(1)

# regles a source imposee : on repeint ces texels une seconde fois, depuis les seuls texels justes qui conviennent
for faux_r, expr in ciblees:
    ok = peint & eval(expr, {"np": np}, V)
    es = np.argwhere(ok); es = es[::max(1, len(es)//400000)]
    if not len(es) or not faux_r.any(): continue
    a2 = cKDTree(np.c_[pos_t[es[:, 0], es[:, 1]], nor_t[es[:, 0], es[:, 1]]*k_or])
    ef = np.argwhere(faux_r)
    d2, i2 = a2.query(np.c_[pos_t[ef[:, 0], ef[:, 1]], nor_t[ef[:, 0], ef[:, 1]]*k_or], k=6)
    w2 = 1/np.maximum(d2, 1e-6); w2 /= w2.sum(1, keepdims=True)
    tex[ef[:, 0], ef[:, 1]] = (tex[es[i2][..., 0], es[i2][..., 1]]*w2[..., None]).sum(1)
    print("SOURCE", expr, "texels", len(ef))

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
