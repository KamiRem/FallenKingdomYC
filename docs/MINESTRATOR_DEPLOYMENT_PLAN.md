# Plan MineStrator VNext.1 / V2.1 — 15 novembre 2026

Statut : inventaire authentifié et candidat local préparés. Aucun fichier distant
modifié, aucune commande console ou d'alimentation envoyée, aucun snapshot créé.
Le déploiement attend une autorisation explicite. Ce plan remplace les hypothèses
d'accès de `MINESTRATOR_PREPARATION.md`, conservées comme historique.

## Résultats de l'audit réel

L'ancien script n'enregistrait pas sa sortie. Ses lectures ont été répétées : API
200 sur informations serveur, live, sauvegardes et snapshots ; l'ID des informations
retournées correspond à la configuration locale. La synthèse est conservée dans le
stockage local privé. Le script ajoute maintenant un horodatage et un indicateur
`authenticatedServerReadOnly` vérifié sur le code API et l'identité du serveur.
Une réussite HTTP seule ne suffit pas. La réponse 401 sans clé de la préparation
précédente n'est pas une preuve d'authentification.

SFTP : authentification par mot de passe DPAPI réussie après comparaison de la clé
`ssh-ed25519` à l'empreinte SHA-256 fournie par l'utilisateur. Relevé complet de
305 fichiers et 321 dossiers ; seuls listes, attributs et lectures sont employés.
Les configurations et journaux téléchargés sont chiffrés localement avec DPAPI ;
aucun identifiant ou secret brut n'est imprimé. Le manifeste détaillé, qui contient
des chemins de profils, reste privé et hors Git.

| Élément | Constat |
|---|---|
| État API avant/après inventaire | `offline`, aucun arrêt réalisé par l'agent |
| Port | 22880 |
| Paper | `paper.jar` et `server.jar` correspondent à Paper 26.3-244 |
| FallenKingdom | JAR officiel 2.24.9, empreinte conforme |
| FKAmis | JAR **déjà VNext.1**, identifié par son SHA-256, malgré le numéro commun 1.0.0 |
| Registre du JAR FKAmis | Empreinte cohérente avec le JAR présent |
| État de jeu | Schéma 1 historique, jour 0, non commencé, extension VNext absente |
| Territoires enregistrés | Quatre rayons 80 |
| Cavernes V2.1 | Pas de fichier de métadonnées V2.1 ; la présence physique des cavernes sur l'ancien monde n'est pas prétendue inspectée |
| Réglages | `level-name=world`, `allow-flight=true`, online-mode et whitelist activés, vue 8, simulation 6 |
| Java | Utilisateur : « Java 25 - Performance », image `java/25_perf`, identifiant API 61. Runtime distant non exécuté pour mesure |
| Sauvegardes fournisseur | 44 sauvegardes quotidiennes de ce serveur ; 5 snapshots du **compte**, pas nécessairement de ce serveur |
| Sauvegarde de référence pour la bascule | Non créée ; archives existantes non restaurées par cet audit |

Empreintes réellement lues sur le SFTP :

```text
paper.jar et server.jar
9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf
plugins/FallenKingdom-2.24.9.jar
9127a92a5ad621f74b29ab8e53b6785d4ee30dd15f720c82c64f2c6a5973ba3b
plugins/FKAmis-1.0.0.jar
46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442
```

## Décision technique

Ne pas exécuter aveuglément `apply_vnext1_update.py` sur l'état actuel : son entrée
attend une extension VNext 1 ou 2, absente ici. Le JAR est déjà correct ; c'est une
**bascule vers une nouvelle partie V2.1**, avec état initial complet, qui est préparée.
Le ZIP de mise à jour n'est pas une carte. L'artefact de construction a servi à
construire le monde séparément depuis la référence initiale connue et contrôlée.

Le candidat `.cache/ms15q/runtime/preproduction` provient de la carte construite et
contrôlée sous `.cache/mp15a`. Il reprend les réglages FKAmis, arbitres, whitelist,
ops et propriétés réels, avec fusion des seuls défauts config manquants. L'état
initial, les inventaires et les compteurs de lots proviennent de la nouvelle
référence ; aucun état de l'ancien jeu n'a été injecté. Les bans et réglages
Paper/panel existants resteront en place sur l'hôte.

Le démarrage local s'est fait sur localhost avec Java 25, sans client authentifié.
Après arrêt, les propriétés déclarées distantes, dont le port 22880, ont été remises
dans le candidat. Les contrôles à froid passent : 4 bases, 7 monuments, 6 coffres
de butin, 8 supports, 4 cavernes et 37 128 positions vérifiées dans les cavernes.
L'inspection visuelle et la recette humaine restent à faire. Cette archive n'est
pas déclarée approuvée visuellement par l'agent.

## Transfert exact préparé

Manifeste privé : `.cache/ms15q/transfer-plan-private.json`. Payload privé :
`.cache/ms15q/payload`. Chaque fichier sortant possède son SHA-256 cible. Les
empreintes existantes relevées et les tailles sont conservées lorsque disponibles.
La sauvegarde à froid devra compléter les empreintes de **tous** les anciens fichiers.

| Groupe | Fichiers sortants |
|---|---:|
| `world/`, dimensions intégrées comprises | 121 |
| `plugins/FKAmis/` | 5 |
| `plugins/FallenKingdom/` | 8 |
| `maintenance/` | 7 |
| `FKAmis.sha256`, `RUNTIME_LOCK.json` | 2 |
| `map-v2-construction.json`, `map-v21-caverns.json` | 2 |
| Nouveau `DEPLOYMENT_MANIFEST.json` | 1 |
| Total | **146** |

Les JAR Paper/FallenKingdom/FKAmis conformes ne sont pas retransférés. Les propriétés,
whitelist et ops distants restent identiques et figurent dans les vérifications du
manifeste. Les versions, l'image `java/25_perf`, la mémoire et les allocations du
panel ne changent pas. Les deux références de maintenance par défaut et V2.1
contrôlent maintenant aussi les minerais/cavernes, au lieu d'un modèle V2 obsolète.

Le remplacement concerne des **arbres entiers**, pas une superposition de régions :
`world`, `plugins/FKAmis` et `plugins/FallenKingdom`. Il couvre 142 anciens fichiers
actuellement relevés dans ces arbres. Des dossiers séparés `world_nether` ou
`world_the_end` ne seront traités que s'ils apparaissent au contrôle final ; le
relevé actuel utilise les dimensions intégrées à `world`.

Après sauvegarde externe vérifiée et autorisation, garder les anciens arbres dans
une quarantaine privée distincte avant de déposer les nouveaux. Conserver aussi
l'ancien `BACKUP_MANIFEST.json` comme document historique, pas comme preuve de la
nouvelle instance. Archiver chaque ancienne version des autres fichiers remplacés.
Les archives `.ai-backups`, les références, bibliothèques, caches, configuration
Paper/Bukkit/Spigot, EULA, bans et scripts de lancement ne sont pas supprimés.
Aucun nettoyage automatique n'est prévu.

## Sauvegarde obligatoire avant bascule

1. Après autorisation, revérifier `offline`, le port, les empreintes des JAR et
   l'absence de changement depuis ce relevé. Ne pas démarrer l'ancien serveur.
2. Garantir qu'aucun planificateur/opérateur ne peut relancer ou écrire pendant la
   maintenance. L'accès SFTP ne donne pas de shell ni de Python distant par lui-même.
3. Si les outils Python peuvent être exécutés sur l'hôte, utiliser la maintenance
   à froid avec verrou partagé et verrous natifs. Sinon obtenir du fournisseur un
   mécanisme de maintenance exclusif équivalent. **Deux observations API offline
   ne constituent pas un verrou.** Sans garantie fiable, la bascule reste bloquée.
4. Capturer toute l'instance et les paramètres du panel : tous mondes/dimensions,
   profils, plugins, états natifs et FKAmis, configurations, rôles, lots, historiques,
   permissions et accès. Conserver les sauvegardes précédentes et leur provenance.
5. Stocker une copie complète **hors de l'instance**, privée, avec manifeste par
   fichier et SHA-256 externe conservé localement. Une sauvegarde fournisseur seule
   ne remplace pas la copie externe ni la vérification.
6. Relire les fichiers source arrêtés et comparer chaque hash, vérifier le ZIP et
   restaurer dans un espace neuf. Les fichiers peuvent contenir des secrets : ni Git
   ni logs publics. Ne pas lancer une copie contenant des accès réels sur une
   interface publique. Contrôler l'espace nécessaire au backup et à la quarantaine.

La sauvegarde réelle n'a PAS été créée par cet audit. L'exercice de rollback local
précédent portait sur une fixture ; il ne prouve pas la restauration du serveur réel.

## Exécution E, seulement après accord

Une fois les prérequis de sauvegarde et l'approbation satisfaits :

1. Geler le point de référence et les deux manifestes (ancien complet et cible).
   Tout écart matériel exige un nouveau plan et une nouvelle approbation avant écriture.
2. Préserver les anciens arbres/fichiers, déposer les 146 fichiers du payload dans
   les destinations exactes. Ne pas transférer les outils de construction/sondes,
   les secrets de connexion locaux, les logs locaux ou les fichiers de test.
3. Relire les fichiers distants et vérifier chaque SHA cible ainsi que les fichiers
   déclarés conservés. Vérifier l'absence de profils et d'états anciens dans le
   nouveau monde et les dossiers de plugins actifs.
4. Démarrer après accord, en accès restreint. Vérifier logs sans erreur, Java 25,
   Paper/FK/FKAmis, jour 0, extension 2, 4 rayons 40, 4 spawns et intégrité carte.
5. Vérifier admins/whitelist/protections, enregistrer les deux cadres officiels de
   portail dans la nouvelle carte, puis inspecter les cavernes en jeu. Aucune
   génération de portail Vanilla ou modification de Java pour contourner un échec.
6. Après inspection humaine, sceller une référence initiale V2.1 avec ses politiques
   effectives. Ouvrir la partie uniquement après recette ; ne pas lancer `fka start`
   automatiquement pendant la validation technique.

## Rollback complet

En cas d'échec, maintenir l'accès fermé et arrêter la nouvelle instance conformément
à l'autorisation reçue. Sauvegarder son état pour diagnostic. Restaurer **toute** la
sauvegarde réelle vérifiée, pas seulement l'ancien JAR ou un fichier joueur : les
versions, mondes, profils, états natifs et FKAmis, portails, rôles, lots, historiques,
manifestes et paramètres du panel appartiennent au même point de référence.

Comparer chaque hash au manifeste ancien, vérifier port 22880 et image
`java/25_perf`, puis démarrer isolé et contrôler les logs/équipes/inventaires. Le
point ancien relevé aujourd'hui contient un JAR VNext.1 avec un état historique et
rayons 80 : restaurer exactement le point choisi, sans inventer un downgrade VNext
fd12 à sa place. Si une restauration vers une autre révision est souhaitée, choisir
son archive complète et vérifier sa compatibilité séparément. Ne pas rendre deux
copies de la même partie accessibles simultanément.

## Sources et rapports

- API : [documentation officielle MineStrator](https://api.minestrator.com/).
- Vérification de clé SSH : [API Paramiko officielle](https://docs.paramiko.org/en/stable/api/client.html).
- `tests/results/minestrator-inventory.json` : audit expurgé.
- `tests/results/minestrator-transfer-plan.json` : préparation et contrôles du candidat.
- `.cache/ms15q/transfer-plan-private.json` : liste exacte privée des fichiers et hashes.
- `configs/artifacts.lock.json` : versions Minecraft inchangées, nouvelles dépendances
  du client d'inventaire **local** verrouillées ; installation isolée `.tools/ms-audit`.
- Six tests `tests/test_minestrator_inventory.py` passent sans réseau : empreinte,
  refus avant mot de passe, lecture/hash, liens, chemins dangereux et fichier instable.

L'audit n'autorise aucun déploiement. Aucune action distante d'écriture n'a été
effectuée et aucune approbation E n'a encore été reçue.
