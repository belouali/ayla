import json, base64, os, subprocess, urllib.request, re, sys
exec(open('gen_voices2.py').read().split('os.makedirs("sys"')[0])
TAKES=[("a2_prise4","Ils étaient là hier !","Ayla, 16 ans, ton conversationnel et rapide, surprise sincère, comme si elle protestait à voix haute devant l'écran : incrédule, un peu haletante, débit vif, sans tristesse."),
       ("a2_prise5","Mais… ils étaient là hier !","Ayla, 16 ans, surprise et incrédulité, débit rapide et naturel, comme une ado qui n'en revient pas, avec une petite hésitation sur « Mais »."),
       ("a2_prise6","Ils étaient là hier.","Ayla, 16 ans, phrase dite vite et simplement, sur le ton de la conversation, avec de la surprise dans la voix, sans dramatiser, sans pause au milieu.")]
for k,t,tone in TAKES:
    take(k,"coral",tone,t,"la comédienne qui joue Ayla, 16 ans",outdir="vo2")
    subprocess.run([FF,"-y","-loglevel","error","-i",f"vo2/{k}.wav","-af","silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse",f"vo4/{k}.wav"],check=True)
    subprocess.run([FF,"-y","-loglevel","error","-i",f"vo4/{k}.wav","-c:a","libmp3lame","-q:a","3",f"{k}.mp3"],check=True)
    d=subprocess.run([FF,"-i",f"vo4/{k}.wav"],capture_output=True,text=True).stderr.split("Duration:")[1][:12]; print(k,d)
