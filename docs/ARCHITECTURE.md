# Architecture

## Révision VNext courante

Voir [FKAMIS_VNEXT.md](FKAMIS_VNEXT.md). `ItemBan` ne remplace que les équipements
réellement modifiés, préservant le cycle de tir des squelettes. `DamageDiagnostics`
observe la chaîne tir/impact/dégâts/santé avec débit borné. La production utilise
l'API Paper ; les corps NMS ne sont présents que dans le JAR de recette séparé.

`CaptureDisplay` affiche le même `CaptureClock`, avec alertes et contributeurs.
`ProtectedPlaces` indexe de petites emprises par chunk. `RespawnProtection` persiste
une échéance absolue par UUID pour le PvP réciproque, sans bloquer le PvE.
`ConfigCommands`, `GameSettings`, `AtomicData` et `SettingsTransaction` valident et
enregistrent les règles sans perdre les clés inconnues. L'intervalle des lots reste
dans `supplies.yml`. `MatchInformation` lit les mêmes états et compteurs.

`MatchStatistics` constitue le modèle unique UUID ; `Statistics` collecte après
protections et exporte les historiques. Le snapshot atomique `state.yml` conserve
`schema: 1` avec `vnext.version: 1`, statistiques et grâce. `ResetService` prépare
un candidat sans l'appliquer à chaud ; `maintenance/new_match.py` utilise le verrou
partagé pour sauvegarder puis appliquer à froid ou restaurer un point initial entier.
Les versions futures sont refusées, les clés inconnues conservées. Les anciennes
sections de cette page décrivent la base toujours réutilisée.

## Base gameplay réutilisée

Voir [GAMEPLAY_UPDATE.md](GAMEPLAY_UPDATE.md) pour la livraison ciblée, les causes,
les limites de preuve, l'installation et le rollback. Le rapport définitif est
`tests/results/gameplay-update-delivery.json`. Paper 26.3-244 / Java 25 / FK 2.24.9
inchangé ; 1 à 4 membres par équipe (défaut 2), arbitre UUID indépendant, lit valide
ou centre sûr pour les morts, construction neutre libre, capture sans condition de
regard, locator bar désactivée, mobs suspendus au jour 0 et `/fka announce <message>`.
Les guides des anciennes livraisons restent historiques.

## Rôles, réapparitions et compatibilité native

`PlayerRoles` décide du mode à partir du rôle UUID, de l'attribution et des captures,
jamais du nombre de morts. `Administrators` stocke les UUID atomiquement dans
`admins.yml`, gère les permissions temporaires, les confirmations console, les
autorisations sensibles d'une action/60 secondes et `admin-audit.log`. Les UUID
restent hors du roster. Le schéma d'état reste 1, avec une clé additionnelle de capacité ; aucune identité ou appartenance n'est réinitialisée.

`NativeAdminBridge` enveloppe uniquement les registrations de protection FK 2.24.9
identifiées. Il délègue les callbacks originaux aux mêmes priorités pour les
participants, les ignore pour les arbitres concernés et restaure les handlers
natifs à l'arrêt. Il ne remet jamais globalement un événement tiers à non annulé.
Le respawn natif différé est remplacé par une seule décision FKAmis : lit/ancre valide ou centre sûr via `SafeCentralSpawn`, sans toucher aux spawns de départ. Les événements de mode, connexion, respawn, monde et le tick
convergent vers la même politique. `DeathLimit` natif est zéro.

Les filtres de captures, présence, lots et rassemblement utilisent les participants
actifs ; ni arbitre ni spectateur ne réinitialise une capture. `CaptureClock` conserve les 1 200 ticks ; le seuil se base désormais sur l’effectif officiel et `CaptureGeometry` remplace le regard. `TipsManager.cancelBroadcasts()` désactive
seulement la tâche des conseils, sans modifier le JAR tiers ou filtrer le chat.

## Services de la révision gameplay

`TeamCapacity` valide la configuration (1 à 4) et sa compatibilité avec le roster
UUID enregistré ; le nombre connecté ne réduit pas le seuil de capture.
`CaptureGeometry` calcule les cellules horizontales debout reliées au coffre, avec
distance 3D et niveau commun, sans aucun appel de ligne de vue. `CaptureClock`
reste le compteur continu. La validation humaine des salles reste obligatoire.

`LobbyMobs` conserve les mobs existants avec leurs UUID et un journal de propriétés
dans leur PDC, les suspend et les masque à J0 ; les restaurations suivent le
chargement des chunks et le départ effectif. `SPAWN_MOBS` et `LOCATOR_BAR` sont des
gamerules Paper 26.3. `SafeCentralSpawn` ne génère aucun chunk et ne modifie aucun
bloc ; il cherche un carré sûr existant dans les 16 blocs autour du centre.
`Announcements` utilise des composants Adventure littéraux, des titres et un son,
avec autorité UUID/console et journalisation, sans désérialisation de balises.

## Corrections de la v2

`GameplayRules` centralise les décisions pures PvE/PvP, minage et rassemblement.
`Protections` ne bloque plus des causes environnementales entières au jour 1.
`DamageAttribution` utilise la source Paper et des marqueurs persistants sur chunks
et entités pour les actes attribuables. Le minage adverse reste refusé après J3 ;
les listes d'explosion conservent les défenses avant assauts et toujours les objectifs.

`TeamTeleportService` valide tous les spawns, charge leurs chunks et limite le transfert
administratif à l'avant-partie ou la pause confirmée. `ChunkLeases` partage les tickets
entre ce service et `SupplyService`. Le filtre `ItemBan` est conservé, configuré avec
les deux nouveaux matériaux ; aucune modification du moteur de capture.

`TerrainCleanup` contrôle supports et connexion au tronc. L'outil temporaire
`FKMapV2Corrections`, issu des sources de test, ne travaille que dans `map-v2-fixes`
avant la partie. Il ne reconstruit pas le terrain et ne remplit aucun coffre.
Voir [V2_CORRECTIONS.md](V2_CORRECTIONS.md).

## Extension carte v2

La v2 ajoute un `SupplyService` dans FKAmis et deux composants purs : `SupplyClock`
pour le temps actif et `LootTable` pour les poids et budgets. Ils utilisent la section
`supplies` du même instantané atomique ; aucun second plugin de ravitaillement n'est installé.
La v2 initiale conservait le moteur de capture ; la révision courante remplace son filtre visuel par CaptureGeometry et adapte le seuil, sans changer CaptureClock. Les coffres réservés
sont explicitement exclus de la déclaration d'objectif et du déplacement des territoires.

`FKMapV2Builder` est un **outil de chantier séparé**, compilé depuis les sources de
test, exécuté uniquement dans `runtime/map-v2`, puis retiré des plugins. Ses accès
réfléchis servent à préparer les territoires et points de départ avant une partie ;
ils ne font pas partie du JAR de jeu. Les modifications du monde sont réparties sur
plusieurs ticks, avec préchargement asynchrone des chunks existants. La partie n'est
pas utilisée comme éditeur en cours de jeu. Voir [MAP_V2](MAP_V2.md) et [LOOT_SYSTEM](LOOT_SYSTEM.md).

## Deux plugins de jeu

Paper fournit le serveur, les sauvegardes vanilla et spark intégré. FallenKingdom de
syldium conserve les équipes, couleurs, territoires, protections classiques de
construction, chat d'équipe et affichage. Son JAR officiel est téléchargé intact,
sans recompilation ni modification.

FKAmis complète les besoins propres à cette partie :

- Répartition de quatre équipes et un à quatre comptes (players-per-team), indexés par UUID authentifié.
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
| LuckPerms | Non requis : rôle arbitre UUID géré directement par FKAmis, sans OP automatique |
| Plugin de sauvegarde | Remplacé par des archives à froid et un verrou OS ; pas de copie à chaud incertaine |
| Générateur de terrain | Génération vanilla récente, sans dépendance et avec structures naturelles limitées par inspection |
| Carte web/Dynmap | Inutile ; risques de révélation des salles et consommation mémoire supplémentaire |

## Sources

- [Sources et licence FallenKingdom](https://github.com/syldium/FallenKingdom/tree/v2.24.9)
- [Wiki officiel](https://github.com/syldium/FallenKingdom/wiki)
- [API World Paper 26.2 : absence d'horloge dans certaines dimensions](https://jd.papermc.io/paper/26.2/org/bukkit/World.html)
