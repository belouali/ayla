# Allege un objet Poly Haven (CC0) pour le web : polygones reduits, textures 512, un seul GLB, base au sol.
import bpy, sys, glob, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; DOS, OUT, CIBLE = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glob.glob(os.path.join(DOS, "*.gltf"))[0])
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH']
tot = sum(len(o.data.polygons) for o in ms)
for o in ms:
    n = len(o.data.polygons)
    if tot > CIBLE and n > 200:
        d = o.modifiers.new("dec", "DECIMATE"); d.ratio = max(.05, CIBLE/tot)
        with bpy.context.temp_override(object=o, active_object=o): bpy.ops.object.modifier_apply(modifier=d.name)
for im in bpy.data.images:
    if im.size[0] > 512: im.scale(512, int(512*im.size[1]/im.size[0]))
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
zmin = min(p.z for p in pts); cx = (min(p.x for p in pts)+max(p.x for p in pts))/2; cy = (min(p.y for p in pts)+max(p.y for p in pts))/2
for o in [o for o in bpy.context.scene.objects if o.parent is None]: o.location -= Vector((cx, cy, zmin))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_image_format='JPEG', export_jpeg_quality=82)
dims = (max(p.x for p in pts)-min(p.x for p in pts), max(p.y for p in pts)-min(p.y for p in pts), max(p.z for p in pts)-zmin)
print("OBJET", os.path.basename(OUT), tot, "->", sum(len(o.data.polygons) for o in ms), "faces", os.path.getsize(OUT)//1024, "Ko", "taille", [round(x,2) for x in dims])
