import json, base64, os, subprocess, urllib.request, re
exec(open('gen_voices.py').read().split('ONLY=set')[0].replace('for key,role,text in LINES:',''))  # reuse K, FF, call(), ROLES
text="Vous connaissez Luno et Kio ?"; voice,tone=ROLES["ayla_urgent"]
norm=lambda s: re.sub(r"[^a-zàâçéèêëîïôûùüÿœ ]","",s.lower())
for attempt in range(4):
    sysmsg=f"Séance de doublage. Tu es la comédienne qui joue Ayla, 16 ans. La réplique à enregistrer est, entre guillemets : « {text} ». Quand l'utilisateur dit « Action », tu prononces uniquement cette réplique, mot pour mot, rien d'autre : pas de réponse, pas de rire, pas de didascalie, pas de mot supplémentaire. Interprétation : {tone}"
    r=call({"model":"openai/gpt-audio","modalities":["text","audio"],"audio":{"voice":voice,"format":"wav"},"messages":[{"role":"system","content":sysmsg},{"role":"user","content":"Action."}]})
    tr=r.get("transcript","") if "error" not in r else "ERR"
    print(attempt, repr(tr[:100]))
    if norm(tr).strip()==norm(text).strip() or (len(tr)<45 and "luno" in tr.lower() and "kio" in tr.lower()):
        open("vo2/a3.pcm","wb").write(r["pcm"]); subprocess.run([FF,"-y","-loglevel","error","-f","s16le","-ar","24000","-ac","1","-i","vo2/a3.pcm","vo2/a3.wav"],check=True)
        subprocess.run([FF,"-y","-loglevel","error","-i","vo2/a3.wav","-af","silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse","vo3/a3.wav"],check=True)
        print("OK a3", subprocess.run([FF,"-i","vo3/a3.wav"],capture_output=True,text=True).stderr.split("Duration:")[1][:12]); break
