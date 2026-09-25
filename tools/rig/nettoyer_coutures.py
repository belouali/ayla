# Coutures blanches : chaque ilot UV est rogne de quelques texels sur son bord,
# puis le bord est repeint depuis l'interieur de l'ilot (diffusion). La geometrie ne change pas.
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index("--")+1:]; SRC, OUT = a[0], a[1]; ROGNE = int(a[2]) if len(a) > 2 else 4
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]; me = ob.data
mat = me.materials[0]; img = [n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image][0]
W, H = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)
# couverture des ilots : cuisson d'une emission blanche sur les UV du modele
cov = bpy.data.images.new("cov", W, H)
mc = bpy.data.materials.new("cov"); mc.use_nodes = True; nt = mc.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); e_ = nt.nodes.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = (1, 1, 1, 1)
nt.links.new(e_.outputs["Emission"], o_.inputs["Surface"]); t_ = nt.nodes.new("ShaderNodeTexImage"); t_.image = cov; nt.nodes.active = t_
me.materials.clear(); me.materials.append(mc)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1; sc.render.bake.margin = 0
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.object.bake(type='EMIT')
m = np.array(cov.pixels[:], dtype=np.float32).reshape(H, W, 4)[..., 0] > .5
# erosion de ROGNE texels
e = m.copy()
for _ in range(ROGNE):
    e = e & np.roll(e, 1, 0) & np.roll(e, -1, 0) & np.roll(e, 1, 1) & np.roll(e, -1, 1)
w = e.astype(np.float32)
def flou(a, n=1):
    for _ in range(n):
        p = np.pad(a, ((1,1),(1,1),(0,0)), mode='edge')
        a = (p[:-2,1:-1]+p[2:,1:-1]+p[1:-1,:-2]+p[1:-1,2:]+2*p[1:-1,1:-1])/6
    return a
def diffuse(rgb, w):
    def bas(c, p): return (c[0::2,0::2]+c[1::2,0::2]+c[0::2,1::2]+c[1::2,1::2], p[0::2,0::2]+p[1::2,0::2]+p[0::2,1::2]+p[1::2,1::2])
    pyr = [(rgb*w[..., None], w)]
    while pyr[-1][1].shape[0] > 8: pyr.append(bas(*pyr[-1]))
    haut = None
    for c, p in reversed(pyr):
        base = np.where(p[..., None] > 1e-5, c/np.maximum(p, 1e-5)[..., None], 0.)
        if haut is not None:
            gros = flou(np.repeat(np.repeat(haut, 2, 0), 2, 1)[:base.shape[0], :base.shape[1]], 1)
            base = np.where(p[..., None] > 1e-5, base, gros)
        haut = base
    return np.where(w[..., None] > .5, rgb, haut)
px[..., :3] = diffuse(px[..., :3], w); px[..., 3] = 1
print("ILOTS", round(100*float(m.mean()), 1), "% couverts ;", round(100*float((m & ~e).mean()), 2), "% repeints en bordure")
img.pixels = px.ravel().tolist()
img.filepath_raw = os.path.splitext(OUT)[0] + "_tex.png"; img.file_format = 'PNG'; img.save()
me.materials.clear(); me.materials.append(mat)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_image_format='AUTO')
print("SORTIE", OUT)
