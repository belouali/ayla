#!/bin/zsh
# compose.sh <mix.wav> <out.mp4> : overlays the text layer on the 3D layer and adds the soundtrack
set -e
cd "$(dirname "$0")"
FF=$(/opt/homebrew/opt/python@3.11/bin/python3.11 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -framerate 30 -i frames_base/f%05d.jpg -framerate 30 -i frames_ui/f%05d.png -i "$1" -filter_complex "[0:v][1:v]overlay=0:0:format=auto[v]" -map "[v]" -map 2:a -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart -map_metadata -1 -metadata title="Ayla & FriendLoop – Teaser" -metadata artist="Saida Belouali" "$2"
"$FF" -v error -i "$2" -f null - 2>&1 | head -2
"$FF" -y -loglevel error -i "$2" -vf scale=1280:720 -c:v libx264 -preset medium -crf 24 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -map_metadata -1 -metadata title="Ayla & FriendLoop – Teaser" -metadata artist="Saida Belouali" "${2%.mp4}_720p.mp4"
ls -la "$2" "${2%.mp4}_720p.mp4"
