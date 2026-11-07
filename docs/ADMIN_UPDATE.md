# Mise à jour ciblée : arbitre, survie et tips

Profil : Paper **26.3 build 244 STABLE**, Java 25, FallenKingdom officiel 2.24.9
inchangé. La nouvelle révision de **FKAmis 1.0.0** est identifiée par son SHA-256,
pas par un changement du nom de fichier. Aucun monde à retransférer. Le moteur
de capture `CaptureClock`, ses 60 secondes, deux attaquants, rayon 2,5 et ligne de
vue restent conservés.

## Cause et corrections

FKAmis assimilait `team == null` à une élimination. Connexion et tick périodique
réimposaient alors SPECTATOR. Un ancien mode enregistré pouvait aussi rester en
place avant le départ. Ces deux chemins utilisent maintenant une politique unique :

| Situation | Mode |
|---|---|
| Nouveau compte avant attribution, jour 0 | SURVIVAL, hors roster et hors gameplay |
| Participant d’un royaume actif | SURVIVAL, y compris après mort/reconnexion |
| Royaume capturé | SPECTATOR, durable après mort, reconnexion et redémarrage |
| Arbitre autorisé par UUID, hors équipe | CREATIVE avec vol |
| Compte sans équipe après lancement | SPECTATOR, hors participation |

**Morts illimitées** : zombie, squelette, lave, chute, PvP ou assaut ne retirent
aucune vie, équipe ou progression. La règle native `DeathLimit` est forcée à zéro.
Le lit ou l’ancre déjà validé par l’événement Paper est conservé ; sinon un participant
actif revient au spawn sûr de son équipe. L’ancien TP natif différé de réapparition
est remplacé par cette décision unique. Une capture complète reste la seule
élimination automatique. Les spectateurs et l’arbitre ne réinitialisent pas une
capture par leur départ, mort ou téléportation.

## Autoriser le véritable arbitre

Le statut OP **ne confère pas ce rôle**. La permission `fkamis.admin` est désactivée
par défaut ; les actions sensibles vérifient aussi l’UUID enregistré. Les commandes
de gestion ci-dessous sont **réservées à la console réelle du panel**, jamais à un
joueur OP ni à l’arbitre en jeu :

```text
fka admin uuid PseudoOfficielConnecte
fka admin grant UUID_OFFICIEL
fka admin grant UUID_OFFICIEL confirm
fka admin list
fka admin revoke UUID_OFFICIEL confirm
```

Copier l’UUID affiché par la première commande, issu d’un compte réellement authentifié
sur le serveur en `online-mode=true`. La commande sans `confirm` affiche seulement
l’action à confirmer. Un participant déjà attribué est refusé : avant départ, le
retirer explicitement avec `fka unassign Pseudo`, puis autoriser l’arbitre.
`fka assign` refuse réciproquement un arbitre. Aucune attribution automatique d’équipe.

Les autorisations sont enregistrées atomiquement dans **`plugins/FKAmis/admins.yml`**,
séparément du `state.yml` de partie. Ce fichier privé est créé vide s’il n’existe pas ;
aucun UUID réel n’est livré ni committé. Il est conservé lors d’une nouvelle mise à jour.
L’arbitre retrouve automatiquement CREATIVE à la connexion et après redémarrage.
Une révocation retire ses permissions ajoutées ; elle ne l’inscrit pas comme participant.
Le rôle ne modifie pas son statut OP persistant. Aucun OP n’est nécessaire pour l’arbitre.

## Pouvoirs et neutralité

L’arbitre reçoit les permissions Bukkit enregistrées des commandes, sans dépendance
LuckPerms. Les protections natives de FallenKingdom sont déléguées avec leurs mêmes
priorités ; elles sont ignorées seulement pour les acteurs autorisés sur les événements
concernés. Aucun refus d’un autre plugin n’est annulé globalement.

Exemptions : construction/casse dans les royaumes, seaux, interactions et conteneurs
ordinaires, déplacements, TP et portails/dimensions fermées, interventions pendant
une pause et filtrage de son inventaire personnel. L’arbitre est immunisé aux dégâts
et ses coups directs/projectiles ne blessent pas les participants. Il peut intervenir
sur des mobs ; ces interventions restent des actes d’arbitrage à employer avec retenue.
Les objets interdits restent filtrés pour les joueurs, les distributions et les drops.

Il ne compte jamais pour la présence active, les huit places du roster, le timer de
ravitaillement, la capture/contestation, les éliminations ou la victoire. Sa déconnexion
ne provoque aucune pause. `/fka teams tpall` transporte seulement les participants.
La console attend toujours **quatre binômes**, pas neuf participants, pour `fka start`.

Les blocs d’objectif et de ravitaillement restent protégés même contre une casse
créative accidentelle. L’arbitre ne récupère aucun lot de ravitaillement. Les lots
étant virtuels, utiliser `/fka supply list` pour inspecter les sites/états, sans ouvrir
leur inventaire comme un stock normal.

Pour une réparation destructive nécessaire, **mettre la partie en pause et sauvegarder**,
puis depuis la console :

```text
fka admin unlock UUID_ARBITRE x y z confirm
```

L’arbitre doit être connecté ; la cible se trouve dans son monde actuel. L’autorisation
vaut **60 secondes et une seule casse/pose réussie sur ce bloc**. Elle ne relance pas
la partie. Réparer et réinspecter l’objectif/site avant de reprendre ; ne pas changer
les coordonnées ou recharger un lot. Pour une intervention complexe, préférer la
restauration complète du point précédent à un bricolage du `state.yml`.

`setblock`, `fill`, `clone`, `place`, `data`, `execute` peuvent contourner les événements
de protection : ils sont réservés à une **intervention explicite par console**,
après sauvegarde. Les commandes ordinaires d’arbitrage et de TP restent disponibles.
Les journaux privés `plugins/FKAmis/admin-audit.log` et console enregistrent attribution,
révocation, constructions/casses, interactions, TP et commandes. Les commandes hors
FKAmis sont journalisées par leur nom, sans recopier les messages privés/arguments sensibles.

## Tips

Origine identifiée : **FallenKingdom `TipsManager`**, tâche asynchrone de conseils
chaque trois minutes avant le départ. Aucune option de désactivation n’existe dans
sa configuration 2.24.9. FKAmis appelle l’API publique `cancelBroadcasts()` au chargement
et lors de la synchronisation des phases, via l’option :

```yaml
disable-native-tips: true
```

Cette option vaut aussi `true` si elle est absente d’une ancienne configuration.
L’avertissement natif de passage créatif n’est pas envoyé à l’arbitre à chaque correction
de mode. Aucun filtre global de chat et aucune modification des traductions natives :
annonces de jour, ravitaillement, capture, élimination, victoire, erreurs et avertissements
importants restent en place.

## Installation MineStrator sans remplacer le monde

Livraison : `dist/fallenkingdom-admin-update.zip`, rapport et empreintes dans
`tests/results/admin-update-delivery.json`. Le ZIP contient le JAR corrigé, son
empreinte, les outils de maintenance et ce guide. Il **ne contient ni monde,
state.yml, admins.yml, territoires, identités ni plugin de recette**.

1. Dans la console : `fka pause`, `fka save`, puis `stop`. Attendre l’état complètement
   arrêté ; désactiver temporairement les relances planifiées. **Jamais `/reload`.**
2. Faire une sauvegarde **complète à froid**, vérifier son ZIP et télécharger une
   copie externe : monde, dimensions, inventaires, configurations, plugins et état
   au même instant. Conserver cette sauvegarde comme retour arrière.
3. Vérifier le SHA-256 de la livraison et celui du JAR dans le rapport. Conserver
   `paper.jar` 26.3-244 et FallenKingdom 2.24.9 ; ne pas lancer d’installateur de monde.
4. Par SFTP, remplacer seulement `plugins/FKAmis-1.0.0.jar` et `FKAmis.sha256` par les
   fichiers de `payload/`. Si les scripts de maintenance sont utilisés, remplacer
   aussi les deux fichiers de `payload/maintenance/`. **Ne toucher ni au monde,
   ni à state.yml, ni à admins.yml existant, ni à supplies.yml.**
5. Dans le `server.properties` existant, modifier seulement : `max-players=10`,
   `gamemode=survival`, `force-gamemode=false`. Conserver port **22880**, `level-name`,
   authentification et whitelist strictes. Garder Java 25 Performance et environ
   6154M gérés par le panel. Ajouter `disable-native-tips: true` à la racine de la
   configuration FKAmis, sans remplacer ses autres paramètres.
6. Avec Python 3.11+ disponible, les étapes 2, 4 et 5 peuvent être réalisées sur
   l’instance arrêtée par `python apply_admin_update.py --server /chemin/instance`.
   Ce script vérifie le payload et la version, prend un backup complet vérifié,
   applique uniquement ces fichiers/clés et compare monde/état/rôles existants avant
   et après. Il ne démarre pas le serveur. Sans Python sur le panel, suivre le SFTP
   manuel ; ne pas rapatrier toute la carte pour une simple mise à jour.
7. Démarrer depuis le panel, vérifier les deux plugins et l’absence d’ERROR/SEVERE.
   `fka status` doit retrouver le jour, les équipes et les éliminations existants,
   en pause. Au jour 0, aucune partie ne doit être lancée par cette opération.
8. Whitelister **les huit participants et l’arbitre**, sans désactiver online-mode.
   Autoriser l’UUID de l’arbitre via console ; tester son CREATIVE, une construction
   ordinaire, un TP en pause et le refus de casser un objectif/site sans autorisation.
9. Tester avec de vrais comptes : nouveau joueur, morts PvE/PvP, lit/spawn, capture
   incomplète puis complète, reconnect/restart d’un éliminé, départ de l’arbitre,
   huit participants plus arbitre simultanés et absence de tips. Ne pas utiliser
   les interfaces Player simulées comme preuve de ces connexions.

Le manifeste initial du paquet monde 26.3 reste une référence historique ; après
mise à jour il ne décrit plus la nouvelle révision du JAR. Mettre à jour son relevé
d’exécutables si la maintenance est manuelle ; le script actualise `RUNTIME_LOCK.json`.

## Retour arrière

En cas de problème : `stop`, attendre l’arrêt total, conserver la copie en échec.
Restaurer **la sauvegarde complète prise juste avant la mise à jour** dans un dossier
ou service neuf, avec son ancien JAR et ses propres fichiers de configuration.
Vérifier SHA/manifeste, démarrer isolé et confirmer jour/équipes/inventaires, puis
basculer seulement après validation. Ne jamais restaurer le monde seul, le seul
state.yml ou un inventaire d’un autre instant. Garder une seule copie accessible.
Il n’y a aucun changement de version de monde : rester en Paper 26.3, aucun downgrade.

Les régressions et essais réellement effectués sont détaillés dans le rapport
de livraison ; aucun accès distant ni lancement officiel n’a été effectué par l’agent.
