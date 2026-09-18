# Nettoyage + coloration par projection frontale de la planche de reference.
import bpy, bmesh, sys, os, math
a = sys.argv[sys.argv.index("--")+1:]
SRC, REF, OUT, CIBLE, TAILLE = a[0], a[1], a[2], int(a[3]), int(a[4])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active; ob.name = "perso"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data; n0 = len(me.polygons)

# --- socle : Hunyuan sort en Z haut, sujet de face vers -Y ------------------
bm = bmesh.new(); bm.from_mesh(me)
zs = [v.co.z for v in bm.verts]
zmin, zmax = min(zs), max(zs); h = zmax - zmin
haut = [v.co for v in bm.verts if v.co.z > zmin + 0.30*h]
cx = sorted(c.x for c in haut)[len(haut)//2]
cy = sorted(c.y for c in haut)[len(haut)//2]
def loin(f, k):
    c = f.calc_center_median()
    return math.hypot(c.x-cx, c.y-cy) > k*h
sup = [f for f in bm.faces
       if (max(v.co.z for v in f.verts) < zmin + 0.05*h and loin(f, 0.20))
       or (os.environ.get('DALLE','1')=='1' and max(v.co.z for v in f.verts) < zmin + 0.035*h
           and abs(f.normal.z) > 0.80 and loin(f, 0.11))]
if sup: bmesh.ops.delete(bm, geom=sup, context='FACES')
bm.to_mesh(me); bm.free()
me.update()
# on ne garde que le plus gros morceau
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')
morceaux = [o for o in bpy.context.selected_objects if o.type == 'MESH']
morceaux.sort(key=lambda o: len(o.data.polygons), reverse=True)
seuil = max(24, int(0.02 * len(morceaux[0].data.polygons)))
gardes = [o for o in morceaux if len(o.data.polygons) >= seuil]
for o in morceaux:
    if o not in gardes: bpy.data.objects.remove(o, do_unlink=True)
# normales vers l'exterieur, piece par piece
for o in gardes:
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bv = bmesh.new(); bv.from_mesh(o.data); vol = bv.calc_volume(signed=True); bv.free()
    if vol < 0:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
for o in gardes: o.select_set(True)
bpy.context.view_layer.objects.active = gardes[0]
if len(gardes) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active; ob.name = "perso"
me = ob.data
print("MORCEAUX", len(morceaux), "gardes", len(gardes))

bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0006)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.customdata_custom_splitnormals_clear()
# volume signe negatif : les normales regardent vers l'interieur

if len(me.polygons) > CIBLE:
    d = ob.modifiers.new("dec", "DECIMATE"); d.ratio = CIBLE/len(me.polygons)
    bpy.ops.object.modifier_apply(modifier=d.name)
bpy.ops.object.shade_smooth()

me.uv_layers.new(name="bake"); me.uv_layers.active = me.uv_layers["bake"]
me.uv_layers["bake"].active_render = True
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')

# --- cadre du maillage apres nettoyage -------------------------------------
import numpy as _np
_co = _np.empty(len(me.vertices)*3, dtype=_np.float32)
me.vertices.foreach_get("co", _co); _co = _co.reshape(-1, 3)
bnds = [(float(_np.percentile(_co[:, i], 0.15)), float(_np.percentile(_co[:, i], 99.85))) for i in range(3)]
zs = _co[:, 2]
print("BOITE", [(round(a,3), round(b,3)) for a, b in bnds])
UP, LAR, DEP = 2, 0, 1          # convention Hunyuan apres import glTF
# sens de la vue : les pieds pointent vers l'avant
zmin2, zmax2 = min(zs), max(zs)
pieds = [v.co.y for v in me.vertices if v.co.z < zmin2 + 0.06*(zmax2-zmin2)]
corps = sum(v.co.y for v in me.vertices)/len(me.vertices)
SENS = float(os.environ.get("SENS", "-1"))
print("SENS", "face vers -Y" if SENS < 0 else "face vers +Y")
# la planche est recadree au plus juste sur le sujet : les deux boites coincident

ref = bpy.data.images.load(os.path.abspath(REF))
mat = bpy.data.materials.new("proj"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
emi = nt.nodes.new("ShaderNodeEmission")
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
axn = ["X","Y","Z"]

def maprange(inp, fmin, fmax):
    m = nt.nodes.new("ShaderNodeMapRange")
    m.inputs[1].default_value = fmin; m.inputs[2].default_value = fmax
    m.inputs[3].default_value = 0.0;  m.inputs[4].default_value = 1.0
    m.clamp = True
    nt.links.new(inp, m.inputs[0]); return m.outputs[0]

u = maprange(sep.outputs[axn[LAR]], bnds[LAR][0], bnds[LAR][1])
if SENS > 0:
    _m = nt.nodes.new("ShaderNodeMath"); _m.operation = 'SUBTRACT'
    _m.inputs[0].default_value = 1.0; nt.links.new(u, _m.inputs[1]); u = _m.outputs[0]
v = maprange(sep.outputs[axn[UP]], bnds[UP][0], bnds[UP][1])
uinv = nt.nodes.new("ShaderNodeMath"); uinv.operation = 'SUBTRACT'
uinv.inputs[0].default_value = 1.0; nt.links.new(u, uinv.inputs[1])

def coords(uu):
    c = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(uu, c.inputs[0]); nt.links.new(v, c.inputs[1]); return c.outputs[0]

tf = nt.nodes.new("ShaderNodeTexImage"); tf.image = ref; tf.extension = 'EXTEND'
nt.links.new(coords(u), tf.inputs["Vector"])
nt.links.new(tf.outputs["Color"], emi.inputs["Color"])
nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
me.materials.clear(); me.materials.append(mat)

# visibilite : la planche est une vue de face, donc normale vers -Y
nsep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Normal"], nsep.inputs["Vector"])
vis = nt.nodes.new("ShaderNodeMath"); vis.operation = 'MULTIPLY_ADD'
vis.inputs[1].default_value = 7.0 * SENS; vis.inputs[2].default_value = -0.9
vis.use_clamp = True
nt.links.new(nsep.outputs["Y"], vis.inputs[0])

import numpy as np
img = bpy.data.images.new("tex", TAILLE, TAILLE)
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img; nt.nodes.active = tn
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 2
sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False
sc.render.bake.margin = 10
bpy.ops.object.bake(type='EMIT')
coul = np.array(img.pixels[:], dtype=np.float32).reshape(TAILLE, TAILLE, 4)

# seconde cuisson : ou la projection est valable
mimg = bpy.data.images.new("msk", TAILLE, TAILLE)
nt.links.new(vis.outputs[0], emi.inputs["Color"])
tn.image = mimg; nt.nodes.active = tn
bpy.ops.object.bake(type='EMIT')
msk = np.array(mimg.pixels[:], dtype=np.float32).reshape(TAILLE, TAILLE, 4)[..., 0]
w = (msk > 0.35).astype(np.float32)

# diffusion pyramidale lissee : les zones non vues heritent du voisinage
def flou(a, n=1):
    for _ in range(n):
        p = np.pad(a, ((1,1),(1,1),(0,0)), mode='edge')
        a = (p[:-2,1:-1]+p[2:,1:-1]+p[1:-1,:-2]+p[1:-1,2:]+2.0*p[1:-1,1:-1])/6.0
    return a
def descend(c, p):
    cs = (c[0::2,0::2]+c[1::2,0::2]+c[0::2,1::2]+c[1::2,1::2])
    ps = (p[0::2,0::2]+p[1::2,0::2]+p[0::2,1::2]+p[1::2,1::2])
    return cs, ps
pyr = [(coul[..., :3]*w[..., None], w)]
while pyr[-1][1].shape[0] > 8:
    pyr.append(descend(*pyr[-1]))
haut = None
for c, p in reversed(pyr):
    base = np.where(p[..., None] > 1e-5, c/np.maximum(p, 1e-5)[..., None], 0.0)
    if haut is not None:
        gros = flou(np.repeat(np.repeat(haut, 2, 0), 2, 1)[:base.shape[0], :base.shape[1]], 2)
        base = np.where(p[..., None] > 1e-5, base, gros)
    haut = base
haut = flou(haut, 1)
rgb = np.where(w[..., None] > 0.5, coul[..., :3], haut)
coul[..., :3] = rgb; coul[..., 3] = 1.0
img.pixels = coul.ravel().tolist()
img.filepath_raw = os.path.splitext(OUT)[0] + "_tex.png"; img.file_format = 'PNG'; img.save()
mimg.filepath_raw = os.path.splitext(OUT)[0] + "_masque.png"; mimg.file_format='PNG'; mimg.save()
print("VISIBLE", round(100*float(w.mean()), 1), "pour cent de l'atlas")

fin = bpy.data.materials.new("perso"); fin.use_nodes = True
b = fin.node_tree.nodes["Principled BSDF"]
t2 = fin.node_tree.nodes.new("ShaderNodeTexImage"); t2.image = img
fin.node_tree.links.new(t2.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.9
if "Specular IOR Level" in b.inputs: b.inputs["Specular IOR Level"].default_value = 0.22
me.materials.clear(); me.materials.append(fin)
while me.color_attributes: me.color_attributes.remove(me.color_attributes[0])
while len(me.uv_layers) > 1:
    for l in me.uv_layers:
        if l.name != "bake": me.uv_layers.remove(l); break
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print(f"PROJETE {os.path.basename(OUT)} | {n0} -> {len(me.polygons)} faces | haut={axn[UP]} larg={axn[LAR]} prof={axn[DEP]}")
