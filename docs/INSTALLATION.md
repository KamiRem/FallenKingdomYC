# Installation locale Windows

Si ce workspace contient déjà `runtime/local/world`, l'installation et la génération
ont déjà été exécutées. Utiliser `server.ps1 validate`, puis `server.ps1 start` ; ne
pas relancer `install` sur ce dossier. Pour une autre partie, utiliser un nouveau `-Name`.

## Préparer les outils

Utiliser Windows 10/11 x64, Python 3.11 ou plus récent et PowerShell. Prévoir plusieurs
Go libres pour Java, les bibliothèques Paper, les mondes et les copies de sauvegarde.
Java et Maven sont portables dans `.tools`, sans modification permanente du PATH ni
installation système. Les archives sont fixées dans `configs/artifacts.lock.json`.

```powershell
.\scripts\bootstrap.ps1
.\scripts\build.ps1
python -m unittest discover -s tests -v
.\scripts\server.ps1 install
```

Le bootstrap vérifie SHA-256 pour Paper, FallenKingdom et Java ; Maven est vérifié avec
le SHA-512 publié par Apache. Une empreinte différente bloque l'installation. Maven
utilise `.cache/m2` et une API Paper précise, sans dépendance SNAPSHOT.

Un nouveau serveur possède une whitelist vide, aucun OP et `eula=false`. Les scripts
ne modifient jamais implicitement cette valeur.

## EULA et premier démarrage

Lire [l'EULA Minecraft](https://www.minecraft.net/eula). Si vous l'acceptez :

```powershell
.\scripts\server.ps1 accept-eula -Accept
.\scripts\server.ps1 start
```

Le script écoute seulement `127.0.0.1:25565` avec 4 Go de heap maximum. Le port public
n'est pas ouvert. Le premier lancement télécharge les bibliothèques Mojang et Paper,
puis crée réellement les dimensions et les fichiers de configuration natifs. Une
connexion Internet reste requise pour authentifier les comptes officiels.

Attendre `FKAmis prêt` et `Done (...)`. Vérifier ensuite :

```powershell
# Depuis une autre console, après le démarrage :
.\scripts\server.ps1 check-logs
```

## Préparer la carte et les équipes

Dans la console du serveur, sans slash :

```text
whitelist add VotrePseudo
op VotrePseudo
fka pregen
```

Rejoindre avec Minecraft Java **26.2**, puis `/gamemode creative` avant la partie pour
l'inspection. La prégénération peut prendre plusieurs minutes. Attendre sa fin avant
de définir les bases. Les emplacements `±500, ±500` sont des candidats à inspecter,
pas des terrains garantis. Suivre [MAP_GUIDE.md](MAP_GUIDE.md).

Se placer sur un sol sûr, puis, pour chaque royaume :

```text
/fka territory Rouge 100
/fka spawn Rouge
/fka terrain Rouge confirm
```

La confirmation atteste une inspection humaine : terrain naturel sans fort prêt à
l'emploi, ressources et déplacements comparables. Répéter avec `Bleue`, `Verte`,
`Jaune`, en gardant les majuscules indiquées. Aucun bloc n'est généré par ces commandes.

Ajouter les huit joueurs à la whitelist depuis la console. Chaque joueur doit se
connecter une fois avant l'attribution pour enregistrer son UUID officiel :

```text
fka assign Pseudo1 Rouge
fka assign Pseudo2 Rouge
fka assign Pseudo3 Bleue
fka assign Pseudo4 Bleue
fka assign Pseudo5 Verte
fka assign Pseudo6 Verte
fka assign Pseudo7 Jaune
fka assign Pseudo8 Jaune
```

Les pseudos sont des exemples, à remplacer. Le serveur ne connaît pas vos huit noms.
Retirer OP aux participants, repasser les inventaires en état survival légitime,
puis lancer depuis la console `fka start` lorsque tous sont connectés. La console
permet d'arbitrer même avec huit emplacements occupés. Ne jamais utiliser `fk game start`.

## Arrêt et redémarrage

```text
fka pause
stop
```

Attendre la sortie complète. Le wrapper crée automatiquement une archive vérifiée.
Au prochain lancement, `fka status` affiche le jour conservé ; `fka resume` reprend.
Ne pas utiliser `/reload` ou un outil de rechargement de plugins.

## Importation d'une autre carte

Avant le **premier** lancement et avec une carte dont l'usage est autorisé :

```powershell
.\scripts\server.ps1 import-world -Source 'C:\Cartes\MondeNaturel'
```

La source doit contenir `level.dat`, être fermée dans Minecraft et avoir une version
compatible. L'import refuse de remplacer un monde existant. Pour une autre graine,
modifier `level-seed` avant toute génération dans une nouvelle instance `-Name essai2`.
Voir les particularités des dimensions 26.2 dans le guide de carte.
