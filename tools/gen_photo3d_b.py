import json, base64, os, urllib.request, re, sys
K=open(os.path.expanduser('~/.config/openrouter/key')).read().strip()
H={"Authorization":"Bearer "+K,"Content-Type":"application/json","HTTP-Referer":"https://belouali.github.io/ayla/","X-Title":"Ayla teaser"}
base=("Trois personnages cadrés en buste, regard caméra, sourires discrets, dans un appartement chaleureux rempli de livres et de dossiers de recherche, lumière douce. "
 "Au centre une adolescente de 16 ans, peau hâlée, cheveux bruns coupés au carré avec une frange, veste jaune matelassée, un petit carnet en papier à la main. "
 "À gauche sa mère, chercheuse d'une quarantaine d'années, cheveux sombres, chemise bleu clair rayée, foulard rouge. À droite son père, chercheur d'une quarantaine d'années, plus grand, veste bleu nuit à boutons, nez marqué, sourcils épais. "
 "Aucun texte, aucun logo, aucun filigrane. Format paysage 4:3.")
STYLES=[("stopmotion","Photographie d'un plateau de film d'animation en stop-motion : trois marionnettes articulées en tissu, feutre et bois peint, coutures visibles, petites imperfections, décor miniature construit à la main, lumière de plateau douce, léger grain de pellicule. Aucune brillance plastique, pas de rendu numérique lisse. "),
        ("peinture","Illustration peinte à la gouache et au crayon, façon album jeunesse contemporain : coups de pinceau visibles, papier texturé, couleurs sobres et un peu ternes, visages simples et sincères, composition posée comme une photo de famille. Pas de rendu numérique lisse, pas de visages symétriques parfaits. "),
        ("jeu","Capture d'écran d'un jeu vidéo indépendant en 3D à l'esthétique volontairement simple : personnages aux formes rondes et aux textures mates, ombrage doux sans reflets, couleurs un peu désaturées, décor épuré, comme une scène jouée dans le moteur du jeu. Pas de rendu cinématographique, pas de peau brillante. ")]
for k,st in STYLES:
    payload={"model":"google/gemini-3.1-flash-image","modalities":["image","text"],"messages":[{"role":"user","content":st+base}]}
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=json.dumps(payload).encode(),headers=H),timeout=300))
        ims=r["choices"][0]["message"].get("images") or []
        if not ims: print(k,"no image"); continue
        url=ims[0]["image_url"]["url"]; b=re.sub(r"^data:image/\w+;base64,","",url); ext="png" if "png" in url[:30] else "jpg"
        open(f"photo3d_{k}.{ext}","wb").write(base64.b64decode(b)); print("OK",k,ext)
    except Exception as e: print(k,"ERR",str(e)[:150])
