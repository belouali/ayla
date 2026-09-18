#!/bin/zsh
# Publie jeu/game.html sur https://belouali.github.io/ayla/
set -e
cd "$(dirname "$0")"
[ -n "$1" ] || { echo "usage: ./publier.sh \"message du commit\""; exit 1; }
BUILD=$(date +%Y%m%d%H%M%S)
/usr/bin/python3 - "$BUILD" <<'PY'
import sys
build=sys.argv[1]
lignes=open('jeu/game.html',encoding='utf-8').read().split('\n')
corps='\n'.join(lignes[2:]).replace('__BUILD__',build)
html=('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
 '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
 '<title>Ayla et FriendLoop</title>\n'
 '<meta name="description" content="Conte-jeu sur l\'éthique de l\'intelligence artificielle. '
 'Prototype 3D jouable en français, anglais et arabe.">\n</head>\n<body>\n'+corps+'\n</body>\n</html>\n')
open('site/index.html','w',encoding='utf-8').write(html)
open('site/version.json','w').write('{"build":"%s"}\n'%build)
print('site construit', build)
PY
cd site && git add -A && git commit -q -m "$1" && git push -q origin main && git log --oneline -1
for i in $(seq 1 16); do
  if curl -s "https://belouali.github.io/ayla/version.json?ts=$RANDOM" | grep -q "$BUILD"; then echo "en ligne"; break; fi
  echo "attente de la mise en ligne ($i)"; sleep 15
done
