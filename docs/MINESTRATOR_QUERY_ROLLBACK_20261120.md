# Query, rollback historique et V2.1 — 20 novembre 2026

**Rollback fonctionnel validé localement ; candidat V2.1 avec Query validé sur
localhost. Aucun déploiement ni accès API/SFTP MineStrator pendant cette mission.**
L'archive historique, son manifeste et les 305 fichiers originaux restent intacts.
Ce complément remplace les réserves Query précédentes, sans réécrire leurs preuves
ni modifier les règles générales d'AGENTS.md.

## Choix Query et MineBoard

`enable-query=false` figurait déjà dans le profil privé de `host_ops.py` au commit
`1e73325`. Aucun contrôle d'authentification, whitelist ou intégrité ne dépend de
cette désactivation. C'est une politique de limitation des services annexes,
distincte des conditions nécessaires à l'accès sécurisé au jeu.

La [documentation Paper](https://docs.papermc.io/paper/reference/server-properties/)
sépare le service d'information GameSpy4 Query du service de console RCON.
Query ne donne aucun droit de jeu ou d'administration, mais divulgue des
informations serveur/joueurs. La whitelist ne filtre pas ce service UDP.

MineStrator explique dans son [MineNews #5 de 2026](https://minestrator.com/blog/article/minenews-5-mineboard-nouveautes-serveur-2026)
qu'un défaut du port Query empêchait l'affichage de la liste des joueurs dans
MineBoard. Cette dépendance documentée justifie de **conserver Query activé sur
22880**. Elle ne prouve pas que tous les indicateurs CPU/RAM ou la console en
dépendent. Aucun essai du panel réel n'a été effectué : la preuve fournisseur
est publique, les essais de protocole sont exclusivement locaux.

## Profils explicites et protections

| Profil | Places | Query | Ports imposés |
|---|---:|---|---|
| `private` | 5 à 20 | Désactivé | Politique générique conservée |
| `historical-rollback` | 10 exactement | Activé | Jeu TCP et Query UDP 22880 |
| `v21-minestrator` | 20 exactement | Activé | Jeu TCP et Query UDP 22880 |

`--profile` sélectionne explicitement la politique. La CLI peut aussi lire
`validationProfile` dans le manifeste de déploiement ; le nouveau manifeste
déclare `v21-minestrator`. Sans déclaration, le défaut reste `private`. Un profil
inconnu ou des ports/valeurs Query différents sont refusés. Il n'y a aucune
inférence depuis Query. L'API Python `check(root)` conserve son défaut privé.

Authentification, whitelist stricte/imposée, RCON et command blocks désactivés,
mot de passe RCON absent, difficulté/PvP, EULA déjà acceptée, SHA des trois JAR,
classe FKAmis et exactement deux plugins de production restent contrôlés.
Management et JMX actifs sont aussi refusés. Verrous et protections de restauration
sont conservés ; `configure`, `backup` et `start` propagent le même profil.

Les lanceurs V2.1 peuvent utiliser le profil explicitement déclaré dans le nouveau
manifeste, sans ajouter de fichier aux 148 cibles. Pour le rollback, les anciens
outils embarqués ne sont pas remplacés : la recette utilise les outils externes
actuels du projet et le profil historique explicite.

## Recette historique

Nouvelle copie privée : `C:\Users\youne\FKBackups\RB-QUERY-20261120-02\preproduction`.
305 fichiers comparés au manifeste avant test. **Seul `FKAmis.sha256` est corrigé
manuellement dans la copie**, conformément au JAR historique intact et au registre.
SHA du JAR : `46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442`.
Aucune donnée V2.1 n'entre dans cette copie.

Le premier essai `RB-QUERY-20261120-01` a été arrêté proprement : Windows affichait
le socket local sous la forme IPv6 `::ffff:127.0.0.1`, faussement refusée par le
comparateur. La normalisation `ipaddress` corrige cette représentation ; adresses
publiques/génériques et IP MineStrator sous forme IPv4 ou IPv6 encapsulée restent
refusées. La première copie reste conservée comme essai non validé.

| Contrôle du second essai | Résultat |
|---|---|
| Maintenance avant/après | Réussie, 10 places et Query actif conservés |
| Runtime | Paper 26.3-244, Java 25.0.5, FallenKingdom 2.24.9 et ancien FKAmis chargés |
| Démarrage et arrêt | Réussis, code Java 0, aucune WARN/ERROR/SEVERE |
| Commandes | Versions, plugins, statut, validation config, ravitaillements, arbitres, liste puis stop |
| Réseau | TCP et UDP locaux 22880 ; quatre observations réseau |
| Query réel | Challenge/statistiques : capacité 10, zéro joueur |
| Profils | Quatre fichiers de profils et six fichiers protégés identiques par SHA-256 |
| Monde | 76 régions, 21 865 chunks ; aucune région ni aucun chunk ajouté/supprimé |
| Inventaires/butins | 1 000 emplacements de chunks/fichiers avec données non vides comparés |
| Partie | Jour 0, non lancée, équipes/spawns/objectifs conservés, rayons 80, capacité historique 2 par équipe |
| Accès | Whitelist, OP/bans conservés sémantiquement, rôles et configuration de ravitaillement protégés |
| Originaux | Archive, manifeste, 305 contenus et métadonnées locales relevées inchangés |

Le schéma 1 a été lu par le parseur sûr puis chargé par le JAR réel. Les inventaires
non vides et tables de butin sont comparés par contenu/multiplicité dans chaque
chunk/fichier ; les profils sont aussi comparés intégralement. Ce contrôle n'est
pas une comparaison de chaque bloc après ticking. Le point sauvegardé est au
jour 0 : aucun scénario de reprise d'une partie active ni client authentifié
n'est inventé pour le qualifier.

## Écritures normales et limites

**37 fichiers modifiés, 4 ajoutés, 0 supprimé** dans la copie ; liste exhaustive
privée dans `runtime-diff-private.json`.

- Ajouts : `.control.lock`, `world/session.lock`, `.paper/console_history`, `logs/latest.log`.
- `server.properties` : seul `server-ip` devient `127.0.0.1` par l'option CLI
  d'isolation ; dix places, Query actif et ports 22880 restent inchangés.
- Les YAML Paper sont réenregistrés sans différence sémantique détectée.
- Le JAR historique ajoute les champs manquants `players-per-team: 2`, `vnext`
  et `vnext1` à l'état, sans changer le schéma principal, le jour ou les équipes.
- `RespawnAtHome` passe de vrai à faux dans l'état et la sauvegarde FallenKingdom :
  FKAmis réapplique sa politique existante `Rule.RESPAWN_AT_HOME=false`, les
  réapparitions étant gérées par le complément. Cette écriture est identifiée,
  sans prétendre que le démarrage conserve chaque octet.
- `level.dat`/`level.dat_old`, données de temps/météo/règles/bordures, régions et
  métadonnées spark sont réenregistrés ; les comparaisons ci-dessus restent réussies.

Le diff YAML ne journalise que des chemins, jamais les valeurs. Journaux bruts,
inventaires et états restent privés hors Git. Les permissions Linux, UID/GID et
attributs non restaurés sous Windows restent à réappliquer/vérifier sur l'hôte.
Paper a effectué ses connexions HTTPS automatiques : l'essai n'est pas sans réseau
sortant. Aucun outil API/SFTP ni identifiant MineStrator n'est utilisé. TCP/UDP sont
contrôlés en loopback ; aucun pare-feu système n'a été ajouté. La limite acceptée
de la sauvegarde sans verrou partagé fournisseur reste inchangée.

## Candidat V2.1 finalisé

Sortie privée indépendante : `C:\Users\youne\FKBackups\V21-QUERY-20261120-01`.
La préparation précédente `V21-FOUR-20261120-01` est conservée.

Règles inchangées : quatre équipes de 1 à 4, maximum 16 participants, arbitre
séparé, 20 places, captures 60 secondes/2,5 blocs avec seuil solo ou deux selon
l'effectif officiel, quatre cavernes et rayons 40. Les **121 fichiers de monde
restent identiques par SHA-256**. JAR quatre membres inchangé :
`38180caa28442bad838ef395779d9075a33a2c624bc71e2286488ac0e32fb31a`.

La copie de recette démarre et s'arrête proprement, sans erreur ni lancement de
partie, au jour 0. TCP et UDP vérifiés locaux ; Query annonce **20 places, zéro
joueur**. La CLI du nouvel outil portable passe avec le profil déclaré. Les
**152 empreintes du manifeste complet** sont vérifiées : transferts hors
auto-empreinte et fichiers conservés.

Toujours **148 chemins transférables**, dont seulement trois différents de la
préparation précédente : `server.properties`, `maintenance/host_ops.py` et
`DEPLOYMENT_MANIFEST.json`. Query revient à vrai ; la seule propriété différente
de la source réelle est maintenant `max-players=10` → `20`. IP de production,
ports et autres paramètres restent conservés dans le candidat jamais démarré
directement. Le démarrage est réservé à sa copie de recette.

Dans la sortie privée : `payload/DEPLOYMENT_MANIFEST.json`,
`transfer-plan-private.json`, `v21-fourplayers-transfer-private.zip` et son sidecar
SHA-256. Utiliser ces nouvelles empreintes, pas l'ancienne archive. L'archive de
transfert n'est pas une sauvegarde complète d'instance.

## Tests et disponibilité

**95 tests Python réussis** : profils, déclarations, inversions refusées, ports,
auth/whitelist/RCON/command blocks, JMX/management, SHA, IPv4/IPv6 et inventaires.
Code Java de jeu inchangé : les preuves du commit `04a730f` restent 53 tests Java
et 571 assertions Paper pour les équipes.

Le blocage applicatif du rollback est levé **sur Windows localement**, avec ses
écritures normales identifiées. Les validations techniques V2.1 passent. Avant
bascule réelle restent : inspection humaine, whitelist (deux comptes, non élargie),
mesures à 16 participants plus arbitre et précontrôle distant frais (identité,
arrêt, SHA source, espace disque, redémarrages). Le panel réel n'a pas été validé
par le seul protocole Query local. **Aucune bascule autorisée ou exécutée ; attendre
un accord séparé.**
