# Allège un maillage généré puis lui applique les couleurs de sa planche de référence.
import sys, numpy as np, trimesh, fast_simplification
from PIL import Image
from scipy import ndimage

CIBLE = 45000  # faces visées

def orienter(m):
    # Hunyuan sort déjà Y vers le haut ; on ne redresse que si Y est nettement le plus petit
    e = m.extents
    if e[1] < 0.6*max(e[0], e[2]):
        R = trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0])
        m.apply_transform(R)
    return m

def retirer_socle(m):
    # le générateur ajoute parfois une dalle plate sous le personnage
    parts = m.split(only_watertight=False)
    if len(parts) <= 1: return m
    hmax = max(p.extents[1] for p in parts)
    gardees = [p for p in parts if p.extents[1] > 0.25*hmax]
    if not gardees: return m
    if len(gardees) != len(parts):
        print(f"   socle retiré : {len(parts)-len(gardees)} morceau(x) plat(s)")
    return trimesh.util.concatenate(gardees)

def couper_dalle(m):
    # enlève la dalle plate au sol, même si elle touche le personnage
    v = m.vertices; ymin = v[:,1].min(); h = m.extents[1]
    jambes = v[(v[:,1] > ymin + 0.05*h) & (v[:,1] < ymin + 0.35*h)]
    if len(jambes) < 20: return m
    cx, cz = jambes[:,0].mean(), jambes[:,2].mean()
    rayon = 0.20*h
    f = m.faces
    bas = (v[f][:,:,1].max(axis=1) < ymin + 0.06*h)
    cen = v[f].mean(axis=1)
    loin = np.hypot(cen[:,0]-cx, cen[:,2]-cz) > rayon
    jeter = bas & loin
    if jeter.any():
        print(f"   dalle coupée : {int(jeter.sum())} faces au sol")
        m.update_faces(~jeter); m.remove_unreferenced_vertices()
    return m

def alleger(m, cible=CIBLE):
    if len(m.faces) <= cible: return m
    v, f = fast_simplification.simplify(np.asarray(m.vertices, dtype=np.float32),
                                        np.asarray(m.faces, dtype=np.int32),
                                        1 - cible/len(m.faces))
    return trimesh.Trimesh(vertices=v, faces=f, process=False)

def couleurs(m, img_path):
    a = np.asarray(Image.open(img_path).convert('RGB')).astype(int); H,W,_ = a.shape
    bg = np.concatenate([a[:,:8].reshape(-1,3), a[:,-8:].reshape(-1,3), a[:8,:].reshape(-1,3)]).mean(0)
    mask = np.abs(a-bg).sum(2) > 60
    cols = np.nonzero(mask.sum(0) > H*0.01)[0]; rows = np.nonzero(mask.sum(1) > W*0.01)[0]
    x0,x1,y0,y1 = cols.min(), cols.max(), rows.min(), rows.max()
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    plein = a[idx[0], idx[1]]
    v, n = m.vertices, m.vertex_normals
    mn, mx = v.min(0), v.max(0)
    u = (v[:,0]-mn[0])/(mx[0]-mn[0]); w = (v[:,1]-mn[1])/(mx[1]-mn[1])
    px = np.clip((x0+u*(x1-x0)).astype(int), 0, W-1)
    py = np.clip((y1-w*(y1-y0)).astype(int), 0, H-1)
    c = plein[py, px].astype(float)
    cheveux = plein[int(y0+0.035*(y1-y0)), int((x0+x1)/2)].astype(float)
    tete = w > 0.84; dos = n[:,2] < -0.15
    c[tete & dos] = cheveux
    flou = tete & (n[:,2] >= -0.15) & (n[:,2] < 0.25)
    c[flou] = 0.5*c[flou] + 0.5*cheveux
    # les couleurs de l'image sont en sRGB ; glTF attend du linéaire
    lin = (np.clip(c,0,255)/255.0) ** 2.2 * 255.0
    m.visual = trimesh.visual.ColorVisuals(mesh=m, vertex_colors=lin.astype(np.uint8))
    return m

if __name__ == "__main__":
    src, ref, out = sys.argv[1], sys.argv[2], sys.argv[3]
    m = trimesh.load(src, force='mesh', process=False)
    n0 = len(m.faces)
    m = orienter(m); m = retirer_socle(m); m = couper_dalle(m); m = alleger(m); m = couleurs(m, ref)
    m.export(out)
    print(f"{out}: {n0} -> {len(m.faces)} faces, taille {np.round(m.extents,2)}")
