import json, base64, os, subprocess, urllib.request, re, sys
exec(open('gen_voices2.py').read().split('os.makedirs("sys"')[0])
TAKES=[("a2_prise1","Ils étaient là, hier…","Ayla, 16 ans, voix basse et triste, incrédule, comme pour elle-même. Marque une courte pause après « là », puis « hier » clairement articulé, en laissant la phrase en suspens."),
       ("a2_prise2","Ils étaient là hier…","Ayla, 16 ans, la gorge serrée, lente, chaque mot détaché : « ils », « étaient », « là », « hier ». Pas de souffle exagéré."),
       ("a2_prise3","Ils étaient là, hier.","Ayla, 16 ans, voix jeune et naturelle, abattue, débit normal, ton d'évidence douloureuse.")]
for k,t,tone in TAKES:
    take(k,"coral",tone,t,"la comédienne qui joue Ayla, 16 ans",outdir="vo2")
    subprocess.run([FF,"-y","-loglevel","error","-i",f"vo2/{k}.wav","-af","silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse","-c:a","libmp3lame","-q:a","3",f"{k}.mp3"],check=True)
