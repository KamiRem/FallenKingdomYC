# Déployer le profil retenu : Paper 26.3 sur MineStrator

## Préparation courante : quatre membres, 20 novembre 2026

Voir [les règles, le manifeste et les réserves](FOUR_PLAYERS_20261120.md).
V2.1 est préparée localement à **20 places**, quatre royaumes de 1 à 4 participants,
arbitre distinct. Le plan actuel porte sur **148 fichiers** et propose Query
désactivé sur la nouvelle instance seulement. Whitelist et paramètres panel
restent protégés. Aucun transfert ou changement distant n'est autorisé.
Le point historique conserve ses **10 places** ; son test fonctionnel reste
bloqué par Query activé. Les livraisons et consignes ci-dessous sont historiques.

## Livraison ciblée VNext.1 courante

Lire [le guide VNext.1](FKAMIS_VNEXT_1.md), `tests/results/vnext1-delivery.json`
et les empreintes externes. Extraire `dist/fallenkingdom-vnext1-update.zip` hors
instance, arrêter et sauvegarder tout le serveur, puis lancer
`python apply_vnext1_update.py --server /chemin/instance`. L'outil refuse les
objectifs incompatibles avec le rayon 40 avant toute écriture et sauvegarde à froid.
Il conserve port 22880, paramètres panel et données ; seul `allow-flight=true` est
imposé dans les propriétés. Redémarrer isolé en pause, inspecter, puis recette humaine.
Un retour à VNext restaure toute la sauvegarde dans un dossier neuf.

Pour une nouvelle carte, utiliser séparément `dist/fallenkingdom-map-v2.1-build.zip`
sur une référence initiale approuvée, jamais sur une partie jouée. Inspecter la
sortie et sceller avec `maintenance/new-match-reference-v2.1.json`. Aucun fichier
de monde ne se trouve dans le paquet de mise à jour.

## Livraison ciblée VNext précédente

Lire les dix étapes du [guide VNext](FKAMIS_VNEXT.md), le rapport
`tests/results/vnext-delivery.json` et les SHA-256 externes. Paquet courant :
`dist/fallenkingdom-vnext-update.zip`. Arrêter, sauvegarder intégralement à froid,
puis `python apply_vnext_update.py --server /chemin/instance`. Le JAR, les outils,
les clés config manquantes et le registre sont mis à jour ; monde, progression,
arbitres et ravitaillements restent conservés. Port 22880, Paper 26.3-244, Java 25
et paramètres du panel restent ceux de l'hôte. Redémarrer en pause et vérifier
les données avant recette humaine. Retour arrière par sauvegarde complète dans
une destination neuve ; remplacer le seul JAR ne suffit pas après migration.

## Livraison gameplay précédente

Voir [GAMEPLAY_UPDATE.md](GAMEPLAY_UPDATE.md) pour la livraison ciblée, les causes,
les limites de preuve, l'installation et le rollback. Le rapport définitif est
`tests/results/gameplay-update-delivery.json`. Paper 26.3-244 / Java 25 / FK 2.24.9
inchangé ; 1 à 4 membres par équipe (défaut 2), arbitre UUID indépendant, lit valide
ou centre sûr pour les morts, construction neutre libre, capture sans condition de
regard, locator bar désactivée, mobs suspendus au jour 0 et `/fka announce <message>`.
Les guides des anciennes livraisons restent historiques.

## Serveur déjà installé : appliquer la livraison ciblée

Ne pas retransférer le monde. Utiliser **`dist/fallenkingdom-admin-update.zip`** :
JAR FKAmis et empreinte, maintenance compatible dix places et patch limité aux
clés de configuration. Sauvegarder intégralement à froid avant intervention.
Conserver `world/`, `state.yml`, territoires, `supplies.yml`, whitelist et
`admins.yml` existant. Aucun `/reload`. Voir [la procédure et le retour arrière](ADMIN_UPDATE.md).

Mettre `max-players=10`, `gamemode=survival`, `force-gamemode=false` ; conserver
authentification/whitelist, Paper 26.3, Java 25 Performance et le port 22880.
Whitelist : huit participants **plus l'arbitre**, rôles attribués par UUID via console.
Le guide complet ci-dessous concerne une installation initiale ; le serveur en
place reçoit seulement cette mise à jour ciblée.

Le paquet courant est **`dist/fallenkingdom-preproduction-26.3.zip`**, avec son
`.zip.sha256` et son rapport `tests/results/preproduction-package-26.3.json`.
Le profil est Paper **26.3 build 244 STABLE**, Java 25 Performance, FallenKingdom
officiel 2.24.9 et FKAmis 1.0.0 compilé contre l’API 26.3. Aucun JAR de chantier ou
recette n’est inclus. La copie locale propre est `runtime/preproduction-26-3`.

Le propriétaire a choisi **MineStrator MyBox Perf 8**, mémoire panel environ **6154M**,
port **22880**. Le service distant est annoncé vide/arrêté ; aucun accès distant
n’a été effectué. Le paquet contient déjà `server-ip=` vide, `server-port=22880`,
`level-name=world` et la whitelist/authentification obligatoires.

1. Lire [l’audit et les limites de compatibilité](PREPRODUCTION_AUDIT.md).
2. Appliquer [le transfert SFTP, Java/JAR et démarrage MineBoard](HOST_INSTALLATION.md).
3. Prouver [une sauvegarde/restauration complète à froid](BACKUP_RESTORE.md).
4. Effectuer [la recette humaine à huit et les mesures de charge](MULTIPLAYER_ACCEPTANCE.md).
5. Repartir du ZIP 26.3 initial selon [OFFICIAL_LAUNCH.md](OFFICIAL_LAUNCH.md), puis
   signer [la checklist](PRODUCTION_CHECKLIST.md) avant toute commande de lancement officiel.

La référence `runtime/map-v2-fixes`, `runtime/local`, `runtime/map-v2`, le ZIP 26.2
et les sauvegardes historiques sont intacts. Les fixtures sous `.cache/` ne sont
jamais des sources de déploiement. Une carte convertie en 26.3 ne doit pas être
rouverte en 26.2 : retrouver l’ancien état exige une nouvelle restauration de
l’archive 26.2 et ses JAR, dans un espace distinct, sans écrasement.

Le [comparatif d’hébergement daté](HOSTING_COMPARISON.md) reste disponible comme
historique du choix ; il ne faut plus commander un autre service pour cette installation.
