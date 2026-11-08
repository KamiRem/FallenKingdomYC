# Sauvegarder et restaurer sans mélanger les états

## Réinitialisation VNext

Voir la [procédure VNext](FKAMIS_VNEXT.md) avant `fka reset prepare/confirm`.
La confirmation nécessite zéro joueur, arrête proprement Paper et crée seulement
une demande à froid. `host_ops.py reset-logical --token ...` sauvegarde puis change
la progression seule : constructions, inventaires et butins pris restent conservés.
`seal-initial --approve-initial` puis `restore-initial` concernent une référence
initiale VNext explicitement approuvée et une destination vide. Aucun mélange
d'inventaires en cours et de carte initiale n'est effectué. Rôles et règles divergents
refusent la restauration. Les historiques restent dans l'ancienne instance archivée.
Les sauvegardes `.fk-backups`, `.fk-updates` et `.fk-resets` ne s'emboîtent pas.
Pour annuler une demande en attente, utiliser `host_ops.py reset-cancel` à froid.

Deux archives distinctes : la **référence initiale scellée** pour repartir proprement,
et les **sauvegardes de partie** pour reprendre une progression. Leurs versions et
SHA-256 doivent être conservés avec leur date UTC. Ne jamais injecter l’inventaire,
`state.yml` ou les régions d’une archive dans un autre instant de jeu.

Profil courant : **Paper 26.3-244 / Java 25**, paquet initial
`dist/fallenkingdom-preproduction-26.3.zip`, rapport
`tests/results/preproduction-package-26.3.json`. Restaurer une sauvegarde 26.3
avec ses JAR 26.3 ; l’ancien ZIP 26.2 reste conservé pour une restauration 26.2
séparée, jamais pour remplacer seulement le JAR d’un monde converti.

## Sauvegarde à froid

1. Annoncer la maintenance, lancer `fka pause`, puis `fka save` dans la console.
2. Saisir `stop`, attendre la fin de Java, l’état arrêté du panel et la fin des écritures.
   Désactiver tout redémarrage planifié pendant l’opération. `save-all` seul n’est
   pas une preuve de cohérence entre monde et plugins.
3. Si Python 3.11+ est disponible : `python maintenance/host_ops.py backup`.
   Le contrôle commun et les verrous natifs `session.lock` refusent un serveur actif.
   Le ZIP est relu intégralement, possède un manifeste par fichier et un `.zip.sha256`.
   Les anciennes archives de `.fk-backups/` sont exclues pour éviter leur emboîtement.
4. Télécharger ZIP et empreinte sur un stockage séparé de l’hôte, privé. Ils contiennent
   désormais les identités, inventaires, whitelist et objectifs secrets de la partie.
   Ne jamais les committer ni les partager aux équipes.
5. Sans Python sur l’hôte : serveur arrêté, créer un snapshot complet dans le panel,
   télécharger **toute l’instance** via SFTP dans un dossier neuf, puis utiliser les
   outils Python localement pour sceller cette copie. Les contrôles de verrou locaux
   ne prouvent pas que le service distant est arrêté : vérifier le panel explicitement.

Rotation proposée : point avant chaque session, après chaque session et avant chaque
mise à jour ; conserver au moins les sept derniers points journaliers, quatre hebdomadaires,
la référence initiale et tous les points précédant une migration. Contrôler l’espace
libre ; déplacer les anciens points vers le stockage externe sans suppression automatique
des historiques. Répéter un exercice de restauration avant lancement, puis mensuellement.

## Restauration vérifiée

1. Arrêter le service de destination et archiver son état actuel. Retenir un point
   précis et son **JAR Paper d’origine**. Aucun downgrade d’un monde converti.
2. Comparer le ZIP au SHA-256 externe conservé hors de l’hôte. Le manifeste interne
   détecte les fichiers manquants ou altérés ; l’empreinte externe doit provenir du
   relevé de confiance, pas d’un fichier recalculé sur une archive douteuse.
3. Créer un nouvel espace vide et séparé, jamais un écrasement. Depuis l’ancienne copie :

   ```text
   python maintenance/host_ops.py restore --archive /chemin/fk-point.zip --destination /chemin/nouvelle-instance
   ```

   Le script exige le fichier `.zip.sha256`, vérifie chaque entrée et refuse les
   destinations non vides et les chemins dangereux. Sans Python distant, restaurer
   localement puis transférer intégralement vers un service vide arrêté.
4. Avant tout démarrage : couper l’accès des joueurs/fermer le port du service de test
   dans le panel ou écouter sur loopback. Une sauvegarde créée après `fka pause` est
   en pause ; une archive provenant d’un jeu actif peut reprendre active. La restauration
   ne réécrit pas artificiellement cet état.
5. Vérifier les versions et empreintes des JAR, dimensions, équipes, jour, pause,
   inventaires, salles, éliminations, ravitaillements/temps restant. Démarrer isolé,
   contrôler les logs, tester une connexion autorisée et l’absence de duplication
   d’un butin déjà pris. Arrêter proprement après la vérification.
6. Basculer l’adresse/port vers la nouvelle instance seulement après validation humaine.
   Ne jamais faire tourner deux copies de la même partie accessibles aux joueurs.
   Garder l’ancienne arrêtée, identifiée par date et version. Reprendre avec `fka resume`
   uniquement lorsque l’état attendu est confirmé.

Le fournisseur annonce ses propres snapshots et restaurations ; leur fréquence ne
garantit pas à elle seule une capture atomique des fichiers Minecraft et FKAmis.
La sauvegarde à froid et le contrôle d’une restauration complète restent nécessaires.
