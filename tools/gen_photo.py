import json, base64, os, urllib.request, re, sys
K=open(os.path.expanduser('~/.config/openrouter/key')).read().strip()
H={"Authorization":"Bearer "+K,"Content-Type":"application/json","HTTP-Referer":"https://belouali.github.io/ayla/","X-Title":"Ayla teaser"}
models=json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/models",headers=H)))["data"]
img=[m["id"] for m in models if "image" in (m.get("architecture",{}).get("output_modalities") or [])]
print("image models:",img)
pref=[m for m in img if "gemini" in m and "image" in m]+[m for m in img if "openai" in m]+img
prompt=("Photographie de famille réaliste, prise dans un appartement lumineux rempli de livres et de documents de recherche, lumière douce de fin d'après-midi, léger grain argentique. "
 "Trois personnes cadrées en buste, regard caméra, sourires discrets : au centre une adolescente de 16 ans, peau hâlée, cheveux bruns coupés au carré, veste jaune matelassée ; "
 "à sa gauche sa mère, chercheuse d'une quarantaine d'années, cheveux sombres attachés, chemise claire ; à sa droite son père, chercheur d'une quarantaine d'années, barbe courte, lunettes, pull sombre. "
 "Aucun texte, aucun logo, aucun filigrane. Format paysage 4:3.")
for mid in pref[:3]:
    try:
        payload={"model":mid,"modalities":["image","text"],"messages":[{"role":"user","content":prompt}]}
        r=json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=json.dumps(payload).encode(),headers=H),timeout=300))
        msg=r["choices"][0]["message"]; ims=msg.get("images") or []
        if not ims: print(mid,"no image", str(msg)[:200]); continue
        url=ims[0]["image_url"]["url"]; b=re.sub(r"^data:image/\w+;base64,","",url); ext="png" if "png" in url[:30] else "jpg"
        open("family_photo."+ext,"wb").write(base64.b64decode(b)); print("OK",mid,"family_photo."+ext, len(b)//1024,"KB"); break
    except Exception as e:
        print(mid,"ERR",str(e)[:200])
