# Planche de controle : chaque animation a quatre instants, de profil et de trois quarts.
import bpy, sys, math, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; SRC, OUT = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
rig = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
acts = [x for x in bpy.data.actions]
print("ACTIONS", [(x.name, tuple(x.frame_range)) for x in acts])
sc = bpy.context.scene
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.55, .58, .64, 1)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 3)); s = bpy.context.object
s.rotation_euler = (math.radians(50), 0, math.radians(-35)); s.data.energy = 3.2
bpy.ops.mesh.primitive_plane_add(size=6); 
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x = 360; sc.render.resolution_y = 440
sc.view_settings.view_transform = 'Standard'
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 50
fichiers = []
for act in acts:
    rig.animation_data.action = act
    f0, f1 = act.frame_range
    for vue, ang in (("profil", 90), ("troisq", 35)):
        r = math.radians(ang); d = 3.0
        cam.location = Vector((d*math.sin(r), -d*math.cos(r), 0.62))
        cam.rotation_euler = (Vector((0, 0, 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for i in range(4):
            fr = f0 + (f1 - f0)*i/4
            sc.frame_set(int(fr), subframe=fr - int(fr))
            p = f"{OUT}_{act.name}_{vue}_{i}.png"; sc.render.filepath = p
            bpy.ops.render.render(write_still=True); fichiers.append(p)
print("PLANCHE", len(fichiers))
