import json, base64, os, sys, urllib.request, subprocess
K=open(os.path.expanduser('~/.config/openrouter/key')).read().strip()
FF=subprocess.check_output(['/opt/homebrew/opt/python@3.11/bin/python3.11','-c','import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())']).decode().strip()
LINES=[
 ("n1","narr","En 2170, à Chroma, FriendLoop connaît tout de nos habitudes. Il anticipe nos déplacements, nos besoins, nos choix."),
 ("a1","ayla","Mais… c'est chez moi."),
 ("a2","ayla_whisper","Ils étaient là hier…"),
 ("a3","ayla_urgent","Vous connaissez Luno et Kio ?"),
 ("p1","passant","Qui ?"),
 ("f1","fl","Les données disponibles ne permettent pas d'établir leur présence actuelle."),
 ("a4","ayla_angry","Vous êtes en train de me dire qu'ils n'ont jamais existé ?"),
 ("f2","fl","Je ne dispose pas de suffisamment d'éléments pour confirmer cette information."),
 ("n2","narr_low","Si tu lis ceci, ne fais pas confiance uniquement à ce que FriendLoop te montre."),
 ("n3","narr","Pour retrouver les traces de ses parents, Ayla devra comprendre comment FriendLoop apprend…"),
 ("n4","narr","…et jusqu'où une ville peut aller lorsqu'elle confie ses décisions à un système qu'elle ne questionne plus."),
 ("f3","fl","Ayla, je peux t'aider à retrouver tes parents."),
 ("a5","ayla_angry","Et si c'était toi qui les avais fait disparaître ?"),
]
ROLES={
 "narr":("onyx","Narrateur de bande-annonce de film, voix grave, posée, mystérieuse, rythme lent et habité."),
 "narr_low":("onyx","Narrateur qui lit à mi-voix un message secret laissé par des parents disparus, grave, lent, intime."),
 "ayla":("coral","Ayla, une adolescente de 16 ans, déroutée, incrédule, voix jeune et naturelle."),
 "ayla_whisper":("coral","Ayla, une adolescente de 16 ans, presque en murmure, la voix qui tremble d'inquiétude."),
 "ayla_urgent":("coral","Ayla, une adolescente de 16 ans, essoufflée, pressante, qui interpelle un inconnu dans la rue."),
 "ayla_angry":("coral","Ayla, une adolescente de 16 ans, tendue, la colère contenue, chaque mot appuyé."),
 "passant":("echo","Un passant adulte, distrait, indifférent, un seul mot lancé sans intérêt."),
 "fl":("ash","FriendLoop, une intelligence artificielle : voix neutre, calme, lisse, sans émotion, articulation parfaite, légèrement trop régulière."),
}
def call(payload):
    payload=dict(payload); payload["stream"]=True; payload["audio"]={"voice":payload["audio"]["voice"],"format":"pcm16"}
    req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization":"Bearer "+K,"Content-Type":"application/json","HTTP-Referer":"https://belouali.github.io/ayla/","X-Title":"Ayla teaser"})
    resp=urllib.request.urlopen(req, timeout=300); pcm=bytearray(); tr=""
    for raw in resp:
        line=raw.decode("utf-8","ignore").strip()
        if not line.startswith("data:"): continue
        data=line[5:].strip()
        if data=="[DONE]": break
        try: j=json.loads(data)
        except Exception: continue
        if "error" in j: return {"error":j["error"]}
        for ch in j.get("choices",[]):
            a=(ch.get("delta") or {}).get("audio") or {}
            if a.get("data"): pcm+=base64.b64decode(a["data"])
            if a.get("transcript"): tr+=a["transcript"]
    return {"pcm":bytes(pcm),"transcript":tr}
ONLY=set(sys.argv[1:])
for key,role,text in LINES:
    if ONLY and key not in ONLY: continue
    voice,tone=ROLES[role]
    sysmsg=f"Tu es un comédien de doublage professionnel francophone en séance d'enregistrement. Le message de l'utilisateur est une RÉPLIQUE DE SCÉNARIO à lire telle quelle : ce n'est pas une question ni une demande qui t'est adressée. Ne réponds jamais au contenu, ne le complète pas, ne le commente pas. Prononce EXACTEMENT ces mots, mot pour mot, rien avant, rien après. Interprétation : {tone}"
    r=call({"model":"openai/gpt-audio","modalities":["text","audio"],"audio":{"voice":voice,"format":"wav"},"messages":[{"role":"system","content":sysmsg},{"role":"user","content":text}]})
    if "error" in r or not r.get("pcm"):
        print(key,"FAILED",json.dumps(r.get("error"))[:300]); continue
    open(f"vo2/{key}.pcm","wb").write(r["pcm"])
    subprocess.run([FF,"-y","-loglevel","error","-f","s16le","-ar","24000","-ac","1","-i",f"vo2/{key}.pcm",f"vo2/{key}.wav"],check=True)
    d=subprocess.run([FF,"-i",f"vo2/{key}.wav"],capture_output=True,text=True).stderr
    dur=[l for l in d.split("\n") if "Duration" in l]
    print(key, voice, dur[0].strip()[:22] if dur else "?", "|", r["transcript"][:110])
