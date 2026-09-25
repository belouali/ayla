# Nettoyage d'un modele TRELLIS : dalle residuelle sous les pieds, creux sombres dans la surface.
# Usage : blender -b --python nettoyer_trellis.py -- entree.glb sortie.glb [trous]
#   creux : pastilles "x:z:rayon" separees par des virgules (coordonnees normalisees : pieds a 0, hauteur 1, vue de face)
#   iris  : cercles "x:z:rayon" ou les iris gris-bleu deviennent bruns (comme la planche)
#   DALLE=0 dans l'environnement : garde les faces claires au sol (chaussures blanches)
import bpy, bmesh, sys, numpy as np
a=sys.argv[sys.argv.index("--")+1:]
SRC,OUT=a[0],a[1]
ZONES=[tuple(map(float,t.split(":"))) for t in a[2].split(",")] if len(a)>2 and a[2] else []
IRIS=[tuple(map(float,t.split(":"))) for t in a[3].split(",")] if len(a)>3 and a[3] else []
import os; COULEUR_DALLE=os.environ.get("DALLE","1")!="0"
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
ms=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
if len(ms)>1: bpy.ops.object.join()
ob=bpy.context.view_layer.objects.active; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=ob.data
co=np.empty(len(me.vertices)*3,np.float32); me.vertices.foreach_get("co",co); V=co.reshape(-1,3)
zmin=float(V[:,2].min()); H=float(V[:,2].max()-zmin); hi=V[V[:,2]>zmin+.3*H]; cx,cy=float(np.median(hi[:,0])),float(np.median(hi[:,1]))
N=lambda p:((p[0]-cx)/H,(p[1]-cy)/H,(p[2]-zmin)/H)
img=None
for n in me.materials[0].node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image: img=n.image; break
W,Hh=img.size; P=np.array(img.pixels[:],np.float32).reshape(Hh,W,4)
bm=bmesh.new(); bm.from_mesh(me); uvl=bm.loops.layers.uv.active
def couleur(f):
    u=np.mean([l[uvl].uv[:] for l in f.loops],0); x=int(np.clip(u[0]*W,0,W-1)); y=int(np.clip(u[1]*Hh,0,Hh-1)); return P[y,x,:3]

# --- dalle : faces claires et neutres au ras du sol, et tout ce qui deborde loin du corps
sup=[]
for f in bm.faces:
    zs=[N(v.co)[2] for v in f.verts]
    if max(zs)>.1: continue
    c=N(f.calc_center_median()); r=np.hypot(c[0],c[1]); col=couleur(f)
    lum=col@[.3,.59,.11]; sat=col.max()-col.min()
    if r>.33 or (COULEUR_DALLE and lum>.42 and sat<.12): sup.append(f)
bmesh.ops.delete(bm,geom=sup,context='FACES')
print("DALLE faces", len(sup))

# --- creux : une pastille posee sur la surface voisine couvre chaque puits sombre ;
#     elle reprend un texel de la peau ou du tissu d'a cote (une seule matiere, texture intacte)
if ZONES:
    from mathutils import Vector, Matrix
    for px,pz,R in ZONES:
        bm.faces.ensure_lookup_table()
        autour=[f for f in bm.faces if (lambda n: n[1]<.05 and np.hypot(n[0]-px,n[2]-pz)<=R*3)(N(f.calc_center_median()))]
        A=np.array([N(f.calc_center_median()) for f in autour])
        anneau=np.hypot(A[:,0]-px,A[:,2]-pz)>R
        garde=anneau&(A[:,1]<=np.percentile(A[anneau][:,1],50))
        X=np.c_[np.ones(garde.sum()),A[garde][:,0],A[garde][:,2]]; c0,cb,cc=np.linalg.lstsq(X,A[garde][:,1],rcond=None)[0]
        plan=lambda x,z: c0+cb*x+cc*z
        # texel voisin : face de surface, claire, juste hors du puits
        best=None
        for f,n in zip(autour,A):
            d=np.hypot(n[0]-px,n[2]-pz)
            if R<d<R*2.2 and n[1]<=plan(n[0],n[2])+.001:
                col=couleur(f); l=col@[.3,.59,.11]
                if l>.25 and (best is None or d<best[0]): best=(d,f)
        uvc=Vector(np.mean([l[uvl].uv[:] for l in best[1].loops],0)) if best else None
        nrm=Vector((cb,-1.0,cc)).normalized()
        centre=Vector((px*H+cx,(plan(px,pz)-.0025)*H+cy,pz*H+zmin))
        rot=nrm.to_track_quat('Z','Y').to_matrix().to_4x4()
        res=bmesh.ops.create_circle(bm,cap_ends=True,cap_tris=True,segments=20,radius=R*H,matrix=Matrix.Translation(centre)@rot)
        nf={f for v in res['verts'] for f in v.link_faces}
        for f in nf:
            if f.normal.dot(nrm)<0: f.normal_flip()
            f.material_index=0
            if uvc is not None:
                for l in f.loops: l[uvl].uv=uvc
        print("CREUX pastille", (px,pz,R), "texel", uvc is not None)
    bm.normal_update()
# --- iris : dans les cercles donnes, les pixels gris (peu satures, ni blanc ni cheveu) passent au brun (le blanc de l'oeil et la peau restent)
if IRIS:
    masque=np.zeros((Hh,W),bool)
    for f in bm.faces:
        n=N(f.calc_center_median())
        if n[1]>.05 or not any(np.hypot(n[0]-x,n[2]-z)<=r for x,z,r in IRIS): continue
        pts=np.array([l[uvl].uv[:] for l in f.loops])*[W,Hh]
        x0,y0=np.floor(pts.min(0)).astype(int)-1; x1,y1=np.ceil(pts.max(0)).astype(int)+1
        masque[np.clip(y0,0,Hh-1):np.clip(y1,0,Hh-1)+1, np.clip(x0,0,W-1):np.clip(x1,0,W-1)+1]=True
    c=P[...,:3]; lum=c@np.array([.3,.59,.11],np.float32); sat=c.max(-1)-c.min(-1)
    bleu=masque&(lum>.09)&(lum<.38)&(sat<.14)
    brun=np.array([.36,.19,.09],np.float32)
    P[bleu,:3]=brun*np.clip(lum[bleu]/.3,.35,1.6)[:,None]
    img.pixels[:]=P.ravel(); img.pack(); print("IRIS pixels", int(bleu.sum()))
bm.to_mesh(me); bm.free()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print("NETTOYE", OUT)
