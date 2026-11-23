# MineStrator 513365 — installation V2.2 du 23 novembre 2026

**V2.2 déployée et prête pour recette humaine.** Le serveur est en ligne,
jour 0, partie non lancée, whitelist inchangée à deux comptes. Dernier contrôle
de conservation : **17:47:16, heure de Paris**. Une seule demande de démarrage
technique a été envoyée. Aucun rollback distant n'a été nécessaire.
Contrôle de clôture à **17:55:46** : API toujours `online`, Query UDP et statut
TCP répondent à vingt places, zéro connecté ; aucune nouvelle commande console
ou d'alimentation envoyée pendant ce contrôle.

Le propriétaire a approuvé les 33 restaurations du puits et ses quatre valeurs
de hauteur, et a explicitement dispensé d'inspection humaine préalable. Aucune
visite graphique ou connexion de joueur n'est présentée comme réalisée.
Voir l'[autorisation dérogatoire](MINESTRATOR_V22_DEPLOY_DEROGATION_20261123.md),
le [reçu expurgé](../tests/results/minestrator-v22-installation-20261123.json)
et les [17 fichiers réellement installés](MINESTRATOR_V22_DEPLOY_FILES_20261123.tsv).

## 1. Précontrôle frais

API authentifiée : serveur 513365, adresse/port attendus, état arrêté. SFTP à clé
hôte épinglée avant authentification. Nouveau relevé privé
`MS-V22-PREFLIGHT-20261123-02` : **311 fichiers actifs, tous relus deux fois et
identiques au précédent audit**. Java 25 Performance, Paper 26.3-244, FK officiel
2.24.9, ancien FKAmis, vingt places, Query 22880, whitelist et watchdog conformes.
`restart-on-crash=false` est déjà en place et reste conservé.

Le propriétaire confirme actuellement 50 Go disponibles ; le plan nécessite
environ 2,86 Go supplémentaires. L'espace sous quota n'est pas mesuré indépendamment
par l'API ou SFTP statvfs, non disponible. Les mécanismes internes de planification,
la file d'alimentation et l'auto-restart hébergeur ne sont pas exposés par ces
accès. Leur limite est signalée et la poursuite explicitement demandée. Aucun
réglage du panel n'a été modifié.

Les archives historiques, leurs manifestes et les 305 fichiers de restauration
originaux sont recontrôlés conformes avant intervention. Les sources géologiques,
propositions antérieures et leurs archives restent intactes.

## 2. Nouvelle sauvegarde complète et restauration

Opération **`MS-COLD-V22-20261123-01`**, hors Git/instance :
`C:\Users\youne\FKBackups\MS-COLD-V22-20261123-01`.

**463 fichiers, 366 dossiers, 653 314 681 octets**, avec profils, inventaires,
mondes, états, rôles, accès, journaux, quarantaines, dossiers vides et verrous.
Les fichiers absents de la répétition partielle précédente sont bien inclus.

| Artefact privé | SHA-256 |
|---|---|
| `instance.zip` — 554 345 220 octets | `18b387d5c824c5a892c98dcf1c009ce22666c09228ab2df42bd8434692656684` |
| `manifest.json` | `758654db5341f361b0bcb7125eb94e1671275fab34b47f17fb71776f4a33e21d` |

Double lecture distante SHA-256, contrôles SFTP corrigés et réinventaires, archive
relue et restauration complète neuve : tous les octets concordent. **152 régions
et 43 711 chunks décodés**, quarantaines comprises, 111 JAR contrôlés par CRC et
33 YAML analysés par un parseur sûr. Aucun fichier distant modifié pendant cette
sauvegarde. La surveillance API confirme l'état arrêté pendant l'opération.

Démarrage réel d'une seconde copie locale en Java 25.0.5, arrêt propre, zéro
erreur/avertissement : 76 régions et 21 846 chunks conservés, 996 emplacements
d'inventaires/butins comparés, quatre fichiers joueur et 152 fichiers techniques
inchangés. Équipes, spawns, objectifs et état historique conservés. L'archive,
le manifeste et la restauration originale restent inchangés.
Le [rapport de sauvegarde](MINESTRATOR_V22_CURRENT_BACKUP_20261123.md) précise
les preuves et les limites Windows/POSIX.

## 3. Reconstruction depuis l'état actuel

Le candidat repart des **463 fichiers restaurés actuels**, sans fusion avec une
ancienne partie. Les quatre régions sont reconstruites à partir de leurs octets
actuels, avec vérification des états avant édition ; aucune région d'une ancienne
livraison n'est substituée aveuglément.

- **22 219 restaurations naturelles** conservées et **33 cellules du puits**
  restaurées fidèlement depuis l'archive initiale approuvée.
- Quatre valeurs de heightmaps corrigées pour cette seule colonne ; éclairage
  invalidé pour recalcul, autres colonnes/NBT/inventaires préservés.
- **4 710 400 états de blocs comparés** à l'archive dans 46 chunks : conformes.
- Empreinte historique de **37 128 points** conservée et complètement conforme ;
  complément explicite des 33 cellules, soit **37 159 positions uniques**.
- **Zéro exception de terrain** ; aucune reconstruction arbitraire, structure
  décorative ajoutée, modification de dimension ou affaiblissement de validateur.
- Bases, spawns, monuments, ravitaillements, profils, règles et accès conservés.

Dernier JAR FKAmis validé, installé sous `plugins/FKAmis-1.0.0.jar` :
`905b0f4b11192d26cd59b82b151525ad3b69f7f1803c65760589800404345ca5`.
Sa version déclarée reste 1.0.0 ; son empreinte identifie la livraison V2.2.

Les références portent l'approbation du propriétaire et la dispense de visite,
avec `humanInspectionPerformed=false`. Le nouveau manifeste compte **157 entrées**.
Le périmètre reste **17 fichiers : 12 remplacements et cinq créations**.
Le vieux manifeste de transfert de 148 fichiers n'est pas utilisé.

| Artefact final intégré | SHA-256 |
|---|---|
| `DEPLOYMENT_MANIFEST.json` | `db27f94828f5db36425e7195fa31f903b4463a48b856f83b1a35ac68d2993690` |
| `v22-final-current-transfer-private.zip` | `d8f070a62585bede2a3965e74ca1c7f70a41d4521c3a64d276e89225a5c9e55e` |

Ce ZIP privé contient les 17 cibles et un manifeste d'emballage non installé ;
ce n'est ni une sauvegarde complète ni un ZIP de construction de carte.

## 4. Simulation et installation réellement effectuées

Les validateurs de maintenance, de manifeste, de référence de partie initiale et
de terrain réussissent. Le candidat complet démarre sur une seconde copie locale
indépendante : zéro erreur/avertissement, inventaires et états conservés, source
inchangée. **194 tests Python passent**, dont les contrôles d'écriture exclusive,
conflits, propriétaires, démarrage unique, interdiction des commandes de partie
et distinction entre ancien et nouveau log de démarrage.

La simulation physique couvre toute la sauvegarde : installation de 17 fichiers,
13 anciennes versions en quarantaine, **480 fichiers attendus**, puis restauration
dans un autre dossier des **463 fichiers originaux**. Six interruptions sont
simulées dans le modèle d'activation/rollback. Les preuves et tentatives locales
restent conservées, sans suppression.

Exécution distante dédiée **`MS-DEPLOY-V22-20261123-01`** :

1. Nouveau contrôle de tous les contenus et métadonnées de source, serveur arrêté.
2. Staging neuf `.fk-stage/MS-DEPLOY-V22-20261123-01`, transfert exclusif des
   17 fichiers, lecture SHA, modes et UID/GID contrôlés.
3. Nouvelle vérification des 463 sources et de la liste complète avant activation.
4. Frontière d'activation journalisée avant le premier déplacement actif.
5. **13 fichiers conservés** sous
   `.fk-quarantine/MS-DEPLOY-V22-20261123-01/files/` : 12 remplacés et l'ancien
   `map-v21-caverns.json`. L'ancien relevé de cavernes est aussi conservé dans
   `reference/history-v21/`, sans être un contrôle actif V2.2.
6. Activation des 17 fichiers, **manifeste en dernier** ; aucun arbre de monde
   complet déplacé pour installer V2.2.
7. **480 fichiers vérifiés à froid** : 315 actifs, 152 historiques et 13 nouveaux
   fichiers de quarantaine. Les **450 fichiers d'origine conservés**, dont 298
   actifs, sont recontrôlés par SHA et métadonnées.

Les fichiers installés conservent leurs modes prévus et UID/GID Linux 999/995.
Les propriétaires des 366 répertoires originaux sont relevés avant écriture.
Aucun chown, effacement, changement de whitelist ou réglage panel n'est effectué.

## 5. Démarrage et contrôles distants

Une seule demande API `start`, après conformité à froid. Le nouveau log de boot
est distingué de l'ancien pour éviter de valider un ancien « Done ». Surveillance
pendant la transition puis avec état `online` attendu.

| Contrôle réel | Résultat |
|---|---|
| Paper | 26.3-244, empreinte approuvée inchangée |
| FallenKingdom | Officiel 2.24.9 chargé, JAR inchangé |
| FKAmis | JAR V2.2 `905b0f4b…345ca5` chargé, marqueur et registre cohérents |
| Logs | **0 ERROR/SEVERE, 0 WARN**, boot terminé |
| Partie | **J0, non lancée**, roster et objectifs vides, aucune commande `fka start` |
| Territoires / spawns | Quatre rayons 40, centres/spawns et blocs de sol/espace conformes |
| Terrain | **37 159 positions uniques** contrôlées à distance, sous-sols naturels sans référence active aux cavernes artificielles |
| Puits | 33 états archivés conformes et quatre heightmaps contrôlées après démarrage |
| Structures | Sept monuments, six coffres de butin et huit supports de ravitaillement vérifiés |
| Effectifs / capture | Quatre joueurs maximum par équipe, 16 participants maximum et arbitre hors effectifs ; capture 60 s / 2,5 blocs conservée |
| Query UDP | Réponse réelle sur 22880, capacité **20** |
| Statut Minecraft TCP | Réponse réelle Paper 26.3, protocole 777, **20 places et 0 connecté** au relevé |
| Whitelist / rôles | Deux comptes inchangés ; quatre fichiers joueur, rôles et ravitaillements relus par SHA après boot |
| Manifeste / références | **13 cibles statiques** relues par SHA après boot ; quatre régions évoluent normalement avec Paper |
| Quarantaines / staging | 152 fichiers historiques contrôlés par métadonnées après boot, 13 nouveaux conservés, **zéro fichier restant en staging** |
| Restart / watchdog | `restart-on-crash=false`, watchdog conservé, aucune réactivation automatique |

Le système de portail officiel est initialisé et sa commande de statut fonctionne :
**aucun cadre enregistré, activation administrative false, voyage fermé/suspendu**.
Aucun portail créé ou activé ; l'accès J2 reste soumis aux règles approuvées.
Le guidage `/fka base` est exposé dans l'aide. Les notifications et le guidage
reposent sur le JAR validé effectivement chargé ; leur affichage et déclenchement
avec un vrai joueur **ne sont pas testés pendant cette installation**. Ils restent
des points de recette humaine, sans test destructif ou partie lancé.

MineBoard : l'API authentifiée confirme `online` dans ses deux champs d'état.
Les champs de version/joueurs de cette réponse sont nuls ; le statut TCP et
Query fournissent les preuves de version/capacité. L'interface graphique du panel
et sa liste visuelle de joueurs n'ont pas été inspectées.

Au contrôle post-boot : **483 fichiers**, dont 318 actifs. Les trois ajouts
observés correspondent à la rotation du journal et aux temporaires du spark
intégré à Paper. Aucun chemin installé attendu n'a disparu. Aucun plugin de test,
profil synthétique ou ancienne variante de carte n'est transféré.

## 6. Écart d'environnement et limites du rollback

**La JVM observée a changé de patch** : ancien boot `25.0.5+8-LTS`, nouveau
`25.0.5.1+2-LTS` Temurin sur Linux. L'identifiant 61 et l'image configurée
`reg.sttr.io/java/25_perf:latest` sont inchangés. Aucune commande de modification
Java ou panel n'a été envoyée. L'origine précise de ce rafraîchissement du runtime
hébergeur n'est pas démontrée par les accès disponibles.

Le profil approuvé reste Java 25 Performance ; les contrôles de compatibilité
distants décrits ci-dessus réussissent avec la JVM effectivement fournie. Les
essais locaux utilisent Java 25.0.5. La sauvegarde des fichiers Minecraft ne
restaure pas l'image, l'OS ou un patch Java fournisseur : un retour bit à bit à
l'ancienne JVM n'est donc pas démontré. Cet écart est consigné, sans le masquer
comme une identité exacte de tous les exécutables.

Le retour des **fichiers et données V2.1** reste fondé sur la nouvelle sauvegarde
complète, vérifiée et démarrée fonctionnellement en local. En cas d'échec futur :
autorisation adaptée, état arrêté confirmé, archive/manifeste/restauration
revérifiés, staging de restauration neuf, conservation de la tentative active
en quarantaine, restauration cohérente des fichiers actifs et contrôle de tous
les contenus originaux, historiques compris. Aucune fusion d'inventaires ou
restauration du seul JAR. Les nouvelles quarantaines de diagnostic restent
conservées ; aucune suppression irréversible n'est nécessaire.

Ce rollback n'a pas été exécuté à distance puisque l'installation réussit. Les
scripts le restreignent à un échec d'activation/démarrage et vérifient ses
préconditions ; il laisse l'ancienne instance arrêtée après restauration. Les
permissions Linux sont planifiées et contrôlées via SFTP, sans prétendre qu'une
restauration Windows applique des propriétaires POSIX.

Les risques d'absence de verrou exclusif et de relance fournisseur non maîtrisée
restent acceptés et documentés. Aucun contrôle ne transforme les doubles lectures
et sondages périodiques en snapshot atomique garanti.

## 7. État laissé et suite

Serveur **en ligne, réservé à la recette**, J0, whitelist stricte inchangée,
`restart-on-crash=false`. Sauvegarde complète et restauration originale sur PC,
quarantaines V2.1 et V2.2 conservées sur l'instance, journaux détaillés privés sous
`C:\Users\youne\FKBackups\MS-DEPLOY-V22-20261123-01`.

La recette humaine peut suivre le [guide de partie](GUIDE_PARTIE_TEST_V22.md)
dans le périmètre autorisé. L'ajout d'identités à la whitelist, la construction
des cadres, leur activation, une partie et les tests destructifs demandent leurs
autorisations distinctes. Aucune preuve de charge à seize participants plus
l'arbitre ni d'inspection graphique n'est revendiquée.
