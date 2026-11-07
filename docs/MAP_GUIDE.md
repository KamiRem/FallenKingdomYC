# Carte naturelle

La variante nettoyée est `runtime/map-v2-fixes`, avec les mêmes centres et monuments.
Les opérations ponctuelles et limites de recette figurent dans [V2_CORRECTIONS.md](V2_CORRECTIONS.md).

## Version compacte actuelle

La candidate v2 se trouve dans `runtime/map-v2`, avec une bordure de **1 200 blocs**,
quatre terrains de rayon 80, quatre drapeaux et sept monuments réellement placés.
Le guide de chantier et les comparaisons techniques sont dans [MAP_V2.md](MAP_V2.md).
Utiliser [le carnet d'inspection](MAP_V2_INSPECTION.md) pour les coordonnées relevées.
Le profil historique de 1 800 blocs reste conservé dans `runtime/local`.

Les indications de génération ci-dessous restent celles du monde source et de son
profil historique. Elles ne doivent pas écraser une carte v2 déjà construite.

## Méthode retenue

Génération vanilla Minecraft 26.2 avec graine fixe, structures vanilla actives et
bordure carrée de **1 800 blocs** centrée sur 0,0. Aucun schéma de château, fort ou
salle des coffres n'est importé. La variété réelle des biomes et reliefs dépend de
la graine ; elle doit être inspectée, et n'est jamais déduite du seul numéro de graine.

| Méthode étudiée | Avantages | Limites | Choix |
|---|---|---|---|
| Vanilla + sélection de graine | Ressources naturelles, aucune dépendance, grottes et reliefs récents | Choisir et inspecter les terrains | Retenue |
| Carte existante | Direction artistique maîtrisée | Licence, ressources survival, version et bases à vérifier | Import préparé |
| Vanilla + schémas | Quelques ruines choisies | Butin et dépendance WorldEdit à vérifier | Option ultérieure, aucun schéma fourni |
| WorldPainter / générateur dédié | Contrôle du relief | Travail manuel, couches minières/structures et compatibilité à vérifier | Non nécessaire pour huit joueurs |

`maps/v1-manifest.json` conserve la graine et les anciennes zones candidates.
`maps/manifest.json` référence la candidate v2 construite dans ce workspace.
Ces manifestes ne prétendent pas qu'un monde existe sur un nouveau clone.
Le monde effectivement généré se trouve dans `runtime/<nom>/world` ; consulter le
rapport de tests pour distinguer génération exécutée et inspection manuelle restante.

## Prégénération

La graine retenue est **123456789**, après sondage réel de six graines supplémentaires
avec neuf points dans chacun des quatre secteurs. Les 216 mesures sont disponibles
dans `maps/seed-survey.csv`. La première graine `728461903257` a été rejetée : deux
secteurs océaniques et deux secteurs enneigés ne correspondaient pas au projet.

| Secteur candidat, graine retenue | Observations réelles aux neuf points |
|---|---|
| Rouge, nord-ouest | Prairie et forêts de bouleaux, relief plus élevé, bosquets en hauteur |
| Bleue, nord-est | Forêt de bouleaux et vieux bouleaux, huit points sans eau de surface |
| Verte, sud-ouest | Plaines, cerisiers et rivière |
| Jaune, sud-est | Forêts, rivière et jardin pâle à l'ouest ; déplacer le centre vers un terrain sûr hors du jardin pâle |

Les altitudes du sondage sont celles de la surface supérieure, parfois la canopée,
et ne sont pas des altitudes de téléportation sûres. Ce relevé justifie le choix de
la graine ; l'équilibre minier, les structures et les accès restent à inspecter.

Dans la console avant la partie :

```text
fka pregen
```

La tâche charge au plus trois chunks asynchrones à la fois jusqu'à la bordure avec une marge de
32 blocs, demande son déchargement puis termine par une sauvegarde. La génération
reste naturelle ; elle ne construit pas de fort. Ne pas jouer pendant cette opération.
Le Nether sera exploré naturellement au jour 2 ; sa bordure est de 225 blocs de côté
(rapport 8:1). L'End reste fermé.

Ne pas confondre la bordure avec les limites des royaumes. Les quatre territoires
sont des carrés d'environ 201 × 201 blocs pour un rayon de 100, sur toute la hauteur.
La bordure mondiale laisse une grande zone neutre pour l'exploration et le combat.

## Inspection et choix des quatre territoires

Les points `(-500,-500)`, `(500,-500)`, `(-500,500)`, `(500,500)` sont uniquement des
candidats géométriques. Leur altitude est inconnue avant génération. Ne pas y envoyer
les joueurs sans vérifier le terrain. Les deux voisins seraient distants d'environ
1 000 blocs, soit quelques minutes de déplacement selon le relief.

Avec le compte d'administration avant lancement :

1. Explorer chacun des quatre quarts en créatif, depuis un point sûr. Vérifier sol
   solide et espace debout au point de départ ; éviter mer, volcan de lave, fosse,
   falaise infranchissable et sommet extrême.
2. Rechercher bois, pierre, nourriture, eau et accès souterrain dans un rayon comparable.
   Comparer distance au centre, dénivelé, rivières et accès entre les bases.
3. Refuser un territoire contenant un village défendable, manoir, poste de pillards,
   ruine exploitable comme fort ou structure donnant un butin décisif. Déplacer le
   centre ; si le quart entier est mauvais, tester une autre graine dans une nouvelle instance.
4. Conserver des défenses naturelles différentes mais pas une seule base presque
   inaccessible. Une rivière ou une montagne doit laisser plusieurs approches légitimes.
5. Se placer sur un terrain naturel, puis `/fka territory Rouge 100` et `/fka spawn Rouge`.
6. Exécuter `/fka survey` pour obtenir un CSV hauteur/biome autour des centres. Avant
   définition, les quatre candidats ±500 sont utilisés. Ce sondage ne mesure pas les
   minerais et ne certifie pas l'équilibre.
7. Après vérification, `/fka terrain Rouge confirm`, puis les trois autres équipes.

Le lancement reste bloqué tant que les quatre confirmations ne sont pas enregistrées.
Ces confirmations relèvent d'un contrôle humain, pas d'une preuve automatique.

## Structures d'exploration

Garder quelques villages, ruines, temples ou mines en zone neutre. Ils ne doivent pas
remplacer un fort, et le butin doit être raisonnablement accessible aux quatre équipes.
Marquer dans votre carnet d'arbitrage privé les structures retenues et les distances,
sans fournir de carte révélant les salles cachées. Si trop de structures importantes
se concentrent dans un quart, préférer une autre graine ou déplacer les territoires.

Ce projet n'ajoute aucun butin custom, aucune construction préfabriquée et aucun
coffre objectif prédéfini. Le coffre déclaré est posé par l'équipe pendant le jeu.

## Importer un monde existant

Utiliser une carte librement utilisable ou une carte dont vous avez obtenu l'autorisation.
Conserver l'attribution et sa licence dans un fichier privé de provenance. Le projet
ne fournit aucune carte tierce dont les droits seraient incertains.

Installer une instance neuve sans la lancer, puis :

```powershell
.\scripts\server.ps1 import-world -Name carte-importee -Source 'C:\Cartes\MonMonde'
```

Le dossier doit contenir `level.dat`. Le script refuse une source verrouillée, un lien
symbolique ou le remplacement d'un monde existant. Ne jamais rétrograder une carte
ouverte en 26.3 vers 26.2.

Minecraft/Paper 26.x emploie une organisation des dimensions différente des anciens
dossiers `world_nether` et `world_the_end`. Copier **tout le dossier world** et vérifier
le résultat au démarrage. Pour une carte ancienne Spigot, effectuer sa migration dans
une copie de travail avec la procédure officielle Paper, puis l'inspecter avant jeu.
Le script ne prétend pas convertir arbitrairement tous les formats historiques.

[Guide Paper des mises à jour 26.1](https://papermc.io/news/26-1/)
