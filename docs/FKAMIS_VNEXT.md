# FKAmis VNext — exploitation et preuves

Révision indépendante de FallenKingdom, branche `feature/fkamis-vnext`, basée sur
la livraison gameplay `83e721d8ac12feefdb590976747f88d6825b3243976c7e9f10b1cc35fac5239d`.
Paper **26.3 build 244**, Java **25**, FallenKingdom officiel **2.24.9** restent
inchangés. Aucun accès à MineStrator. Les archives précédentes restent historiques.
Le rapport courant est [vnext-delivery.json](../tests/results/vnext-delivery.json).

## Risques de l'audit et décisions

- Le nettoyage d'équipement pouvait réinitialiser l'IA ; la reproduction compare
  l'ancien JAR, le balayage suspendu et le même arc réappliqué avant de tester le correctif.
- Les protections natives FK et complémentaires peuvent se superposer ; les
  callbacks et priorités restent conservés, avec observation avant/après et régressions.
  Le JAR officiel reste intact ; sa déclaration historique 26.2 ne devient pas une
  certification amont 26.3. Les recettes locales contrôlent cette combinaison précise.
- Monde, inventaires et progression ne partagent pas une transaction à chaud ; le
  reset n'applique rien avant arrêt et sauvegarde complète sous verrous.
- Configuration, compteur de lots et migration pourraient diverger ; journal
  d'intention et récupération déterministe gardent une source de stockage existante.
- Un passé statistique absent ne peut pas être reconstitué ; les anciennes parties
  sont signalées partielles et les historiques terminés ne sont jamais remplacés.
- Les événements et interfaces simulés ne prouvent pas le rendu réseau ; la
  checklist humaine et les mesures de charge sur l'hôte restent explicites.

## Diagnostic des squelettes

Le balayage `ItemBan.sweep()` remettait toutes les secondes le même arc dans la
main des squelettes. Dans le JAR Paper 26.3-244 contrôlé localement,
`AbstractSkeleton.onEquipItem()` appelle `reassessWeaponGoal()`, qui retire puis
réinstalle le comportement de tir. Répéter cette opération avant la fin du cycle
empêchait le squelette de décocher. Aucun événement DAMAGE ne pouvait apparaître.

Le précédent test créait directement une flèche et contournait ce cycle d'IA.
La nouvelle reproduction avec l'ancien binaire montre zéro tir et aucune perte
de santé ; suspendre son seul balayage périodique rétablit tirs et dégâts.
Réappliquer volontairement le même arc chaque seconde reproduit le défaut.
Voir [la reproduction causale](../tests/results/vnext-physics-baseline.json).

Le correctif clone l'objet avant nettoyage et écrit uniquement les équipements,
cases d'inventaire et curseurs réellement différents. Les objets interdits restent
supprimés. Aucune priorité de protection n'est abaissée ; aucun dégât n'est forcé.
La recette du JAR livré observe IA naturelle, lancement, collision, événement Paper
et baisse effective de santé : [matrice physique](../tests/results/vnext-physics-fixed.json).

Le corps joueur utilisé est un véritable `ServerPlayer` NMS dans le monde, avec
santé et collisions réelles, sans connexion réseau authentifiée. Ces accès NMS
existent uniquement dans le JAR de recette séparé, absent du paquet de production.
Les projectiles de joueur de cette matrice sont lancés par l'API ; le tir à l'arc
depuis un vrai client reste dans la checklist humaine.

Diagnostic temporaire, accessible arbitre UUID/console même pendant la partie :

```text
fka config set damage-debug true
fka config get damage-debug
fka config set damage-debug false
```

Les lignes `[FK-DIAG ...]` couvrent ciblage, arc, lancement, impact, dégâts avant/après
protections FKAmis et callbacks natifs, puis santé au tick suivant. Elles indiquent
mode, rôle, équipe, invulnérabilité, ticks d'immunité, absorption et source Paper.
Le débit est borné ; activer seulement le temps de la reproduction. Le diagnostic
observe les événements et ne les débloque pas. Les UUID des logs restent privés.

## Captures et lieux protégés

La BossBar affiche la progression du `CaptureClock` existant ; elle ne possède
aucun second timer. Elle suit les attaquants éligibles présents, se retire lors
d'une contestation, pause, mort, déconnexion, changement de monde ou fin de partie.
Les défenseurs connectés reçoivent titre, chat et cloche au début, avec un délai
de dix secondes entre alertes d'une même équipe. La capture annonce publiquement
l'équipe attaquante et celle éliminée. Les contributeurs de la tentative continue
sont crédités une fois, sans multiplier le nombre de captures de l'équipe.

Sept monuments, huit supports de ravitaillement et le centre sûr sont protégés.
Les emprises des monuments reprennent leurs plans, avec une marge horizontale
d'un bloc, un bloc sous le sol et deux au-dessus du plan. Les sites de ravitaillement
ont un rayon de deux blocs, de Y−1 à Y+3 ; le centre un rayon de trois blocs, de
Y−2 à Y+4. Les coordonnées proviennent des métadonnées existantes, jamais d'une
reconstruction. L'index par chunk évite de parcourir le monde à chaque événement.

Les gardes couvrent outils, pose et obstruction, explosions, fluides, pistons,
gravité, feu, croissance, distributeurs et transferts automatiques d'inventaire.
Les explosions retirent seulement les blocs protégés de leur liste : un creeper
peut toujours blesser un participant. Ouvrir normalement un coffre de butin reste
possible ; aucun coffre consommé n'est rempli à nouveau. La collecte et l'expiration
des ravitaillements restent celles de `SupplyService`.

L'arbitre UUID peut bâtir et casser dans ces emprises ; les gardes sensibles
préexistantes des coffres objectifs et des supports techniques restent applicables.
Les participants et spectateurs restent soumis à leurs permissions habituelles,
y compris au jour zéro. Les métadonnées des sept monuments sont obligatoires :
ne pas supprimer `map-v2-construction.json` sur l'instance.

Après une réapparition pour décès, le participant actif reçoit par défaut cinq
secondes de protection **PvP réciproque** : il ne peut ni subir ni infliger de PvP,
ni contribuer offensivement à une capture. Le PvE reste actif. Une actionbar indique
le temps restant. L'échéance absolue persiste ; reconnexion, téléportation et monde
ne la prolongent pas. Aucun nouveau délai n'est donné à un spectateur éliminé.

## Configuration

Toutes les commandes `config` sont réservées à l'arbitre UUID et à la console :

```text
fka config list
fka config get <paramètre>
fka config set <paramètre> <valeur>
fka config validate
fka config defaults
fka config diff
```

| Paramètre | Défaut | Contraintes |
|---|---:|---|
| players-per-team | 2 | entier 1 à 4, compatible avec le roster |
| capture-seconds | 60 | entier 1 à 3600 |
| capture-players | 2 | entier 1 à 4, seuil adapté à l'effectif officiel |
| capture-radius | 2.5 | nombre fini de 1.5 à 8 |
| pvp-day | 2 | entier 1 à 1000, au plus assault-day |
| assault-day | 3 | entier 1 à 1000 |
| nether-day | 2 | entier 1 à 1000, au plus assault-day |
| respawn-protection-seconds | 5 | entier 0 à 30, zéro désactive |
| supply-interval-seconds | 1800 | entier 60 à 86400, au moins la durée d'un lot |
| damage-debug | false | true ou false, diagnostic temporaire |

Les règles structurantes sont verrouillées dès le démarrage, même en pause ou
après la victoire. Une diminution incompatible avec les affiliations enregistrées
est refusée. Les modifications avec des lots actifs sont refusées. Les valeurs
inconnues sont conservées ; les valeurs non numériques, non finies ou incohérentes
sont refusées avant écriture. Le rayon minimal préserve une géométrie de capture
possible ; les salles doivent toujours être validées.

`supply-interval-seconds` est le nom de commande de la clé de stockage existante
`supplies.yml: interval-seconds` ; aucun second compteur ni clé concurrente n'est
ajouté. Les écritures config/ravitaillement utilisent un journal d'intention avec
SHA-256, fichiers temporaires synchronisés et remplacements atomiques. Une écriture
interrompue est terminée avant chargement au prochain démarrage ; une provenance
différente est refusée. Ne pas éditer les fichiers pendant cette récupération.
Les modifications sont inscrites dans `admin-audit.log`.

## Statistiques et informations

Commandes publiques, sans position d'objectif ou d'ennemi :

```text
fka stats
fka stats match
fka stats player <pseudo>
fka stats team <Rouge|Bleue|Verte|Jaune>
fka stats leaderboard
fka info
fka info teams
fka info phases
fka info supplies
```

Le modèle utilise les UUID, conserve les pseudos, équipes, kills, morts totales et
PvP, dégâts PvP, contributions aux captures et temps actif. Les agrégats d'équipe
sont dérivés de ce modèle, avec objectifs perdus, survie et classement. Une même
vie ne produit qu'une mort ; la réapparition ouvre la vie suivante. L'attribution
utilise la source Paper et les marqueurs indirects existants, jamais la proximité.
Les morts naturelles ne produisent aucun kill ; arbitres, interventions de console
`generic_kill`, spectateurs et dégâts amicaux sont exclus du compétitif.

Les dégâts comptés sont les dégâts PvP finaux non annulés, plafonnés aux points de
vie restants : hors absorption et sur-dégâts létaux. Le temps actif et les pauses
sont mesurés par horloge monotone lorsque le serveur tourne ; l'arrêt n'ajoute pas
de temps actif. Le temps réel total inclut les arrêts. Le temps individuel demande
un participant vivant connecté en SURVIVAL, hors pause. Un match déjà commencé
avant VNext porte la mention **collecte partielle** ; aucun passé n'est inventé.
Le rang zéro dans les données ou le classement d'un ancien match signifie inconnu ;
seules les éliminations observées depuis l'activation ont un ordre et une durée connus.
La collecte persistante suit l'instantané d'état ; un arrêt brutal peut perdre les
toutes dernières observations non encore sauvegardées.

À la victoire, le bilan et le classement sont annoncés. Les fichiers permanents
`plugins/FKAmis/history/<match-id>/result.json`, `result.csv` et `result-teams.csv`
sont créés. Une nouvelle partie obtient un nouvel identifiant ; un historique
différent existant ne peut pas être écrasé. Les exports de reset sont aussi gardés.
`info` lit les phases, affiliations et le compteur restant de `SupplyService`,
avec suspension visible en pause. La locator bar reste désactivée.

## Réinitialisation : deux opérations distinctes

Ces commandes ne sont pas des outils d'édition du monde en direct. Elles demandent
arbitre UUID ou console. Désactiver au préalable les redémarrages automatiques du
panel, pauses planifiées et toute autre maintenance concurrente.

```text
fka pause
fka reset status
fka reset prepare
fka reset cancel
```

`prepare` explique les conséquences et fournit un jeton valable cinq minutes.
Faire quitter **tous** les joueurs, arbitre compris, puis depuis la console :

```text
fka reset confirm <jeton>
```

Une partie active, un joueur encore connecté, un jeton faux/expiré ou un changement
de progression/configuration refusent la confirmation. Le plugin sauvegarde,
archive les statistiques, prépare un candidat et une demande signée par empreintes,
puis arrête Paper. Il n'applique aucun état vierge à chaud. Un redémarrage avec cette
demande en attente est refusé. Attendre la fin de Java et l'état arrêté du panel.
La demande à froid expire après quinze minutes ; conserver le jeton hors des logs publics.

**Reset logique**, serveur arrêté :

```text
python maintenance/host_ops.py reset-logical --token <jeton>
```

L'outil prend le verrou partagé et les verrous natifs, contrôle état/candidat/JAR,
crée et relit une sauvegarde complète dans `.fk-resets/`, puis remplace atomiquement
le seul `state.yml`. Il remet jour, progression, affiliations, objectifs déclarés,
validations et statistiques à zéro. Il conserve carte, dimensions, inventaires,
constructions, coffres posés, butins déjà pris, configurations, arbitres et historique.
Les lots actifs deviennent expirés ; les identifiants d'événements et lots consommés
restent conservés. Les territoires et spawns d'équipe restent identiques. Il faudra
attribuer les équipes et revalider les salles. Ce mode ne reconstitue pas une carte neuve.

Annuler une demande hors ligne, sans toucher au monde ou à l'état :

```text
python maintenance/host_ops.py reset-cancel
```

**Restauration complète initiale** : préparer une copie initiale propre avec les
mêmes binaires VNext, règles, arbitres et accès souhaités. L'ancienne archive 26.3
seule contient un ancien FKAmis ; elle n'est pas directement une référence VNext.
Inspecter cette nouvelle copie en jeu avant approbation humaine. Serveur arrêté :

```text
python maintenance/host_ops.py seal-initial --archive /stockage/fk-initial-vnext.zip --approve-initial
```

Le contrôle automatique vérifie jour zéro, absence d'affiliations/objectifs,
quatre territoires/spawns, sept structures (6 689 blocs contrôlés), six inventaires
de butin de référence et huit supports. Il ne remplace pas l'inspection visuelle.
L'archive scellée doit rester hors de l'instance, avec `.zip.sha256` et `.approved.json`.
La référence fournie décrit la carte déjà approuvée ; aucune régénération n'a lieu.

Après une nouvelle préparation/confirmation et l'arrêt de l'ancienne partie :

```text
python maintenance/host_ops.py restore-initial --token <jeton> --archive /stockage/fk-initial-vnext.zip --destination /instances/fk-nouvelle
```

La destination doit être neuve, vide, séparée. L'outil sauvegarde intégralement
l'ancienne instance et restaure **tous** les fichiers d'un même point initial,
avec manifeste et contrôles de carte. Les JAR doivent être les mêmes. Toute divergence
des règles, rôles ou listes d'accès refuse l'opération ; sceller alors une nouvelle
référence propre. Seuls les commentaires de date de `server.properties` sont ignorés
pour cette comparaison, toutes ses propriétés sont comparées. Aucun mélange de
monde initial et d'inventaires de partie n'est permis. L'ancienne instance et ses
historiques restent archivés et arrêtés ; ne pas les publier aux joueurs.

## Migration et installation MineStrator

Paquet ciblé : `dist/fallenkingdom-vnext-update.zip` ; JAR séparé :
`dist/vnext/FKAmis-1.0.0.jar`. Le ZIP n'embarque ni monde, ni `state.yml`, `admins.yml`,
`supplies.yml`, inventaire, objectif ou plugin de recette. Lire son manifeste et
son rapport avant transfert. Les sommes finales sont dans `vnext-delivery.json`
et les fichiers `.sha256` externes.

1. Faire `fka pause`, puis `fka save`. Annoncer la maintenance, faire quitter les
   joueurs, `stop`, attendre la fin de Java. Désactiver l'auto-redémarrage du panel.
2. Sauvegarder **toute** l'instance à froid et télécharger le point avec son SHA-256.
   Les scripts appliquent le verrou partagé ; une simple copie à chaud est refusée.
3. Comparer le ZIP au SHA-256 du rapport conservé séparément. Extraire le paquet
   hors de l'instance ; ne pas superposer son dossier `payload/` sans contrôle.
4. Avec Python 3.11+ : `python apply_vnext_update.py --server /chemin/instance`.
   L'outil accepte la révision gameplay `83e721...` ou son propre binaire final,
   vérifie Paper/FK intacts, crée un point complet supplémentaire et copie le JAR,
   son empreinte et les outils de maintenance. Il conserve les données de jeu.
5. Seules les clés config absentes sont ajoutées, dont `respawn-protection-seconds: 5`.
   Les valeurs et clés existantes restent conservées ; `supplies.yml` n'est pas remplacé.
6. `FKAmis.sha256` et l'entrée FKAmis de `RUNTIME_LOCK.json` sont actualisées.
   Conserver le port **22880**, Java **25**, Paper **26.3-244**, mémoire et autres
   paramètres du panel. L'outil ne modifie pas les paramètres d'hébergement.
7. Redémarrer sans `/reload`, accès joueurs encore fermé. Le schéma principal reste
   `schema: 1`, avec extension additive `vnext.version: 1` et statistiques/grâce.
   Les clés inconnues sont conservées. Une version future incompatible refuse le départ.
8. Vérifier `plugins`, versions, logs sans ERROR/SEVERE, `fka status`, `fka config validate`,
   `fka info`, `fka supply status` et `fka admin list`. La reprise reste en pause.
9. Comparer jour, équipes, objectifs, territoires, spawns, inventaires, historique,
   lots consommés/actifs et règles au relevé précédent. Ne pas effacer un état refusé.
10. Exécuter la checklist ci-dessous sur une copie avant d'ouvrir la partie officielle.

Sans Python distant : arrêter depuis le panel, télécharger une copie complète,
appliquer et vérifier localement, puis retransférer uniquement les fichiers ciblés
et la fusion config contrôlée. Mettre à jour les deux registres SHA. Le verrou local
ne prouve jamais l'arrêt de MineStrator : vérifier son état explicitement.

Un temporaire `.new`, `.reset-new` ou `.vnext-new` préexistant demande examen :
les outils refusent de l'écraser. Conserver les fichiers et le point complet ;
ne pas supprimer un journal ou un temporaire au hasard pour forcer le démarrage.

## Retour arrière

Arrêter la nouvelle instance, conserver un point de son état et choisir la sauvegarde
complète prise **avant** mise à jour. Vérifier le SHA-256 externe et restaurer dans
une destination neuve avec `host_ops.py restore`. Restaurer ensemble monde,
inventaires, plugins, règles, progression, ravitaillements et arbitres. Ne pas revenir
au seul ancien JAR après migration. Paper reste 26.3-244 : aucun downgrade de monde.
Démarrer isolé, vérifier le registre, la pause, le jour, les inventaires et coffres,
puis basculer le service humainement. Garder l'autre instance arrêtée.

Une sauvegarde prise juste avant l'application d'un reset contient sa demande et
son candidat. Après restauration complète de ce point, exécuter `host_ops.py reset-cancel`
à froid avant le premier démarrage : seule cette préparation est retirée, la
progression restaurée reste intacte. Ce chemin de retour est aussi testé localement.

## Validation et checklist humaine

Les preuves automatisées se trouvent dans `tests/results/vnext-*.json` : tests
unitaires, événements Paper, formats 1 à 4, matrice de santé physique, sauvegarde,
reset logique, restauration initiale isolée, mise à jour et rollback complet.
Les rapports distinguent assertions techniques, corps NMS et vrais clients.
Les micro-mesures BossBar, index de protection et sérialisation ne constituent pas
un test de charge avec seize personnes. Les TPS/MSPT/RAM locaux à vide décrivent
seulement la copie testée, pas l'hébergement.

- Avec des comptes Java 26.3 authentifiés : squelette naturellement apparu et
  invoqué, santé avant/après, armures, J1/J2/J3, zone neutre et base, respawn.
- PvP réel mêlée/arc/TNT/distributeur : J1 refusé, J2 neutre autorisé et base
  protégée, J3 base autorisée ; arbitre créatif et éliminé spectateur invulnérables.
- Grâce cinq secondes dans les deux sens, reconnexion/TP sans prolongation, PvE actif.
- Captures à plusieurs : BossBar fluide, interruption/remise à zéro, alertes titre/chat/son
  uniquement aux défenseurs, délai anti-spam, annonce globale et crédit des contributeurs.
- Centre, sept monuments, huit sites : limites réelles, coffres accessibles, butins
  consommés inchangés, TNT/creepers/eau/lave/pistons/distributeurs/gravité sans sabotage.
- OP ordinaire, non OP, arbitre UUID et spectateur : permissions attendues, aucun
  secret dans `info`. Tester console, déconnexions et règles verrouillées après départ.
- Morts, lits, inventaires et statistiques sur vrais clients ; bilan/export après victoire.
- Inspecter visuellement la carte et les salles. Les coordonnées proposées ne sont
  pas validées visuellement par l'agent. Approuver séparément toute référence initiale.
- Mesurer TPS/MSPT/RAM/ping sur MineStrator avec 4 à 16 participants et un arbitre,
  dont captures simultanées et lots. Pour 16+1, prévoir la capacité du panel ; aucune
  modification automatique de `max-players` ou de la mémoire n'est effectuée.

La livraison technique ne vaut pas acceptation multijoueur complète de production.
