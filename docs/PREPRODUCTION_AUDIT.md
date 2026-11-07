# Audit de préproduction — 7 novembre 2026

La référence **`runtime/map-v2-fixes` est conservée intégralement**, ainsi que les
historiques. Sa validation visuelle est une **attestation du propriétaire dans sa
demande**, pas une inspection en client réalisée par l’agent. Aucun monde reconstruit,
aucune mécanique de jeu modifiée, aucun abonnement commandé, aucune partie officielle
lancée. La préparation fournit une copie initiale privée et les procédures de recette.

## Versions et décision

| Composant | Référence livrée | Contrôle |
|---|---|---|
| Paper / Minecraft | 26.2 build 135 STABLE | JAR officiel intact, empreinte vérifiée ; branche **hors maintenance** |
| Java local | Temurin 25.0.5+8, HotSpot | Exécution réelle ; Java 25 requis aussi chez l’hôte |
| FallenKingdom | 2.24.9 officiel | JAR inchangé, dernière release publique relevée le 7 novembre |
| FKAmis | 1.0.0 corrigé | Exactement le binaire de la carte approuvée, compilé contre Paper 26.2 |
| Candidat maintenu | Paper 26.3 build 244 STABLE | Testé uniquement sur copies, branche `test/paper-26.3-preprod` |

L’[API officielle Paper 26.2](https://fill.papermc.io/v3/projects/paper/versions/26.2)
indique `UNSUPPORTED`, fin de support **2026-11-03**.
L’[API 26.3](https://fill.papermc.io/v3/projects/paper/versions/26.3) indique `SUPPORTED` ;
le [build 244](https://fill.papermc.io/v3/projects/paper/versions/26.3/builds) est STABLE,
publié le 6 novembre. Le [guide Paper](https://docs.papermc.io/paper/getting-started/)
requiert Java 25 pour cette génération. Ces statuts sont datés, pas une garantie future.

La [release officielle FallenKingdom 2.24.9](https://github.com/syldium/FallenKingdom/releases/tag/v2.24.9)
reste la dernière dans l’[API des releases](https://api.github.com/repos/syldium/FallenKingdom/releases/latest),
avec compatibilité déclarée jusqu’à **26.2**, sans déclaration 26.3. Ne pas modifier
le JAR tiers, compiler une branche de développement à sa place ou assimiler un test
local à un engagement de support de l’auteur.

**Décision :** conserver l’export 26.2 pour reproduire exactement la référence ; ne
pas le présenter comme une production durable maintenue. Paper 26.3 est un candidat
sérieux pour une **préproduction supplémentaire**, ses contrôles techniques ayant
réussi. Son adoption officielle reste conditionnée à l’inspection de la copie convertie,
la recette des huit comptes et la décision du propriétaire sur cette compatibilité
non déclarée par FallenKingdom. Aucune migration directe de la référence ni downgrade.

## Empreintes SHA-256 des exécutables

```text
Paper 26.2-135
ef3dbc68b013deafdbbee3bebf1ba351671ebcda94a8f136809b7532d5ba2fe1
FallenKingdom 2.24.9
9127a92a5ad621f74b29ab8e53b6785d4ee30dd15f720c82c64f2c6a5973ba3b
FKAmis 1.0.0 corrigé
5245f0a20426b9e15c38b55a8acf87d56d3fbfd54b4d146720a738d670981d6a
Paper 26.3-244 (branche de test uniquement)
9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf
```

Seuls **FallenKingdom et FKAmis** figurent dans `plugins/*.jar` du paquet. Java est
fourni par l’hébergeur. Maven/JUnit et les probes servent au développement, sans
dépendance d’exécution de jeu supplémentaire. Aucun WorldEdit, outil de construction,
nettoyage, diagnostic ou recette n’est transféré. Le bootstrap Paper reconstruit ses
bibliothèques de plateforme au premier démarrage ; le JDK Windows n’est pas exporté.

## Référence, état initial et export

La sauvegarde intégrale à froid est :

```text
backups/map-v2-fixes/fk-20261107T123041264839Z.zip
SHA-256 049d307047506cf2449defb3417841b4c9e8b8fcc02a04f85c33a494dc8f7d60
```

Ses **285 fichiers** sont relevés en privé, puis comparés avant/après préparation.
L’archive comprend l’intégralité de la référence, y compris les anciens accès et
données de visite ; elle reste locale, privée et exclue de Git.
Le ZIP de déploiement courant et son empreinte exacte sont dans
`tests/results/preproduction-package.json` du dépôt, sans coordonnées secrètes ni
comptes. Il possède `BACKUP_MANIFEST.json`, `DEPLOYMENT_MANIFEST.json`,
`RUNTIME_LOCK.json` et un fichier externe `.zip.sha256`. Tous les fichiers sont relus
avant publication du ZIP ; restauration dans un dossier neuf et comparaison intégrale.

Les **121 fichiers de monde conservés** sont copiés octet pour octet, y compris les
trois dimensions sous `world/dimensions/minecraft/`, régions/entités/POI et données du
monde. Les quatre profils de visite individuels sont exclus du paquet. Les quatre
bases de rayon 80, les drapeaux, sept monuments et huit sites restent en place.
Les **six coffres de monuments contenant du butin** ont été lus dans les régions :
matériaux et quantités correspondent aux plans, sans régénération. Le monument sans
table de butin n’est pas compté comme coffre manquant. Les plans originaux sont livrés
comme références, pas exécutés par un plugin de chantier.

État FKAmis inchangé : jour 0, `started=false`, aucun gagnant/éliminé, roster et
objectifs vides, spawns et équipes natives conservés ; confirmations de terrains encore
vides à enregistrer dans la copie après inspection. Ravitaillement activé, mode test
désactivé, délai 1 800 secondes actives, événement 0, aucun lot consommé/historique.
Coordonnées et tables : `plugins/FKAmis/supplies.yml` ; règles : `config.yml` ;
territoires/spawns : `state.yml` et sauvegarde native. Ne pas les dissocier du monde.

## Accès et sécurité

La référence contenait un OP, deux entrées de whitelist et un cache de visites.
Ils restent dans la sauvegarde intégrale, **pas dans le paquet de déploiement** :
listes d’accès vides, profils/statistiques/avancements de visite exclus, cache
`PlayerManager` natif vidé dans la seule copie. Les règles et équipes natives restent
conservées. Les logs, historique console, caches de comptes et de plugins sont omis.
Les UUID d’entités et autres données structurelles du monde sont préservés ; leur
présence ne constitue pas un compte administrateur ou un secret d’hébergement.

Authentification officielle, whitelist stricte, huit places, PvP serveur activé pour
laisser les plugins appliquer les phases, difficulté normale, RCON/query/command blocks
désactivés. Mot de passe RCON vide, secret proxy vide contrôlé. Aucun identifiant de
panel, mot de passe SFTP ou jeton n’est intégré. Le paquet initial écoute localement ;
IP/port ne seront adaptés **qu’après choix de l’hôte**, sur la copie transférée.
Utiliser la console du panel plutôt qu’un participant OP ; le lancement normal
refuse des participants OP. Ne pas ajouter de plugin de permissions pour cette seule recette.

La carte et les objectifs futurs restent privés même sans compte exporté. Les ZIP
dans `dist/`, mondes, backups et worktree de test sont exclus de Git. L’EULA copiée
provient de l’acceptation explicite antérieure pour les essais locaux ; aucun script
n’accepte de nouvelles conditions. Voir les [conditions Minecraft](https://www.minecraft.net/eula).

## Contrôles réellement exécutés

- **16 tests Python** des verrous, archives, chemins dangereux, restauration neuve,
  empreintes externes, manifeste initial et exclusion des sauvegardes imbriquées.
- Démarrage réel de la préproduction 26.2 avec les deux plugins seuls, état jour 0,
  arrêt propre, refus d’une sauvegarde concurrente. Aucun ERROR/SEVERE ; avertissement
  attendu de version Paper ancienne. `preproduction-smoke.json` enregistre les preuves.
- Sauvegarde complète après arrêt, restauration indépendante et comparaison des
  **287 fichiers** de ce point : `preproduction-recovery.json`.
- Démarrage réel de la copie Paper 26.3-244, deux plugins inchangés, jour 0, arrêt
  propre, aucun ERROR/SEVERE après contrôle corrigé de l’encodage console Windows.
- **189 assertions techniques sur Paper 26.3** : règles natives 23 + redémarrage 5 ;
  gameplay corrigé 112 ; ravitaillements 43 + redémarrage 6. Le premier essai du probe
  de ravitaillement manquait de dossier pour son rapport ; une nouvelle fixture avec
  ce dossier a passé la suite. Aucun changement de gameplay n’a été nécessaire.

Les fixtures restent dans `.cache/paper-26.3-worktree/runtime/`, séparées de la copie
de migration propre. Elles ont réellement modifié leurs propres blocs et états ;
elles ne sont jamais une carte à déployer. Les 112 contrôles gameplay utilisent
**huit interfaces Player simulées, zéro client authentifié**. Les mesures TPS/MSPT
collectées au démarrage sont à vide ; elles ne prédisent pas la charge à huit.
Le rapport `tests/results/paper-26.3-migration.json` distingue explicitement ces limites.

## Performances et étapes restantes

Prévision de capacité : service **8 Go**, heap initiale environ 6 Go, CPU moderne
à bonnes performances par cœur, NVMe et France proche des joueurs ; vue 8,
simulation 6 conservées. Ce dimensionnement est une hypothèse à tester, sans promesse
de TPS. Relever l’usage total du conteneur, pas seulement la heap. Les huit connexions,
leur ping, les explosions et captures doivent être mesurés sur l’hôte choisi.

Suivre [l’hébergement](HOSTING_COMPARISON.md), [l’installation](HOST_INSTALLATION.md),
[la recette réelle](MULTIPLAYER_ACCEPTANCE.md), [les sauvegardes](BACKUP_RESTORE.md),
[le lancement depuis l’archive initiale](OFFICIAL_LAUNCH.md) et
[la checklist](PRODUCTION_CHECKLIST.md). Le choix de version, la commande du service,
la recette humaine et le lancement restent au propriétaire.
