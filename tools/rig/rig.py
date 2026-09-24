# Squelette, poids et animations (repos, marche, course) pour un personnage genere.
# Usage : blender -b --python rig.py -- modele.glb articulations.json nom sortie.glb [taille_texture]
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--")+1:]
SRC, JSN, NOM, OUT = a[0], a[1], a[2], a[3]
TEX = int(a[4]) if len(a) > 4 else 1536
J = json.load(open(JSN))[NOM]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
corps = bpy.context.view_layer.objects.active; corps.name = NOM
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# --- normalisation identique au releve : pieds a 0, hauteur 1, centre du haut du corps
co = np.empty(len(corps.data.vertices)*3, np.float32); corps.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
zmin = co[:, 2].min(); H = co[:, 2].max() - zmin
hi = co[co[:, 2] > zmin + 0.3*H]
cx = float(np.median(hi[:, 0])); cy = float(np.median(hi[:, 1]))
corps.location = (-cx, -cy, -zmin); bpy.ops.object.transform_apply(location=True)
corps.scale = (1/H, 1/H, 1/H); bpy.ops.object.transform_apply(scale=True)
co = np.empty(len(corps.data.vertices)*3, np.float32); corps.data.vertices.foreach_get("co", co); V = co.reshape(-1, 3)

# --- sens : les pointes de pied depassent vers l'avant
pieds = V[V[:, 2] < 0.035]
cheville_y = V[(V[:, 2] > 0.06) & (V[:, 2] < 0.10)][:, 1].mean()
avant = cheville_y - np.percentile(pieds[:, 1], 1)
arriere = np.percentile(pieds[:, 1], 99) - cheville_y
SENS = -1 if avant >= arriere else 1
print("SENS", NOM, "regarde -Y" if SENS < 0 else "regarde +Y", round(float(avant), 3), round(float(arriere), 3))
if SENS > 0:
    corps.rotation_euler = (0, 0, math.pi); bpy.ops.object.transform_apply(rotation=True)
    corps.data.vertices.foreach_get("co", co); V = co.reshape(-1, 3)
    for k in ("epaule", "coude", "poignet", "main", "hanche", "genou", "cheville"):
        J[k] = [[-J[k][1][0], J[k][1][1]], [-J[k][0][0], J[k][0][1]]]

def prof(x, z, rx=0.035, rz=0.02):
    s = V[(np.abs(V[:, 0]-x) < rx) & (np.abs(V[:, 2]-z) < rz)]
    if len(s) < 6: s = V[(np.abs(V[:, 0]-x) < rx*2.5) & (np.abs(V[:, 2]-z) < rz*2.5)]
    if len(s) < 3: return 0.0
    return float((np.percentile(s[:, 1], 6) + np.percentile(s[:, 1], 94))/2)
def P3(x, z, rx=0.035): return Vector((x, prof(x, z, rx), z))

cz, hc = J["cou"], J["hanche_c"]
colonne_z = hc + 0.36*(cz - hc); poitrine_z = hc + 0.72*(cz - hc)
axe = {k: P3(0, z, 0.08) for k, z in (("bassin", hc), ("colonne", colonne_z), ("poitrine", poitrine_z), ("cou", cz - 0.012))}
tete_bas = P3(0, cz + 0.045, 0.06); tete_haut = Vector((0, tete_bas.y, 0.995))

arm = bpy.data.armatures.new("os"); rig = bpy.data.objects.new("squelette", arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
def os_(nom, t, q, parent=None, lie=False):
    b = eb.new(nom); b.head = t; b.tail = q
    if parent: b.parent = eb[parent]; b.use_connect = lie
    return b
os_("bassin", axe["bassin"], axe["colonne"])
os_("colonne", axe["colonne"], axe["poitrine"], "bassin", True)
os_("poitrine", axe["poitrine"], axe["cou"], "colonne", True)
os_("cou", axe["cou"], tete_bas, "poitrine", True)
os_("tete", tete_bas, tete_haut, "cou", True)
for i, c in ((0, "R"), (1, "L")):
    ep = P3(*J["epaule"][i]); co_ = P3(*J["coude"][i]); po = P3(*J["poignet"][i]); ma = P3(*J["main"][i], 0.03)
    cl = Vector((ep.x*0.28, axe["cou"].y, J["epaule"][i][1] - 0.012))
    os_("clavicule."+c, cl, ep, "poitrine")
    os_("bras."+c, ep, co_, "clavicule."+c, True)
    os_("avantbras."+c, co_, po, "bras."+c, True)
    os_("main."+c, po, ma, "avantbras."+c, True)
    ha = P3(*J["hanche"][i], 0.04); ge = P3(*J["genou"][i]); ch = P3(*J["cheville"][i])
    f = V[(V[:, 2] < 0.04) & (np.abs(V[:, 0]-ch.x) < 0.05)]
    orteil = Vector((ch.x, float(np.percentile(f[:, 1], 3)) + 0.015 if len(f) else ch.y - 0.07, 0.018))
    os_("cuisse."+c, ha, ge, "bassin")
    os_("jambe."+c, ge, ch, "cuisse."+c, True)
    os_("pied."+c, ch, orteil, "jambe."+c, True)
# roulis : l'axe X local de chaque os = +X du monde, pour que X soit le tangage
def aligne(b):
    y = (b.tail - b.head).normalized()
    x = Vector((1, 0, 0)) - y*y.x
    if x.length < 1e-4: x = Vector((0, 0, 1)) - y*y.z
    b.align_roll(x.normalized().cross(y))   # align_roll oriente l axe Z local : Z = X x Y
for b in eb: aligne(b)
bpy.ops.object.mode_set(mode='OBJECT')

# --- poids : squelette pose sur un double revoxelise, puis transfert
bpy.ops.object.select_all(action='DESELECT')
corps.select_set(True); bpy.context.view_layer.objects.active = corps
bpy.ops.object.duplicate(); proxy = bpy.context.object; proxy.name = "proxy"
for m in list(proxy.data.materials): pass
proxy.data.materials.clear()
for g in list(proxy.vertex_groups): proxy.vertex_groups.remove(g)
proxy.data.remesh_voxel_size = 0.006
bpy.ops.object.voxel_remesh()
print("VOXEL faces", len(proxy.data.polygons))
if len(proxy.data.polygons) > 60000:
    d = proxy.modifiers.new("dec", "DECIMATE"); d.ratio = 60000/len(proxy.data.polygons)
    bpy.ops.object.modifier_apply(modifier=d.name)
bpy.ops.object.select_all(action='DESELECT')
proxy.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
tot = {g.name: 0.0 for g in proxy.vertex_groups}
for v in proxy.data.vertices:
    for gg in v.groups: tot[proxy.vertex_groups[gg.group].name] += gg.weight
vides = [k for k, w in tot.items() if w < 1e-3]
print("PROXY groupes", len(proxy.vertex_groups), "faces", len(proxy.data.polygons), "vides", vides)

for b in arm.bones: corps.vertex_groups.new(name=b.name)
dt = corps.modifiers.new("transfert", "DATA_TRANSFER")
dt.object = proxy; dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.ops.object.select_all(action='DESELECT'); corps.select_set(True); bpy.context.view_layer.objects.active = corps
bpy.ops.object.modifier_apply(modifier=dt.name)

# accessoire tenu (baton de Saren) : entierement porte par la main
if "baton" in J:
    bt = J["baton"]; xm = bt["x_max"] if SENS < 0 else bt["x_max"]
    ids = [v.index for v in corps.data.vertices if v.co.x < xm and v.co.z < bt["z_max"]]
    for g in corps.vertex_groups: g.remove(ids)
    corps.vertex_groups[bt["os"]].add(ids, 1.0, 'REPLACE')
    print("BATON", len(ids), "sommets portes par", bt["os"])

bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.data.objects.remove(proxy, do_unlink=True)
sans = sum(1 for v in corps.data.vertices if not v.groups)
print("SANS POIDS", sans, "sur", len(corps.data.vertices))
if sans:
    ids = [v.index for v in corps.data.vertices if not v.groups]
    corps.vertex_groups["bassin"].add(ids, 1.0, 'REPLACE')
# faces basses tendues entre les deux jambes : elles se dechireraient a chaque pas
jambeL = {corps.vertex_groups[n].index for n in ("cuisse.L", "jambe.L", "pied.L")}
jambeR = {corps.vertex_groups[n].index for n in ("cuisse.R", "jambe.R", "pied.R")}
def cote(v):
    l = sum(g.weight for g in v.groups if g.group in jambeL)
    r = sum(g.weight for g in v.groups if g.group in jambeR)
    return 1 if l > 0.6 else (-1 if r > 0.6 else 0)
cotes = [cote(v) for v in corps.data.vertices]
bm = bmesh.new(); bm.from_mesh(corps.data); bm.verts.ensure_lookup_table()
mauv = []
for fa in bm.faces:
    if max(v.co.z for v in fa.verts) > 0.30: continue
    cs = {cotes[v.index] for v in fa.verts}
    if 1 in cs and -1 in cs: mauv.append(fa)
    elif max(v.co.z for v in fa.verts) < 0.025 and abs(fa.calc_center_median().x) < 0.035 and abs(fa.normal.z) > 0.6:
        mauv.append(fa)
bmesh.ops.delete(bm, geom=mauv, context='FACES')
bm.to_mesh(corps.data); bm.free()
print("MEMBRANE", len(mauv), "faces retirees entre les jambes")
corps.parent = rig
am = corps.modifiers.new("squelette", "ARMATURE"); am.object = rig

# --- animations -------------------------------------------------------------
FPS = 30; bpy.context.scene.render.fps = FPS
ALL = {"ado":   dict(marche=1.00, course=0.64, jambe=0.46, genou=0.95, bras=0.42, rebond=0.012, penche=0.03, baton=False),
       "jeune": dict(marche=1.00, course=0.62, jambe=0.48, genou=1.00, bras=0.40, rebond=0.012, penche=0.03, baton=False),
       "ancien":dict(marche=1.15, course=0.74, jambe=0.36, genou=0.75, bras=0.30, rebond=0.009, penche=0.08, baton=False),
       "sage":  dict(marche=1.40, course=0.90, jambe=0.26, genou=0.55, bras=0.10, rebond=0.006, penche=0.14, baton=True)}[J["allure"]]
pb = rig.pose.bones
for b in pb: b.rotation_mode = 'XYZ'
BAS = pb["bassin"].bone.head_local.copy()

def pose(r, loc=(0, 0, 0)):
    for b in pb: b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
    for nom, e in r.items(): pb[nom].rotation_euler = e
    pb["bassin"].location = loc

def action(nom, duree, f):
    n = int(round(duree*FPS)); act = bpy.data.actions.new(nom)
    rig.animation_data_create(); rig.animation_data.action = act
    for i in range(n + 1):
        t = i / n; r, loc = f(2*math.pi*t)
        pose(r, loc)
        for b in pb:
            b.keyframe_insert("rotation_euler", frame=i)
        pb["bassin"].keyframe_insert("location", frame=i)
    for fc in act.fcurves:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
        fc.modifiers.new('CYCLES')
    tr = rig.animation_data.nla_tracks.new(); tr.name = nom
    tr.strips.new(nom, 0, act); rig.animation_data.action = None
    act.use_fake_user = True

# rotation positive sur X : un os qui descend part vers l'arriere, un os qui monte penche vers l'avant
def marche(ph, k=1.0, course=False):
    A = ALL; s = math.sin(ph); c = math.cos(ph)
    J_ = A["jambe"]*k; G = A["genou"]*k; B = A["bras"]*k
    r = {}
    for cote, dph in (("L", 0.0), ("R", math.pi)):
        p = ph + dph; sp = math.sin(p); cp = math.cos(p)
        cuisse = -J_*sp
        genou = 0.10*k + G*max(0.0, cp)**1.6 + (0.25*G*max(0.0, -cp) if course else 0.0)
        r["cuisse."+cote] = (cuisse, 0, 0)
        r["jambe."+cote] = (genou, 0, 0)
        r["pied."+cote] = (-(cuisse + genou)*0.55 - 0.15*max(0.0, sp)*k, 0, 0)
        if A["baton"] and cote == "R":
            r["bras."+cote] = (-0.05, 0, 0); r["avantbras."+cote] = (-0.10, 0, 0)
        else:
            bs = B*sp if cote == "L" else -B*sp
            flex = (-1.25 - 0.35*max(0.0, -bs/B if B else 0)) if course else (-0.18 - 0.22*max(0.0, -bs/B if B else 0))
            r["bras."+cote] = (bs, 0, -0.05 if cote == "L" else 0.05)
            r["avantbras."+cote] = (flex, 0, 0)
    pen = A["penche"] + (0.16 if course else 0.0)
    r["bassin"] = (0, 0.07*s*k, 0)
    r["colonne"] = (pen*0.5, -0.05*s*k, 0.015*math.sin(2*ph))
    r["poitrine"] = (pen*0.5, -0.04*s*k, 0)
    r["cou"] = (-pen*0.5, 0.02*s, 0)
    r["tete"] = (-pen*0.3 + 0.015*math.cos(2*ph), 0.02*s, 0)
    reb = A["rebond"]*(2.2 if course else 1.0)
    return r, (0, reb*math.cos(2*ph) - reb, 0)   # location de l'os : y local = vers le haut

def repos(ph):
    A = ALL
    r = {"poitrine": (0.018*math.sin(2*ph) + A["penche"]*0.5, 0, 0),
         "colonne": (A["penche"]*0.5, 0, 0.012*math.sin(ph)),
         "cou": (-A["penche"]*0.4, 0, 0),
         "tete": (0.02*math.sin(2*ph + 1.0) - A["penche"]*0.2, 0.10*math.sin(ph), 0.02*math.sin(ph + 0.5)),
         "bassin": (0, 0, -0.012*math.sin(ph))}
    for cote, sg in (("L", 1), ("R", -1)):
        if A["baton"] and cote == "R":
            r["bras.R"] = (-0.05, 0, 0); r["avantbras.R"] = (-0.10, 0, 0); continue
        r["bras."+cote] = (0.035*math.sin(2*ph + (0 if cote == "L" else 0.6)), 0, -sg*0.035)
        r["avantbras."+cote] = (-0.16 - 0.04*math.sin(2*ph), 0, 0)
    for cote in ("L", "R"):
        r["cuisse."+cote] = (0.0, 0, 0); r["jambe."+cote] = (0.02, 0, 0); r["pied."+cote] = (-0.01, 0, 0)
    return r, (0, -0.004*(1 - math.cos(2*ph)), 0)

if os.environ.get("TEST"):
    pose({"cuisse.L": (-0.6, 0, 0), "jambe.R": (1.0, 0, 0), "bras.L": (0.6, 0, 0), "avantbras.R": (-1.0, 0, 0),
          "colonne": (0.35, 0, 0), "pied.R": (0.5, 0, 0), "bras.R": (0, 0, 0.3)})
    sc = bpy.context.scene; w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.8, .8, .85, 1)
    sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x = 420; sc.render.resolution_y = 500
    sc.view_settings.view_transform = 'Standard'
    bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 50
    for nom, ang in (("profil", 90), ("face", 0)):
        r = math.radians(ang); cam.location = Vector((3*math.sin(r), -3*math.cos(r), 0.55))
        cam.rotation_euler = (Vector((0, 0, 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = OUT + "_" + nom + ".png"; bpy.ops.render.render(write_still=True)
    sys.exit(0)
action("repos", 6.4, repos)
action("marche", ALL["marche"], lambda ph: marche(ph))
action("course", ALL["course"], lambda ph: marche(ph, 1.55, True))
pose({})

# --- texture allegee et export -------------------------------------------------
for img in bpy.data.images:
    if img.size[0] > TEX: img.scale(TEX, TEX)
mat = corps.data.materials[0] if corps.data.materials else None
if mat and mat.use_nodes:
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Roughness"].default_value = 0.88; b.inputs["Metallic"].default_value = 0.0
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); corps.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True,
    export_animations=True, export_animation_mode='NLA_TRACKS', export_skins=True,
    export_image_format='JPEG', export_jpeg_quality=86, export_apply=False,
    export_yup=True, export_force_sampling=True, export_frame_step=1)
print("RIG", NOM, "os", len(arm.bones), "faces", len(corps.data.polygons), "->", OUT, os.path.getsize(OUT)//1024, "Ko")
