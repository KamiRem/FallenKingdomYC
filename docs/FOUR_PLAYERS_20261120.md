# Quatre membres par royaume — préparation du 20 novembre 2026

**Complément ultérieur :** le [rapport Query/rollback](MINESTRATOR_QUERY_ROLLBACK_20261120.md)
lève le blocage du rollback et remplace le candidat ci-dessous par une révision
avec Query activé, toujours 148 fichiers. Les résultats précédents restent historiques.

**Préparation locale terminée ; bascule distante bloquée.** Les règles ci-dessous
remplacent le défaut de deux membres. Paper 26.3-244, Java 25 et FallenKingdom
officiel 2.24.9 restent inchangés. Aucun accès API/SFTP MineStrator pendant ce travail.
AGENTS.md et les sauvegardes historiques n'ont pas été modifiés.

## Règles et commandes

Quatre royaumes inchangés : Rouge, Bleue, Verte et Jaune. `players-per-team: 4`
est une **limite**, pas un effectif obligatoire. Chaque royaume peut démarrer
avec 1, 2, 3 ou 4 membres ; les effectifs mixtes sont autorisés. Un royaume vide
ou un cinquième membre est refusé, même avec `start override`. Cette option ne
sert plus à contourner le remplissage et conserve ses contrôles existants sur
la présence et le statut OP. L'arbitre UUID reste hors roster et statistiques.

Avant départ, `/fka assign <pseudo connecté> <équipe>` et `/fka unassign <pseudo>`
permettent les changements. Retirer d'abord un membre avant sa réaffectation ;
une destination pleine est refusée sans affectation. `/fka info teams` affiche
effectif officiel/capacité. `/fka config set players-per-team 1..4` reste disponible
avant départ, sans pouvoir réduire sous un effectif enregistré. Les règles et
effectifs sont verrouillés après départ, y compris en pause.

La capture conserve 60 secondes, 2,5 blocs, et `capture-players: 2` : un seul
membre officiel suffit en solo ; deux attaquants présents sont requis pour un
roster de 2, 3 ou 4. Les déconnectés restent officiels. Un départ ne réduit donc
pas le seuil ; une capture continue seulement si les présences réelles restent
suffisantes. Défenseur, troisième équipe, mur, étage distinct, mort et pause
conservent les interruptions existantes. Arbitres et spectateurs sont exclus.

## Audit des fonctionnalités

| Fonction | Résultat |
|---|---|
| Affectation et lancement | Défaut 4 ; lancement avec effectifs mixtes ; plafond dur existant conservé |
| Informations | Affichage de l'effectif officiel et de la capacité |
| Téléportations et réapparitions | Itérations par UUID sans limite de deux ; comportement conservé |
| Captures, BossBars, ActionBars | Seuil officiel déjà indépendant du plafond ; comportement conservé |
| Élimination et spectateurs | Élimination par royaume, application à chaque membre ; aucun plafonnement à deux |
| Statistiques | Stockage par UUID et agrégats par royaume ; 16 membres et sérialisation vérifiés |
| Victoire et scoreboards natifs | Quatre royaumes ; trois éliminations désignent le survivant, indépendamment de leur effectif |
| Configuration, sauvegarde et reset | Capacité persistée ; contrôles d'effectif/schéma conservés ; reset logique réservé à une nouvelle partie |

Les configurations existantes explicitement à deux ne sont pas converties
automatiquement. Les installateurs historiques conservent leurs valeurs de
compatibilité. Le nouveau candidat reçoit explicitement quatre, sans reprendre
les états, inventaires ou compteurs de l'ancienne partie.

## Tests exécutés

Preuves : `tests/results/fourplayers-*.json` et
`tests/results/minestrator-rollback-local-20261120.json`.

- 53 tests Java réussis ; 86 tests Python réussis.
- 12 démarrages Paper de la suite fonctionnalités : quatre formats réels de
  roster synthétique, capacité configurée à quatre, 422 assertions.
- 47 assertions de commandes avec corps NMS : affectations successives de 1 à 4
  dans les quatre royaumes, cinquième refusé, arbitre exclu, retrait/réaffectation,
  contrôles de terrain conservés, démarrage de 16 participants et statistiques.
- Trois phases VNext : 102 assertions configuration, statistiques, victoire,
  conservation au redémarrage et reset sur fixture exclusivement synthétique.
- Déconnexions pendant capture, défenseur et troisième équipe, 60 secondes,
  élimination puis réapparition **de chaque membre** des équipes de 1 à 4,
  conservation du roster après redémarrage et victoire.
- Sauvegarde/restauration des profils 10 et 20 places avec données factices ;
  refus Query, whitelist permissive, capacité hors limites et SHA invalide.

Zéro client authentifié. Les corps NMS et doubles API ne prouvent ni rendu client,
ni comportement réseau multijoueur, ni charge stable à 17 connexions MineStrator.
Les premières tentatives de la nouvelle sonde ont révélé deux défauts de fixture
(normalisation du chemin, précondition de confirmation des terrains). Elles sont
conservées dans `.cache/vn1/runtime/probe-fourplayers-20` et `-21`. La tentative 22
passe. La première a nécessité l'arrêt du seul processus local orphelin après un
défaut du lanceur ; le traitement du délai a été corrigé. Aucun de ces essais ne
concerne les données historiques. La tentative réussie signale un avertissement
Paper de sauvegarde manuelle pendant l'autosave, aucune ERROR/SEVERE.

Reproduction locale (prendre un numéro `--attempt` neuf pour chaque copie) :

```powershell
./scripts/build.ps1 -Features -FourPlayers -VNext
python -B -m unittest discover -s tests
python -B scripts/vnext1_tests.py --suite four --attempt 30 --port 25635 --report-prefix fourplayers
python -B scripts/vnext1_tests.py --suite features --size 4 --attempt 30 --port 25634 --report-prefix fourplayers
```

Répéter `features` avec `--size 1`, `2`, `3` pour les autres effectifs. Les essais
à froid refusent une destination existante ; ils ne suppriment pas les copies.
Ne pas relancer le rollback historique avant résolution explicite de Query.

## Carte et spawns

La préparation réutilise le candidat V2.1 antérieur vérifié par son manifeste.
Les **121 fichiers de monde** sont identiques par SHA-256 ; les quatre cavernes,
la bordure, les centres et les spawns ne sont pas déplacés. Les quatre territoires
restent des carrés inclusifs de rayon 40, soit 81 × 81 = 6 561 colonnes chacun.

Les références initiales ont été contrôlées à nouveau : bases, monuments, butins,
ravitaillements et quatre cavernes. Un contrôle conservateur trouve **15 cellules
praticables** au même niveau dans un carré de cinq blocs autour de chaque spawn
(sol plein connu, pieds/tête libres). Il n'ajoute aucune position automatique de
téléportation et n'est pas une preuve d'absence de bousculade à quatre clients.

L'espace technique n'impose pas d'agrandissement pour quatre membres. L'équilibrage
des minerais par personne change : budget identique par équipe, partagé entre
ses membres. Aucun minerai, butin ou relief n'a été ajouté. Circulation, esthétique,
empilement au spawn et équilibrage nécessitent encore une inspection humaine.

## MineStrator, capacité et performances

Le nouveau profil prépare `max-players=20`, soit 16 participants, l'arbitre et
trois places techniques supplémentaires, toutes soumises à la whitelist stricte.
`online-mode`, `white-list`, `enforce-whitelist`, port 22880, distances 8/6 et
paramètres de mémoire/panel sont conservés. La whitelist réelle contient
**deux comptes** : elle n'a pas été élargie. Les UUID des participants et de
l'arbitre devront être vérifiés et autorisés avant une recette à 17 connexions.
OP ne remplace pas le rôle arbitre.

Le nouveau `server.properties` diffère en deux points : 10 → 20 places et
`enable-query=true` → `false`, pour respecter le profil privé de maintenance et
éviter un service UDP supplémentaire. **Cette seconde proposition est uniquement
locale** ; son effet sur les statistiques/indicateurs de MineBoard n'est pas
vérifié. Aucun réglage ni allocation du panel n'a été changé. La capacité de
l'offre réellement attribuée et une éventuelle réécriture au démarrage du panel
restent à vérifier avant bascule ; un démarrage localhost ne les certifie pas.

L'offre publique [MyBox Perf 8](https://minestrator.com/order/mybox/myboxperf8-v4)
annonce 8 Go ; cela ne prouve ni l'allocation effective de cette instance ni une
garantie à 17 joueurs. Le contexte historique indique environ 6154M Java et
`java/25_perf`, inchangés. Doubler les participants peut augmenter les chunks
chargés, entités, transferts et génération Nether ; le risque principal est le
budget de tick et la mémoire en exploration dispersée. Cette appréciation est
une inférence technique, pas une mesure de l'hôte.

Les micro-mesures locales sérialisent les statistiques de 16 membres en environ
78 µs et mettent à jour une BossBar pour deux doubles en environ 2,7 µs. Les TPS
de construction de la sonde ne mesurent pas une charge stable. Le démarrage du
candidat utilise Java 25.0.5, sans erreur, zéro joueur et sans lancement de partie.
Ne pas modifier les distances ou la mémoire sur la base de ces seuls essais.
Prévoir une recette graduelle à 4/8/16 participants plus arbitre, captures
simultanées et exploration Nether ; relever MSPT, TPS, RAM/GC et ping. Les
[distances Paper](https://docs.papermc.io/paper/reference/server-properties/) et
le [profilage spark intégré](https://docs.papermc.io/paper/profiling/) documentent
les contrôles de charge à employer. Aucun profil n'a été publié vers un service.

## Candidat et manifeste de transfert

Sortie privée neuve, hors Git :
`C:\Users\youne\FKBackups\V21-FOUR-20261120-01`.

- `preproduction-candidate/` : nouvelle instance préparée, jamais démarrée.
- `preproduction-smoke/` : copie de recette démarrée puis arrêtée sur localhost.
- `payload/DEPLOYMENT_MANIFEST.json` : empreintes de la nouvelle instance.
- `transfer-plan-private.json` : anciennes/nouvelles empreintes, aucune exécution.
- `v21-fourplayers-transfer-private.zip` et sidecar : archive privée de transfert.
- `preparation.json`, `spawn-audit.json`, journaux privés de démarrage.

Le plan compte désormais **148 fichiers cibles**, remplaçant les 146 précédents :
le JAR FKAmis recompilé et `server.properties` s'ajoutent aux chemins existants.
Les autres entrées mises à jour incluent marqueur, registre, configuration,
capacité persistée et outils. Les SHA-256 complets et préconditions sont dans les
manifestes privés ; le résumé partageable est `fourplayers-candidate.json`.
Le fichier de contrôle `BACKUP_MANIFEST.json` ajouté par l'archive n'est pas une
149e cible de transfert. La référence Paper `server.jar`, absente du candidat
de construction, a été lue depuis la restauration historique et vérifiée identique
à `paper.jar` ; les deux alias sont conservés dans le plan distant.

JAR indépendant : `dist/fourplayers-20261120/FKAmis-1.0.0.jar`, SHA-256
`38180caa28442bad838ef395779d9075a33a2c624bc71e2286488ac0e32fb31a`.
Les anciens ZIP de mise à jour et de construction restent des livraisons
historiques avec leurs anciennes empreintes. Ne pas les confondre avec ce nouveau
plan, ni transférer l'archive privée sans autorisation séparée.

## Rollback historique : essai arrêté avant Paper

Nouvelle copie : `C:\Users\youne\FKBackups\RB-20261120-01\preproduction`.
Les 305 fichiers originaux, le manifeste, leurs métadonnées locales relevées et
l'archive `MS-COLD-20261119-02/instance.zip` sont confirmés inchangés. SHA archive :
`255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf`.

Seul le marqueur de la copie a été réconcilié avec son ancien JAR intact
`46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442`.
Le registre est cohérent, `max-players=10` est conservé et accepté par le
validateur externe actuel. Le schéma 1 et les structures d'équipes/spawns sont
lisibles avec le parseur YAML sûr ; cette lecture statique ne valide pas leur
chargement applicatif.

Le contrôle `deployment/host_ops.py:check` échoue ensuite sur **`enable-query=true`**,
alors que le profil privé exige `false`. Query utilise le port 22880 dans cette
configuration. L'essai s'arrête ici : aucune correction Query, aucun démarrage
Paper, aucun reset ni réécriture de données historiques. L'ancien validateur
imposant huit places n'a pas été installé ou modifié dans la copie.

**Rollback fonctionnel non validé.** Une reprise nécessite une décision explicite
sur Query pour une nouvelle copie isolée, sans changer la sauvegarde ni supprimer
le contrôle de maintenance. Les permissions POSIX, UID/GID et dates Linux ne sont
pas réappliqués ou validés par la restauration Windows ; ils restent consignés
dans le manifeste d'origine. L'absence de verrou partagé de l'hôte reste la limite
acceptée de la sauvegarde à froid, pas une garantie absolue ajoutée ici.

## Conditions avant toute bascule

Résoudre l'essai du rollback puis obtenir un démarrage fonctionnel réussi ;
valider la politique Query et les capacités effectives MineBoard ; compléter
la whitelist avec des identités approuvées ; effectuer l'inspection humaine de
carte et les essais multijoueurs. Réauditer en lecture seule le serveur arrêté
et les SHA source, l'espace disque et les mécanismes de redémarrage, puis faire
approuver le manifeste **148 fichiers**. Aucune autorisation de sauvegarde ou de
test local ne vaut autorisation de déploiement.
