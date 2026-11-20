# Installation contrôlée V2.1 — 20 novembre 2026

**Installation réussie, serveur réservé à la recette. Partie officielle non lancée.**

Opération `MS-DEPLOY-V21-20261120-01`, serveur MineStrator **513365**,
candidat **V21-QUERY-20261120-01**, autorisé après lecture du rapport du commit
`c0ccdd9`. Le propriétaire a explicitement accepté, pour cette opération,
l'absence de verrou de maintenance exclusif et la politique de relance après
crash de l'hébergeur non vérifiée. Cette dérogation ciblée ne modifie pas
`AGENTS.md` et n'autorise ni lancement de partie ni tests destructifs.

Le [reçu technique](../tests/results/minestrator-deployment-20261120.json)
conserve les compteurs, empreintes et limites. Les journaux détaillés, données,
références de carte et accès restent hors Git.

## Contrôles et exécution réelle

| Étape | Résultat |
|---|---|
| Préconditions avant écriture | Identité/API authentifiée, SFTP avec clé hôte épinglée, serveur arrêté, paramètres panel identiques à la référence |
| Source historique | Métadonnées de 305 fichiers et 321 dossiers conformes ; 18 fichiers critiques relus par SHA-256 ; audit complet précédent non recommencé |
| Patch approuvé | Seul `settings.restart-on-crash` passe de `true` à `false` ; original conservé, watchdog inchangé |
| Staging | 148 fichiers créés exclusivement, relus après transfert puis vérifiés une seconde fois avant quarantaine |
| Quarantaine | 142 fichiers dans trois arbres, neuf anciennes versions individuelles et le Spigot original : **152 fichiers préservés** |
| Activation | Trois nouveaux arbres puis fichiers individuels, manifeste posé en dernier ; aucun écrasement de quarantaine ni effacement par l'outil |
| Installation à froid | **148 SHA-256, 148 modes et 148 propriétaires UID/GID vérifiés**, plus cinq fichiers conservés et le patch Spigot |
| Avant démarrage | 153 fichiers conservés recontrôlés par métadonnées ; liste exacte de 302 fichiers actifs ; nouvelle relecture des 148 SHA et des cinq contrôles conservés |
| Démarrage | Une seule demande `start` API, le 20/11 à **23:41:49 heure de Paris** ; `Done (4.905s)` à 23:41:56 |
| Contrôle fonctionnel | Terminé à 23:42:11 ; **zéro erreur et zéro avertissement** dans le journal capturé |
| Accès réseau | Query UDP répond, API MineBoard à 20 places ; statut Minecraft TCP confirmé à 23:43:34, protocole 777, Paper 26.3, 0/20 joueurs |
| Dernier contrôle API authentifié | **23:50:15 heure de Paris : `online`, 0/20 joueurs**, requête GET uniquement |

L'installation à froid s'est déroulée entre 23:29:00 et 23:37:53, heure de Paris.
La surveillance a enregistré 106 observations `offline` pendant cette phase,
avec un intervalle maximal de 5,134 s. La phase de démarrage a enregistré 41
observations `offline`, `starting`, puis `online`, au maximum espacées de 5,136 s.
La pause de préparation locale entre ces deux sessions de surveillance dure
environ 72 s, sans commande ni transfert distant ; arrêt et intégrité ont été
recontrôlés lors de la seconde session avant l'unique commande de démarrage.
Aucun démarrage inattendu ni divergence critique n'a été observé.

Les **115 tests Python locaux passent**, dont 14 tests du déploiement : refus
d'écrasement, création exclusive, intégrité avant renommage, interruption de
copie sur perte de contrôle, refus des mutations API hors périmètre, détection
de fichiers imprévus/modifiés et refus de rollback implicite d'une installation
saine. Les réponses SFTP de ces tests sont simulées ; la carte privée est aussi
contrôlée en lecture seule.

## Fichiers réellement installés et empreintes

Les **148 chemins, tailles et empreintes** sont exactement ceux de la
[liste exhaustive approuvée](MINESTRATOR_148_FILES_20261120.tsv).
Ils comprennent 121 fichiers de monde, cinq fichiers FKAmis, huit fichiers du
plugin officiel, sept outils/références de maintenance, le JAR FKAmis et six
fichiers racine. Le manifeste privé relu après activation correspond à cette
liste, sans ajout de comptes ou d'inventaires historiques.

| Élément | SHA-256 vérifié |
|---|---|
| `DEPLOYMENT_MANIFEST.json` installé | `bc99993cf2796991a97adf92c12091bea86e5b5166c503258d1311aa227948e6` |
| FKAmis installé | `38180caa28442bad838ef395779d9075a33a2c624bc71e2286488ac0e32fb31a` |
| Paper conservé | `9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf` |
| FallenKingdom officiel conservé | `9127a92a5ad621f74b29ab8e53b6785d4ee30dd15f720c82c64f2c6a5973ba3b` |
| `spigot.yml` installé, hors des 148 cibles | `63e939902bc52b0868598205130a94bb5e9f3733073008a05399fddfef687667` |
| `spigot.yml` original en quarantaine | `4764ac315bbd64efe70161977c18c5ce372c72aef5302b75a2648a82c5a88678` |

Les cinq fichiers contrôlés et conservés sont `paper.jar`, `server.jar`,
`plugins/FallenKingdom-2.24.9.jar`, `whitelist.json` et `ops.json`.
Le JAR officiel n'a pas été modifié. Les modes et UID/GID des fichiers installés
correspondent aux sources attendues ; les nouveaux fichiers ont les modes
prévus et le même propriétaire de service que les fichiers conservés.

Les SHA du monde et des états décrivent l'installation **avant démarrage**.
Les journaux, verrous de session, horodatages/compteurs de monde, caches de
plugins et sérialisations de propriétés sont des fichiers vivants susceptibles
d'être réécrits normalement par Paper. Leur immobilité binaire après démarrage
n'est pas revendiquée. Aucun reset ni commande de réinitialisation n'a été envoyé.

## Versions, règles et carte observées

- Java **25.0.5+8-LTS** observé sur Linux ; image Java 25 Performance et paramètres
  MineBoard conservés. Paper **26.3-244**, FallenKingdom **2.24.9**, FKAmis **1.0.0**.
- Capacité **20**, port de jeu et Query **22880**, whitelist stricte et ses **deux
  comptes existants inchangés**. Aucun ajout de participant ou d'opérateur.
- Quatre équipes Rouge, Bleue, Verte, Jaune, chacune affichée **0/4**, actives.
  Maximum 16 participants ; arbitre hors effectifs. Validation de configuration réussie.
- Paramètres effectifs affichés : `players-per-team: 4`, `capture-seconds: 60`,
  `capture-radius: 2.5`. Le JAR validé conserve le seuil de deux attaquants
  pour un effectif officiel d'au moins deux membres, et un pour une équipe solo ;
  aucun scénario de capture en jeu n'a été exécuté pendant cette installation.
- **Jour 0, `started=false`, aucun membre officiel ni objectif de progression.**
- Quatre territoires de rayon **40**, coordonnées des quatre spawns conformes.
  Les blocs immédiatement autour des spawns correspondent à la référence.
- Quatre cavernes vérifiées par **37 128 points de référence dans 47 chunks**,
  sans changement de dimensions ni de topographie par le déployeur.
- Portail officiel non activé ; voyage fermé/suspendu, aucune sortie Vanilla générée
  selon la commande de diagnostic. Aucune traversée ou activation effectuée.

Les contrôles de blocs et de fichiers sont techniques. Ils ne remplacent pas
une inspection visuelle des cavernes, de leurs accès ou de la jouabilité des
spawns par un joueur authentifié.

## Query, MineBoard et premières mesures

Query écoute sur `0.0.0.0:22880` selon Paper et a répondu au protocole UDP avec
une capacité de **20**. L'API utilisée par MineBoard a également renvoyé **0/20**.
Le rendu visuel du panneau n'a pas été inspecté pendant cette opération.
L'[API officielle](https://api.minestrator.com/) distingue la transmission des
commandes de leur exécution ; les sorties attendues ont ici été vérifiées dans
le journal du serveur, au-delà du seul code HTTP 200.

Mesures immédiates à vide, quelques secondes après démarrage :

| Indicateur | Observation et limite |
|---|---|
| TPS affichés 1/5/15 min | 19,5 / 19,5 / 19,5 ; fenêtres encore très incomplètes au démarrage |
| MSPT 5 s, moyenne/min/max | 1,1 / 0,6 / 4,8 ms |
| MSPT 10 s et 1 min, moyenne/min/max | 3,2 / 0,2 / 195,6 ms ; pic pendant le démarrage |
| Mémoire API | `current=1325`, `limit=8000`, `percent=16` ; unité brute non certifiée indépendamment |
| Ping de statut TCP depuis ce PC | 18,063 ms ; mesure réseau sans authentification de joueur |
| GC | Non mesuré dans cette recette initiale |

Ces valeurs **ne démontrent pas les performances à 17 connexions réelles**.
La recette à 4, 8, 16 participants puis avec l'arbitre doit suivre le
[protocole préparé](MINESTRATOR_RECETTE_ET_WHITELIST_20261120.md), avec TPS,
MSPT, RAM, GC et ping sur des fenêtres stabilisées. Les identités supplémentaires
doivent être vérifiées et approuvées ; aucune n'a été inventée.

## Données conservées et retour arrière

Sauvegarde source immuable sur le PC, hors dépôt et hors instance :
`C:\Users\youne\FKBackups\MS-COLD-20261119-02`.

| Élément original, inchangé | SHA-256 |
|---|---|
| `instance.zip` | `255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf` |
| `manifest.json` | `b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1` |

Les **305 fichiers de `restore/` ont été revérifiés et restent inchangés**.
Le rollback historique à dix places et Query activé a déjà réussi localement ;
aucun rollback distant n'a été nécessaire pendant cette installation.

Conservation distante, sans suppression :

```text
.fk-quarantine/MS-DEPLOY-V21-20261120-01/trees/world/
.fk-quarantine/MS-DEPLOY-V21-20261120-01/trees/plugins/FKAmis/
.fk-quarantine/MS-DEPLOY-V21-20261120-01/trees/plugins/FallenKingdom/
.fk-quarantine/MS-DEPLOY-V21-20261120-01/files/
.fk-stage/MS-DEPLOY-V21-20261120-01/
```

Les 142 fichiers des arbres et les dix versions individuelles ont été vérifiés
par SHA après leur déplacement. Le staging subsiste, avec ses dossiers résiduels ;
ses fichiers validés ont été promus par renommage. Aucun nettoyage automatique.

Le journal des 31 renommages, les 149 transferts vérifiés (148 + Spigot), le reçu
des permissions, les observations API et les logs privés se trouvent dans
`C:\Users\youne\FKBackups\MS-DEPLOY-V21-20261120-01`.
Leurs empreintes sont consignées dans le reçu technique public ; leurs contenus
privés ne sont pas publiés.

En cas d'anomalie critique dans le périmètre autorisé : confirmer identité,
arrêt stable, capacité et intégrité du point historique ; arrêter proprement si
nécessaire, préserver l'instance V2.1 par renommage vers une nouvelle quarantaine
`failed-instance`, puis restaurer les 305 fichiers dans l'espace applicatif neuf.
Ne jamais superposer les deux mondes ni revenir au seul JAR. Réconcilier le
marqueur `FKAmis.sha256` de l'instance restaurée avec son JAR historique
`46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442`,
sans toucher au point original. **Conserver `restart-on-crash=false`**, y compris
en rollback : restaurer `true` n'est pas autorisé implicitement. Ces deux
adaptations de l'instance restaurée sont explicites, le reste revient au point -02.
Contrôler tous les SHA, les modes/UID/GID, dix places et Query, puis utiliser le
validateur externe compatible `historical-rollback` avant tout redémarrage.

Le script ponctuel `scripts/minestrator_deploy.ps1` refuse un dossier existant
en phase `install`, un deuxième `start`, et un rollback implicite d'une
installation saine. Il ne doit pas être relancé à l'aveugle. Le rollback
automatisé prévu laisserait l'instance restaurée arrêtée pour contrôle ; il n'a
pas été exécuté ni présenté comme testé à distance aujourd'hui.

## Politique finale et réserves

**`restart-on-crash=false` est effectivement laissé en place**, relu et vérifié
après démarrage. Watchdog Spigot/Paper et délais conservés ; aucun autre réglage
du panel modifié. Une réactivation de la relance Spigot exige une validation
préalable de son comportement et de la politique de production.

Aucune anomalie critique observée. Restent les limites connues : absence de
verrou exclusif, politique de relance hébergeur non vérifiée, états échantillonnés
plutôt que preuve d'absence de processus concurrent. La page publique
[statut MineStrator](https://minestrator.com/statut) affichait les services
opérationnels ; cela ne certifie pas l'absence de maintenance ciblée sur l'hôte.
Les informations manuelles du propriétaire sur l'espace libre, les tâches,
le calendrier et les actions en attente restent la base de ces préconditions.

**GO pour la recette restreinte. Pas de lancement de partie officielle ni de
tests destructifs sans autorisation distincte.** Les vérifications humaines,
l'affichage réel MineBoard et la charge avec joueurs restent à effectuer.
