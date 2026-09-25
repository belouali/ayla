# Refait la surface d'un personnage genere : une seule peau etanche (revoxelisation),
# nouveau depliage UV, et transfert des couleurs de l'original par projection (bake selected-to-active).
# Supprime fentes, coques internes, eclats, et coutures blanches de l'atlas d'origine.
import bpy, bmesh, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index("--")+1:]
SRC, OUT = a[0], a[1]
VOX = float(a[2]) if len(a) > 2 else 0.0024      # en fraction de la hauteur
CIBLE = int(a[3]) if len(a) > 3 else 42000
TAILLE = int(a[4]) if len(a) > 4 else 2048

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
src = bpy.context.view_layer.objects.active; src.name = "source"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in src.data.vertices]); H = co[:, 2].max() - co[:, 2].min()

# materiau source -> emission de sa propre texture
img_src = None
for m in src.data.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: img_src = n.image; break
    if img_src: break
ms_ = bpy.data.materials.new("emi_source"); ms_.use_nodes = True; nt = ms_.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); e_ = nt.nodes.new("ShaderNodeEmission"); t_ = nt.nodes.new("ShaderNodeTexImage")
t_.image = img_src; t_.interpolation = 'Closest'
nt.links.new(t_.outputs["Color"], e_.inputs["Color"]); nt.links.new(e_.outputs["Emission"], o_.inputs["Surface"])
src.data.materials.clear(); src.data.materials.append(ms_)

# nouvelle peau
bpy.ops.object.select_all(action='DESELECT'); src.select_set(True); bpy.context.view_layer.objects.active = src
bpy.ops.object.duplicate(); peau = bpy.context.object; peau.name = "peau"
peau.data.materials.clear()
for g in list(peau.vertex_groups): peau.vertex_groups.remove(g)
while peau.data.uv_layers: peau.data.uv_layers.remove(peau.data.uv_layers[0])
peau.data.remesh_voxel_size = VOX*H
bpy.ops.object.voxel_remesh()
print("REVOXEL", len(peau.data.polygons), "faces")
if len(peau.data.polygons) > CIBLE:
    d = peau.modifiers.new("dec", "DECIMATE"); d.ratio = CIBLE/len(peau.data.polygons)
    with bpy.context.temp_override(object=peau, active_object=peau):
        bpy.ops.object.modifier_apply(modifier=d.name)
lis = peau.modifiers.new("lisse", "CORRECTIVE_SMOOTH"); lis.iterations = 4; lis.factor = .4
with bpy.context.temp_override(object=peau, active_object=peau):
    bpy.ops.object.modifier_apply(modifier=lis.name)
bpy.ops.object.shade_smooth()
print("PEAU", len(peau.data.polygons), "faces")
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(float(os.environ.get("ANGLE_UV","80"))), island_margin=float(os.environ.get("MARGE_UV","0.0015")))
bpy.ops.uv.select_all(action='SELECT')
try:
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method='ANY', scale=True, merge_overlap=False, margin_method='FRACTION', margin=0.0012, shape_method='CONCAVE')
except TypeError:
    bpy.ops.uv.pack_islands(rotate=True, margin=0.0012)
bpy.ops.object.mode_set(mode='OBJECT')
_uv = peau.data.uv_layers.active.data
_aire = 0.0
for poly in peau.data.polygons:
    pts = [_uv[li].uv for li in poly.loop_indices]
    for k in range(1, len(pts)-1):
        a_, b_, c_ = pts[0], pts[k], pts[k+1]
        _aire += abs((b_.x-a_.x)*(c_.y-a_.y)-(c_.x-a_.x)*(b_.y-a_.y))/2
print("DIAG aire UV", round(100*_aire, 1), "% ; couches", [l.name for l in peau.data.uv_layers], "active rendu", [l.name for l in peau.data.uv_layers if l.active_render])

img = bpy.data.images.new("peau_tex", TAILLE, TAILLE)
mp = bpy.data.materials.new("peau"); mp.use_nodes = True
tn = mp.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img; mp.node_tree.nodes.active = tn
peau.data.materials.append(mp)

sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
bk = sc.render.bake
bk.use_selected_to_active = True; bk.cage_extrusion = .012*H; bk.max_ray_distance = .03*H; bk.margin = 0
bpy.ops.object.select_all(action='DESELECT'); src.select_set(True); peau.select_set(True); bpy.context.view_layer.objects.active = peau
bpy.ops.object.bake(type='EMIT')
px = np.array(img.pixels[:], dtype=np.float32).reshape(TAILLE, TAILLE, 4)
print("DIAG source", img_src.name if img_src else None, img_src.size[:] if img_src else None, "non noir", round(100*float((px[...,:3].sum(2)>.003).mean()),1), "%")

# couverture de la nouvelle peau (ce que les UV occupent)
bk.use_selected_to_active = False
cov = bpy.data.images.new("cov", TAILLE, TAILLE)
mc = bpy.data.materials.new("cov"); mc.use_nodes = True; ntc = mc.node_tree; ntc.nodes.clear()
oc = ntc.nodes.new("ShaderNodeOutputMaterial"); ec = ntc.nodes.new("ShaderNodeEmission"); ec.inputs["Color"].default_value = (1, 1, 1, 1)
ntc.links.new(ec.outputs["Emission"], oc.inputs["Surface"]); tc = ntc.nodes.new("ShaderNodeTexImage"); tc.image = cov; ntc.nodes.active = tc
peau.data.materials.clear(); peau.data.materials.append(mc)
bpy.ops.object.select_all(action='DESELECT'); peau.select_set(True); bpy.context.view_layer.objects.active = peau
bpy.ops.object.bake(type='EMIT')
w = (np.array(cov.pixels[:], dtype=np.float32).reshape(TAILLE, TAILLE, 4)[..., 0] > .5).astype(np.float32)
print("DIAG couverture UV", round(100*float(w.mean()),1), "%")
# les texels ou le rayon n'a rien trouve (noir pur) ne comptent pas
w *= (px[..., :3].sum(2) > .003)

def flou(a, n=1):
    for _ in range(n):
        p = np.pad(a, ((1,1),(1,1),(0,0)), mode='edge')
        a = (p[:-2,1:-1]+p[2:,1:-1]+p[1:-1,:-2]+p[1:-1,2:]+2*p[1:-1,1:-1])/6
    return a
def diffuse(rgb, w):
    def bas(c, p): return (c[0::2,0::2]+c[1::2,0::2]+c[0::2,1::2]+c[1::2,1::2], p[0::2,0::2]+p[1::2,0::2]+p[0::2,1::2]+p[1::2,1::2])
    pyr = [(rgb*w[..., None], w)]
    while pyr[-1][1].shape[0] > 8: pyr.append(bas(*pyr[-1]))
    haut = None
    for c, p in reversed(pyr):
        base = np.where(p[..., None] > 1e-5, c/np.maximum(p, 1e-5)[..., None], 0.)
        if haut is not None:
            gros = flou(np.repeat(np.repeat(haut, 2, 0), 2, 1)[:base.shape[0], :base.shape[1]], 2)
            base = np.where(p[..., None] > 1e-5, base, gros)
        haut = base
    return np.where(w[..., None] > .5, rgb, flou(haut, 1))
px[..., :3] = diffuse(px[..., :3], w); px[..., 3] = 1
img.pixels = px.ravel().tolist()
img.filepath_raw = os.path.splitext(OUT)[0] + "_tex.png"; img.file_format = 'PNG'; img.save()
print("COUVERT", round(100*float(w.mean()), 1), "pour cent de l'atlas")

fin = bpy.data.materials.new("perso"); fin.use_nodes = True
b = fin.node_tree.nodes["Principled BSDF"]; tf = fin.node_tree.nodes.new("ShaderNodeTexImage"); tf.image = img
fin.node_tree.links.new(tf.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .88
peau.data.materials.clear(); peau.data.materials.append(fin)
bpy.data.objects.remove(src, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT'); peau.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_image_format='AUTO')
print("SORTIE", OUT)
