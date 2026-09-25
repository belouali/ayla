# TRELLIS ne voit que la face : il devine le dos, souvent plus pale. On ramene les couleurs du dos
# sur celles de la face, bande par bande (cheveux, veste...) : luminosite a l'echelle (le relief reste), teinte de face,
# fondu sur les flancs (seulement ce qui est plus pale que la face) pour ne pas marquer de couture.
# Usage : blender -b --python equilibrer_dos.py -- entree.glb sortie.glb "z0:z1,z0:z1,..."
import bpy, bmesh, sys, numpy as np
a=sys.argv[sys.argv.index("--")+1:]; SRC,OUT=a[0],a[1]
BANDES=[tuple(map(float,t.split(":"))) for t in a[2].split(",")]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
ms=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
if len(ms)>1: bpy.ops.object.join()
ob=bpy.context.view_layer.objects.active; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=ob.data; V=np.array([v.co[:] for v in me.vertices]); zmin=V[:,2].min(); H=V[:,2].max()-zmin
hi=V[V[:,2]>zmin+.3*H]; cx,cy=np.median(hi[:,0]),np.median(hi[:,1])
img=[n.image for n in me.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image][0]
W,Hh=img.size; P=np.array(img.pixels[:],np.float32).reshape(Hh,W,4)
uv=me.uv_layers.active.data
etiq=np.zeros((Hh,W),np.int16)   # 0 rien ; 2k+1 face de la bande k ; 2k+2 dos de la bande k
yface=np.full((Hh,W),-9,np.float32) # profondeur de la face (y normalise, <0 devant)
for f in me.polygons:
    c=f.center; z=(c.z-zmin)/H; y=(c.y-cy)/H
    k=next((i for i,(z0,z1) in enumerate(BANDES) if z0<=z<=z1), None)
    if k is None: continue
    lab=2*k+(1 if y<0 else 2)
    pts=np.array([uv[i].uv[:] for i in f.loop_indices])*[W,Hh]
    x0,y0=np.floor(pts.min(0)).astype(int); x1,y1=np.ceil(pts.max(0)).astype(int)
    gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    for t in range(1,len(pts)-1):
        A,B,C=pts[0],pts[t],pts[t+1]; d=(B[1]-C[1])*(A[0]-C[0])+(C[0]-B[0])*(A[1]-C[1])
        if abs(d)<1e-9: continue
        l1=((B[1]-C[1])*(gx-C[0])+(C[0]-B[0])*(gy-C[1]))/d; l2=((C[1]-A[1])*(gx-C[0])+(A[0]-C[0])*(gy-C[1]))/d
        ins=(l1>=-.05)&(l2>=-.05)&(1-l1-l2>=-.05)
        yy=np.clip(np.arange(y0,y1+1),0,Hh-1); xx=np.clip(np.arange(x0,x1+1),0,W-1)
        sub=etiq[np.ix_(yy,xx)]; sub[ins]=lab; etiq[np.ix_(yy,xx)]=sub
        sy=yface[np.ix_(yy,xx)]; sy[ins]=y; yface[np.ix_(yy,xx)]=sy
c=P[...,:3]; LUM=np.array([.3,.59,.11],np.float32)
lum=c@LUM; r_=np.maximum(c[...,0],1e-3); gr=c[...,1]/r_; br=c[...,2]/r_
for k,(z0,z1) in enumerate(BANDES):
    fa=(etiq==2*k+1)&(c[...,0]>c[...,2]+.05); do=(etiq==2*k+2)&(c[...,0]>c[...,2]+.05)
    if fa.sum()<50 or do.sum()<50: continue
    # reference de face : la matiere dominante (pour les cheveux, les pixels sombres, pas la peau du visage)
    if np.median(lum[do])<.4: fa&=lum<.22
    Lf,Ld=np.median(lum[fa]),np.median(lum[do])
    gf,bf=np.median(gr[fa]),np.median(br[fa]); gd,bd=np.median(gr[do]),np.median(br[do])
    # dos : correction pleine au-dela de y=.08 ; flancs (y de -.03 a .08) : seulement ce qui est plus pale que la face
    yf=yface; zone=((etiq==2*k+1)|(etiq==2*k+2))&(c[...,0]>c[...,2]+.05)&(yf>-.03)
    pale=np.clip((lum-Lf)/max(Ld-Lf,1e-3),0,1)
    w=np.maximum(np.clip(yf/.08,0,1), np.clip((yf+.03)/.03,0,1)*pale)[zone][:,None]
    L=lum[zone]*(Lf/Ld); g2=gf+(gr[zone]-gd)*.5; b2=bf+(br[zone]-bd)*.5
    r2=L/(LUM[0]+LUM[1]*g2+LUM[2]*b2); neuf=np.clip(np.stack([r2,r2*g2,r2*b2],-1),0,1)
    c[zone]=c[zone]*(1-w)+neuf*w
    print("BANDE",(z0,z1),"lum face",round(float(Lf),3),"dos",round(float(Ld),3),"teinte face",(round(float(gf),3),round(float(bf),3)),"dos",(round(float(gd),3),round(float(bd),3)),"pixels",int(do.sum()))
P[...,:3]=c; img.pixels[:]=P.ravel(); img.pack()
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB'); print("EQUILIBRE", OUT)
