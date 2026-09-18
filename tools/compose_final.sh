#!/bin/zsh
# compose_final.sh <mix.wav> <out.mp4> : opening card + (3D layer ⊕ text layer) + soundtrack
set -e; cd "$(dirname "$0")"
FF=$(/opt/homebrew/opt/python@3.11/bin/python3.11 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -framerate 30 -i frames_intro/f%05d.jpg -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -an part_intro.mp4
"$FF" -y -loglevel error -framerate 30 -i frames_base/f%05d.jpg -framerate 30 -i frames_ui/f%05d.png -filter_complex "[0:v][1:v]overlay=0:0:format=auto[v]" -map "[v]" -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -an part_main.mp4
printf "file 'part_intro.mp4'\nfile 'part_main.mp4'\n" > parts.txt
"$FF" -y -loglevel error -f concat -safe 0 -i parts.txt -c copy part_all.mp4
"$FF" -y -loglevel error -i part_all.mp4 -i "$1" -filter_complex "[1:a]apad=pad_dur=2[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t 95.6 -movflags +faststart -map_metadata -1 -metadata title="Ayla & FriendLoop – Teaser" -metadata artist="Saida Belouali" "$2"
"$FF" -v error -i "$2" -f null - 2>&1 | head -2
"$FF" -y -loglevel error -i "$2" -vf scale=1280:720 -c:v libx264 -preset fast -crf 24 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -map_metadata -1 -metadata title="Ayla & FriendLoop – Teaser" -metadata artist="Saida Belouali" "${2%.mp4}_720p.mp4"
"$FF" -i "$2" 2>&1 | grep -o "Duration: [0-9:.]*"; ls -la "$2" "${2%.mp4}_720p.mp4"
