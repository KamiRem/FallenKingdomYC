# Fallen Kingdom privé — quatre royaumes et un arbitre

**V2.1 installée sur MineStrator, serveur réservé à la recette.** Le
[rapport d'installation du 20 novembre](docs/MINESTRATOR_INSTALLATION_20261120.md)
confirme les 148 fichiers, leurs empreintes, Paper/plugins, Query à 20 places,
les quatre territoires/spawns et les quatre cavernes. Partie au jour 0 non
lancée, whitelist inchangée à deux comptes, `restart-on-crash=false` et watchdog
actif. Les risques de verrou exclusif absent et de relance hébergeur non vérifiée
ont été explicitement acceptés pour cette opération. L'[audit préalable](docs/MINESTRATOR_FINAL_PREFLIGHT_20261120.md)
reste conservé comme preuve historique. Voir la
[liste exacte des 148 fichiers](docs/MINESTRATOR_148_FILES_20261120.tsv) et le
[protocole whitelist/recette](docs/MINESTRATOR_RECETTE_ET_WHITELIST_20261120.md).

Préparation du 20 novembre : [1 à 4 membres par royaume, V2.1 à 20 places](docs/FOUR_PLAYERS_20261120.md),
jusqu'à 16 participants et l'arbitre. Le nouveau manifeste privé comporte 148
fichiers ; le plan antérieur de 146 fichiers est périmé. Rollback historique à
10 places préservé. Le [complément Query et rollback](docs/MINESTRATOR_QUERY_ROLLBACK_20261120.md)
valide son démarrage fonctionnel et finalise Query activé pour MineStrator.
Le déploiement contrôlé a ensuite été autorisé et réalisé ; ses preuves sont dans
`tests/results/minestrator-deployment-20261120.json`. Les ZIP ci-dessous restent
ceux de la livraison précédente ; le candidat privé de 148 fichiers et
`tests/results/query-rollback-delivery.json` définissent la préparation actuelle.

La livraison courante est [FKAmis VNext.1 et carte V2.1](docs/FKAMIS_VNEXT_1.md).
Le ZIP `dist/fallenkingdom-vnext1-update.zip` met à jour VNext et les territoires
à froid, avec sauvegarde complète ; il ne contient aucun monde ni état de joueur.
L'artefact séparé `dist/fallenkingdom-map-v2.1-build.zip` construit quatre cavernes
sur une copie initiale uniquement. Le [rapport courant](tests/results/vnext1-delivery.json)
distingue essais locaux et recette humaine restant à faire ; il précède l'installation
MineStrator documentée ci-dessus.
Le guidage utilise une ActionBar privée ; la Locator Bar native reste désactivée.
Les [preuves VNext](docs/FKAMIS_VNEXT.md) et livraisons antérieures sont conservées.

La précédente [mise à jour arbitre, survie et tips](docs/ADMIN_UPDATE.md) se déploie
avec `dist/fallenkingdom-admin-update.zip`, sans retransfert de carte ni remplacement
de `state.yml`. Voir `tests/results/admin-update-delivery.json` pour la nouvelle
empreinte FKAmis et les résultats. Dix places techniques, whitelist stricte, rôle
arbitre UUID distinct du statut OP ; morts illimitées avant capture du royaume.

Le projet utilise désormais **Paper 26.3 build 244 STABLE**, **Java 25**,
**FallenKingdom officiel 2.24.9** et **FKAmis 1.0.0 compilé contre l’API 26.3**.
La carte corrigée a été restaurée depuis l’archive initiale puis convertie dans
`runtime/preproduction-26-3`, avec contrôles des blocs, coffres et dimensions.
Aucune mécanique réécrite, aucune reconstruction ni recharge de butin.

La référence complète initiale historique est **`dist/fallenkingdom-preproduction-26.3.zip`** ; elle ne sert pas à mettre à jour une partie existante.
Son SHA-256, ses versions et les résultats sont dans
[le rapport de livraison 26.3](tests/results/preproduction-package-26.3.json).
Il ne contient que les deux plugins de production, sans comptes/inventaires de test,
identifiants d’hébergement, logs locaux ou plugins de chantier/recette.

Le propriétaire a choisi **MineStrator MyBox Perf 8**, Java 25 Performance,
environ **6154M** de mémoire Java gérés par le panel et le port **22880**.
Le paquet contient déjà le bon port, `server-ip=` vide et `level-name=world`.
L'installation contrôlée n'a lancé aucune partie officielle.

- [Audit technique, résultats et limites](docs/PREPRODUCTION_AUDIT.md).
- [Transfert MineStrator étape par étape](docs/HOST_INSTALLATION.md).
- [Recette réelle avec huit comptes authentifiés](docs/MULTIPLAYER_ACCEPTANCE.md).
- [Sauvegardes et restauration complète](docs/BACKUP_RESTORE.md).
- [Préparation d’une partie officielle propre](docs/OFFICIAL_LAUNCH.md).
- [Checklist finale](docs/PRODUCTION_CHECKLIST.md).

Les références `runtime/local`, `runtime/map-v2`, `runtime/map-v2-fixes`, le ZIP
26.2 et les sauvegardes historiques sont conservés intacts. La branche de test
`test/paper-26.3-preprod` et ses résultats précédents restent disponibles ; les
fixtures `.cache/` ne doivent jamais être déployées. Aucun downgrade d’un monde converti.

## Validation disponible

VNext passe **46 tests Java, 38 Python et 764 assertions Paper**, plus quinze cas
physiques avec mesures de santé. Installation ciblée, migration additive, refus de
versions futures, reset à froid et restauration/rollback entiers sont contrôlés.
Les rapports détaillent les micro-mesures et la stabilisation locale à vide ; la
charge et le rendu avec des comptes authentifiés restent à valider humainement.

La campagne gameplay précédente passe **32 tests Java, 28 Python et 654 assertions
Paper** sur le même JAR, dont les formats de 1 à 4 membres par équipe. Les deux
configurations de capacité incompatibles sont aussi testées en refus de démarrage.
Les essais réels d'installation, sauvegarde et rollback figurent dans le rapport.
VNext reproduit désormais la cause : réécrire chaque seconde le même arc réinitialise
le comportement de tir. Le correctif n'écrit que les équipements modifiés. Les
rapports physiques montrent des tirs et une baisse réelle de santé d'un corps
`ServerPlayer`, sans client authentifié. Voir les chiffres du rapport VNext.

La migration initiale avait passé 19 tests Java, 21 Python et 217 assertions ;
son archive reste inchangée. La révision actuelle ajoute le rôle d'arbitre, la
politique de réapparition et l'arrêt des tips, avec **24 tests Java et 24 Python**
et une nouvelle recette Paper détaillée dans `admin-update-delivery.json`.
Ces nombres décrivent la livraison précédente. La révision gameplay adapte la géométrie et le seuil de capture ; le JAR officiel reste inchangé. Consulter le rapport courant pour les nouveaux résultats.

**Aucun client authentifié pendant ces essais.** Les huit interfaces Player du probe
gameplay ne remplacent pas huit personnes connectées. Chat réseau, interfaces clients,
inspection visuelle 26.3 et mesures TPS/MSPT/RAM/ping sur l’hôte restent à valider.
FallenKingdom 2.24.9 déclare encore 26.2 ; la compatibilité technique locale 26.3
constatée et cette réserve sont détaillées dans l’audit.

## Reprendre localement sans toucher aux références

```powershell
./scripts/server.ps1 validate -Name preproduction-admin-update
./scripts/server.ps1 start -Name preproduction-admin-update -Port 25588
```

Client local **Minecraft Java 26.3**, `127.0.0.1:25588`. La whitelist est vide au
départ : ajouter les comptes depuis la console, sans OP les participants. Le port
25588 ci-dessus est une surcharge locale ; le paquet destiné à MineStrator conserve 22880.
Le démarrage technique ne lance pas la partie ; ne saisir `fka start` que sur la
bonne copie de recette ou, après validation, lors du lancement officiel humain.

## Développement

Python 3.11+, Java 25, Maven 3.9.11 ; outils Windows portables disponibles localement.
Sur une nouvelle installation : `./scripts/bootstrap.ps1`, puis `./scripts/build.ps1`.
Les téléchargements sont figés par versions/hashes, jamais `latest`. L’EULA d’une
installation neuve reste non acceptée jusqu’à décision explicite de son propriétaire.
Les mondes, profils joueurs, objectifs, JAR téléchargés, sauvegardes et ZIP sont privés,
exclus de Git. La carte approuvée ne se reconstruit pas depuis les seuls fichiers Git.

Voir [le plan des tests](docs/TEST_PLAN.md), [la compatibilité/licences](docs/COMPATIBILITY.md),
[les règles](docs/GAME_RULES.md), [le guide admin](docs/ADMIN_GUIDE.md) et
[le fonctionnement du butin](docs/LOOT_SYSTEM.md).
