# Transfert du paquet 26.3 vers MineStrator

## Mise à jour du service existant

Le monde est déjà installé : **ne pas renvoyer le paquet monde**. Suivre
[ADMIN_UPDATE.md](ADMIN_UPDATE.md) pour `fallenkingdom-admin-update.zip` :
pause/save/stop, backup complet à froid, remplacement du seul FKAmis et de son
empreinte, clés de configuration ciblées et maintenance adaptée. Aucun écrasement
de `state.yml`, des territoires ou des données des joueurs. Conserver les rôles
`admins.yml` existants ; la console configure le neuvième compte arbitre par UUID.
`max-players=10`, `gamemode=survival`, `force-gamemode=false`, whitelist obligatoire
pour les huit participants et l'arbitre. La mémoire 6154M, Java 25 Performance et
le port 22880 restent ceux du panel. Les étapes suivantes décrivent l'installation
initiale, pas une opération à rejouer sur le monde en place.

Le propriétaire a choisi **MyBox Perf 8**, service de 8 Go, **Java 25 Performance**,
heap annoncée d’environ **6154M**, port principal **22880**. Le serveur distant est
annoncé vide et arrêté. Ces informations viennent du propriétaire ; l’agent n’a
accédé ni au panel ni au SFTP et n’a modifié aucun fichier distant.

## 1. Choisir le bon paquet et vérifier son empreinte

Utiliser exclusivement `dist/fallenkingdom-preproduction-26.3.zip` et son
`.zip.sha256`. Le SHA-256 de confiance et les résultats de restauration sont dans
`tests/results/preproduction-package-26.3.json`. Garder une copie du ZIP et de ce
rapport hors de l’hébergement. Ne pas transférer un dossier probe, la branche de
fixtures, une ancienne archive 26.2 ou le dossier Git complet.

Sous PowerShell :

```powershell
Get-FileHash .\dist\fallenkingdom-preproduction-26.3.zip -Algorithm SHA256
```

Comparer exactement au rapport, puis extraire dans un dossier local **neuf**.
Si Python 3.11+ est disponible sur le PC, depuis le dossier extrait :

```text
python maintenance/host_ops.py verify-baseline
python maintenance/host_ops.py check
```

Le premier contrôle décrit l’état initial : il devient naturellement différent
après personnalisation ou jeu. Ne pas remplacer des fichiers de partie jouée pour
le faire repasser. Le manifeste interne d’archive couvre aussi ce manifeste initial.

## 2. Préparer le panel sans générer un autre monde

Laisser le service arrêté, désactiver les relances planifiées pendant le transfert.
Conserver **Java 25 Performance** et la mémoire actuelle d’environ **6154M** ; ne pas
la doubler avec des options JVM contradictoires et ne pas allouer toute la limite
8 Go à la heap. Le surplus sert à la mémoire native, threads et conteneur.
Vérifier la commande effective après démarrage. Ne pas installer « dernière version »
de Paper, de pack ou de plugins et désactiver leur mise à jour automatique.

Le paquet est déjà configuré :

```properties
server-ip=
server-port=22880
level-name=world
online-mode=true
white-list=true
enforce-whitelist=true
max-players=10
enable-rcon=false
enable-query=false
enable-command-block=false
```

Ne pas renseigner l’IP publique comme IP d’écoute interne. Ne pas remettre 25565 ou
25579 à la place du port attribué. Si MineStrator impose une propriété interne,
suivre sa valeur documentée sur cette seule copie. Aucun proxy/crossplay n’est requis.

## 3. Transférer tous les fichiers par SFTP

Depuis MineBoard, relever hôte SFTP, port SFTP, utilisateur et empreinte de clé.
Le **port SFTP est distinct du port de jeu 22880**. Vérifier la clé dans WinSCP ou
FileZilla, conserver le mot de passe dans un gestionnaire privé. Aucun secret ne
doit entrer dans Git, un document de recette ou le paquet.

Transférer le contenu du dossier extrait directement à la racine du service vide.
On doit obtenir cette structure, sans dossier supplémentaire englobant :

```text
paper.jar
server.properties
eula.txt
artifacts.lock.json
FKAmis.sha256
RUNTIME_LOCK.json
DEPLOYMENT_MANIFEST.json
world/
  dimensions/minecraft/overworld/
  dimensions/minecraft/the_nether/
  dimensions/minecraft/the_end/
plugins/
  FallenKingdom-2.24.9.jar
  FKAmis-1.0.0.jar
  FallenKingdom/
  FKAmis/
maintenance/
```

Inclure les autres fichiers du ZIP, notamment configurations Paper/Bukkit/Spigot,
références, notices et fichiers cachés utiles. **Ne pas déplacer les dimensions**
vers `world_nether`/`world_the_end`. Les bibliothèques/caches de plateforme ne sont
pas livrés : Paper les retéléchargera par HTTPS au premier démarrage.
L’EULA est copiée depuis l’acceptation explicite existante ; aucun script n’accepte
de nouvelles conditions à votre place.

Si le panel extrait lui-même le ZIP, vérifier l’arborescence et les empreintes
avant tout démarrage. Sans Python distant, vérifier localement puis retélécharger
les fichiers distants dans un autre dossier pour comparaison SHA-256. Ne pas
fusionner avec un monde généré par un installateur : conserver cet éventuel monde
à part et utiliser un espace vide, sans effacement d’une partie existante.

## 4. Sélectionner le JAR et démarrer techniquement

MineBoard → **Paramètres → Hébergement** : sélectionner exactement **paper.jar**
comme fichier de démarrage et conserver **Java 25 Performance**. Le
[guide officiel MineStrator](https://minestrator.com/blog/article/installer-version-custom-minecraft-serveur-minestrator)
documente ce choix de fichier et de Java. Le panel gère environ 6154M ; l’équivalent
d’une commande manuelle serait `java -Xms1G -Xmx6154M -jar paper.jar --nogui`.
Ne pas remplacer le lancement du panel par `start.sh` si Python ou les commandes
personnalisées ne sont pas disponibles. Les scripts fournis restent facultatifs.

Démarrer une fois depuis le panel. Cela démarre le **serveur**, pas la partie FK.
Dans la console et `logs/latest.log`, vérifier : Java 25, Paper **26.3-244**,
FallenKingdom **2.24.9**, FKAmis **1.0.0**, puis `Done`. Les deux plugins doivent
être actifs ; aucun probe/outil de chantier ne doit être chargé. Spark éventuellement
intégré à Paper ne correspond pas à un JAR de diagnostic ajouté par le projet.
Lire tous les WARN et refuser toute ERROR/SEVERE bloquante ou plugin désactivé.

Console : `version`, `plugins`, `fka status`, `fka supply status`.
Attendu : jour **0**, installation/pause, aucun roster ni objectif, ravitaillement
activé avec délai initial 1 800 secondes actives, mode test désactivé. Ne pas lancer
`fka start`, `fka start override`, `fk game start`, `pregen` ou un constructeur de carte
pour vérifier l’installation.

## 5. Préparer l’accès des huit vrais comptes

La whitelist et les OP livrés sont vides. Depuis la console : `whitelist on`,
puis `whitelist add <pseudo_officiel>` pour chaque compte. `whitelist list` doit
contenir les huit participants et le compte arbitre prévus. Ne pas désactiver online-mode et ne pas OP les
participants. Administrer depuis la console du panel.
Les clients doivent utiliser **Minecraft Java 26.3**. Adresse : celle indiquée par
le panel, port **22880**. Tester aussi le refus d’un compte hors whitelist.
Les mots de passe du panel/SFTP ne sont jamais ceux à distribuer aux joueurs.

## 6. Sauvegarder avant invitation et jouer uniquement la recette

Vérifier SmartBackup dans le panel, puis effectuer un point complet à froid :
`fka pause`, `fka save`, `stop`, attendre l’arrêt total, sauvegarder et télécharger
une copie externe. Prouver une restauration dans un espace distinct selon
[BACKUP_RESTORE.md](BACKUP_RESTORE.md). Un snapshot pendant l’exécution ne remplace
pas cette preuve de cohérence monde/plugins.

Inviter les sept amis et suivre [MULTIPLAYER_ACCEPTANCE.md](MULTIPLAYER_ACCEPTANCE.md).
Les quatre binômes se configurent par `fka assign <pseudo_connecté> <équipe>` ;
inspecter/confirmer les terrains, prévisualiser puis confirmer `/fka teams tpall`.
Le lancement de la **recette** sera une action humaine sur la copie dédiée.
Après validation, le lancement officiel repartira d’une restauration du ZIP 26.3
initial, jamais d’un nettoyage partiel du monde de recette.
