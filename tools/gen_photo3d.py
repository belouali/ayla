import json, base64, os, urllib.request, re, sys
K=open(os.path.expanduser('~/.config/openrouter/key')).read().strip()
H={"Authorization":"Bearer "+K,"Content-Type":"application/json","HTTP-Referer":"https://belouali.github.io/ayla/","X-Title":"Ayla teaser"}
base=("Trois personnages cadrés en buste, regard caméra, sourires discrets, dans un appartement chaleureux rempli de livres et de dossiers de recherche, lumière douce. "
 "Au centre une adolescente de 16 ans, peau hâlée, cheveux bruns coupés au carré avec une frange, veste jaune matelassée, un petit carnet en papier à la main. "
 "À gauche sa mère, chercheuse d'une quarantaine d'années, cheveux sombres, chemise bleu clair rayée, foulard rouge. À droite son père, chercheur d'une quarantaine d'années, plus grand, veste bleu nuit à boutons, nez marqué, sourcils épais. "
 "Aucun texte, aucun logo, aucun filigrane. Format paysage 4:3.")
STYLES=[("pixar","Rendu 3D de film d'animation moderne, style Pixar ou DreamWorks : personnages stylisés aux grands yeux expressifs, formes douces et arrondies, peau et tissus détaillés, éclairage cinématographique. "),
        ("clay","Rendu 3D stylisé façon figurines en argile ou en vinyle de collection, très propres et légèrement brillantes, profondeur de champ, éclairage de studio chaleureux. "),
        ("lowpoly","Rendu 3D d'un jeu vidéo indépendant contemporain : personnages stylisés à proportions cartoon mais visages modelés et expressifs, textures propres, éclairage doux, esprit d'un jeu d'aventure narratif. ")]
for k,st in STYLES:
    payload={"model":"google/gemini-3.1-flash-image","modalities":["image","text"],"messages":[{"role":"user","content":st+base}]}
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=json.dumps(payload).encode(),headers=H),timeout=300))
        ims=r["choices"][0]["message"].get("images") or []
        if not ims: print(k,"no image"); continue
        url=ims[0]["image_url"]["url"]; b=re.sub(r"^data:image/\w+;base64,","",url); ext="png" if "png" in url[:30] else "jpg"
        open(f"photo3d_{k}.{ext}","wb").write(base64.b64decode(b)); print("OK",k,ext)
    except Exception as e: print(k,"ERR",str(e)[:150])
