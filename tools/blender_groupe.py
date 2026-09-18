import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]
OUT = a[0]; FICH = a[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
HAUT = [1.75, 1.68, 1.70, 1.78]          # tailles relatives des personnages
objs = []
for i, f in enumerate(FICH):
    avant = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    neufs = [o for o in bpy.context.scene.objects if o not in avant and o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in neufs: o.select_set(True)
    bpy.context.view_layer.objects.active = neufs[0]
    if len(neufs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bb = [Vector(c) for c in o.bound_box]
    h = max(p.z for p in bb) - min(p.z for p in bb)
    s = HAUT[i % len(HAUT)] / h
    o.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    bb = [Vector(c) for c in o.bound_box]
    o.location = (i*1.30 - 1.30*(len(FICH)-1)/2,
                  -(max(p.y for p in bb)+min(p.y for p in bb))/2,
                  -min(p.z for p in bb))
    objs.append(o)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,0))
sm = bpy.data.materials.new("sol"); sm.use_nodes = True
sm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.15,.16,.19,1)
sm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
bpy.context.object.data.materials.append(sm)
ctr = Vector((0, 0, 0.95)); d = 11.0
pos = Vector((0.0, -d, 1.35))
bpy.ops.object.camera_add(location=pos); cam = bpy.context.object; cam.data.lens = 58
cam.rotation_euler = (ctr-pos).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera = cam
def lampe(p, e, t, c=(1,1,1)):
    bpy.ops.object.light_add(type='AREA', location=p); L = bpy.context.object.data
    L.energy = e; L.size = t; L.color = c
    bpy.context.object.rotation_euler = (ctr-Vector(p)).to_track_quat('-Z','Y').to_euler()
lampe((-4,-5,4.5), 1500, 5, (1,.97,.92))
lampe(( 5,-3,2.6),  650, 4, (.87,.92,1))
lampe(( 0, 5,4.0),  900, 5, (1,.95,.9))
w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.05,.055,.07,1)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.render.resolution_x = 1400; sc.render.resolution_y = 760
sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'Medium High Contrast'
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
print("GROUPE", OUT)
