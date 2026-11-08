# Mise à jour gameplay FKAmis — Paper 26.3 / MineStrator

## Périmètre et fichiers

Cette révision couvre les huit demandes sur Paper **26.3 build 244**, Java **25**,
FallenKingdom officiel **2.24.9 inchangé**. FKAmis garde le nom/version 1.0.0 pour
compatibilité avec les outils ; son SHA-256 identifie précisément la révision.
La livraison courante est `dist/fallenkingdom-gameplay-update.zip`, le JAR seul est
`dist/gameplay-update/FKAmis-1.0.0.jar`. Les empreintes et résultats définitifs sont
consignés dans `tests/results/gameplay-update-delivery.json` et dans le manifeste du ZIP.
Les anciennes archives restent des références historiques ; ne pas redéployer un monde.

Remplacer seulement le JAR FKAmis, son empreinte et, si utilisés, les deux scripts
`maintenance/serverlib.py` et `maintenance/host_ops.py`. Fusionner les paramètres
ci-dessous dans la configuration existante ; le fragment livré n'est pas un fichier
complet à déposer par-dessus `config.yml`.

**Conserver intégralement** : `world/` et dimensions, profils/inventaires, whitelist,
UUID, `plugins/FKAmis/state.yml`, `admins.yml`, `supplies.yml`, données FallenKingdom,
territoires, objectifs, validations, butin et progression des ravitaillements.
Aucun de ces fichiers privés n'est inclus dans le ZIP. Ni Paper ni le JAR officiel
FallenKingdom ne doivent être remplacés par cette mise à jour.

## Causes établies et changements

| Demande | Diagnostic et comportement livré |
|---|---|
| PvE et flèches | L'attribution existante distingue déjà un tireur squelette d'un joueur. Le refus signalé n'est pas établi dans le JAR local ; ne pas lui inventer une cause. La nouvelle priorité explicite au tireur Mob empêche une source indirecte incohérente de reclasser sa flèche en PvP. Aucun événement annulé n'est globalement réautorisé. `damage-debug` permet de relever cause, tireur, attribution et annulation native/finale sur une copie. |
| Mort sans lit | L'ancien `onRespawn` choisissait le spawn d'équipe. Il utilise maintenant le centre sûr de l'Overworld, près de 0,0, avec carré libre 3x3, sol plein, absence d'eau/lave/dangers, bordure et territoire neutre. Le lit/ancre déclaré valide par Minecraft reste prioritaire. |
| Barre de localisation | Aucun réglage ne la désactivait. `GameRules.LOCATOR_BAR=false` est appliqué aux mondes chargés, nouveaux mondes et transitions de partie. Aucun scoreboard ou packet ajouté. |
| Construction neutre | `BlockListener.event(BlockPlaceEvent)` du plugin officiel refuse les blocs ordinaires hors base via `ALLOWED_BLOCKS`. Son callback est ignoré uniquement pour une pose neutre autorisée ; TNT, bases ennemies, objectifs, ravitaillements, pauses et autres annulations restent contrôlés. |
| Capture sans regard | L'ancien filtre appelait `Player.hasLineOfSight` ; les handlers de mouvement/mort/TP réinitialisaient aussi trop largement les captures, ce qui devenait problématique avec des équipes élargies. Le filtre est remplacé par une composante de cellules debout reliées aux faces du coffre, même monde/niveau et distance 3D. Ni orientation ni rayon visuel ne sont utilisés. |
| Effectifs 1 à 4 | Les limites de `assign`, `MatchState.start` et `loadState` étaient codées à deux. `TeamCapacity` valide la capacité et les rosters persistés ; seuil de capture = minimum du paramètre et des membres officiels UUID. |
| Monde sans mobs visibles J0 | Aucun service ne gérait l'avant-partie. `LobbyMobs` bloque les nouveaux mobs et suspend/masque les existants sans les tuer. Leurs UUID, équipement et propriétés sont conservés, notamment les deux gardiens de crypte. |
| Annonces | Nouvelle commande arbitre/console : titre, sous-titre borné, chat distinctif et son modéré, avec journal d'audit. |

L'enquête PvE doit distinguer un événement autorisé et la réception effective d'un
impact par un client. Le rapport inclut la comparaison avec le précédent binaire.
L’arbitre CREATIVE est volontairement immunisé et ne représente pas un participant SURVIVAL pour cette recette. Une éventuelle invulnérabilité vanilla, un plugin supplémentaire, un état de pause,
une autre révision déployée ou un problème d'impact doivent être vérifiés avec les
logs de l'instance concernée ; ces hypothèses ne sont pas présentées comme des causes.

## Configuration et commandes

```yaml
players-per-team: 2
damage-debug: false
disable-native-tips: true
```

`players-per-team` accepte uniquement les entiers 1 à 4 ; défaut 2 pour un ancien
fichier sans cette clé. `capture-players` conserve le défaut 2, accepte 1 à 4 ;
`capture-radius: 2.5` et `capture-seconds: 60` restent les défauts.
Ne pas modifier la capacité d'une partie commencée. L'état enregistre désormais
`players-per-team` comme clé supplémentaire du schéma 1 ; les anciennes sauvegardes
restent lisibles avec capacité 2. Une diminution sous l'effectif existant ou un
changement en cours de partie refuse le démarrage, sans effacer `state.yml`.
L'augmentation avant départ conserve chaque membre et exige ensuite de compléter
les quatre équipes. Pour une nouvelle partie, utiliser une référence complète dans
une nouvelle instance selon BACKUP_RESTORE.md ; ne jamais effacer seulement l'état.

`/fka start` exige quatre équipes complètes, soit 4, 8, 12 ou 16 participants UUID,
connectés et non OP. L'arbitre n'en fait pas partie. Le contrôle exige au moins
`4 * players-per-team + 1` connexions autorisées par `max-players`.
`/fka start override` reste une dérogation explicite de recette, jamais un dépassement
de capacité. `/fka assign`, `/fka unassign` et `/fka teams tpall [confirm]` restent
les commandes de gestion. Les quatre spawns de départ sont conservés ; le centre
sert aux morts sans point personnel valide.

Nouvelle commande :

```text
/fka announce Un événement spécial commence au centre dans 5 minutes !
```

Arbitre UUID ou console seulement, y compris avant départ et en pause. OP seul ne
suffit pas. Texte simple de 1 à 240 caractères Unicode ; accents et ponctuation
conservés, codes §/& et caractères de contrôle refusés. Les balises sont du texte
littéral, aucun parseur MiniMessage. Sous-titre limité à 80 caractères avec ellipse ;
le message complet figure dans le chat. Titre 5 secondes, transitions de 0,4/0,8 s,
cloche à volume 0,65. Pas de délai bloquant pour une annonce urgente, l'autorité UUID
et l'audit limitent les abus. Les conseils périodiques restent désactivés ; les annonces
automatiques importantes sont conservées. L'arbitre choisit un texte public : la
commande n'ajoute jamais les coordonnées d'un objectif à son message.

La syntaxe console réellement testée est :

```text
minecraft:gamerule minecraft:locator_bar false
```

Le plugin utilise l'API native, sans dépendre de cette commande. Voir les
[GameRules Paper 26.3](https://jd.papermc.io/paper/26.3/org/bukkit/GameRules.html).

## Géométrie de capture et centre

Les pieds doivent être au niveau du coffre (tolérance verticale 0,6 bloc), dans le
rayon 3D de 2,5 blocs autour de son centre supérieur. Des cellules horizontales
libres sur deux blocs de haut doivent relier la position à une face du coffre,
sans sortir du rayon ou du territoire. Un mur plein, un plancher séparant deux
étages, l'eau et les angles infranchissables ne deviennent pas des passages.
Une salle peut avoir un accès en coude : regarder ailleurs ou tourner le dos n'a
aucun effet. Ce contrôle volontairement conservateur ne traite pas un saut, une
trappe ou un demi-bloc comme un passage debout garanti. Prévoir un sol continu au
niveau du coffre. La validation et l'inspection manuelle d'un accès survival légal
restent obligatoires avant J3 ; la géométrie locale ne prouve pas tout le fort.

Le seuil repose sur les membres officiels du royaume attaquant, jamais ceux présents
à cet instant. Un défenseur conteste, des attaquants de royaumes différents bloquent,
les spectateurs/arbitres ne comptent pas. Les distances et effectifs sont recalculés chaque tick. Une sortie ou une mort
interrompt si l'effectif requis n'est plus atteint ; la déconnexion déclenche la
pause habituelle. Le déplacement d'un troisième allié ou la mort d'un défenseur
éloigné n'annule plus globalement les captures d'autres joueurs. Le temps reste 1 200 ticks continus ; une
baisse de TPS l'allonge. L'action bar des seuls attaquants indique la progression,
sans coordonnées et sans diffusion aux autres équipes.

Le centre est choisi dans un rayon borné de 16 blocs de 0,0, uniquement dans des
chunks déjà générés. Le plugin ne dégage pas de blocs et ne crée pas de plateforme.
Il vérifie le point avant utilisation et recherche un autre carré si celui-ci devient
dangereux. En absence de tout carré sûr, le démarrage ou la réapparition échoue avec
arrêt de sécurité : sécuriser le centre par l'arbitre sur une copie restaurée puis
retester. Garder cette petite zone praticable. La position technique relevée dans
les logs reste soumise à inspection humaine en jeu.

## Mobs et conservation de carte

Au jour 0, `SPAWN_MOBS=false` et tous les `CreatureSpawnEvent` de Mob sont bloqués
(naturel, spawner, reproduction, œuf et commandes inclus). Les mobs existants ne sont
**pas supprimés** : invisibles pour les clients, sans IA/gravité/collision, invulnérables,
silencieux et protégés du despawn. Leurs propriétés initiales sont enregistrées dans
leur PDC persistant. Les chargements de chunks, connexions et changements de monde
réappliquent le masquage ; les transformations sont bloquées avant départ.
Les joueurs, armor stands et displays ne sont pas suspendus.

Il reste donc des entités Mob conservées côté serveur, sans présence visible ou
interaction de jeu : c'est nécessaire pour préserver les gardiens et éviter une
suppression définitive. Au départ, `SPAWN_MOBS=true`, difficulté NORMAL, visibilité et
propriétés d'origine restaurées. Les mobs des chunks non chargés seront restaurés
à leur chargement. Une pause après lancement ne relance pas le nettoyage J0 ; elle
conserve le gel et les protections de pause existants. Ne pas retirer FKAmis pendant
une suspension J0 sans restaurer le point complet ou réactiver les mobs via cette
révision : leur PDC fait partie de la cohérence monde/plugin.

## Installation MineStrator détaillée

Aucune opération distante n'a été réalisée par l'agent.

1. Prévenir les joueurs, `fka pause` si la partie est active, `fka save`, puis `stop`.
   Vérifier l'arrêt complet dans le panel et désactiver les redémarrages planifiés.
2. Créer une sauvegarde **complète à froid** de l'instance et la télécharger avec son
   SHA-256 sur un stockage privé séparé. Utiliser le contrôle partagé et les verrous
   natifs décrits dans BACKUP_RESTORE.md ; aucune copie à chaud.
3. Télécharger le ZIP ciblé et son `.zip.sha256`, comparer l'empreinte au rapport.
   Extraire dans un dossier séparé. Ne pas transférer `.cache/`, probes ou mondes de recette.
4. Via SFTP, remplacer `plugins/FKAmis-1.0.0.jar` par
   `payload/plugins/FKAmis-1.0.0.jar`. Éliminer toute ancienne copie concurrente du même
   plugin dans `plugins/` en la conservant hors du dossier chargé. Copier `FKAmis.sha256`
   à la racine. Le plugin officiel FallenKingdom reste strictement inchangé.
5. Fusionner les trois clés de configuration ci-dessus si absentes, garder la capacité
   2 de la partie existante et tous les autres paramètres. Ne jamais remplacer le
   fichier par le fragment `.example.yml`. Si utilisés, remplacer les deux scripts
   de maintenance par ceux du payload. Actualiser l'empreinte FKAmis dans RUNTIME_LOCK.json
   si ce registre est présent ; l'installateur optionnel le fait automatiquement.
6. Pour un prochain format élargi, préparer **manuellement**, serveur arrêté,
   `max-players=20` dans server.properties/le panel MineStrator (16 participants,
   1 arbitre et 3 places de marge). Conserver `online-mode=true`, whitelist stricte,
   port **22880**, `server-ip=` vide, `gamemode=survival`, `force-gamemode=false`.
   Ne pas ajouter des comptes à la whitelist automatiquement. Avec 8 participants,
   les dix places existantes suffisent ; aucun changement automatique du port ou
   de capacité serveur n'est effectué par l'installateur.
7. Garder Paper 26.3-244 et Java 25 ; démarrer avec le profil/mémoire du panel existants.
   Vérifier FKAmis actif, absence d'erreurs, jour, pause, rôles, équipes, objectifs et
   ravitaillements. Après redémarrage, une partie commencée reste en pause.
   Ne pas faire `/reload` ni lancer la partie officielle pour tester un paquet.
8. Exécuter la recette humaine ci-dessous sur une copie isolée, puis reprendre la
   partie par `fka resume` uniquement après contrôle humain.

Option Python 3.11+ : depuis le ZIP extrait, serveur arrêté :

```text
python apply_gameplay_update.py --server /chemin/instance
```

L'outil vérifie les empreintes, verrouille l'instance, sauvegarde intégralement avant
remplacement et compare les données protégées byte pour byte. Il ajoute seulement
les clés absentes, conserve un `players-per-team` existant valide, ne modifie pas
server.properties et ne démarre jamais le serveur. Les JAR précédents reconnus sont
les deux révisions locales livrées, identifiées dans UPDATE_MANIFEST.json. Une autre
révision demande un contrôle de provenance, pas un contournement du hash.
Sans Python sur MineStrator : utiliser SFTP et le snapshot complet du panel ; les
verrous locaux d'une copie téléchargée ne prouvent pas l'arrêt de l'hébergement.

## Rollback

Arrêter le serveur. Conserver le point courant à part. Vérifier le SHA de l'archive
complète prise juste avant mise à jour ; la restaurer dans une **nouvelle instance
vide arrêtée**, selon BACKUP_RESTORE.md. Restaurer ensemble mondes, joueurs, plugin,
configuration, état, rôles et données de ravitaillements. Tester isolé avant bascule.
Ne pas recopier seulement l'ancien `state.yml` ou seulement un inventaire.
Cette restauration reste sous Paper 26.3, sans downgrade de monde. Un simple ancien
JAR sur un monde J0 suspendu n'est pas le rollback documenté.

## Recette automatique et humaine

Commandes reproductibles :

```powershell
./scripts/build.ps1 -Probe -Corrections -MapV2 -Migration -Administration -Features
python -m unittest discover -s tests -p 'test_*.py'
python scripts/features_tests.py --suite features --size 2 --attempt N
```

Choisir un numéro N neuf, jamais écraser une recette. Quatre formats sont testés
sur copies distinctes ; les suites admin/core/gameplay/supplies/native sont rejouées.
La campagne finale passe **32 tests Java, 28 Python et 654 assertions Paper**, zéro échec final, plus cinq assertions comparatives sur l’ancien JAR et deux refus de capacité attendus. Les avertissements et empreintes figurent dans le rapport.
Les 60 secondes de capture sont vérifiées comme 1 200 appels du moteur/ticks,
pas comme 60 secondes de présence réseau d'utilisateurs authentifiés.
Les tests J0 conservent puis rechargent un mob réel et vérifient ses propriétés.
La livraison réelle est installée sur copie, démarrée, comparée et son backup restauré.

**Aucun client authentifié** dans ces essais. Cocher en recette privée :

- [ ] Quatre formats réels 1/2/3/4 membres, affectation/refus de dépassement et tpall.
- [ ] Arbitre UUID créatif/vol, OP ordinaire sans exemption, 16 participants + arbitre.
- [ ] J0 : aucun mob visible après connexion/changement de monde/restart ; gardiens,
      armor stands et displays conservés ; J1 mobs visibles et spawn naturel NORMAL.
- [ ] Impacts réels squelette/zombie/creeper/araignée/noyé/sorcière, dangers naturels ;
      J1 PvP mêlée/flèche refusé, J2 neutre autorisé/bases protégées, pause protégée.
      Si un impact manque, activer temporairement `damage-debug` sur la copie et relever
      les logs, le SHA du JAR installé, les plugins et l'état de partie.
- [ ] Mort sans lit, lit valide/détruit, depuis base/neutre/assaut, reconnexion/restart ;
      SURVIVAL actif, SPECTATOR éliminé, CREATIVE arbitre et inventaires vanilla cohérents.
- [ ] Barre de localisation absente sur tous les clients/dimensions après restart.
- [ ] Construction/minage/coffres/fours neutres J1/J2/J3, refus ennemi/objectifs/sites,
      TNT seulement selon les règles J3, pause et objets interdits conservés.
- [ ] Capture sans regarder/dos, sortie/mort/déconnexion/contestation/mélange, mur/étage,
      seuil solo et effectif officiel malgré déconnexion, élimination/restart/victoire.
- [ ] Annonces console/arbitre avant partie, active et pause : accents, son, rendu titre,
      texte complet chat, message long, refus joueur/formatage, aucune fuite d'objectif.
- [ ] Ravitaillements après 30 minutes actives, butins déjà pris non rechargés,
      pause/reprise/restore cohérents, conseils périodiques toujours absents.
- [ ] TPS/MSPT/RAM/ping à 16 joueurs sur MyBox Perf 8 ; aucune capacité de performance
      à seize joueurs n'est revendiquée à partir des mesures serveur à vide.
