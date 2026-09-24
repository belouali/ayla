# Detecte les articulations d'un personnage debout (Z haut, face -Y), hauteur ramenee a 1.
# Ecrit un JSON de reperes et une vue de face bien eclairee pour verification.
import bpy, sys, json, os
import numpy as np
a = sys.argv[sys.argv.index("--")+1:]; SRC, OUT = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.empty(len(ob.data.vertices)*3, np.float32); ob.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
zmin = co[:, 2].min(); H = co[:, 2].max() - zmin
hi = co[co[:, 2] > zmin + 0.3*H]
cx = float(np.median(hi[:, 0])); cy = float(np.median(hi[:, 1]))
V = (co - np.array([cx, cy, zmin])) / H          # repere normalise

def tranche(z, e=0.006):
    return V[np.abs(V[:, 2] - z) < e]

def trous(xs, lo, hi_, pas=0.008):
    """intervalles vides le long de x entre lo et hi"""
    bins = np.arange(lo, hi_ + pas, pas)
    h, _ = np.histogram(xs, bins)
    return bins, h

# --- entrejambe : plus haut z ou un vide separe les deux jambes pres de x=0
entre = None
for z in np.arange(0.62, 0.10, -0.005):
    s = tranche(z); s = s[np.abs(s[:, 0]) < 0.13]
    if len(s) < 20: continue
    bins, h = trous(s[:, 0], -0.13, 0.13)
    mid = len(h)//2
    zone = h[mid-3:mid+3]
    gauche = h[:mid-3].sum(); droite = h[mid+3:].sum()
    if zone.sum() == 0 and gauche > 5 and droite > 5:
        entre = float(z); break
robe = entre is None
if robe: entre = 0.44

# --- jambes : centres a mi-cuisse et au genou
def centre_jambe(z, cote):
    s = tranche(z, 0.01); s = s[(np.abs(s[:, 0]) < 0.16)]
    s = s[s[:, 0]*cote > 0.005]
    if len(s) < 5: return [cote*0.06, 0.0]
    return [float(s[:, 0].mean()), float(s[:, 1].mean())]

hanche_z = min(entre + 0.035, 0.58)
cheville_z = 0.055
genou_z = cheville_z + 0.52*(hanche_z - cheville_z)

# --- aisselle : plus haut z ou un vide separe bras et torse
aisselle = None
for z in np.arange(0.80, 0.40, -0.005):
    s = tranche(z)
    if len(s) < 20: continue
    ok = 0
    for cote in (-1, 1):
        xs = s[:, 0]*cote
        xs = xs[xs > 0.02]
        bins, h = trous(xs, 0.02, 0.40)
        nz = np.nonzero(h)[0]
        if len(nz) < 4: continue
        # un vide d'au moins 2 cases entre deux zones pleines
        pleins = h > 0
        for i in range(1, len(pleins)-2):
            if pleins[:i].any() and not pleins[i] and not pleins[i+1] and pleins[i+2:].any():
                ok += 1; break
    if ok == 2:
        aisselle = float(z); break
if aisselle is None: aisselle = 0.62
epaule_z = aisselle + 0.075
cou_z = epaule_z + 0.045

# --- bras : grappe exterieure sous l'aisselle
def grappe_bras(z, cote):
    s = tranche(z, 0.008)
    xs = s[:, 0]*cote
    s = s[xs > 0.02]; xs = xs[xs > 0.02]
    if len(s) < 4: return None
    order = np.argsort(xs); xs = xs[order]; s = s[order]
    sauts = np.nonzero(np.diff(xs) > 0.012)[0]
    if len(sauts) == 0: return None
    ext = s[sauts[-1]+1:]
    return ext

bras = {}
for cote, nom in ((-1, "R"), (1, "L")):     # x negatif = cote droit du personnage
    pts = []
    for z in np.arange(aisselle - 0.01, 0.20, -0.01):
        g = grappe_bras(z, cote)
        if g is None or len(g) < 3: 
            if pts: break
            continue
        pts.append((float(z), float(g[:, 0].mean()), float(g[:, 1].mean()), float(g[:, 0].max()-g[:, 0].min())))
    if not pts:
        pts = [(aisselle, cote*0.15, 0.0, 0.05), (0.40, cote*0.18, 0.0, 0.05)]
    bas = pts[-1][0]
    main_bas = bas
    poignet_z = min(main_bas + 0.075, aisselle - 0.12)
    coude_z = poignet_z + 0.5*(epaule_z - poignet_z) + 0.01
    def a_z(z):
        best = min(pts, key=lambda p: abs(p[0]-z)); return [best[1], best[2]]
    ep_x = a_z(aisselle)[0] - cote*0.025
    bras[nom] = {"epaule": [ep_x, a_z(aisselle)[1], epaule_z],
                 "coude": a_z(coude_z) + [coude_z],
                 "poignet": a_z(poignet_z) + [poignet_z],
                 "main": a_z(main_bas + 0.02) + [main_bas + 0.01],
                 "trace": pts[::3]}

jambes = {}
for cote, nom in ((-1, "R"), (1, "L")):
    hx, hy = centre_jambe(hanche_z - 0.06, cote)
    kx, ky = centre_jambe(genou_z, cote)
    ax, ay = centre_jambe(cheville_z + 0.03, cote)
    s = V[(V[:, 2] < 0.05) & (V[:, 0]*cote > 0.005) & (np.abs(V[:, 0]) < 0.2)]
    toe_y = float(np.percentile(s[:, 1], 3)) if len(s) else ay - 0.08
    jambes[nom] = {"hanche": [hx, hy, hanche_z], "genou": [kx, ky, genou_z],
                   "cheville": [ax, ay, cheville_z], "orteil": [ax, toe_y, 0.015]}

tete = tranche(0.93, 0.02)
R = {"H": float(H), "centre": [cx, cy, float(zmin)], "robe": robe,
     "entrejambe": entre, "aisselle": aisselle, "cou_z": cou_z, "epaule_z": epaule_z,
     "tete_y": float(tete[:, 1].mean()) if len(tete) else 0.0,
     "bras": bras, "jambes": jambes}
json.dump(R, open(OUT + ".json", "w"), indent=1)

# vue de face eclairee
ob.location = (-cx, -cy, -zmin); bpy.ops.object.transform_apply(location=True)
ob.scale = (1/H, 1/H, 1/H); bpy.ops.object.transform_apply(scale=True)
sc = bpy.context.scene
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.2
bpy.ops.object.camera_add(location=(0, -5, 0.5), rotation=(1.5708, 0, 0)); cam = bpy.context.object
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.1; sc.camera = cam
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x = 1000; sc.render.resolution_y = 1000
sc.view_settings.view_transform = 'Standard'
sc.render.filepath = OUT + "_face.png"; bpy.ops.render.render(write_still=True)
print("REPERES", OUT, "robe" if robe else "jambes", "entrejambe", round(entre, 3), "aisselle", round(aisselle, 3))
