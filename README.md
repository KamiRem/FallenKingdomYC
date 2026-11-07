# Fallen Kingdom privé — huit amis

La **préproduction** est préparée à partir de `runtime/map-v2-fixes`, visuellement
approuvée par le propriétaire et conservée intacte. Commencer par
[l’audit](docs/PREPRODUCTION_AUDIT.md), le [choix d’hébergement](docs/HOSTING_COMPARISON.md)
et le [guide de transfert](docs/HOST_INSTALLATION.md). Le ZIP privé et ses empreintes
sont identifiés dans [le rapport de livraison](tests/results/preproduction-package.json).
La [recette réelle à huit](docs/MULTIPLAYER_ACCEPTANCE.md) et le
[lancement propre](docs/OFFICIAL_LAUNCH.md) restent des étapes humaines.
Paper 26.2 est hors maintenance ; la branche `test/paper-26.3-preprod` teste la
migration sur copies, sans adoption automatique ni rétrogradation.
Aucun service n’est commandé et aucune partie officielle n’est lancée.

Les **corrections de la v2** sont préparées dans `runtime/map-v2-fixes` : nettoyage
des supports naturels, PvE actif dès J1, minage adverse interdit en permanence,
élytres et pommes enchantées interdites, `/fka teams tpall [confirm]`.
`runtime/local` et `runtime/map-v2` sont conservés. Voir [le bilan des corrections](docs/V2_CORRECTIONS.md).

```powershell
# Utiliser la copie de recette ; conserver la référence map-v2-fixes arrêtée.
.\scripts\server.ps1 start -Name preproduction -Port 25580
```

Le **premier chantier v2**, conservé dans `runtime/map-v2`, possède une bordure de 1 200 blocs,
royaumes voisins à environ 408–482 blocs, terrains aménagés, quatre drapeaux, sept
monuments et ravitaillements toutes les 30 minutes actives. L'instance historique
`runtime/local` est conservée. Lire [la livraison v2](docs/MAP_V2.md),
[le fonctionnement du butin](docs/LOOT_SYSTEM.md) et [le carnet d'inspection](docs/MAP_V2_INSPECTION.md).

La validation visuelle de `map-v2-fixes` a été donnée dans la demande de préparation
de production ; la recette avec huit comptes reste à faire avant le démarrage officiel.
Les sections ci-dessous décrivent aussi les profils historiques.

Projet Windows prêt à installer : **Paper 26.2 build 135**, **Java 25**,
**FallenKingdom 2.24.9** de syldium et complément indépendant **FKAmis 1.0.0**.
Quatre équipes de deux, forts entièrement construits par les joueurs, objectifs
secrets enregistrés par leur équipe, phases avancées uniquement par l'administrateur.

Le dossier `runtime/local` contient l'installation locale. Les mondes, JAR téléchargés,
outils, identités et objectifs sont exclus de Git. Sur un nouveau clone, les scripts
les reconstruisent. L'EULA reste à `false` jusqu'à une acceptation explicite.

Dans ce workspace, la carte **123456789** a réellement été prégénérée sur 1 800 × 1 800
blocs, puis sauvegardée et restaurée en test. Le serveur est arrêté après les essais.
L'EULA a été acceptée explicitement pendant la préparation. Pour reprendre ici :
`.\scripts\server.ps1 start`. Les étapes d'installation ci-dessous concernent une
nouvelle copie du dépôt ; elles refusent de remplacer une partie existante.

## Démarrage sous Windows

Python 3.11+ et PowerShell sont nécessaires. Depuis la racine du dépôt :

```powershell
.\scripts\bootstrap.ps1
.\scripts\build.ps1
.\scripts\server.ps1 install
# Après lecture et acceptation personnelle de https://www.minecraft.net/eula :
.\scripts\server.ps1 accept-eula -Accept
.\scripts\server.ps1 start
```

Connexion locale avec un client **Minecraft Java 26.2** : `127.0.0.1:25565`.
Dans la console : `whitelist add VotrePseudo`, puis `op VotrePseudo` pour préparer
la carte. L'authentification officielle reste active. Aucun mod client requis.

Avant de jouer, suivre [l'installation](docs/INSTALLATION.md), inspecter les quatre
terrains, définir les territoires et attribuer les huit comptes. **Aucun lancement
officiel n'a été effectué et aucun terrain n'est déclaré équilibré automatiquement.**

## Règles initiales

| Phase | PvP | Assauts | Nether |
|---|---|---|---|
| Jour 1 | fermé | fermés | fermé |
| Jour 2 | hors territoires protégés | fermés | ouvert |
| Jour 3 et suivants | ouvert | ouverts, capture en 60 secondes | ouvert |

L'End est fermé jusqu'à décision administrative. Netherite, débris antiques et modèle
d'amélioration en netherite sont interdits dans toutes les dimensions. Les élytres et
pommes dorées enchantées sont aussi interdites ; les pommes dorées ordinaires
restent autorisées. Les mobs et dangers naturels restent actifs dès le jour 1.
La construction
FK classique limite la pose hors de sa base ; le minage adverse reste interdit, les
défenses sont ouvertes à la TNT au jour 3. Voir [le règlement](docs/GAME_RULES.md).

## Administration et maintenance

```powershell
.\scripts\server.ps1 validate
.\scripts\server.ps1 check-logs
# Dans la console du serveur : fka pause, puis stop. Attendre sa fermeture.
.\scripts\server.ps1 backup
.\scripts\server.ps1 restore -Name restauration -Source 'C:\chemin\sauvegarde.zip'
.\scripts\server.ps1 export
```

Le lancement par le script crée une sauvegarde vérifiée après chaque arrêt propre.
Une sauvegarde pendant l'exécution est refusée. La restauration crée une nouvelle
instance et conserve l'original. Les archives de déploiement sont **privées**.

## Documentation

- [Architecture et réutilisation de FallenKingdom](docs/ARCHITECTURE.md)
- [Installation Windows](docs/INSTALLATION.md)
- [Carte naturelle et territoires](docs/MAP_GUIDE.md)
- [Commandes administrateur](docs/ADMIN_GUIDE.md)
- [Guide des huit joueurs](docs/PLAYER_GUIDE.md)
- [Règlement détaillé](docs/GAME_RULES.md)
- [Hébergement, déploiement et sauvegardes](docs/DEPLOYMENT.md)
- [Versions, sources et licences](docs/COMPATIBILITY.md)
- [Tests exécutés et recette multijoueur restante](docs/TEST_PLAN.md)

Les vérifications automatiques ne remplacent pas une partie de recette avec les
clients authentifiés. Le suivi des opérations manuelles figure dans le plan de tests.
