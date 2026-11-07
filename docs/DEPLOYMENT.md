# Hébergement, déploiement et sauvegardes

## Déployer la candidate corrigée après validation

L'instance de travail est `runtime/map-v2-fixes` ; `runtime/local` et `runtime/map-v2`
restent conservés. Les profils corrigés sont dans `configs/map-v2-fixes/`.
Un premier export de la candidate existe dans
`dist/fallenkingdom-map-v2-20261107T011000Z.zip`, avec empreinte et manifeste vérifiés.
Il reste destiné à la recette ; refaire l'export après validation des terrains.
Après inspection avec clients, exporter la candidate arrêtée :

```powershell
.\scripts\server.ps1 backup -Name map-v2-fixes
.\scripts\server.ps1 validate -Name map-v2-fixes
.\scripts\server.ps1 export -Name map-v2-fixes
```

Transférer la copie complète : monde, JAR, `state.yml`, `config.yml` et `supplies.yml`.
Ne pas fusionner seulement les fichiers de régions avec les anciennes équipes.
Les coordonnées de ravitaillement et son compteur font partie de la sauvegarde.
Les plugins `FKMapV2Builder` et `FKMapV2SupplyProbe` sont réservés au chantier et à
la recette : aucun ne doit apparaître dans l'archive de production.
Cela inclut aussi `FKMapV2Corrections` et `FKGameplayProbe`. Ne pas transférer une
instance `probe-*` ou `map-v2-qa-*` comme carte de partie. Le bilan de l'export corrigé
est dans `tests/results/v2-fixes-delivery.json`.

Garder la sauvegarde initiale vérifiée et l'instance historique comme retour arrière.
Une migration vers un nouvel hébergement ne valide pas automatiquement les terrains
ni les performances à huit joueurs. Suivre [MAP_V2.md](MAP_V2.md) avant la mise en ligne.

## Dimensionnement et offre

Pour huit joueurs, deux plugins et une carte prégénérée : viser 6 à 8 Go de RAM
allouée au service et environ 4 à 6 Go de heap Java, processeur moderne à bonnes
performances par cœur, NVMe, Europe proche de la France. Conserver de la mémoire
hors heap ; un abonnement 6 Go ne doit pas être lancé avec `-Xmx6G` sans marge.
Mesurer avec spark intégré avant d'augmenter l'offre. Réglages initiaux : vue 8,
simulation 6, aucune modification des mécaniques redstone/hoppers vanilla.

Comparaison consultée le 6 novembre 2026, tarifs publics en dollars, hors éventuelle
TVA/conversion facturée. Aucun achat, disponibilité de serveur ou latence n'a été testé.

| Offre | Prix affiché | Intérêt | Réserve |
|---|---|---|---|
| Bloom Performance 8 Go | 22 USD/mois | Cœurs dédiés, NVMe, sauvegardes hors site, console et SFTP | Vérifier le total TTC en euros ≤25 €, disponibilité Europe et Java 25 |
| PebbleHost Premium 6 Go | 13,50 USD/mois | Suffisant comme point de départ, Europe, NVMe, sauvegardes annoncées | Accès annoncé FTP ; confirmer un protocole chiffré adapté avant commande |
| PebbleHost Premium 8 Go | 18 USD/mois | Plus de marge sans prendre une grosse offre | Même vérification d'accès et de tarif final |

**Choix conseillé si le total reste dans le budget : Bloom Performance 8 Go dans une
localisation européenne**, pour disposer d'un accès SFTP documenté et de marge CPU.
Si le TTC dépasse 25 €, demander une offre européenne 6 Go avec SFTP et Java 25,
ou confirmer les possibilités chiffrées de PebbleHost Premium 6 Go. Ne pas prendre
Performance+ pour cette partie. Exaroton a été considéré pour sa facturation à l'usage,
mais n'est pas retenu sans confirmation de l'accès aux fichiers requis pour ce JAR custom.

Sources officielles : [offres Bloom](https://bloom.host/minecraft/),
[localisations Bloom](https://bloom.host/locations/),
[gestion des fichiers/SFTP Bloom](https://docs.bloom.host/file-manager-controls),
[sauvegardes Bloom](https://docs.bloom.host/backups),
[offres Premium PebbleHost](https://pebblehost.com/minecraft/premium),
[prix 6 et 8 Go PebbleHost](https://billing.pebblehost.com/index.php?language=french&rp=%2Fstore%2Fpremium-minecraft-hosting),
[tarification exaroton](https://support.exaroton.com/hc/en-us/articles/360019687657-Pricing).

## Préparer le paquet

Avant toute mise à jour ou transfert : `fka pause`, puis `stop`, attendre la fin de Java.

```powershell
.\scripts\server.ps1 backup
.\scripts\server.ps1 validate
.\scripts\server.ps1 export
```

L'archive privée apparaît dans `dist/` avec un SHA-256 et un manifeste des fichiers.
Elle contient les mondes, inventaires, plugins, équipes et objectifs. Elle n'est pas
destinée à GitHub ni à un hébergement public de fichiers. Garder l'archive hors du
serveur de production pour permettre un retour arrière.

## Installation chez l'hébergeur

1. Choisir Java **25**, un JAR personnalisé, port fourni par le panel. Désactiver tout
   remplacement automatique de Paper ou des plugins au démarrage.
2. Arrêter le serveur vide de l'hébergeur. Faire une sauvegarde de son état initial.
3. Vérifier l'archive localement puis envoyer son contenu par SFTP, sans recopier
   `BACKUP_MANIFEST.json` comme fichier de monde. Ne pas mélanger deux parties.
4. Garder `online-mode=true`, whitelist et command blocks désactivés. RCON reste fermé.
   `server-ip` doit rester vide ou suivre l'allocation réseau exacte du panel.
5. Configurer le lancement `java -Xms2G -Xmx4G -jar paper.jar --nogui` ou utiliser le
   lancement du panel. **Ne pas reprendre l'option locale `--host 127.0.0.1` en production.**
6. Confirmer l'EULA via l'interface de l'hébergeur si elle le demande ; aucun script
   ne doit l'accepter à la place de l'administrateur.
7. Démarrer, vérifier deux plugins activés, absence d'ERROR/SEVERE, jour conservé et
   partie en pause. Contrôler les points d'apparition et les salles avant `fka resume`.
8. Faire la recette multijoueur et mesurer TPS/MSPT ; ouvrir la partie officiellement
   seulement après validation. Le transfert ne constitue pas une recette.

## Sauvegardes cohérentes

Sous Windows, le wrapper `start` sauvegarde après chaque arrêt propre. Commande
manuelle : `server.ps1 backup`. Les sauvegardes incluent toute l'installation, donc
le monde et ses dimensions, données de joueurs et fichiers des deux plugins.
Les verrous du wrapper et `session.lock` sont acquis avant la lecture. Aucun simple
`save-off` suivi d'une copie à chaud n'est présenté comme une sauvegarde cohérente.

Sur un panel, programmer **arrêt propre → attendre OFFLINE → sauvegarde → redémarrage**
à la fin d'une session ; le serveur redémarre en pause. Si le panel ne permet pas
d'attendre OFFLINE, arrêter manuellement avant une sauvegarde complète. Une sauvegarde
incrémentale à chaud du prestataire est un supplément, pas la preuve d'un instantané
cohérent entre plugins, monde et inventaires.

Conserver au minimum les sept dernières fins de session, une archive avant chaque
mise à jour et une copie hors machine. Les scripts ne suppriment pas automatiquement
les anciennes archives ; purger les versions plus anciennes après vérification de
la dernière restauration, pour ne pas effacer le seul état sain.

## Restaurer

```powershell
.\scripts\server.ps1 restore -Name restauration -Source 'C:\Sauvegardes\fk-....zip'
.\scripts\server.ps1 validate -Name restauration
.\scripts\server.ps1 start -Name restauration -Port 25566
```

Le manifeste et chaque empreinte sont contrôlés avant extraction ; les chemins
sortant du dossier sont refusés. La destination doit être neuve. Vérifier la copie
sur un autre port, puis remplacer la production arrêtée en conservant l'original.
Restaurer **l'ensemble**, jamais uniquement `state.yml`, le monde ou des inventaires.
Conserver une seule instance active de la partie pour éviter les divergences.

## Mises à jour et sécurité

Pour le complément propre au projet, compiler puis utiliser, serveur arrêté :

```powershell
.\scripts\build.ps1
.\scripts\server.ps1 update-plugin
```

Le script vérifie l'installation, sauvegarde toute la partie, remplace uniquement
le JAR FKAmis et enregistre son empreinte. Il conserve la configuration et la progression.
Les changements de Paper/FallenKingdom demandent une mise à jour explicite du verrou
et une recette complète, pas cette commande dédiée au complément.

Paper 26.2 est retenu pour la compatibilité publiée de FallenKingdom ; Paper annonce
26.3 comme version plus récente. Ne pas suivre le bouton « mise à jour automatique »
du panel. Vérifier une publication compatible du plugin, sauvegarder, actualiser le
verrou d'artefacts puis tester une copie. Aucun downgrade de monde après conversion.

Les participants ne sont pas OP. Ne partager ni console, ni SFTP, ni fichiers d'objectifs.
Les sauvegardes et journaux peuvent contenir des identifiants et des positions privées.
Aucun secret, mot de passe, jeton ou adresse d'hébergement n'est enregistré dans ce dépôt.
