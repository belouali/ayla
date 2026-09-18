# Retire la dalle sous les pieds sans toucher a la texture deja cuite.
import bpy, bmesh, sys, math
f = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f)
ms=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
if len(ms)>1: bpy.ops.object.join()
ob=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=ob.data; n0=len(me.polygons)
bm=bmesh.new(); bm.from_mesh(me)
zs=[v.co.z for v in bm.verts]; zmin,zmax=min(zs),max(zs); h=zmax-zmin
haut=[v.co for v in bm.verts if v.co.z>zmin+0.30*h]
cx=sorted(c.x for c in haut)[len(haut)//2]; cy=sorted(c.y for c in haut)[len(haut)//2]
sup=[fa for fa in bm.faces
     if max(v.co.z for v in fa.verts) < zmin+0.045*h
     and math.hypot(fa.calc_center_median().x-cx, fa.calc_center_median().y-cy) > 0.115*h]
if sup: bmesh.ops.delete(bm, geom=sup, context='FACES')
bm.to_mesh(me); bm.free()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.delete_loose(); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.export_scene.gltf(filepath=f, export_format='GLB')
print("SOCLE retire", n0, "->", len(me.polygons))
