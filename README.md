# Ayla et FriendLoop

Conte-jeu sur l'éthique de l'intelligence artificielle, d'après la Recommandation de l'UNESCO.
Autrice : Saida Belouali.

Jeu en ligne : https://belouali.github.io/ayla/
Dépôt : https://github.com/belouali/ayla (branche `main` = site en ligne, `style-f` = refonte graphique)

## Organisation du dossier

- `jeu/` — sources du jeu
  - `game.html` : version publiée en ligne, tout est dans ce fichier unique (3D, textes FR/EN/AR, sons)
  - `game_styleF.html` : branche graphique, matières mates, ombres, têtes sculptées
- `site/` — dépôt git cloné ; `index.html` est construit à partir de `jeu/game.html`
- `teaser/`
  - `scripts/` : moteur de rendu du teaser et chaîne de montage
  - `voix/` : répliques enregistrées, `systeme/` pour la voix robotique
  - `rendus/` : dernière vidéo, 1080p et 720p, plus la bande son
- `personnages/`
  - `references/` : planches de référence des personnages et image de style
  - `modeles/` : modèles 3D générés
  - `scripts/` : génération des références, des voix, et projection des couleurs
- `documents/` : conte, scénario du teaser, logos

## Publier une nouvelle version du jeu

    ./publier.sh "Message du commit"

Le script reconstruit `site/index.html` depuis `jeu/game.html`, écrit un numéro de version,
pousse sur GitHub et attend que la page en ligne soit à jour. Le jeu vérifie sa version au
chargement et se recharge seul si une version plus récente existe.

## Fabriquer le teaser

Le teaser est calculé image par image à partir du moteur du jeu, en deux couches :
la 3D d'un côté, les textes et cartons de l'autre. Une retouche de texte ne demande donc
pas de recalculer la 3D. `teaser/scripts/compose_final.sh` assemble le tout avec la bande son.

## Clés d'accès

Stockées hors du dossier, lisibles par vous seul :
- OpenRouter : `~/.config/openrouter/key` (voix et images de référence)
- Tripo : `~/.config/tripo/key` (crédits d'interface à zéro pour l'instant)

## État et suite

Fait : prologue et deux missions, trois langues, carte de Chroma, Dôme mémoriel meublé,
course propre à chaque mission, teaser de 95 secondes.
En cours : remplacement des personnages par des modèles 3D générés depuis les planches de
référence. Ayla est faite, sans texture fine. Il manque un jeton Hugging Face pour
débloquer la texture, puis les trois autres personnages, puis le squelette d'animation.

## Branche ayla2 : personnages modelés et animés

Ayla, Saren, Kade et Elio (masqué ou non) sont des modèles 3D texturés, dotés d'un
squelette de dix-neuf os et de trois animations cuites : repos, marche et course.
Le jeu les charge au démarrage (`assets/personnages/anim/*.glb`) et les anime avec
un mélangeur Three.js : fondus enchaînés entre les allures, pas qui reprend au même
point du cycle entre marche et course, foulée suspendue pendant les sauts. Tant qu'un
modèle n'est pas chargé, la silhouette dessinée d'origine reste en place.

Fabrication (dossier `tools/rig/`) : `articulations.json` donne la position des
articulations relevée sur des vues de face quadrillées ; `rig.py` construit le
squelette dans Blender, calcule les poids sur un double revoxelisé puis les transfère,
retire les faces tendues entre les jambes et cuit les animations ; `planche.py`
produit les planches de contrôle.

Construction : `./publier_ayla2.sh` depuis le dossier AYLA ; avec un message, il
commite et pousse la branche. Aperçu : https://raw.githack.com/belouali/ayla/ayla2/index.html

### Matériaux de la ville

Chaussée, sol, trottoirs, place et façades de la ville reçoivent des matériaux réels de
Poly Haven (licence CC0) : `asphalt_02`, `concrete_pavement_02`, `concrete_pavers_02`,
`concrete_tile_facade`, et le ciel nocturne `shanghai_bund` pour les reflets. Ils sont posés
en détail dans l'espace du monde (fonction `detailler`) : chaque surface garde son dessin
(marquages, fenêtres) et gagne le grain, le relief et la rugosité de la matière.
