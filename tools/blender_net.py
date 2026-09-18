# Nettoyage d'un personnage genere : fusion, socle, normales, decimation,
# depliage UV propre, cuisson de la couleur (texture ou sommets), export glTF.
import bpy, bmesh, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
SRC, OUT, CIBLE, TAILLE = a[0], a[1], int(a[2]), int(a[3])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not objs: raise SystemExit("aucun maillage")
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.name = "perso"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
n0 = len(me.polygons)

# --- source de couleur d'origine -------------------------------------------
uv0 = me.uv_layers.active.name if me.uv_layers.active else None
img_src = None
for mat in me.materials:
    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                img_src = n.image; break
    if img_src: break
attr_col = me.color_attributes[0].name if me.color_attributes else None

# --- socle : faces basses et eloignees de l'axe ----------------------------
bm = bmesh.new(); bm.from_mesh(me)
ext = [max(v.co[i] for v in bm.verts) - min(v.co[i] for v in bm.verts) for i in range(3)]
UP = ext.index(max(ext))            # l'axe le plus long est la verticale
A, B = [i for i in range(3) if i != UP]
zs = [v.co[UP] for v in bm.verts]
zmin, zmax = min(zs), max(zs); h = zmax - zmin
ca = sum(v.co[A] for v in bm.verts)/len(bm.verts)
cb = sum(v.co[B] for v in bm.verts)/len(bm.verts)
sup = [f for f in bm.faces
       if max(v.co[UP] for v in f.verts) < zmin + 0.055*h
       and math.hypot(f.calc_center_median()[A]-ca, f.calc_center_median()[B]-cb) > 0.19*h]
if sup: bmesh.ops.delete(bm, geom=sup, context='FACES')
bm.to_mesh(me); bm.free()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0006)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.customdata_custom_splitnormals_clear()

if len(me.polygons) > CIBLE:
    d = ob.modifiers.new("dec", "DECIMATE"); d.ratio = CIBLE/len(me.polygons)
    bpy.ops.object.modifier_apply(modifier=d.name)
bpy.ops.object.shade_smooth()
if hasattr(ob.data, "use_auto_smooth"):
    ob.data.use_auto_smooth = True; ob.data.auto_smooth_angle = math.radians(55)

# --- nouvelle carte UV, sans ecraser l'ancienne ----------------------------
me.uv_layers.new(name="bake")
me.uv_layers.active = me.uv_layers["bake"]
me.uv_layers["bake"].active_render = True
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')

# --- materiau de cuisson : couleur d'origine -> emission -------------------
mat = bpy.data.materials.new("cuisson"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
emi = nt.nodes.new("ShaderNodeEmission")
if img_src is not None and uv0:
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uv0
    ts = nt.nodes.new("ShaderNodeTexImage"); ts.image = img_src
    ts.interpolation = 'Smart'
    nt.links.new(uvn.outputs["UV"], ts.inputs["Vector"])
    nt.links.new(ts.outputs["Color"], emi.inputs["Color"])
    src = "texture"
elif attr_col:
    vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = attr_col
    nt.links.new(vc.outputs["Color"], emi.inputs["Color"])
    src = "sommets"
else:
    emi.inputs["Color"].default_value = (.78,.72,.66,1); src = "uni"
nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
me.materials.clear(); me.materials.append(mat)
img = bpy.data.images.new("tex", TAILLE, TAILLE)
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
nt.nodes.active = tn

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 2
sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False
sc.render.bake.margin = 8
bpy.ops.object.bake(type='EMIT')
png = os.path.splitext(OUT)[0] + "_tex.png"
img.filepath_raw = png; img.file_format = 'PNG'; img.save()

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
print(f"NETTOYE {os.path.basename(OUT)} | {n0} -> {len(me.polygons)} faces | couleur {src} | {TAILLE}px")
