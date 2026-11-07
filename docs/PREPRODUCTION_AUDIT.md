# Audit — promotion définitive du profil Paper 26.3

Le profil du projet est maintenant **Paper 26.3 build 244 STABLE / Java 25**,
sur autorisation explicite du propriétaire. L’hébergement choisi est **MineStrator
MyBox Perf 8**, Java 25 Performance, environ **6154M** de heap gérés par le panel,
port de jeu **22880**. Aucun accès au serveur distant n’a été effectué et aucune
partie officielle n’a été lancée.

## Références protégées et provenance

`runtime/local`, `runtime/map-v2`, `runtime/map-v2-fixes`, les sauvegardes historiques
et l’archive 26.2 sont conservés. Les relevés privés comptent respectivement
268, 278 et 285 fichiers pour ces trois instances ; 23 archives antérieures ont
été relevées avant la migration. Le contrôle final consigne leur intégrité.

Source de la nouvelle instance `runtime/preproduction-26-3` : restauration complète
et vérifiée de **175 fichiers**, avant tout remplacement de version :

```text
dist/fallenkingdom-preproduction-26.2-20261107T125953Z.zip
SHA-256 4156b79fe8d89b2037b049759f0eafd426cdf3adb8d0656d91a0e72fdfc36aa9
```

La carte 26.2 est visuellement approuvée par le propriétaire. L’inspection en client
de la copie 26.3 reste à faire. Aucune reconstruction, prégénération, modification
de coordonnées ni recharge de butin n’a été exécutée. Les fixtures de recette restent
dans `.cache/paper-26.3-final-qa/` et ne sont jamais utilisées comme carte à transférer.

## Versions et changements réels

| Élément | Profil retenu | Contrôle |
|---|---|---|
| Paper | 26.3 build 244 STABLE, commit 35a2d15, 6 novembre 2026 | API officielle et disponibilité HTTP 200 du JAR revalidées le 7 novembre |
| Java | 25 ; local Temurin 25.0.5+8 | Démarrages réels, même version majeure que le panel annoncé |
| FallenKingdom | 2.24.9 officiel | Dernière release publique vérifiée ; JAR strictement inchangé |
| FKAmis | 1.0.0, API de compilation 26.3.build.244-stable | Recompilé et testé ; descripteur api-version 26.3 |

Empreintes SHA-256 :

```text
paper.jar
9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf
plugins/FallenKingdom-2.24.9.jar
9127a92a5ad621f74b29ab8e53b6785d4ee30dd15f720c82c64f2c6a5973ba3b
plugins/FKAmis-1.0.0.jar
9201a72528b8f6699f394c3e495ab7192bde312614f7f3d2bad88edaf9a8ea37
```

Le verrou principal et `configs/paper-26.3/artifacts.lock.json` ciblent ce build fixe,
jamais `latest`. Le POM et `plugin.yml` ont été actualisés ; **aucun fichier Java
de production n’a été modifié**. Les 25 fichiers `.class` de production sont
identiques à ceux du binaire antérieur : les règles n’ont pas été réécrites.
Le nouveau JAR diffère par ses métadonnées de compilation/version minimale.
Ne pas le remplacer dans une instance 26.2 historique : son api-version refuse
désormais le chargement sur une version plus ancienne.

Les ajouts concernent les scripts de conversion/scellement, la comparaison du monde,
les tests et la documentation. Le lecteur Anvil reconnaît les palettes 26.3 : ID
abrégé, objets id/properties et valeurs NBT hétérogènes. Il compare les propriétés
omises à celles du registre Bukkit réel de Paper 26.3 ; il n’invente pas leurs valeurs.

## Conservation de la carte et de l’état

La comparaison couvre la liste complète des fichiers de régions : fichiers inchangés
par SHA-256, puis tous les chunks modifiés par leurs blocs, biomes, block entities,
coffres/PDC et inventaires d’entités. Résultat du candidat : **70 fichiers de régions
identiques, 6 vérifiés sémantiquement**, 5 194 chunks identiques et 9 reconvertis dans
ces derniers fichiers. Aucun chunk perdu/créé, aucun changement de blocs ou de contenu.
Les métadonnées NBT de version, horloges, bordures, éclairage et sauvegarde peuvent
changer normalement ; elles ne sont pas annoncées identiques octet pour octet après conversion.

Restent présents : bordure 1 200, quatre territoires terraformés de rayon 80 et leurs
drapeaux, sept monuments, six coffres dont matériaux/quantités correspondent aux plans,
huit coffres de ravitaillement aux coordonnées initiales. L’état reste jour 0,
`started=false`, aucun roster, objectif secret, gagnant ou éliminé. Ravitaillement
activé, mode test désactivé, événement 0 et 1 800 secondes actives restantes.
Les confirmations de terrains restent à enregistrer dans la copie destinée à jouer.

## Résultats réels et limites

- **19 tests Java** et **21 tests Python** : succès, zéro échec.
- **217 assertions sur Paper réel** avec le binaire final : intégration native 28,
  règles/captures 23 + reprise 5, gameplay 112, ravitaillements 43 + reprise 6.
- Intégration native : quatre équipes/territoires, trois dimensions, règles J2/J3,
  services d’affichage, aide/listes de règles/équipes, complétion, permissions,
  blocage du lancement natif et routage du chat d’équipe/global au niveau événement.
- Démarrage du candidat, sauvegarde complète à froid, restauration de 291 fichiers
  dans `runtime/preproduction-26-3-recovery`, comparaison avant redémarrage et reprise
  réelle au jour 0, deux plugins actifs.
- Le paquet final est également restauré dans un autre dossier neuf, démarré avec
  les deux plugins seuls, contrôlé puis arrêté ; les résultats exacts figurent dans
  `tests/results/preproduction-package-26.3.json` et les rapports `promotion-26.3-*`.

Les démarrages de référence finaux ne présentent pas d’ERROR/SEVERE ni de WARN.
Deux WARN de téléportation annulée sont **attendus dans les cas négatifs** du probe
gameplay : apparition Bleue volontairement rendue dangereuse. Aucun contournement
n’a été appliqué. Les alertes de compilation concernent des API dépréciées, le
systemPath Maven du JAR officiel et Guice/Unsafe dans Maven ; elles ne sont pas des
erreurs de démarrage du serveur.

Un premier essai du nouveau probe avait tenté d’accéder directement à un champ de
FKAmis depuis un autre classloader ; le probe utilise maintenant la réflexion comme
les autres recettes, sans modification de production. Les premiers contrôles hors
ligne ne connaissaient pas les valeurs NBT par défaut de 26.3 ; leur comparaison a
été corrigée. Les journaux de ces essais restent locaux, distincts des résultats finaux.

**Zéro client authentifié** pendant ces vérifications. Le gameplay emploie huit
interfaces Player, le chat deux acteurs d’événement : ni livraison réseau d’un
message à un allié, ni rendu d’interface dans un client n’ont été prouvés. Les TPS/MSPT
relevés sont à vide, sans mesure de charge à huit ni de ping vers MineStrator.

## Compatibilité, sécurité et prochaine étape

Paper 26.3 est annoncé maintenu par l’[API officielle](https://fill.papermc.io/v3/projects/paper/versions/26.3) ;
le [build 244](https://fill.papermc.io/v3/projects/paper/versions/26.3/builds/244) est fixé.
FallenKingdom 2.24.9 reste la [release officielle](https://github.com/syldium/FallenKingdom/releases/tag/v2.24.9),
mais sa déclaration s’arrête à 26.2 : le succès local 26.3 n’est pas une déclaration
de support de l’auteur. L’[API des releases](https://api.github.com/repos/syldium/FallenKingdom/releases/latest)
a été reconsultée. Les API dépréciées devront être surveillées lors d’une future montée
de version, sans correction préventive de gameplay dans cette migration.

Le paquet contient deux JAR de production, aucun probe, log local, ancien backup,
cache de développement, profil ou inventaire de joueur de test, compte OP, jeton
ou secret d’hébergement. Whitelist stricte et authentification officielles imposées,
RCON/query/command blocks désactivés. `server-ip=` vide, port 22880, `level-name=world`.
Les entités et leurs UUID dans le monde restent préservés ; ce ne sont pas des accès.
Les objectifs futurs et sauvegardes de partie resteront privés, hors Git.

Suivre [le transfert MineStrator](HOST_INSTALLATION.md), [la recette réelle à huit](MULTIPLAYER_ACCEPTANCE.md),
[la restauration](BACKUP_RESTORE.md) et [le lancement propre](OFFICIAL_LAUNCH.md).
La promotion technique 26.3 est effectuée ; le lancement officiel attend la recette humaine.
L’ancien audit est conservé dans `PREPRODUCTION_AUDIT_26_2.md` et dans le ZIP 26.2 inchangé.
