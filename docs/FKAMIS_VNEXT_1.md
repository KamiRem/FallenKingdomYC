# FKAmis VNext.1 et carte V2.1

**Actualisation du 20 novembre 2026 :** [quatre membres par royaume](FOUR_PLAYERS_20261120.md),
effectifs de 1 à 4, nouvelle instance à 20 places et plan de 148 fichiers.
Ce complément remplace le défaut à deux et les artefacts courants décrits plus
bas, conservés comme preuves de la livraison précédente. Le rollback historique
à dix places reste inchangé ; son [essai fonctionnel et le choix Query](MINESTRATOR_QUERY_ROLLBACK_20261120.md)
sont désormais validés localement.

Livraison indépendante de VNext, branche `feature/fkamis-vnext-1-map-v2-1`.
Base : commit `c631fad`, JAR VNext `fd12c43c0f33fa84f4721d49de2c248c7cd1609f0c502403dc8155975ecc0cee`.
Paper 26.3-244, Java 25 et FallenKingdom officiel 2.24.9 restent identiques.
L'hébergement MineStrator n'est pas modifié par l'agent.

## Audit et séparation des opérations

Le code précédent mettait la partie en pause dans `onQuit`, limitait le Nether à
`border-size / 8`, n'ancrait pas tous les déplacements et n'offrait aucun menu de
suivi. Les territoires sont réellement des carrés de rayon 80, inclusifs aux deux
extrémités, avec `VERTICAL_LIMIT=0` : ils s'étendent sur toute la hauteur.
La référence testée utilise une bordure Overworld de 1 200 blocs ; la valeur du
fichier existant reste la source de vérité, sans imposer une autre taille à l'hôte.

Deux opérations distinctes :

- **Mise à jour d'une partie existante** : plugin, outils, rayon 40, propriété
  `allow-flight`. Aucun creusement ni remplissage de coffre.
- **Création V2.1** : construction sur une référence initiale vérifiée, dans une
  nouvelle sortie. Ne jamais transférer cette nouvelle topographie sur une partie jouée.

Les risques principaux sont les affiliations/statistiques persistantes, les
coffres hors du nouveau territoire, les sorties Vanilla de portail, les références
asynchrones après déconnexion et la modification de chunks contenant des entités.
La migration refuse les objectifs incompatibles ; les portails ont des destinations
explicites ; les voyages en attente sont annulés après changement de session ;
la construction refuse les collisions et compare ensuite tous les blocs hors plan.

## Guidage vers sa propre base

**La Locator Bar native reste désactivée.** Le repli proposé dans la mission est
implémenté : une ActionBar discrète affiche la direction relative et la distance
horizontale vers le spawn officiel de sa propre équipe. `/fka base` l'affiche à la demande.
L'indication automatique revient toutes les deux secondes en jeu et laisse la
priorité au message de protection après décès. Elle ne lit aucun coffre objectif.

L'audit du JAR API 26.3-244 et des signatures publiques trouve les portées
`WAYPOINT_TRANSMIT_RANGE` / `WAYPOINT_RECEIVE_RANGE` et le style/couleur d'une entité,
mais aucune API publique de point fixe filtrable par destinataire. La documentation
[LivingEntity](https://jd.papermc.io/paper/26.3/org/bukkit/entity/LivingEntity.html)
décrit ces styles d'entité. Les portées seules ne constituent pas un filtre d'équipe.
Des paquets NMS ou une entité invisible auraient ajouté une dépendance interne ou
une surface de fuite ; ils ne sont pas employés en production.

Les deux portées des joueurs sont mises à zéro, leurs valeurs originales conservées
puis restaurées au départ/arrêt. Aucun marqueur d'adversaire, autre base ou objectif,
aucune entité ajoutée, aucun ticket de chunk pour le guidage. Déplacer un adversaire
ne change pas le texte envoyé. Dans le Nether et l'End, le message précise que la
direction interdimensionnelle est indisponible. Les éliminés n'ont pas ce guidage.
Les commandes natives de waypoint/attribut/gamerule/worldborder sont réservées à
la console, comme les autres modifications avancées susceptibles de contourner les règles.

La sonde inspecte les textes réellement envoyés à des corps NMS synthétiques et
les attributs de confidentialité ; **le rendu sur un vrai client reste à contrôler**.

## Quatre cavernes V2.1

Référence d'entrée : `dist/fallenkingdom-preproduction-26.3.zip`, SHA-256
`8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de`.
Les sorties de construction sont des copies distinctes. Une archive avec profils
joueurs, roster, objectifs déclarés ou partie commencée est refusée. Une autre
référence exige une approbation initiale scellée et ses empreintes.

| Royaume | Thème | Sol Y | Profondeur sous base | Marches | Entrées | Distance horizontale accès/base |
|---|---|---:|---:|---:|---:|---:|
| Rouge | Basalte, roche, terre cuite rouge, sans lave | 69 | 42 | 43 | 1 | 36,88 blocs |
| Bleue | Calcite et améthyste | 22 | 42 | 43 | 1 | 36,88 blocs |
| Verte | Mousse, terre racinée et feuillage persistant | 21 | 42 | 41 | 1 | 36,88 blocs |
| Jaune | Tuf, calcite et ambiance minière | 26 | 42 | 41 | 1 | 36,88 blocs |

Le relief Rouge est beaucoup plus haut : comparer la profondeur **relative** évite
de lui imposer un escalier deux fois plus long. Le budget artificiel est identique :
24 minerais de charbon, 24 de fer, 16 de cuivre, 12 de redstone, 6 de lapis, 6 d'or
et 3 de diamant par caverne. Aucun netherite, coffre de récompense ni recharge de butin.
Ce budget ne prétend pas égaliser tous les minerais naturels du reste du monde.

Les volumes sont comparables, avec moins de 2 % d'écart de circulation entre les
deux accès de 43 marches et ceux de 41. Deux accès sont réfléchis pour préserver
les animaux de la référence. Une coque fermée évite un tunnel direct vers une
cavité voisine ; les volumes restent à au moins dix blocs de la limite du territoire.
Pas de lave, magma, feu ou trou vertical artificiel ; éclairage identique dans les
quatre salles. La fondation autour de chaque drapeau et le relief proche du spawn
font partie des volumes interdits au chantier.

L'outil `map_v21_tool.py` effectue un aperçu par défaut, avec rapport des collisions,
volumes, ressources et chunks. Exemple depuis le dépôt :

```text
python scripts/map_v21_tool.py --input dist/fallenkingdom-preproduction-26.3.zip --sha256 8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de --output .cache/vn1/runtime/map-v21-apercu --initial-reference
```

Pour construire : choisir **une autre sortie vide** `map-v21-*`, ajouter `--apply`
et, hors du dépôt, fournir `--plugin`, `--builder`, `--reference`, `--java` et les
bibliothèques Paper existantes via `--dependencies` si nécessaire. Le paquet de
construction contient ces outils et un exemple de commande adapté à son arborescence.
Le serveur d'outil écoute seulement sur loopback. Le constructeur est retiré après
usage et n'entre jamais dans le JAR de jeu.

Avant écriture : sauvegarde complète à froid sous verrou, validation de chaque
matériau source, absence de collision avec block entities/entités/volumes techniques.
Après écriture : comparaison des états de blocs, biomes, inventaires et positions
d'entités, connexité des accès, quatre spawns et coins des territoires. Les différences
de compteurs d'exécution des vaults et l'explicitation de la vitesse normale des fours
sont détaillées ; ni butin ni liste de joueurs récompensés n'est ignoré par le contrôle.
Les règles de croissance et de temps temporairement suspendues sont restaurées.

La nouvelle référence `maintenance/new-match-reference-v2.1.json` permet de contrôler
aussi les cavernes lors du scellement initial. Ne pas sceller une référence contenant
des minerais déjà extraits. **Aucune appréciation esthétique ni validation visuelle
n'est acquise** : inspecter les quatre accès, plafonds, éclairages et thèmes en jeu.

## Territoires de rayon 40

Les centres, spawns et drapeaux restent aux mêmes coordonnées. Les carrés ne se
chevauchent pas. Rayon 80 → 40 signifie côté géométrique 160 → 80 et aire
25 600 → 6 400 : **la surface est divisée par quatre**. Avec des coordonnées de blocs
inclusives, les colonnes discrètes passent de 161² à 81², soit 25 921 → 6 561.

Les protections de construction, minage, fluides, pistons et combat interrogent
toujours les bases natives ; aucune deuxième carte de territoires n'est créée.
La protection verticale reste complète, y compris dans les cavernes. Les phases
PvP J2 et assauts J3, les seuils de capture et les gardes des objectifs restent ceux
de VNext. Un objectif ou son espace minimal de capture hors du nouveau carré
fait **refuser toute la migration**. L'opérateur doit examiner la salle et intervenir
humainement ; aucun coffre n'est déplacé automatiquement.

## Spectateurs

`/fka spectate` ouvre un menu privé ; `/fka spectate <pseudo>` rejoint une position
sûre déjà chargée près d'un participant vivant en SURVIVAL. La cible est revérifiée
au clic. Pas de cible hors ligne, éliminée, arbitre ou dans une dimension fermée.
Une position sans sol sûr, dans un liquide, un bloc ou hors bordure est refusée.

Seuls les éliminés officiels en SPECTATOR et les arbitres UUID y ont accès. Les
participants actifs et visiteurs sont refusés, même OP. Aucun changement d'équipe,
retour SURVIVAL, restauration d'inventaire ou crédit compétitif. Les vrais coffres
restent fermés aux spectateurs ; seule l'interface privée bénéficie d'une exception
ciblée, sans lever les annulations d'autres plugins. La sélection Vanilla d'une
caméra est également limitée aux joueurs actifs autorisés.

Les interfaces sont fermées à la pause/fin et leurs références retirées au départ.
Un spectateur ne se déplace pas pendant une pause ; l'arbitre conserve l'inspection.

## Déconnexions, flight et pause

Une déconnexion ne déclenche plus de pause et ne remet plus toutes les captures
à zéro. Le roster officiel ne diminue pas. Deux membres officiels exigeant deux
attaquants continuent d'en exiger deux ; les autres tentatives continuent selon
leurs présences réelles. Les compteurs de ravitaillement suivent le temps actif,
même sans participant connecté ; le profil existant désactive déjà la pause
Vanilla à serveur vide. Les pauses manuelles restent prioritaires.

Pas de pénalité anti-combat-log ajoutée : départ et retour Vanilla, inventaire
persistant, aucune grâce de respawn sur une simple reconnexion. Une ancienne
partie interrompue redémarre toujours en pause, sans reprise automatique.

`allow-flight=true` devient le défaut des modèles et la seule propriété serveur
modifiée par l'installateur. Un redémarrage est requis. Cette option évite le kick
Vanilla de vol ; elle n'accorde ni vol ni CREATIVE à un participant et ne retire pas
un éventuel anti-cheat. Arbitres CREATIVE et éliminés SPECTATOR gardent leur politique.

En pause, tous les non-arbitres sont ancrés, spectateurs compris : XYZ, gravité,
vélocité, véhicules, projectiles, téléportations ordinaires, interactions et combat
sont bloqués. La caméra spectateur attachée est détachée. L'orientation du regard
reste libre ; aucune tâche ne retéléporte les joueurs en permanence. Respawn et
reconnexion rétablissent l'ancrage. À la reprise ou à l'arrêt, les propriétés
temporaires sont nettoyées. Un repositionnement administratif explicite via le
rassemblement autorisé reste possible et actualise l'ancre.

## Portail Nether unique

Deux cadres d'obsidienne officiels sont enregistrés, un dans chaque dimension.
Leurs intérieurs mesurent 2 à 4 blocs de large et 3 à 5 de haut. L'Overworld doit
être neutre, près du centre, distinct des monuments/ravitaillements/centre protégé.
L'emplacement exact et les chemins depuis les quatre royaumes demandent une
**validation humaine**. Aucune coordonnée proposée n'est réputée inspectée visuellement.

Arbitre en jeu, viser le cadre complet à six blocs maximum :

```text
/fka nether portal register overworld
/fka nether portal register nether
/fka nether portal status
/fka nether portal activate
/fka nether portal deactivate
```

`status`, `activate` et `deactivate` acceptent aussi la console. L'enregistrement
nécessite une désactivation préalable et une sortie sûre hors du portail. Une
activation exige les deux cadres, une partie active et l'ouverture du Nether.
J1 : fermé. J2+ : activable par l'arbitre. Pause : surfaces et voyages suspendus ;
reprise : activation administrative conservée si les cadres sont intacts.

Les créations Vanilla `FIRE` et `NETHER_PAIR` sont annulées. Briquet, charge de feu,
distributeur et ignition indirecte ne peuvent donc créer d'autre route. L'obsidienne
décorative reste autorisée. La plateforme normale de l'End n'est pas bloquée par
cette règle. Les surfaces officielles sont posées par le service, sans recherche
Vanilla à l'arrivée, avec création de portail automatique désactivée.

Chaque traversée autorisée rejoint la sortie fixe sûre de l'autre cadre ; les
retours ne multiplient pas les portails Overworld. Les contournements interdimensionnels
par perle et les déplacements non autorisés sont refusés. Les téléportations
administratives et le suivi spectateur validé restent distincts. L'inventaire suit
le joueur sans copie de récompense ; les véhicules, objets et autres entités ne
franchissent pas cette route. Un bref délai évite les boucles.

Les contrôles sont revérifiés après chargement asynchrone de quelques chunks
**déjà générés**, sans ticket permanent. Départ, changement de session, pause ou
sortie obstruée annulent un voyage en attente. Un cadre cassé désactive les routes
et demande réparation/réactivation de l'arbitre ; aucune sortie de secours n'est
générée ailleurs. Les coordonnées sont persistées dans l'état, pas annoncées au public.

La bordure Overworld garde sa taille configurée. Le Nether utilise la limite
technique de 59 999 968 blocs de diamètre, sans pré-génération de cet espace.
L'exploration normale génère seulement les chunks nécessaires aux joueurs. Les
spectateurs ne génèrent plus de nouveaux chunks. Les distances de vue/simulation
et la mémoire du panel restent inchangées ; mesurer le coût réel avant expansion.

## Installation MineStrator et migration

1. Fermer l'accès, `fka pause`, `fka save`, `stop`. Attendre la fin de Java et
   désactiver l'auto-redémarrage pendant la maintenance.
2. Sauvegarder **l'instance entière à froid**, avec le verrou commun et les verrous
   natifs. Télécharger l'archive et son SHA-256 sur un stockage privé séparé.
3. Vérifier le SHA-256 externe du ZIP VNext.1, extraire hors de l'instance.
4. `python apply_vnext1_update.py --server /chemin/instance`. L'outil vérifie VNext
   `fd12c43c...`, Paper et FK intacts, puis examine les quatre territoires et objectifs
   avant toute écriture. Une incompatibilité exige une intervention humaine.
5. L'outil prend une nouvelle sauvegarde complète, remplace le JAR et les outils,
   fusionne les seuls défauts config absents, réduit les quatre rayons et ajoute
   `allow-flight=true`. Il ne construit aucune caverne. UUID, inventaires, objectifs,
   statistiques, historique, rôles et ravitaillements restent conservés.
6. `FKAmis.sha256` et `RUNTIME_LOCK.json` sont actualisés. Garder le port **22880**,
   Java **25**, Paper **26.3-244** et les paramètres du panel. Ne pas faire `/reload`.
7. Redémarrer isolé. Le schéma principal reste 1 ; l'extension `vnext.version` passe
   de 1 à **2**, avec les portails dans `vnext1.nether`. Les inconnus sont conservés,
   une extension future est refusée. Un ancien VNext refuse ce nouvel état.
8. Vérifier logs, `plugins`, `fka status`, `fka config validate`, `fka admin list`,
   `fka info`, `fka supply status`, `fka nether portal status`, rayons et salles.
   Comparer inventaires et historiques. Reprendre manuellement seulement après contrôle.

Le JAR seul ne réalise pas la réduction des territoires : utiliser l'installateur
contrôlé. Sans Python sur l'hôte, appliquer la migration sur une copie complète
téléchargée à froid, vérifier les différences puis transférer les seuls fichiers
autorisés. Un verrou local ne prouve pas l'arrêt du serveur distant.

Pour une **nouvelle partie V2.1**, construire et inspecter la sortie distincte,
puis sceller cette référence avec le fichier de référence V2.1. Ne pas remplacer
le monde d'une partie existante par cette sortie. Aucun compte de test ne doit être
ajouté à la whitelist officielle ; les copies de recette restent privées et isolées.

## Rollback et recette humaine

Arrêter VNext.1, sauvegarder son état, vérifier l'empreinte du point précédant
l'opération et restaurer **toute l'instance dans un dossier neuf** : mondes,
dimensions, joueurs, JAR, configurations, progression, portails, historique et lots.
Vérifier l'ancien registre et le rayon 80 avant démarrage isolé. Un retour au seul
JAR VNext laisserait un état incompatible. Aucun downgrade de Paper.
Après restauration d'un point pris juste avant reset, annuler sa demande à froid
avec `host_ops.py reset-cancel` avant le démarrage, sans modifier la progression.

Les rapports `tests/results/vnext1-*.json` distinguent événements techniques, corps
NMS et clients authentifiés. Restent indispensables avec des humains Java 26.3 :

- Rendu et confidentialité de l'ActionBar, rotation, mort, reconnexion et dimensions.
- Inspection des quatre cavernes : accès, lumière, plafonds, circulation et thèmes.
- Quatre limites de territoires et salles existantes ; aucune coordonnée secrète publique.
- Spectateur : menu, clic, cible déconnectée/morte, dimensions, coffres et pause.
- Combat/déconnexion et capture à plusieurs, sans diminution du seuil officiel.
- Pause en nage, saut, vol, véhicule et sous latence ; reprise sans blocage résiduel.
- Portails au briquet/charge/distributeur/lave, J1/J2/J3, aller-retour, mort/reconnexion,
  redémarrage, destruction accidentelle et tentative de sortie hors bordure.
- TPS/MSPT/RAM/ping sur MineStrator avec 4 à 16 participants et l'arbitre, exploration
  Nether et captures simultanées. Les mesures locales ne certifient pas cette charge.

Aucun test avec comptes authentifiés ni inspection visuelle n'est prétendu exécuté
sans preuve. Les sauvegardes et mondes restent exclus de Git.

## Résultats de livraison

| Vérification locale | Résultat et portée |
|---|---|
| Tests unitaires | 51 Java et 43 Python réussis |
| Régressions Paper | 11 suites, dont les quatre formats de 1 à 4 membres par royaume |
| Dégâts physiques | 15 cas : squelettes, zombie, creeper, PvP J1/J2/J3, distributeur, grâce, arbitre et spectateur |
| Nouveaux services | 52 assertions puis 3 au redémarrage ; jusqu'à 9 corps NMS, zéro client authentifié |
| Migration et rollback | VNext → VNext.1, inconnus conservés, objectif hors 40 refusé sans écriture, rollback complet comparé puis démarré |
| Inventaire | Profil NMS avec 7 pains conservé à la migration et au retour à la sauvegarde entière |
| Réinitialisations | Reset logique, politiques différentes refusées, restauration initiale complète et retour avant reset |
| Carte | Quatre accès reliés, quatre spawns sûrs, 37 128 positions planifiées sur 47 chunks existants ; aucun chunk ajouté |
| Références | Restauration V2.1 et retour VNext/V2 comparés au manifeste complet puis démarrés |
| Outil autonome | Même plan depuis les seuls fichiers livrés ; maintenance et référence de cavernes vérifiées |
| Refus au démarrage | Extension future 3 et reset confirmé en attente : arrêt, état et politiques inchangés |

Les refus volontaires produisent le message d'erreur attendu de FKAmis. L'arrêt
précoce peut aussi produire `zip file closed` depuis le chargeur du plugin officiel ;
ce cas est enregistré dans le rapport de refus. Les démarrages réussis de migration,
rollback et restauration ne présentent aucune erreur ERROR/SEVERE.

Au repos après 30 secondes, la copie locale mesure 20 TPS, environ 0,3 ms de tick
moyen sur cinq secondes et 514 Mio de tas utilisé. Les micro-mesures avec réflexion
portent sur les mouvements actifs/en pause, l'ActionBar, les deux portails ouverts
et les protections ; elles n'ajoutent aucun chunk. Les TPS de la sonde incluent ses
constructions et son démarrage : ils ne représentent pas une charge stable. Les
valeurs détaillées sont dans `tests/results/vnext1-performance.json`.

Artefacts privés, sans monde ni profil joueur :

- `dist/vnext1/FKAmis-1.0.0.jar` : plugin indépendant de production.
- `dist/fallenkingdom-vnext1-update.zip` : installateur contrôlé, payload et guides.
- `dist/fallenkingdom-map-v2.1-build.zip` : outil autonome, constructeur séparé,
  plugin, registre de blocs et référence initiale ; nécessite l'archive source privée.
- `tests/results/vnext1-delivery.json` : rapport global, preuves et SHA-256 des artefacts.
- Fichiers `.zip.sha256` et `.jar.sha256` adjacents : empreintes externes à vérifier.

SHA-256 du JAR VNext.1 :
`46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442`.
Les deux ZIP ont leurs empreintes définitives dans le rapport global et leurs sidecars.
Paper et FallenKingdom officiel conservent les SHA-256 de `configs/artifacts.lock.json`.

La sortie locale finale pour inspection de la construction autonome est
`.cache/vn1/runtime/map-v21-portable-3`. Elle reste une copie de recette, sans
validation visuelle ni autorisation de la transférer sur une partie existante.
Le port et les propriétés de sa référence sont restaurés après l'écoute technique
sur localhost ; seul `allow-flight` est ajusté. Les rôles et politiques d'une future
partie doivent être fixés avant de sceller sa référence initiale inspectée.
