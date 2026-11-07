# Carte v2 — chantier indépendant et validation

La **variante corrigée** se trouve désormais dans `runtime/map-v2-fixes`. La v2
décrite ci-dessous reste conservée dans `runtime/map-v2`. Le nettoyage ponctuel,
les corrections de règles et la commande de rassemblement sont détaillés dans
[V2_CORRECTIONS.md](V2_CORRECTIONS.md). Aucun nouveau chantier complet n'a été lancé.

La v2 est construite dans **`runtime/map-v2`**, à partir d'une copie intégrale de la
sauvegarde vérifiée du serveur initial. `runtime/local` reste l'instance historique.
Aucun monde n'est supprimé. La copie du premier chantier est conservée sous
`runtime/map-v2-build-1` ; la carte livrée est celle de `map-v2`.

## Livraison présente sur disque

Archive privée de la candidate arrêtée :
`dist/fallenkingdom-map-v2-20261107T011000Z.zip` (368 228 931 octets, 277 fichiers),
avec fichier `.zip.sha256` et manifeste interne vérifié.
SHA-256 : `493dcc51de68f9d98bc2113b94147d82dd3d2e898eb3473993c98c1622544d7c`.
Cette archive précède la validation humaine et ne doit pas être publiée.

Sauvegarde initiale conservée : `backups/local/fk-20261107T002410011936Z.zip`.
Les 268 fichiers de l'original ont été comparés à leur empreinte avant chantier et
sont inchangés. La preuve figure dans `tests/results/map-v2-preservation.json`.
Les profils de configuration livrés sont copiés dans `configs/map-v2/` ; ils ne
contiennent ni progression ni identité de joueur.

Le chantier a modifié 464 985 blocs sur la copie. Après redémarrage, 21 contrôles
réussissent sur le monde réel, dont les six lots fixes exacts. Le ravitaillement a
passé 42 contrôles initiaux et 6 après restauration complète. Mesures sans joueur :
19,93 / 19,85 TPS et 0,83 / 1,17 ms par tick, sur une attente de 200 ticks par phase.
La compilation et les 13 tests Java ainsi que les 12 tests Python sont réussis.
Ces résultats ne valident pas les performances à huit joueurs.

## Méthodes comparées

| Méthode | Intérêt pour ce projet | Décision |
|---|---|---|
| Nouvelle graine vanilla | Ressources et grottes natives | La graine 123456789 possède déjà du relief, des rivières et plusieurs biomes dans la zone compacte ; une nouvelle graine ne suffit pas à créer les lieux demandés |
| [Terralith](https://modrinth.com/datapack/terralith) | Génération serveur avec blocs vanilla, 26.2 déclaré | Son auteur déconseille l'ajout à un monde existant ; non installé pour éviter une nouvelle dépendance et des fortifications générées non contrôlées |
| [WorldEdit 7.4.6](https://hangar.papermc.io/EngineHub/WorldEdit/versions) | Édition d'un monde déjà généré ; support publié 1.21.4–26.3 | Alternative pertinente pour retouches manuelles ; non requis par le chantier automatisé |
| [FAWE](https://modrinth.com/plugin/fastasyncworldedit) | Manipulation efficace de grandes zones, 26.2 déclaré, GPL-3.0 | Pas nécessaire pour quatre petites zones et sept structures ; évite une dépendance supplémentaire |
| Carte / schematic tiers | Peut fournir une direction artistique aboutie | Aucun pack dont la licence ou la provenance serait incertaine n'a été utilisé |
| Outil Paper de chantier dédié | Accès direct au monde réel, opérations bornées et reproductibles | Retenu pour aménager la copie, puis retiré des plugins de jeu |

Les logiciels tiers ci-dessus n'ont pas été installés pour la production. Leur
compatibilité déclarée n'est pas présentée comme une recette locale effectuée.
Le chantier utilise exactement Paper 26.2 build 135 et Java 25 déjà présents.

## Carte compacte et terres de départ

Bordure **1 200 × 1 200**, centre 0,0. Les quatre centres ont été choisis après
mesure de 36 candidats, pas seulement à partir d'une formule. Territoires carrés
de **rayon 80**, soit 161 blocs inclusifs de côté, sans chevauchement.

Les coordonnées définitives figurent dans `maps/v2/built-manifest.json` et dans le
carnet de téléportation généré après vérification. Les voisins se situent entre
environ **408 et 482 blocs**, contre environ 1 000 auparavant. Une large croix
neutre et les lisières restent disponibles pour l'exploration et les combats.

Chaque zone possède un cœur constructible d'environ 48–64 blocs de large, de petites
variations de hauteur et une transition progressive vers le relief environnant.
Les déblais superficiels sont limités ; les remblaiements reposent sur le terrain,
sans plateforme flottante. Les cavernes et minerais profonds restent ceux du monde
vanilla copié. Les galeries minières et la crypte sont des interventions locales.

Les quatre paysages gardent leurs différences : cerisiers en hauteur, forêt, plaine
et bouleaux. Un mât de neuf blocs porte la couleur du royaume sur un petit socle.
Il est décoratif, n'est pas un objectif et n'a pas de protection invulnérable.
**Aucun château ni rempart d'équipe n'est construit par le chantier.**

Les confirmations `terrain ... confirm` restent à effectuer par l'arbitre après
inspection avec un client. Le chantier ne les coche pas automatiquement.

## Lieux réellement placés

Sept plans originaux figurent dans `maps/v2/structures/*.json`, sous la licence MIT
du projet. Ce format est un plan de blocs lu par `FKMapV2Builder`, **pas un `.schem`
WorldEdit**. Les fichiers sont exploitables par le script de chantier et leurs blocs
solides sont comparés aux blocs du monde lors de la vérification.

- Cercle des quatre vents : point de rencontre ouvert, sans murs et sans lot fixe.
- Temple des racines : colonnade effondrée, autel et petit lot d'exploration.
- Mine des brumes : charpentes, hangar, rails, galerie descendante et ressources minières.
- Tour des vents : tour ruinée avec échelle et plateforme d'observation.
- Camp des éclaireurs : tentes ouvertes, caisses et feu éteint, nourriture et équipement léger.
- Sanctuaire des sources : cercle de pierres, végétation et petit bassin.
- Crypte des veilleurs : salle souterraine, escalier depuis la surface, deux squelettes
  persistants créés une fois et récompense plafonnée à deux diamants. Aucun spawner.

Les emplacements ont été recherchés sur du terrain sec, hors royaumes, avec contrôle
du relief local. Les points d'eau naturels ne sont pas utilisés comme fondations
immergées. Un lac bordé, une petite cascade rocailleuse, des sentiers, des passerelles
soutenues et des formations rocheuses complètent les structures.

Les coffres fixes ne sont remplis que lors du chantier initial. Relancer le chantier
sur une copie déjà marquée est refusé, pour éviter régénération de butin ou destruction
de constructions. La première validation automatique porte sur les fichiers et blocs
réels ; elle ne prétend pas remplacer une inspection esthétique en jeu.

## Reproduire le chantier sur une nouvelle copie

Les outils portables et les JAR officiels doivent déjà être installés. Ne pas utiliser
ces étapes sur une instance existante contenant une partie officielle.

```powershell
# Refuse si map-v2 existe ; sauvegarde et copie uniquement une partie non commencée.
python scripts/map_v2.py prepare
python scripts/map_v2_structures.py
.\scripts\build.ps1 -MapV2
python -u scripts/map_v2.py survey
python -u scripts/map_v2.py build
python -u scripts/map_v2.py verify
```

Le chantier écoute sur `127.0.0.1:25577`. Il conserve le verrou de contrôle de la copie,
charge les chunks existants de façon asynchrone, découpe les modifications sur plusieurs
ticks et arrête proprement Paper après chaque étape. Aucune génération de terrain n'a
lieu pendant les événements de ravitaillement. Le périmètre compact hérite de la
prégénération complète du monde source.

Le plugin de chantier est construit à partir des sources de test, séparément du JAR
FKAmis, puis déplacé hors du dossier plugins. Il refuse toute instance autre que
`runtime/map-v2`, une partie démarrée ou une carte contenant déjà des objectifs secrets.
Un chantier interrompu conserve son marqueur ; restaurer dans une nouvelle copie
avant de recommencer. Ne pas supprimer ce marqueur pour forcer un deuxième remplissage.
Le mode ponctuel `repair-loot` sauvegarde d'abord la candidate et refuse une partie
commencée, tout événement passé ou un coffre non vide. Il a servi une seule fois à
corriger les six inventaires initiaux ; il n'est pas une commande de renouvellement.

## Inspection avec un client Minecraft

```powershell
.\scripts\server.ps1 start -Name map-v2 -Port 25577
```

Utiliser Minecraft Java 26.2 sur `127.0.0.1:25577`. Ajouter le compte arbitre à la
whitelist depuis la console et le passer OP uniquement pour préparer la carte.
Le carnet `docs/MAP_V2_INSPECTION.md` contient les vraies coordonnées et commandes
de téléportation relevées après placement. Aucune image de synthèse n'est présentée
comme une capture de Minecraft : aucun client graphique authentifié n'était disponible.

Contrôler chaque terrain à pied, puis en vue aérienne : transitions, arbres coupés,
falaises, accès de grottes, eau et ressources. Parcourir au moins deux itinéraires
entre chaque paire de voisins. Vérifier la crypte, ses escaliers, le chemin de la tour,
les bords des plans d'eau, les passerelles et tous les supports de ravitaillement.
Chercher également les éventuelles structures vanilla préexistantes dans les limites
des territoires ; les constructions ajoutées par le chantier restent toutes à l'extérieur.

Mesurer les déplacements à quatre équipes avant d'attester l'équilibre. Déplacer un
support ou ajuster une pente en cas d'avantage excessif, sur une nouvelle sauvegarde
de travail, puis refaire `verify`. Les salles secrètes seront construites et déclarées
par les joueurs après le départ ; aucune position n'est prédéfinie par la v2.

## Validation et migration

La livraison reste une **candidate construite**, techniquement testée. L'inspection
visuelle, la recette avec clients et la mesure à huit joueurs restent distinctes.
Valider les quatre terrains avec `/fka terrain <équipe> confirm` seulement après inspection.

Une fois validée, exporter `map-v2` avec `server.ps1 export -Name map-v2` et suivre
`DEPLOYMENT.md`. Pour un hébergeur, transférer l'installation complète arrêtée, pas
seulement les régions de terrain. L'archive contient les territoires, coordonnées des
supports, tables et état atomique. Ne pas fusionner avec une ancienne progression.
Conserver `runtime/local` et sa sauvegarde initiale comme retour arrière ; aucune
bascule automatique vers cette instance n'est effectuée.
