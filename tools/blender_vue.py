# Rendu de controle : un personnage, trois quarts, eclairage studio.
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
SRC, OUT = a[0], a[1]
ANG = float(a[2]) if len(a) > 2 else 28.0
LARG = int(a[3]) if len(a) > 3 else 700

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
if len(ms) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
mn = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb)))
mx = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
ctr = (mn + mx) / 2; taille = max(mx - mn)

# sol
bpy.ops.mesh.primitive_plane_add(size=taille*14, location=(ctr.x, ctr.y, mn.z-0.002))
sol = bpy.context.object
ms2 = bpy.data.materials.new("sol"); ms2.use_nodes = True
ms2.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.16,.17,.2,1)
ms2.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
sol.data.materials.append(ms2)

r = math.radians(ANG)
d = taille * 2.15
cam_pos = Vector((ctr.x + d*math.sin(r), ctr.y - d*math.cos(r), ctr.z + taille*0.16))
bpy.ops.object.camera_add(location=cam_pos)
cam = bpy.context.object; cam.data.lens = 85
dir_v = (ctr - cam_pos)
cam.rotation_euler = dir_v.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

def lampe(pos, e, taille_l, coul=(1,1,1)):
    bpy.ops.object.light_add(type='AREA', location=pos)
    L = bpy.context.object.data
    L.energy = e; L.size = taille_l; L.color = coul
    bpy.context.object.rotation_euler = (ctr - Vector(pos)).to_track_quat('-Z','Y').to_euler()
E = taille*taille*90
lampe((ctr.x - d*.8, ctr.y - d*.7, ctr.z + taille*1.0), E*2.4, taille*1.5, (1,.97,.92))
lampe((ctr.x + d*.9, ctr.y - d*.4, ctr.z + taille*.5), E*1.0, taille*1.4, (.88,.93,1))
lampe((ctr.x, ctr.y + d*.9, ctr.z + taille*.9), E*1.6, taille*1.3, (1,.95,.9))

w = bpy.context.scene.world
if not w:
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.055,.06,.075,1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.render.resolution_x = LARG; sc.render.resolution_y = int(LARG*1.32)
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'Medium High Contrast'
sc.render.filepath = OUT; sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("VUE", OUT)
