# Sequence de profil d'une animation : N images sur un cycle.
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; SRC, OUT, NOM, N = a[0], a[1], a[2], int(a[3])
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
rig = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
act = [x for x in bpy.data.actions if x.name.startswith(NOM)][0]; rig.animation_data.action = act
sc = bpy.context.scene; w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.75, .77, .82, 1)
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x = 260; sc.render.resolution_y = 360
sc.view_settings.view_transform = 'Standard'
bpy.ops.object.camera_add(location=(3, 0, .55)); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 60
cam.rotation_euler = (Vector((0, 0, .5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
f0, f1 = act.frame_range
for i in range(N):
    fr = f0 + (f1-f0)*i/N; sc.frame_set(int(fr), subframe=fr-int(fr))
    sc.render.filepath = f"{OUT}_{i}.png"; bpy.ops.render.render(write_still=True)
