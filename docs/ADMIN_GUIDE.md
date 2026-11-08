# Administration

## Révision gameplay courante

Voir [GAMEPLAY_UPDATE.md](GAMEPLAY_UPDATE.md) pour la livraison ciblée, les causes,
les limites de preuve, l'installation et le rollback. Le rapport définitif est
`tests/results/gameplay-update-delivery.json`. Paper 26.3-244 / Java 25 / FK 2.24.9
inchangé ; 1 à 4 membres par équipe (défaut 2), arbitre UUID indépendant, lit valide
ou centre sûr pour les morts, construction neutre libre, capture sans condition de
regard, locator bar désactivée, mobs suspendus au jour 0 et `/fka announce <message>`.
Les guides des anciennes livraisons restent historiques.

## Arbitre UUID et réapparitions — profil courant

Le guide actuel est [ADMIN_UPDATE.md](ADMIN_UPDATE.md). Un arbitre hors équipe
rejoint en CREATIVE ; 4 à 16 participants jouent en SURVIVAL. Le format actuel de huit participants utilise dix places ; prévoir vingt places pour seize participants, avec whitelist stricte. OP ne suffit pas : autoriser l'UUID officiel
via la console `fka admin grant UUID confirm`. `fka admin uuid PseudoConnecte`
affiche cet UUID ; `revoke UUID confirm` retire le rôle. Les autorisations privées
sont dans `plugins/FKAmis/admins.yml`, distinct de l'état de partie.

Les morts sont illimitées tant que le royaume est actif. Seule une capture complète
élimine l'équipe et impose SPECTATOR de façon persistante. Les tips natifs sont
désactivés ; les annonces de partie restent conservées. La mise à jour se fait
serveur arrêté, par JAR/configuration ciblés, sans retransfert de carte ni état écrasé.
Les références map-v2 et map-v2-fixes ci-dessous restent historiques et intactes.

## Variante v2 corrigée

Historique : `runtime/map-v2-fixes` a été utilisé pour les corrections, sans remplacer les deux instances
précédentes. Voir [V2_CORRECTIONS.md](V2_CORRECTIONS.md) pour le nettoyage et les preuves.
Le profil ajoute `ELYTRA` et `ENCHANTED_GOLDEN_APPLE` à `extra-banned` ; garder
`GOLDEN_APPLE` autorisée et `ban-netherite-family: true`.

`/fka teams tpall` rassemble les participants connectés sur leurs spawns enregistrés,
avec `fkamis.admin`, avant départ. Après départ : mettre en pause puis utiliser
`/fka teams tpall confirm`. Refus pendant une partie active ou après victoire.
Spectateurs, éliminés et sans équipe sont ignorés. Un spawn dangereux refuse tout le
lot ; les annulations externes restent respectées et l'opération est journalisée.
La pause native et le gel des mondes restent actifs pendant ce rassemblement.

## Carte v2 et ravitaillements

La copie `runtime/map-v2` contient déjà ses territoires et apparitions, préparés sans
fortification. Les quatre confirmations de terrain restent à donner après inspection
visuelle. Ne pas redéfinir les centres avec les anciennes coordonnées ±500.
Les coordonnées publiques exactes sont dans [MAP_V2_INSPECTION.md](MAP_V2_INSPECTION.md).

Les commandes `/fka supply status|list|enable|disable|reload|add|remove|test` sont
documentées avec leur syntaxe et permissions dans [LOOT_SYSTEM.md](LOOT_SYSTEM.md).
`status` est public ; les autres demandent `fkamis.admin`. La commande de test ne
fonctionne que sur une copie marquée `test-mode: true` avant tout démarrage de partie.
La configuration livrée garde ce mode de test à `false`.

Les commandes `/fka` sensibles demandent le rôle explicite UUID d’arbitre (OP seul insuffisant). La console
possède ce droit ; les participants doivent rester non OP. Les équipes sont exactement
`Rouge`, `Bleue`, `Verte`, `Jaune`. Les arguments d'équipe respectent la casse.

## Commandes effectivement implémentées

| Commande | Usage et garde-fou |
|---|---|
| `/fka announce <message>` | Arbitre UUID/console ; titre, chat, son, texte simple 1–240 caractères |
| `/fka help` | Aide adaptée aux permissions |
| `/fka status` | Jour et royaumes actifs, aucune position d'objectif |
| `/fka assign <pseudo connecté> <équipe>` | Avant lancement ; capacité players-per-team, UUID du compte officiel |
| `/fka unassign <pseudo>` | Retrait avant lancement |
| `/fka territory <équipe> <rayon>` | Centre à votre position, monde world ; rayon 40–150, séparation et bordure contrôlées ; ne génère aucun bloc |
| `/fka terrain <équipe> confirm` | Attestation d'inspection humaine avant lancement |
| `/fka spawn <équipe>` | Point d'apparition à votre position dans le territoire, avant lancement |
| `/fka teams tpall [confirm]` | Admin ou console ; avant partie ou en pause confirmée ; spawns sûrs, aucun changement d'équipe/inventaire |
| `/fka start` | Quatre terrains confirmés, quatre équipes complètes, 4 × players-per-team comptes connectés et non OP, apparitions sûres |
| `/fka start override` | Dérogation explicite de l'administrateur pour répartition incomplète/présences/OP ; jamais au-delà de players-per-team par équipe ; terrains toujours requis |
| `/fka pause` | Arrêt des interactions, déplacement et tick des mondes ; annulation des captures |
| `/fka resume` | Reprise explicite ; objectifs valides exigés à partir du jour d'assaut |
| `/fka nextday` | Avance d'une phase ; toutes les salles actives doivent être valides pour passer au jour 3 |
| `/fka end open` | Autorise l'End ; reste soumis à la pause |
| `/fka end close` | Ferme l'End ; faire revenir les joueurs auparavant |
| `/fka room register` | Joueur : cibler son coffre ordinaire ; préparation en cours seulement ; aucun affichage de coordonnées |
| `/fka room inspect <équipe>` | Admin uniquement : position privée et état de validation |
| `/fka room validate <équipe>` | Admin : après inspection de l'accès, contrôle coffre/espace/territoire ; mettre en pause pour modifier pendant les assauts |
| `/fka room invalidate <équipe>` | Retire la validation ; en pause pendant les assauts |
| `/fka win <équipe>` | Victoire administrative d'une équipe encore active ; fin en pause |
| `/fka save` | Écrit l'état et demande la sauvegarde joueurs/mondes/plugins ; ne remplace pas une archive à froid |
| `/fka pregen` | Avant la partie : génère les chunks de l'Overworld jusqu'à la bordure + marge ; une seule tâche à la fois |
| `/fka survey` | Avant la partie : échantillonne hauteur et biome autour des bases définies dans un CSV privé |

`/fk team list` et `/fk rules list` restent consultables. Les autres commandes `/fk`
sont bloquées pour préserver la progression et empêcher la visualisation d'une salle
adverse. **Ne pas contourner le verrou par des commandes imbriquées dans la console.**
La console reste une autorité de confiance, capable de modifier le serveur et ses fichiers.

## Enregistrer et inspecter une salle

1. L'équipe construit sa salle et pose un coffre ordinaire dans son territoire.
2. Elle cible le coffre et lance `/fka room register`. Le coffre ne se déplace pas et
   n'est pas fourni par le serveur. Les autres coffres restent du stockage normal.
3. L'arbitre consulte la position en privé avec `/fka room inspect Rouge`.
4. Vérifier un accès survival légal, deux emplacements accessibles autour du coffre,
   un espace debout relié aux faces de l'objectif, sans obligation de regard et la possibilité d'une brèche par TNT ou par un passage.
5. `/fka room validate Rouge`, puis recommencer pour les autres royaumes.

L'algorithme vérifie l'existence, le territoire et min(capture-players, players-per-team) places debout proches reliées aux faces du coffre. Il ne
peut pas prouver qu'un labyrinthe est franchissable depuis l'extérieur : l'inspection
humaine est obligatoire. Une nouvelle déclaration retire la validation précédente.
Une salle validée devenue techniquement invalide déclenche une pause.

Le coffre objectif est indestructible et ne peut pas être déplacé par un piston ni
détruit par une explosion ; les défenses autour sont attaquables au jour 3. Ne pas
l'enfermer dans une protection permanente ou une coque d'obsidienne sans entrée légale.

## Paramètres modifiables

Serveur arrêté, modifier `plugins/FKAmis/config.yml`, puis redémarrer. Valeurs initiales :
`players-per-team: 2`, `damage-debug: false`, `pvp-day: 2`, `assault-day: 3`, `nether-day: 2`, `capture-seconds: 60`,
`capture-players: 2`, `capture-radius: 2.5`, `border-size: 1800`.
La durée accepte 1–3 600 secondes, le rayon un nombre fini entre 0 et 8 excluant 0,
et la bordure 600–4 000 blocs. Ces bornes évitent une configuration incontrôlée.
Les règles natives correspondantes sont synchronisées par l'extension. Ne pas
changer les noms des équipes au milieu d'une partie. Une modification de bordure
demande une nouvelle inspection des territoires.

`ban-netherite-family` contrôle les matériaux contenant `NETHERITE` et `ANCIENT_DEBRIS`.
`extra-banned` accepte d'autres noms Material Bukkit. Un nom inconnu empêche le démarrage
pour éviter une interdiction silencieusement ignorée. Modifier les interdictions exige
une sauvegarde et une nouvelle recette ; les objets interdits sont retirés, sans compensation.

## Fin de session et incident

Mettre en pause, prévenir les joueurs, puis `stop`. Éviter de tuer Java. Après redémarrage,
contrôler le jour, les salles et les éliminations avant de reprendre. Après un crash,
utiliser une archive complète si le monde et l'état présentent une incohérence.
Ne pas restaurer la fonction native `fk game restore` : elle pourrait dupliquer des
objets par rapport au monde courant. Elle est volontairement verrouillée.
