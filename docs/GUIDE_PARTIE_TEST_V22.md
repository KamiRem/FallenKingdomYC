# Partie test Fallen Kingdom V2.2 — guide pratique

**Procédure préparée, aucune commande distante exécutée.** Attendre la bascule
V2.2 et les autorisations explicites de whitelist, préparation des cadres et
lancement de partie. MineStrator est encore en V2.1 au moment du préflight.
Le [rapport préalable](MINESTRATOR_V22_PREFLIGHT_20261123.md) contient les réserves.

Les commandes de jeu ci-dessous s'emploient dans la console MineBoard, sans `/`.
En client, préfixer les commandes par `/`. Les commandes Python sont réservées
au PC et aux copies complètes locales, comme indiqué dans leurs paragraphes.
Remplacer les paramètres `<…>` par des données vérifiées ; aucun pseudo, UUID
ni emplacement n'est inventé ici.

## 1. Choisir le groupe disponible

Quatre équipes non vides, **1 à 4 membres chacune**, soit **4 à 16 participants**.
L'arbitre reste hors effectifs. Quatre, cinq, six ou huit participants conviennent ;
les effectifs n'ont pas besoin d'être tous égaux. Répartir aussi équitablement que
possible avec l'accord des joueurs. Moins de quatre participants ne permet pas
de conserver les quatre équipes exigées : attendre des joueurs supplémentaires,
sans joueur synthétique ou modification cachée des règles.

La capacité technique 20 ne donne pas de droit d'accès aux inconnus. Désigner un
arbitre indépendant ; s'il utilise un compte en jeu, ce compte s'ajoute aux
participants. Les paliers 16/17 ne sont pas imposés à la première partie.

## 2. Identités et whitelist, après approbation

Recueillir le nom Java actuel et vérifier nom ↔ UUID auprès du service officiel,
puis faire approuver la liste et les rôles. Ne jamais calculer un UUID offline,
utiliser une identité de bot ou demander un mot de passe/jeton Microsoft.
Conserver la liste hors Git. Revoir les deux comptes existants sans les supprimer
automatiquement. Garder `online-mode`, whitelist et enforcement activés.

```text
whitelist on
whitelist add <nom_Java_verifie_et_approuve>
whitelist list
```

Contrôler l'UUID écrit dans la whitelist ; au premier login authentifié :

```text
fka admin uuid <nom_connecte_verifie>
```

Cette commande ne confère aucun rôle. La source des identités et leur approbation
ne sont pas remplacées par le seul contenu de `usercache.json`.

## 3. Désigner l'arbitre et préparer la référence initiale

La gestion du rôle se fait dans la console, pas via OP seul :

```text
fka admin grant <UUID_arbitre_verifie> confirm
fka admin list
fka status
fka config validate
fka info teams
fka info phases
```

L'arbitre ne doit pas être affecté à une équipe. Pour corriger une erreur avant
partie, retirer d'abord le joueur du roster avec `fka unassign <nom>`, puis
attribuer le rôle. Ne pas retirer les anciens rôles sans décision explicite.

Avant le scellement initial, inspecter les quatre bases/spawns/rayons et les
sous-sols naturels, sans consommer les butins. Les affectations temporaires de
visite doivent être retirées avant le scellement. Vérifier l'état de départ des
inventaires ; le profil de recette existant est celui d'un arbitre. Sa conservation
ne doit pas devenir un apport compétitif à une équipe. Aucune remise à zéro
d'inventaire n'est implicite.

Après autorisation, préparer les cadres éteints (§5), puis arrêter proprement et
sceller une référence initiale complète **avant les affectations définitives** :
J0, roster/membres natifs vides, aucun objectif, bonnes politiques, JAR et terrain
approuvés. Depuis le PC, pour une copie locale complète déjà contrôlée :

```text
python -B <instance_complete>/maintenance/host_ops.py check
python -B <instance_complete>/maintenance/host_ops.py verify-baseline
python -B <instance_complete>/maintenance/host_ops.py seal-initial --archive <dossier_prive_hors_instance>/initial-test-v22.zip --approve-initial --reference <instance_complete>/maintenance/new-match-reference-v2.2.json
```

Ces commandes ne sont pas exécutées par cette préparation. Elles exigent la
bonne copie complète, les contrôles réussis et l'approbation de la référence ;
ne pas les lancer sur le payload partiel. La politique MineStrator est déclarée
par le manifeste (profil de capacité/Query nommé historiquement `v21-minestrator`).
Sceller les politiques finales après tout changement approuvé de whitelist/rôle,
pas en modifiant une ancienne archive. Restaurer et tester une autre copie locale.

## 4. Affecter et contrôler les équipes, avant départ

Tous les participants définitifs doivent être connectés et non OP. Après accord
sur les comptes concernés :

```text
deop <participant_approuve>
fka assign <participant_connecte> Rouge
fka assign <participant_connecte> Bleue
fka assign <participant_connecte> Verte
fka assign <participant_connecte> Jaune
fka info teams
```

Répéter seulement pour les joueurs réels disponibles. Pour déplacer quelqu'un :

```text
fka unassign <nom>
fka assign <nom_connecte> <equipe>
```

Un cinquième membre est refusé. Les effectifs sont verrouillés après départ ;
une déconnexion ne retire pas le joueur officiel. Les nouveaux comptes non affectés
ne deviennent pas compétiteurs au milieu de la partie.

Après inspection réelle, répéter pour les quatre équipes :

```text
fka terrain Rouge confirm
fka terrain Bleue confirm
fka terrain Verte confirm
fka terrain Jaune confirm
fka teams tpall
```

Le rassemblement contrôle les spawns et exclut l'arbitre. Vérifier visuellement
sol, espace et absence de danger, puis parcourir les limites 40/41. La commande
`fka spawn <equipe>` **modifie** le spawn : ne pas l'utiliser comme lecture.
L'arbitre peut rejoindre un participant avec la console :

```text
minecraft:tp <arbitre> <participant>
```

Tester `/fka base` pour chaque équipe. L'ActionBar automatique s'affiche pendant
la partie active, toutes les deux secondes ; avant départ, la commande permet
la vérification. Aucun guidage compétitif pour l'arbitre hors roster ou les éliminés.

## 5. Portail Nether officiel : construire, enregistrer, activer

Choisir et inspecter deux emplacements sûrs : un Overworld neutre à moins de
64 blocs du centre, hors centre/monuments/ravitaillements protégés, et un Nether.
Pas de coordonnées proposées comme déjà validées. L'arbitre construit en Creative
un cadre complet, **coins compris**. Intérieur 2–4 de largeur et 3–5 de hauteur ;
le petit cadre complet fait 4 × 5 à l'extérieur. Prévoir sortie et sol sûrs,
hors surface, sans lave ni obstruction. Ne pas allumer au briquet.

Pour atteindre une position Nether déjà inspectée avec le seul compte arbitre,
la console peut employer, après autorisation de cette préparation :

```text
minecraft:execute in minecraft:the_nether run minecraft:tp <arbitre> <X_valide> <Y_valide> <Z_valide>
```

Cette téléportation administrative ne constitue pas un accès de participant J1.
L'enregistrement exige l'arbitre **en jeu**, en visant chaque cadre à six blocs
maximum ; exécuter depuis son client dans la bonne dimension :

```text
/fka nether portal register overworld
/fka nether portal register nether
/fka nether portal status
```

Construire ne fait qu'ajouter l'obsidienne. Enregistrer associe les cadres et leurs
sorties, sans ouvrir le voyage. **Activer n'est possible qu'à partir de J2**, partie
active hors pause et deux cadres valides :

```text
fka nether portal activate
fka nether portal status
fka nether portal deactivate
```

Status/activation/désactivation acceptent aussi la console. Désactiver avant tout
remplacement de cadre. Les briquets, charges, distributeurs ou cadres supplémentaires
ne créent pas de route de jeu ; OP seul n'est pas arbitre. Les téléportations
d'arbitrage et le suivi spectateur autorisé restent des outils distincts.

Contrôler l'aller-retour avec de vrais participants, inventaires et sorties,
sur un protocole restaurable approuvé. Un redémarrage reprend en pause ; les
associations et l'activation administrative persistent, mais pas l'ouverture
automatique avant reprise. Un cadre endommagé ou une sortie dangereuse ferme le service.

## 6. J1, J2, J3 : lancer et jouer normalement

Contrôles pré-départ : quatre équipes non vides, tous les participants connectés,
pas d'OP joueur, spawns sûrs, terrains confirmés, référence initiale complète
vérifiée, état J0 et absence de partie déjà commencée. Ne pas utiliser `override`
pour faire disparaître une erreur de préparation.

```text
fka start
fka status
```

J1 : récolte, construction et exploration normales selon les protections,
PvP et Nether fermés. Chaque équipe place un coffre simple dans son territoire,
avec accès réellement praticable pour des attaquants. Pendant J1/J2, un membre
vise son propre coffre à cinq blocs maximum et lance depuis son client :

```text
/fka room register
```

L'arbitre inspecte en privé, puis valide chaque objectif :

```text
fka room inspect Rouge
fka room validate Rouge
fka room inspect Bleue
fka room validate Bleue
fka room inspect Verte
fka room validate Verte
fka room inspect Jaune
fka room validate Jaune
```

Ne pas publier les coordonnées de ces commandes dans le chat de partie ou Git.
Prévoir sol stable, espace debout et approche au même étage, dans la portée de
capture. Les murs ou un autre étage ne doivent pas permettre une capture à travers.
Une validation automatique ne remplace pas l'inspection de l'accès.

Les jours sont **manuels** : décider des durées avec les joueurs avant départ.
Au moment convenu :

```text
fka nextday
fka status
```

Premier passage : J2, PvP hors royaumes protégés et activation Nether possible.
Après vérification des quatre objectifs, répéter pour J3 : assauts ouverts.
Ne pas accélérer les règles pour présenter une simulation comme une partie normale.

Une capture exige 60 s de ticks continus à portée 2,5 blocs selon la géométrie
existante. Équipe attaquante officiellement solo : un présent ; effectif officiel
2/3/4 : deux présents. Les déconnectés restent comptés. Un défenseur ou une
troisième équipe conteste ; distance, mort et présence insuffisante interrompent.
Une capture élimine toute l'équipe, y compris ses absents à leur retour ; les morts
ordinaires n'éliminent pas. La dernière équipe restante gagne automatiquement.

## 7. Pauses, incidents, reconnexions

```text
fka pause
fka status
fka nether portal status
fka config validate
fka resume
```

Contrôler la cause avant `resume`. Le portail est suspendu pendant la pause.
En partie déjà commencée, `fka teams tpall confirm` n'est autorisé qu'en pause
administrative ; ne pas s'en servir pour modifier un combat. Les captures partielles
sont abandonnées en pause/redémarrage. Les reconnectés gardent équipe et rôle,
sans nouvelle grâce de respawn accordée par simple reconnexion.

Un boot conserve la progression en pause : contrôler avant reprise, **ne pas
relancer `fka start`**. En cas d'erreur critique de données, arrêter selon le
protocole autorisé et préserver les journaux ; ne pas éditer des YAML à chaud,
forcer `win`, supprimer un profil, reset ou changer les règles pour continuer.

La mort sans lit/ancre valide renvoie au centre naturel sûr ; un lit/ancre valide
reste respecté. La grâce PvP de cinq secondes ne protège pas contre les mobs.
Un éliminé reste Spectator ; `/fka spectate [nom]` suit les cibles actives selon
les restrictions existantes, sans réintégration ni manipulation d'inventaire.

## 8. Mesures et résultats

Mesurer le groupe réellement connecté : repos, 4, 8, 16 puis arbitre si disponibles.
Ne pas modifier les effectifs d'une partie commencée pour fabriquer des paliers.
Un groupe plus petit produit un résultat valide pour ce groupe, pas pour 17 connexions.
À cinq ou six joueurs, relever ce palier réel et noter les paliers supérieurs
comme non mesurés ; aucun faux compte ne complète les effectifs.

Depuis la console autorisée, après vérification de l'aide de la version :

```text
tps
mspt
spark tps
spark ping
spark health show --memory
spark gcmonitor
spark profiler start
spark profiler stop --save-to-file
```

Conserver les profils en privé, sans téléversement par défaut. Relever à la minute
TPS, MSPT moyen/p95, RAM JVM/conteneur, compte/temps/pauses GC et ping médian/p95 ;
noter chunks, entités et scènes. Utiliser le
[CSV de mesure](../tests/results/v22-partie-test-performance-template.csv).
Voir les détails et sources [Paper/spark](V22_VALIDATION_FINALE_ET_PARTIE_TEST_20261123.md).

Après victoire naturelle :

```text
fka status
fka stats match
fka stats leaderboard
fka stats team Rouge
fka stats team Bleue
fka stats team Verte
fka stats team Jaune
fka save
```

Il n'existe pas de commande `fka stats export` : les fichiers `result.json`,
`result.csv` et `result-teams.csv` sont exportés **automatiquement à la fin** sous
`plugins/FKAmis/history/<matchId>/`. La commande `save` en ligne n'est pas une
sauvegarde complète à froid. Conserver logs, audit arbitre, statistiques et preuves
visuelles privées, avec heure/phase/attendu/observé pour chaque incident.

## 9. Sauvegarder la partie puis restaurer le départ

Après autorisation : sortie des joueurs, arrêt propre, contrôle API arrêté et
verrou partagé ou dérogation approuvée. Sauvegarder **toute l'instance terminée**
dans un nouveau dossier hors instance/Git, relire les SHA et restaurer/valider une
copie. Le périmètre doit être recalculé après l'exploration et les nouveaux profils.
Conserver cette archive, les résultats et les précédentes quarantaines.

Pour revenir à la référence initiale scellée : autorisation spécifique, destination
neuve, restauration complète et SHA, contrôle des politiques, inventaires et terrain,
démarrage isolé d'une autre copie puis activation contrôlée. Ne pas fusionner
inventaires de test et inventaires initiaux. Un simple reset logique ne remet
pas les minerais, butins ou inventaires en état de départ.

Le workflow de maintenance existant peut préparer une demande après fin/pause :

```text
fka reset prepare
fka reset confirm <jeton_affiche_et_approuve>
```

Cette confirmation arrête le serveur et crée une demande de maintenance à froid ;
**ne pas l'exécuter sans l'autorisation de retour propre**. Sur une copie complète
locale à froid, avec le jeton correspondant et l'archive initiale approuvée :

```text
python -B <instance_complete>/maintenance/host_ops.py restore-initial --token <jeton> --archive <dossier_prive>/initial-test-v22.zip --destination <dossier_neuf_distinct> --reference <instance_complete>/maintenance/new-match-reference-v2.2.json
```

Si les politiques ou le JAR ont changé depuis le scellement, l'outil doit refuser ;
ne pas contourner ce contrôle. Revoir une référence adaptée avec approbation.
Respecter le délai du jeton affiché ; un refus pour expiration ou contexte modifié
doit être traité par le protocole autorisé, jamais par édition manuelle de la demande.
Une partie officielle future conserve ses propres approbations, comptes et
sauvegardes ; rien ne démarre automatiquement après restauration.
