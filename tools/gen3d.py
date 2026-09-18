from gradio_client import Client, handle_file
import os, shutil, sys, time
T=open(os.path.expanduser('~/.config/hf/token')).read().strip()
def gen(nom, img, endpoint="/generation_all", **kw):
    t0=time.time()
    c=Client("tencent/Hunyuan3D-2.1", token=T, verbose=False)
    p=dict(image=handle_file(img), steps=30, guidance_scale=5.0, octree_resolution=256,
           check_box_rembg=True, num_chunks=8000, randomize_seed=False, seed=1234)
    p.update(kw)
    r=c.predict(api_name=endpoint, **p)
    outs = r if isinstance(r,(list,tuple)) else [r]
    got=[]
    for x in outs:
        v = x.get('value') if isinstance(x,dict) else x
        if isinstance(v,str) and os.path.exists(v) and v.lower().endswith(('.glb','.obj','.ply')):
            dst=f"assets/gen/{nom}_texture{os.path.splitext(v)[1]}"
            shutil.copy(v,dst); got.append((dst, os.path.getsize(dst)//1024))
    print(nom, "->", got, "en", round(time.time()-t0), "s")
    return got
if __name__=="__main__":
    nom=sys.argv[1]; img=sys.argv[2]
    ep=sys.argv[3] if len(sys.argv)>3 else "/generation_all"
    try: gen(nom, img, ep)
    except Exception as e: print("ECHEC", nom, "|", str(e)[:300])
