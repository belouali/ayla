# Detoure chaque planche et etale les couleurs du sujet vers l'exterieur.
from PIL import Image
import numpy as np
from scipy import ndimage
def masque(a):
    H,W,_=a.shape
    yy,xx=np.mgrid[0:H,0:W]
    bord=np.zeros((H,W),bool); bord[:6]=bord[-6:]=True; bord[:,:6]=bord[:,-6:]=True
    base=np.stack([np.ones(H*W),xx.ravel(),yy.ravel(),(xx*xx).ravel(),(yy*yy).ravel(),(xx*yy).ravel()],1)
    pred=np.zeros((H,W,3))
    for c in range(3):
        coef,*_=np.linalg.lstsq(base[bord.ravel()],a[...,c].ravel()[bord.ravel()],rcond=None)
        pred[...,c]=(base@coef).reshape(H,W)
    m=np.abs(a-pred).sum(2)>26
    m=ndimage.binary_opening(m,np.ones((3,3)))
    lab,n=ndimage.label(m)
    if n: m=lab==(1+np.argmax(ndimage.sum(m,lab,range(1,n+1))))
    m=ndimage.binary_closing(m,np.ones((9,9)))
    return ndimage.binary_fill_holes(m)
for p in ["saren","kade","elio","ayla"]:
    a=np.asarray(Image.open(f"refs/{p}_face.png").convert("RGB")).astype(float)
    m=masque(a)
    ys,xs=np.where(m); x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
    sub=a[y0:y1+1,x0:x1+1].astype(np.uint8); ms=m[y0:y1+1,x0:x1+1]
    coeur=ndimage.binary_erosion(ms,np.ones((9,9)))   # rim ecarte : pas de fond dans l'etalement
    _,idx=ndimage.distance_transform_edt(~coeur,return_indices=True)
    out=sub.copy(); ext=~ms
    out[ext]=sub[idx[0],idx[1]][ext]
    out=np.where(ext[...,None], ndimage.uniform_filter(out.astype(float),size=(9,9,1)), out).astype(np.uint8)
    Image.fromarray(out).save(f"refs/{p}_fill.png")
    print(f"{p:6s} boite {x1-x0+1}x{y1-y0+1}  sujet {100*ms.mean():.0f}% de la boite")
