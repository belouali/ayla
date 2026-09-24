# Vue de face et de profil orthographiques, normalisees : pieds a z=0, hauteur 1.
import bpy, sys, json
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]; SRC,OUT=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ms=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
if len(ms)>1: bpy.ops.object.join()
ob=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
import numpy as np
co=np.empty(len(ob.data.vertices)*3,np.float32); ob.data.vertices.foreach_get("co",co); co=co.reshape(-1,3)
zmin=co[:,2].min(); H=co[:,2].max()-zmin
hi=co[co[:,2]>zmin+0.3*H]; cx=float(np.median(hi[:,0])); cy=float(np.median(hi[:,1]))
ob.location=(-cx,-cy,-zmin); bpy.ops.object.transform_apply(location=True)
s=1.0/H; ob.scale=(s,s,s); bpy.ops.object.transform_apply(scale=True)
m=bpy.data.materials.new("g"); m.use_nodes=True
b=m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value=(.7,.7,.72,1)
sc=bpy.context.scene
for vue,pos,rot in (("face",(0,-5,0.5),(1.5708,0,0)),("profil",(5,0,0.5),(1.5708,0,1.5708))):
    bpy.ops.object.camera_add(location=pos,rotation=rot); cam=bpy.context.object
    cam.data.type='ORTHO'; cam.data.ortho_scale=1.1; sc.camera=cam
    bpy.ops.object.light_add(type='SUN',location=(0,-3,3)); bpy.context.object.data.energy=3
    sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=1000; sc.render.resolution_y=1000
    sc.render.filepath=OUT+"_"+vue+".png"; bpy.ops.render.render(write_still=True)
print("ORTHO", json.dumps({"H":float(H),"cx":cx,"cy":cy,"zmin":float(zmin)}))
