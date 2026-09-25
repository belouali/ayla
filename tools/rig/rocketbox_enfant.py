# Convertit un enfant Rocketbox (MIT) en GLB pour le jeu : textures allegees, hauteur 1,
# animations assises transferees depuis les clips Bip01, face +Z dans le jeu.
import bpy, sys, os, glob, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
DOSSIER, ANIMS, OUT = a[0], a[1].split(","), a[2]
TEX = int(a[3]) if len(a) > 3 else 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx = glob.glob(os.path.join(DOSSIER, "*.fbx"))[0]
bpy.ops.import_scene.fbx(filepath=fbx, automatic_bone_orientation=False)
arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
corps = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
for o in list(bpy.context.scene.objects):
    if o.type == 'EMPTY': bpy.data.objects.remove(o, do_unlink=True)
pref = arm.data.bones[0].name.split(" ")[0]           # Bip02 pour les enfants
# textures : couleur et relief, reduites
tex = {os.path.basename(p): p for p in glob.glob(os.path.join(DOSSIER, "Textures", "*.tga"))}
for m in corps.data.materials:
    zone = "head" if "head" in m.name else "body"
    col = next((p for n, p in tex.items() if f"{zone}_color" in n), None)
    nor = next((p for n, p in tex.items() if f"{zone}_normal" in n), None)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0]); b.inputs["Roughness"].default_value = .8
    if col:
        im = bpy.data.images.load(col); im.scale(TEX, TEX)
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if nor:
        imn = bpy.data.images.load(nor); imn.scale(TEX, TEX); imn.colorspace_settings.name = 'Non-Color'
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = imn; nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
# animations : copie des orientations en espace monde depuis le squelette source, puis cuisson
IGNORES = ("Finger", "Eye", "Lip", "Mouth", "Jaw", "Tongue", "Cheek", "brow", "Brow", "Masseter", "Caninus", "Nose", "Ear", "Footsteps")
bpy.context.view_layer.update()
bbk = [corps.matrix_world @ Vector(c) for c in corps.bound_box]
H_enfant = max(p.z for p in bbk) - min(p.z for p in bbk)
pistes = []
for chemin in ANIMS:
    objs_av = set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=chemin, automatic_bone_orientation=False)
    nouveaux = set(bpy.context.scene.objects) - objs_av
    src = [o for o in nouveaux if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action]
    for o in nouveaux:
        if not src or o is not src[0]: bpy.data.objects.remove(o, do_unlink=True)
    if not src: print("PAS D'ACTION", chemin); continue
    src = src[0]; act_src = src.animation_data.action
    src.scale = [x*H_enfant/1.78 for x in src.scale]             # proportions d'enfant pour la hauteur du bassin
    fin = int(min(361, act_src.frame_range[1]))
    sp = src.data.bones[0].name.split(" ")[0]
    for pb in arm.pose.bones:
        for c in list(pb.constraints): pb.constraints.remove(c)
        nom_src = sp + pb.name[len(pref):]
        if nom_src not in src.pose.bones or any(k in pb.name for k in IGNORES): continue
        c = pb.constraints.new('COPY_ROTATION'); c.target = src; c.subtarget = nom_src
        c.target_space = 'WORLD'; c.owner_space = 'WORLD'
        if pb.name.endswith("Pelvis"):
            cl = pb.constraints.new('COPY_LOCATION'); cl.target = src; cl.subtarget = nom_src; cl.target_space = 'WORLD'; cl.owner_space = 'WORLD'
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    arm.animation_data_create(); arm.animation_data.action = None
    bpy.ops.nla.bake(frame_start=1, frame_end=fin, step=2, only_selected=True, visual_keying=True,
                     clear_constraints=True, use_current_action=False, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    act = arm.animation_data.action; nom = os.path.basename(chemin).split(".")[0]; act.name = nom
    arm.animation_data.action = None; pistes.append(act)
    bpy.data.objects.remove(src, do_unlink=True)
    print("CLIP", nom, len(act.fcurves), "courbes", tuple(act.frame_range))
arm.animation_data_create()
for act in pistes:
    tr = arm.animation_data.nla_tracks.new(); tr.name = act.name.replace("f_", "").replace("m_", "")
    tr.strips.new(tr.name, int(act.frame_range[0]), act); act.use_fake_user = True
arm.animation_data.action = None
# hauteur 1 (mesuree en T-pose sur le maillage), pieds au sol
bpy.context.view_layer.update()
bb = [corps.matrix_world @ Vector(c) for c in corps.bound_box]
zmin = min(p.z for p in bb); H = max(p.z for p in bb) - zmin
s = 1.0/H
arm.scale = [x*s for x in arm.scale]; arm.location = (arm.location.x*s, arm.location.y*s, arm.location.z*s - zmin*s)
bpy.context.view_layer.update()
# hauteur d'assise : bas du bassin et des cuisses dans la pose assise
if pistes:
    arm.animation_data.action = pistes[0]; bpy.context.scene.frame_set(int(pistes[0].frame_range[0])+5)
    dg = bpy.context.evaluated_depsgraph_get(); ev = corps.evaluated_get(dg); me = ev.to_mesh()
    zs = sorted((ev.matrix_world @ v.co).z for v in me.vertices)
    ys = [(ev.matrix_world @ v.co) for v in me.vertices]
    cuisses = [p.z for p in ys if 0.12 < p.z < 0.45]
    print("ASSISE_SOL", round(zs[0], 3), "ASSISE_BAS_DES_FESSES", round(min(cuisses) if cuisses else -1, 3))
    fx = sum(p.x for p in ys)/len(ys); fy = sum(p.y for p in ys)/len(ys)
    avant_pieds = [p for p in ys if p.z < .08]
    print("PIEDS_Y", round(sum(p.y for p in avant_pieds)/max(1,len(avant_pieds)), 3), "CORPS_Y", round(fy, 3))
    ev.to_mesh_clear(); arm.animation_data.action = None
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); corps.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=True,
    export_animation_mode='NLA_TRACKS', export_skins=True, export_image_format='JPEG', export_jpeg_quality=85, export_yup=True)
print("EXPORT", OUT, os.path.getsize(OUT)//1024, "Ko")
