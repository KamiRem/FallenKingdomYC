# Variante locale — quatre cavernes naturelles

> **Variante abandonnée le 23 novembre 2026 à la demande du propriétaire.**
> Archives et preuves conservées comme historique ; ne pas déployer cette carte.
> Voir la [révision V2.2 avec terrain d'origine](V22_VANILLA_UNDERGROUND_20261123.md).

**V2.1-natural-caverns-r2 est prête pour inspection visuelle. Aucun déploiement autorisé ou effectué.**

Le propriétaire a précisé que la refonte concerne **les quatre équipes**. Cette
précision remplace le périmètre « une seule caverne » de la mission initiale.
La carte en recette sur MineStrator n'a pas été consultée ni modifiée pendant
ce travail. Le [reçu technique](../tests/results/natural-caverns-20261121.json)
consigne les résultats sans publier les mondes ou coordonnées de visite.

## Construction et rendu proposé

Source : copie initiale approuvée `V21-QUERY-20261120-01/preproduction-candidate`,
dont le manifeste reste
`bc99993cf2796991a97adf92c12091bea86e5b5166c503258d1311aa227948e6`.
Le premier essai est conservé dans `V21-NATURAL-20261121-01` ; la livraison
courante est dans **`C:\Users\youne\FKBackups\V21-NATURAL-20261121-02`**, hors Git.

Les anciennes salles elliptiques plates et leurs piliers colorés ont été
remplacés par des volumes verticaux, des parois en retrait selon la hauteur,
des sols accidentés, des corniches et des arches rocheuses incurvées. Les veines
de pierre, tuf et andésite suivent des motifs continus ; l'ardoise des abîmes
apparaît dans les parties basses. Une cascade avec bassin est prévue par équipe,
sans lave. Chaque équipe reçoit 24 plaques de lichen lumineux, sans blocs de
glowstone ajoutés ni piliers lumineux réguliers.

L'image fournie a guidé le langage visuel : profondeur, falaises rocheuses,
eau et relief organique. Elle n'a pas été reproduite littéralement.

| Équipe | Hauteur intérieure maximale | Volume d'air planifié | Positions de circulation accessibles | Marge territoriale minimale |
|---|---:|---:|---:|---:|
| Rouge | 39 blocs | 24 157 | 1 280 | 12 blocs |
| Bleue | 38 blocs | 24 105 | 1 294 | 12 blocs |
| Verte | 39 blocs | 24 341 | 1 277 | 12 blocs |
| Jaune | 37 blocs | 24 307 | 1 262 | 12 blocs |

Les anciennes salles comptaient environ 3 700 blocs d'air et onze blocs de
hauteur maximale. Le nouveau volume est beaucoup plus grand pour toutes les
équipes, avec moins de 1 % d'écart de volume entre elles. L'écart du graphe de
circulation reste inférieur à 3 %. Les accès existants, leurs marches et leur
passage sont conservés. Toutes les positions debout des quatre arches sont
reliées à l'accès dans le contrôle de circulation.

Le budget reste exactement **91 blocs de minerais par caverne** : 24 charbon,
24 fer, 16 cuivre, 12 redstone, 6 lapis, 6 or et 3 diamant. Aucun coffre de
récompense, équipement ou minerai supplémentaire n'est ajouté. Les minerais
placés sont accessibles depuis le chemin contrôlé. Le budget concerne le
chantier ; il ne prétend pas égaliser les minerais naturels du reste du monde.

## Comparaison et intégrité

**137 578 blocs modifiés dans 47 chunks et quatre régions Overworld.**
L'éditeur travaille hors ligne, sur une copie neuve, sous verrou de maintenance
local et verrous des mondes. Il refuse les références jouées et les destinations
existantes. La source approuvée est restée inchangée.

Les quatre fichiers de région modifiés sont :

```text
world/dimensions/minecraft/overworld/region/r.-1.-1.mca
world/dimensions/minecraft/overworld/region/r.-1.0.mca
world/dimensions/minecraft/overworld/region/r.0.-1.mca
world/dimensions/minecraft/overworld/region/r.0.0.mca
```

Les corps compressés de **4 049 chunks non ciblés** dans ces quatre régions
sont strictement identiques. Leurs horodatages sont conservés. Pour les chunks
ciblés, **4 812 800 cellules de blocs** ont été comparées : seuls les changements
prévus sont acceptés. Biomes, structures, block entities, inventaires et autres
champs NBT sont conservés. Les données d'éclairage des 47 chunks sont invalidées
explicitement pour recalcul par Paper ; ce changement technique est autorisé
dans la copie et a été validé par le chargement réel du moteur.

Les autres différences de fichiers sont limitées à :

- `DEPLOYMENT_MANIFEST.json`, recalculé pour cette variante ;
- `maintenance/new-match-reference.json` et
  `maintenance/new-match-reference-v2.1.json`, dont seule la partie cavernes évolue ;
- nouveaux `maintenance/new-match-reference-v2.1-natural.json` et
  `map-natural-caverns.json`.

Il y a donc **sept fichiers existants modifiés, deux créés, aucun supprimé** ;
298 fichiers source restent identiques. Les données de construction V2.1
historiques conservées dans le candidat décrivent l'ancien chantier ; le nouveau
plan privé et `map-natural-caverns.json` décrivent cette révision.
Les fichiers temporaires de verrouillage `.control.lock` et `session.lock`
sont exclus des copies et archives : chaque instance recrée ses propres verrous.
Les fichiers persistants du monde restent soumis à la comparaison d'intégrité.

Contrôles réussis :

- bases, spawns, quatre rayons 40, règles, protections et whitelist inchangés ;
- métadonnées du monde, fichiers d'entités et de points d'intérêt identiques ;
- sept monuments, 6 689 blocs de référence et six inventaires de coffres conformes ;
- huit sites de ravitaillement conservés ;
- quatre accès raccordés ; exploration des volumes passables sans ouverture
  souterraine hors des enveloppes, avec sortie limitée à la zone de l'accès existant ;
- voisinages des entités présentes évités, sans déplacement ni suppression ;
- référence initiale vérifiée sur 146 115 points de caverne ;
- profil `v21-minestrator` et **154 empreintes** du nouveau manifeste validés.

Paper 26.3-244, Java 25, FallenKingdom 2.24.9 et le JAR FKAmis sont inchangés.
La capacité reste 20, les effectifs de 1 à 4 par équipe, Query actif sur 22880.
L'état demeure jour 0 non lancé. Aucun inventaire de recette distant n'a été importé.
`AGENTS.md`, les sauvegardes historiques, leurs manifestes et les quarantaines
MineStrator n'ont pas été modifiés. Les SHA de l'archive historique -02 et de
son manifeste ont été recontrôlés.

## Essai Paper et limites

Une **seconde copie indépendante** `paper-validation` a démarré sur
`127.0.0.1:25624`, avec Query également lié au loopback. Une sonde séparée,
absente du candidat et des archives de livraison, a chargé les 47 chunks ciblés
et contrôlé les **137 578 états de blocs** via Bukkit. Les deux plugins de jeu,
les quatre spawns sûrs, les rayons 40 et les capacités ont été validés.

Après dix secondes de simulation, aucun nouveau bloc d'eau n'a été observé.
Le serveur local a terminé proprement : code 0, **zéro ERROR/SEVERE et zéro WARN**.
Le candidat livré est resté identique après ces essais. Les **135 tests Python**
passent, dont vingt tests spécifiques sur NBT, palettes, préservation des chunks,
confinement, chemins et supports de marche.

Ce n'est pas une inspection Minecraft avec un joueur. Le graphe de marche et
la courte simulation ne prouvent pas l'ergonomie de tous les passages, le ressenti
des chutes, l'équilibre PvE ou les performances à 17 connexions. Le lichen éclaire
moins que les anciennes lanternes : luminosité, lisibilité et rencontres de
monstres sont des points prioritaires de la visite. Les coordonnées restent
techniquement contrôlées, sans validation humaine acquise.

## Livrables privés et SHA-256

Tous les fichiers suivants sont dans `V21-NATURAL-20261121-02` :

| Fichier | Usage | SHA-256 |
|---|---|---|
| `v21-natural-caverns-r2-world-private.zip` | Monde complet de la variante et référence naturelle, 123 fichiers | `20a83fd467d37379b97964bffd6e5f6709318bd53d95319eab8b3a0a482aaa5a` |
| `v21-natural-caverns-r2-overlay-private.zip` | Neuf fichiers différents de la référence locale initiale | `b116540bd37114f27b0ec70816582db05032fb78b0001c406eb398d9dfae49e0` |
| `baseline-v21-world.zip` | Point de retour **V2.1 avant refonte**, 121 fichiers de monde | `5a08b894604a1e0ba4d75a00af2f8ea2bafc31cf08165cca91538e88063a1aa4` |

Chaque ZIP a été relu, contrôlé par CRC et comparé à son manifeste SHA-256.
Chaque archive possède un fichier `.sha256`. Le libellé de variante du manifeste
du ZIP baseline identifie l'opération de préparation ; **son contenu est bien
le monde V2.1 source, avant refonte**. Il ne remplace pas la sauvegarde complète
historique `MS-COLD-20261119-02`.

Autres livrables :

- `candidate/` : instance locale de référence, jamais démarrée ;
- `visual-inspection/` : copie de visite propre, préparée et arrêtée, sans sonde ;
- `previews/index.html` et cinq PNG : vues géométriques des quatre cavernes,
  plus une vue de l'ancienne Bleue ; textures et lumière schématiques,
  **ce ne sont pas des captures Minecraft** ;
- `chunks-modified-private.json` : liste exacte des 47 chunks, sections et SHA
  des quatre fichiers de région avant/après ;
- `natural-caverns-plan-private.json` : chaque bloc avant/après, emprises et contrôles ;
- `additional-checks-private.json`, `paper-validation-result.json` et journal Paper privé ;
- `rollback-control/` : restauration de contrôle des 121 fichiers du monde source ;
- `VISITE_LOCALE_PRIVEE.txt` : accès et téléportations vers les quatre entrées,
  à utiliser uniquement dans la console locale avec un compte déjà autorisé ;
- `SHA256SUMS.txt` : empreintes des archives, aperçus et preuves principales.

## Visite et retour arrière local

Ouvrir d'abord `previews/index.html`. Pour une visite Minecraft Java 26.3,
depuis le dépôt, démarrer **uniquement la copie de visite** :

```powershell
.\.tools\ms-audit\Scripts\python.exe -B scripts/natural_caverns_inspect.py --work C:\Users\youne\FKBackups\V21-NATURAL-20261121-02 --start
```

Se connecter à **`127.0.0.1:25625`** avec un compte présent dans la whitelist.
Aucun compte ou rôle n'est ajouté. Le rôle arbitre existant permet la visite.
Inspecter successivement les quatre accès, les plafonds, les corniches, les
arches, les bassins, la visibilité et les retours vers la base. Ne pas lancer
de partie. Saisir `stop` dans la console pour arrêter proprement.

La copie de visite seule conserve `restart-on-crash=false`, avec watchdog actif.
Elle peut recevoir les écritures normales de Paper et de la visite ; les archives
et `candidate/` restent le point de livraison immuable.

Pour annuler l'essai local : arrêter la copie, la conserver sous son nom, puis
repartir d'un **nouveau dossier** copié depuis la référence V2.1 source. Le ZIP
baseline fournit le monde initial ; sa restauration de contrôle est déjà vérifiée.
Pour reconstruire une instance complète, reprendre également les fichiers de jeu,
les deux anciennes références et le manifeste depuis la source intacte. Ne pas
superposer les deux variantes, ni modifier le rollback historique.

## Déploiement futur

**GO pour inspection visuelle ; NO-GO pour transfert distant.**

Cette variante provient de la référence initiale approuvée, pas d'une nouvelle
copie de la recette distante actuelle. L'overlay contient quatre **régions entières** :
il ne doit pas écraser une région où des données de recette ont évolué depuis.
Après validation du rendu et autorisation distincte, il faudra une sauvegarde
à froid actuelle dans le cadre de maintenance applicable, puis une comparaison
et une intégration locale contrôlée. En cas de divergence hors cavernes,
préparer un report des changements bloc par bloc ou une nouvelle instance
explicitement approuvée ; ne pas transférer les régions à l'aveugle.

Prévoir ensuite staging, SHA-256, quarantaine, rollback complet et recette.
Préserver les paramètres MineStrator et `restart-on-crash=false` déjà choisi.
Les archives de cette variante ne contiennent aucun JAR, whitelist,
`server.properties` ou `spigot.yml` à transférer. Le plan précédent de 148 fichiers
ne décrit pas cette variante et ne doit pas être réutilisé pour la déployer.
