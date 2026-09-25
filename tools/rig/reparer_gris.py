# Repeint les taches grises non peintes : un point gris entoure (en 3D) de surface coloree
# prend la couleur mediane de ses voisins ; les zones majoritairement grises restent intactes.
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import kdtree
a = sys.argv[sys.argv.index("--")+1:]; SRC, OUT = a[0], a[1]
RAYON = float(a[2]) if len(a) > 2 else 0.035
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
img = None
for n in me.materials[0].node_tree.nodes:
    if n.type == 'TEX_IMAGE' and n.image: img = n.image; break
W, H = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)
uvl = me.uv_layers.active.data
co = np.array([v.co[:] for v in me.vertices]); hz = co[:, 2].max() - co[:, 2].min()

# couleur echantillonnee a chaque coin de face
nL = len(me.loops)
uv = np.empty(nL*2, np.float32); uvl.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
lv = np.empty(nL, np.int32); me.loops.foreach_get("vertex_index", lv)
xi = np.clip((uv[:, 0]*W).astype(int), 0, W-1); yi = np.clip((uv[:, 1]*H).astype(int), 0, H-1)
cl = px[yi, xi, :3]
def gris(c):
    mx = c.max(-1); mn = c.min(-1); sat = (mx-mn)/np.maximum(mx, 1e-3)
    return (sat < .08) & (mx > .30) & (mx < .95)
g_l = gris(cl)
# par sommet : couleur moyenne et statut
nV = len(me.vertices)
somme = np.zeros((nV, 3)); cpt = np.zeros(nV); gcpt = np.zeros(nV)
np.add.at(somme, lv, cl); np.add.at(cpt, lv, 1); np.add.at(gcpt, lv, g_l)
cv = somme/np.maximum(cpt, 1)[:, None]; gv = gcpt/np.maximum(cpt, 1) > .5

kd = kdtree.KDTree(nV)
for i, p in enumerate(co): kd.insert(p, i)
kd.balance()
r = RAYON*hz
repar = np.zeros(nV, bool); neuve = cv.copy()
lum = cv @ np.array([.2126, .7152, .0722])
for i in range(nV):
    vois = [j for (_, j, _) in kd.find_range(co[i], r)]
    if len(vois) < 8: continue
    vois = np.array(vois)
    if gv[i] and gv[vois].mean() < .45:                    # tache grise isolee
        ok = vois[~gv[vois]]
        neuve[i] = np.median(cv[ok], axis=0); repar[i] = True; continue
    med = np.median(cv[vois], axis=0)
    ecart = np.abs(cv[i]-med).sum()
    disp = np.median(np.abs(cv[vois]-med).sum(1))
    if ecart > .28 and ecart > 3.2*disp and lum[i] < np.median(lum[vois]):   # moucheture ou couture sombre
        neuve[i] = med; repar[i] = True
print("REPARES", int(repar.sum()), "sommets aberrants (gris ou sombres) sur", nV)

# on repeint les triangles UV dont tous les coins sont a reparer
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
uvlay = bm.loops.layers.uv.active
n_f = 0
for f in bm.faces:
    vi = [l.vert.index for l in f.loops]
    if sum(repar[v] for v in vi) < 2: continue
    n_f += 1
    pts = np.array([[l[uvlay].uv.x*W, l[uvlay].uv.y*H] for l in f.loops])
    cols = np.array([neuve[v] if repar[v] else cv[v] for v in vi])
    for k in range(1, len(pts)-1):            # eventail de triangles
        tri = pts[[0, k, k+1]]; tc = cols[[0, k, k+1]]
        x0, y0 = np.floor(tri.min(0)).astype(int) - 1; x1, y1 = np.ceil(tri.max(0)).astype(int) + 1
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W-1), min(y1, H-1)
        if x1 <= x0 or y1 <= y0: continue
        X, Y = np.meshgrid(np.arange(x0, x1+1)+.5, np.arange(y0, y1+1)+.5)
        (ax, ay), (bx, by), (cx, cy) = tri
        d = (by-cy)*(ax-cx) + (cx-bx)*(ay-cy)
        if abs(d) < 1e-9: continue
        w1 = ((by-cy)*(X-cx) + (cx-bx)*(Y-cy))/d; w2 = ((cy-ay)*(X-cx) + (ax-cx)*(Y-cy))/d; w3 = 1-w1-w2
        m = (w1 > -.08) & (w2 > -.08) & (w3 > -.08)       # un peu de marge contre les coutures
        c = w1[..., None]*tc[0] + w2[..., None]*tc[1] + w3[..., None]*tc[2]
        zone = px[y0:y1+1, x0:x1+1, :3]
        zone[m] = c[m]
bm.free()
print("FACES repeintes", n_f)
img.pixels = px.ravel().tolist()
img.filepath_raw = os.path.splitext(OUT)[0] + "_tex.png"; img.file_format = 'PNG'; img.save()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_image_format='AUTO')
print("SORTIE", OUT)
