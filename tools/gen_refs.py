import json, base64, os, re, urllib.request, sys
K=open(os.path.expanduser('~/.config/openrouter/key')).read().strip()
H={"Authorization":"Bearer "+K,"Content-Type":"application/json","HTTP-Referer":"https://belouali.github.io/ayla/","X-Title":"Ayla refs"}
STYLE=("Personnage de film d'animation 3D stylisé, rendu propre et mat, éclairage de studio doux et neutre, "
 "corps entier des pieds à la tête, cadrage centré, personnage debout de face, bras légèrement écartés du corps, pose neutre et symétrique, "
 "fond gris clair uni et parfaitement vide, aucune ombre portée marquée, aucun texte, aucun logo, aucun filigrane, aucun accessoire hors du personnage. Format portrait.")
CHARS={
 "ayla":"Une adolescente de 16 ans, peau hâlée, cheveux bruns coupés au carré avec une frange droite, veste matelassée jaune moutarde fermée, jean bleu foncé, baskets blanches, petit carnet en papier tenu dans la main droite le long du corps. Expression calme et déterminée.",
 "saren":"Un très vieil homme conteur, longue barbe blanche fournie et moustache blanche, cheveux blancs, visage ridé et bienveillant, longue toge de bure brun-beige à la texture rugueuse comme venue d'un autre temps, capuche rabattue dans le dos, corde en guise de ceinture, sandales, un bâton de bois simple tenu dans la main gauche.",
 "kade":"Un homme âgé du quartier populaire, moustache blanche épaisse, casquette de toile verte, veste de travail verte boutonnée, écharpe jaune, pantalon vert foncé, chaussures sombres, ceinture de cuir à boucle dorée. Allure chaleureuse et un peu bourrue.",
 "elio":"Un jeune technicien de maintenance, combinaison de travail bleu nuit avec fermeture éclair et poches poitrine, ceinture à outils, gants, cheveux bruns en bataille, expression prudente. Sans casque ni visière, visage entièrement visible.",
}
VIEWS={"face":"Vue de face, le personnage regarde droit vers l'objectif.","dos":"Vue de dos exactement, même personnage, mêmes vêtements et mêmes couleurs, on ne voit pas le visage."}
todo=sys.argv[1:] or ["ayla:face","saren:face","kade:face","elio:face"]
for t in todo:
    name,view=t.split(":")
    prompt=STYLE+" "+VIEWS[view]+" "+CHARS[name]
    payload={"model":"google/gemini-3.1-flash-image","modalities":["image","text"],"messages":[{"role":"user","content":prompt}]}
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=json.dumps(payload).encode(),headers=H),timeout=300))
        ims=r["choices"][0]["message"].get("images") or []
        if not ims: print(name,view,"pas d'image"); continue
        u=ims[0]["image_url"]["url"]; b=re.sub(r"^data:image/\w+;base64,","",u); ext="png" if "png" in u[:30] else "jpg"
        p=f"refs/{name}_{view}.{ext}"; open(p,"wb").write(base64.b64decode(b)); print("OK",p,os.path.getsize(p)//1024,"KB")
    except Exception as e: print(name,view,"ERR",str(e)[:160])
