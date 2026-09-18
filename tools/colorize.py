import trimesh, numpy as np, sys
from PIL import Image
from scipy import ndimage

def bbox_perso(a, bg, seuil=60):
    m=np.abs(a-bg).sum(2)>seuil; H,W=m.shape
    cols=np.nonzero(m.sum(0)>H*0.01)[0]; rows=np.nonzero(m.sum(1)>W*0.01)[0]
    return cols.min(),cols.max(),rows.min(),rows.max(),m

def colorize(glb_in, img_path, glb_out):
    m=trimesh.load(glb_in, force='mesh', process=False)
    a=np.asarray(Image.open(img_path).convert('RGB')).astype(int); H,W,_=a.shape
    bg=np.concatenate([a[:,:8].reshape(-1,3), a[:,-8:].reshape(-1,3), a[:8,:].reshape(-1,3)]).mean(0)
    x0,x1,y0,y1,mask=bbox_perso(a,bg)
    # remplir le fond par la couleur du pixel de personnage le plus proche
    idx=ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    filled=a[idx[0],idx[1]]
    v=m.vertices; n=m.vertex_normals
    mn,mx=v.min(0),v.max(0)
    u=(v[:,0]-mn[0])/(mx[0]-mn[0]); w=(v[:,1]-mn[1])/(mx[1]-mn[1])
    px=np.clip((x0+u*(x1-x0)).astype(int),0,W-1)
    py=np.clip((y1-w*(y1-y0)).astype(int),0,H-1)
    col=filled[py,px].astype(float)
    # arrière de la tête : couleur des cheveux plutôt que le visage projeté
    hair=filled[int(y0+0.035*(y1-y0)), int((x0+x1)/2)].astype(float)
    tete = w>0.84
    dos  = n[:,2] < -0.15
    col[tete & dos] = hair
    fondu = tete & (n[:,2]>=-0.15) & (n[:,2]<0.25)
    col[fondu] = 0.5*col[fondu] + 0.5*hair
    m.visual = trimesh.visual.ColorVisuals(mesh=m, vertex_colors=np.clip(col,0,255).astype(np.uint8))
    m.export(glb_out)
    print("écrit", glb_out, "| cheveux", hair.astype(int), "| sommets colorés", len(col))

if __name__=="__main__":
    colorize(sys.argv[1], sys.argv[2], sys.argv[3])
