# Architecture

## Deux plugins de jeu

Paper fournit le serveur, les sauvegardes vanilla et spark intégré. FallenKingdom de
syldium conserve les équipes, couleurs, territoires, protections classiques de
construction, chat d'équipe et affichage. Son JAR officiel est téléchargé intact,
sans recompilation ni modification.

FKAmis complète les besoins propres à cette partie :

- Répartition de quatre équipes et deux comptes maximum, indexés par UUID authentifié.
- Territoires définis après inspection sans appeler la génération de drapeau ou mur.
- Phases logiques manuelles, indépendantes de la nuit et de l'horloge réelle.
- Validation des terrains avant lancement, puis objectifs avant l'ouverture des assauts.
- Un coffre explicitement choisi par les propriétaires, sans publier sa position.
- Capture continue, élimination persistante et victoire du dernier royaume.
- Netherite interdite, dimensions contrôlées, protections indirectes et pause renforcée.
- Prégénération asynchrone et rapport sommaire de terrain.

Les commandes natives susceptibles de contourner ces règles sont verrouillées,
y compris depuis la console. Les commandes publiques `fk team list` et `fk rules list`
restent disponibles. Le préfixe du complément est `/fka`.

## Pourquoi adapter la capture

Le code publié de FallenKingdom 2.24.9 a été examiné au tag `v2.24.9`
(`d3d5b00`). `GameRunnable` avance automatiquement les jours ; `CaptureRunnable`
annonce une victoire sans gérer l'élimination à quatre équipes. Dans `ChestsRoom`,
les présences ennemies sont agrégées et la déconnexion n'est pas une garantie
d'interruption dans `ChestRoomRunnable` : un timer peut continuer sans attaquant
connecté. La détection native englobe par ailleurs les coffres de stockage ordinaires.

Ces comportements ne correspondent pas à l'objectif central validé et confidentiel
demandé. La détection/capture native est donc désactivée et remplacée dans le
complément, sans modifier le plugin tiers. Les territoires et restrictions FK sont
conservés ; il ne s'agit pas d'un second système complet de Fallen Kingdom.

## Une seule autorité pour la progression

`plugins/FKAmis/state.yml` contient un instantané atomique : jour, victoire, éliminations,
UUID, membres et territoires natifs, points d'apparition, objectifs et validations.
Les équipes FallenKingdom sont restaurées depuis cet instantané au démarrage pour
éviter un décalage entre deux fichiers de plugins après un arrêt brutal.

La partie native est synchronisée via ses méthodes Java publiques et son horloge est
arrêtée immédiatement. Aucune réflexion Java ni accès NMS dans FKAmis. Cette intégration
utilise aussi des classes internes publiques de FallenKingdom ; la version est donc
strictement contrôlée au chargement. Ne pas mettre à jour son JAR isolément.

Chaque mutation administrative et élimination écrit un fichier temporaire, force les
données sur disque et le remplace atomiquement. Une erreur de lecture ou d'écriture
arrête le serveur. Après redémarrage, la reprise est toujours administrative, en pause.

Les inventaires et blocs restent sauvegardés par Minecraft. Une panne électrique peut
perdre des changements depuis la dernière sauvegarde du monde : aucune transaction
globale entre les fichiers vanilla n'est revendiquée. Les archives à froid sont l'unité
de restauration cohérente ; ne jamais restaurer uniquement l'inventaire d'un joueur.

## Pause

Pause native profonde, refus des interactions, dégâts, inventaires, transferts et
déplacements, puis gel du tick des mondes par l'API Paper. Les commandes de reprise
restent accessibles. Une déconnexion d'un participant actif provoque une pause pour
prévenir les assauts hors présence des défenseurs. Une capture en cours est remise
à zéro à toute pause, déconnexion ou reprise.

## Plugins écartés

| Outil | Décision |
|---|---|
| WorldEdit | Inutile pour une génération naturelle et aucun fort préconstruit ; possible outil ponctuel après nouvelle vérification de version |
| WorldGuard | Double emploi avec les territoires natifs et le complément |
| LuckPerms | Inutile avec un seul rôle de console et `fkamis.admin` réservé OP ; à ajouter si un compte arbitre distinct doit recevoir des droits fins |
| Plugin de sauvegarde | Remplacé par des archives à froid et un verrou OS ; pas de copie à chaud incertaine |
| Générateur de terrain | Génération vanilla récente, sans dépendance et avec structures naturelles limitées par inspection |
| Carte web/Dynmap | Inutile ; risques de révélation des salles et consommation mémoire supplémentaire |

## Sources

- [Sources et licence FallenKingdom](https://github.com/syldium/FallenKingdom/tree/v2.24.9)
- [Wiki officiel](https://github.com/syldium/FallenKingdom/wiki)
- [API World Paper 26.2 : absence d'horloge dans certaines dimensions](https://jd.papermc.io/paper/26.2/org/bukkit/World.html)
