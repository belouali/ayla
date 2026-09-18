import json, base64, os, subprocess, urllib.request, re, sys
exec(open('gen_voices2.py').read().split('os.makedirs("sys"')[0])
TAKES=[("p1_a","Qui ?","verse","Un passant adulte, la trentaine, pressé, interrompu en pleine rue par une adolescente inconnue. Il répond d'un seul mot, distrait et perplexe, sans intérêt, comme quelqu'un qui n'a jamais entendu ces noms. Ton parlé, naturel, pas théâtral."),
       ("p1_b","Qui ça ?","verse","Un passant adulte pressé, interrompu dans la rue. Il répond spontanément, avec une vraie perplexité, sur le ton de la conversation ordinaire, sans dramatiser."),
       ("p1_c","Qui ?","ballad","Un passant adulte indifférent, qui ralentit à peine et repart aussitôt. Un « Qui ? » bref, sec et désintéressé, comme s'il n'avait pas vraiment écouté.")]
for k,t,voice,tone in TAKES:
    if take(k,voice,tone,t,"un passant croisé dans la rue",outdir="vo2"):
        subprocess.run([FF,"-y","-loglevel","error","-i",f"vo2/{k}.wav","-af","silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.2,areverse",f"vo4/{k}.wav"],check=True)
        subprocess.run([FF,"-y","-loglevel","error","-i",f"vo4/{k}.wav","-c:a","libmp3lame","-q:a","3",f"{k}.mp3"],check=True)
        print(k,"dur",subprocess.run([FF,"-i",f"vo4/{k}.wav"],capture_output=True,text=True).stderr.split("Duration:")[1][:12])
