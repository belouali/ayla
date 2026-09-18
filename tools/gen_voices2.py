import json, base64, os, subprocess, urllib.request, re, sys
exec(open('gen_voices.py').read().split('ONLY=set')[0].replace('for key,role,text in LINES:',''))
norm=lambda s: re.sub(r"[^a-zàâçéèêëîïôûùüÿœ ]","",s.lower()).strip()
def take(key,voice,tone,text,who,maxtries=4,outdir="vo2"):
    for attempt in range(maxtries):
        sysmsg=f"Séance de doublage. Tu es {who}. La réplique à enregistrer est, entre guillemets : « {text} ». Quand l'utilisateur dit « Action », tu prononces uniquement cette réplique, mot pour mot, rien d'autre : pas de réponse, pas de rire, pas de didascalie, pas de mot supplémentaire. Interprétation : {tone}"
        r=call({"model":"openai/gpt-audio","modalities":["text","audio"],"audio":{"voice":voice,"format":"wav"},"messages":[{"role":"system","content":sysmsg},{"role":"user","content":"Action."}]})
        tr=r.get("transcript","") if "error" not in r else "ERR"
        ok=norm(tr)==norm(text) or (norm(text) in norm(tr) and len(norm(tr))<len(norm(text))+12)
        print(key,attempt,"OK" if ok else "retry",repr(tr[:80]))
        if ok:
            open(f"{outdir}/{key}.pcm","wb").write(r["pcm"]); subprocess.run([FF,"-y","-loglevel","error","-f","s16le","-ar","24000","-ac","1","-i",f"{outdir}/{key}.pcm",f"{outdir}/{key}.wav"],check=True); return True
    return False
os.makedirs("sys",exist_ok=True)
# Ayla, new take
take("a2","coral","Ayla, 16 ans, la voix basse et brisée, incrédule et triste, comme si elle parlait pour elle-même, débit naturel, sans souffle exagéré.","Ils étaient là hier…","la comédienne qui joue Ayla, 16 ans")
# robotic system lines
SYS=[("s_acces","Accès refusé."),("s_ident","Identité non reconnue."),("s_profil","Aucun profil trouvé."),("s_compte","Compte inexistant."),("s_badge","Badge non valide."),("s_dossier","Dossier introuvable.")]
for k,t in SYS:
    take(k,"ash","un système automatique de contrôle d'accès : voix synthétique, monotone, débit parfaitement régulier, aucune émotion, articulation nette, ton administratif.",t,"la voix d'un système informatique automatisé",outdir="sys")
