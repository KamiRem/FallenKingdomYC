# Installation sur un hébergeur Minecraft

Préparation du 7 novembre 2026. Aucun hébergement commandé ni fichier distant modifié.
Le paquet initial reste Paper **26.2 build 135**, hors maintenance : destiné à la
recette isolée. Lire l’audit avant de décider du lancement public ou d’une migration.
Ne jamais démarrer un monde converti en 26.3 avec un JAR 26.2.

## 1. Commander soi-même après choix

Voir [le comparatif](HOSTING_COMPARISON.md). Choix proposé : MyBox Perf 8, France,
cycle **un mois**, 23,99 € TTC. Alternative : MyBox 8, 13,99 € TTC, sous le budget
prévu. Vérifier le récapitulatif final, le renouvellement et les options : aucun
engagement long ni code promotionnel n’est nécessaire au prix retenu.
Conserver les identifiants du panel/SFTP dans un gestionnaire de mots de passe.
Activer la double authentification si proposée. Ne les mettre ni dans Git ni dans
le paquet. Un essai gratuit n’a pas été créé par l’agent.

## 2. Préparer un service vide et arrêté

Créer une instance **de préproduction**, désactiver son démarrage automatique,
attendre l’état arrêté. Si le panel génère un monde par défaut, l’archiver puis
utiliser un nouvel espace vide ; ne pas fusionner deux mondes. Noter le port de jeu
et l’adresse attribués. Ne pas activer de proxy, Geyser, ViaVersion ou plugins ajoutés
automatiquement. Les huit clients utiliseront Minecraft Java **26.2**, comptes officiels.

## 3. Java et JAR

Dans MineBoard : Paramètres → Hébergement, sélectionner **Java 25**, puis le fichier
de démarrage **paper.jar**. Le [guide officiel custom/JVM](https://minestrator.com/blog/article/installer-version-custom-minecraft-serveur-minestrator)
documente ces deux sélections. Ne pas employer l’installateur « dernière version »
sur les fichiers transférés, ni une mise à jour automatique de Paper ou des plugins.
Sur un autre panel, rechercher « Startup / Server JAR / Java image ».

## 4. Vérifier et transférer le paquet privé

Le chemin exact et le SHA-256 du ZIP figurent dans `tests/results/preproduction-package.json`
du dépôt. Conserver ce rapport et le fichier `.zip.sha256` hors de l’hébergement.
Sous PowerShell : `Get-FileHash '<archive.zip>' -Algorithm SHA256` doit correspondre.
Extraire dans un dossier **neuf**, vérifier avant toute personnalisation :

```text
python maintenance/host_ops.py verify-baseline
python maintenance/host_ops.py check
```

SFTP uniquement : relever serveur, port SFTP et empreinte de clé dans le panel,
vérifier cette empreinte, transférer tous les fichiers extraits à la racine du service.
Inclure les fichiers cachés utiles ; ne pas envoyer le dépôt, `.tools`, `.cache`,
les historiques ou les sauvegardes privées de référence. Ne pas imbriquer un dossier
supplémentaire : `paper.jar`, `server.properties` et `world/` doivent être au même niveau.
Le monde moderne contient **ses trois dimensions dans `world/dimensions/minecraft/`** ;
ne pas les déplacer vers des dossiers `world_nether`/`world_the_end`.

Le manifeste SHA-256 couvre tous les fichiers initiaux, le manifeste d’archive couvre
aussi ce manifeste. Si Python est absent du panel, effectuer ces contrôles sur le PC,
puis retélécharger les fichiers distants dans un autre dossier pour comparer leurs
SHA-256 avant le premier démarrage. Ne pas remplacer un fichier joué pour « réparer »
un manifeste initial devenu différent : il décrit uniquement la livraison initiale.

## 5. Port et mémoire après choix de l’hôte

La livraison conserve l’écoute locale de la référence : `127.0.0.1:25579`.
**Après choix de l’hébergeur**, sur la copie transférée et arrêtée, utiliser :

```text
python maintenance/host_ops.py configure --port PORT_ATTRIBUE
```

Remplacer `PORT_ATTRIBUE` par le nombre du panel. Sans Python, changer seulement
`server-ip=` (vide), `server-port=<port attribué>`. Si l’hôte impose une IP d’écoute
interne, suivre sa valeur documentée. Garder `online-mode=true`, `white-list=true`,
`enforce-whitelist=true`, `max-players=8`, RCON/query/command blocks désactivés.
Ne pas recopier l’IP locale du PC sur le serveur hébergé.

Pour un service de **8 Go**, cible initiale : `-Xms1G -Xmx6G`, avec environ 2 Go de
marge pour mémoire native, threads et conteneur. La limite du panel doit rester 8 Go.
Vérifier les paramètres JVM réellement appliqués et l’usage total ; certains panels
imposent leur propre heap. Si la heap n’est pas réglable, demander au support comment
réserver cette marge **avant de valider la commande**. Ne pas modifier les mécaniques
de jeu pour masquer un manque de CPU. Vue 8, simulation 6 conservées.

## 6. Démarrage

Le panel peut exécuter directement l’équivalent de :

```text
java -Xms1G -Xmx6G -jar paper.jar --nogui
```

L’écoute et le port viennent alors de `server.properties`. Aucun script Python n’est
requis pour jouer. Si le panel accepte une commande personnalisée **et Python 3.11+**,
`start.sh` utilise `SERVER_PORT` et `HEAP_GB=6`, conserve le verrou commun et sauvegarde
après arrêt propre. Ne pas lancer simultanément script et bouton Java du panel.
Le script Windows local : `./start.ps1 -Port 25580 -Memory 4` écoute seulement sur loopback.
La JVM Linux du fournisseur remplace le JDK Windows local, qui n’est pas livré.
Paper téléchargera ses bibliothèques/cache adaptés à la plateforme au premier lancement :
un accès HTTPS sortant et de l’espace libre sont nécessaires.

L’EULA a été copiée après l’acceptation explicite du propriétaire pour les tests
locaux. Lire personnellement [l’EULA](https://www.minecraft.net/eula) et les conditions
de l’hébergeur pour cet usage ; aucun script n’accepte de nouvelles conditions à votre place.

## 7. Authentification et permissions

La whitelist et la liste OP livrées sont **vides**. Depuis la console du panel :
`whitelist on`, puis `whitelist add <pseudo officiel>` pour chacun des huit comptes.
Vérifier `whitelist list`. Administrer depuis la console du panel : aucun participant
ne doit rester OP. `fka assign <pseudo connecté> <Rouge|Bleue|Verte|Jaune>` attribue les
équipes, deux membres chacune. Ne pas utiliser `fk game start` ni `fka start override`.
Un compte hors whitelist doit être refusé. Les accès panel/SFTP ne sont pas ceux des joueurs.

## 8. Contrôles console et journaux

Vérifier Java 25, Paper 26.2-135, les messages d’activation de FallenKingdom **2.24.9**
et FKAmis **1.0.0**, puis `Done`. `plugins` doit montrer les deux plugins actifs.
Spark éventuellement intégré à Paper est une fonction de Paper, aucun JAR diagnostic
supplémentaire n’est fourni. Contrôler `logs/latest.log` : aucun ERROR/SEVERE,
exception répétée, échec d’authentification réseau ou plugin désactivé. Lire les WARN,
notamment l’avertissement attendu de version Paper ancienne.
`fka status` : jour 0, installation/pause ; `fka supply status` : configuration active,
aucun événement consommé. Contrôler les quatre bases, drapeaux, sept monuments,
coffres et huit sites avec la feuille de recette. Ne pas reconstruire/prégénérer.

## 9. Sauvegardes puis invitation

Activer/vérifier les sauvegardes automatiques du fournisseur ; elles complètent les
[sauvegardes à froid](BACKUP_RESTORE.md). Faire un arrêt propre et un point complet
avant la session, télécharger une copie externe, prouver une restauration dans un
espace séparé. Inviter les sept amis seulement après ces contrôles et suivre
[la recette à huit](MULTIPLAYER_ACCEPTANCE.md). Le démarrage technique du serveur
ne lance pas la partie : `fka start` sera une action humaine de recette ou de lancement,
sur l’instance appropriée.
