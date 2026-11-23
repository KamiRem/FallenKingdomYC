# V2.2 — validation finale et préparation d'une partie complète

Ce rapport concerne la préparation locale issue de `ded565d`. **MineStrator reste
en V2.1** : aucune connexion, écriture, commande d'alimentation, modification de
whitelist ni partie distante pendant cette mission. Les démarrages et parties
automatiques décrits ci-dessous utilisent uniquement des copies privées de test.

Les résultats définitifs, empreintes et le verdict sont consignés dans le
[reçu de campagne](../tests/results/v22-final-validation-20261123.json).
Les mondes, journaux, identités synthétiques et archives restent hors Git :
`C:\Users\youne\FKBackups\V22-FINAL-20261123-02`.

**Verdict : GO pour préparer le déploiement et la partie test.** Les validations
locales retenues sont réussies. Cela n'autorise ni transfert ni ouverture de
partie : inspection authentifiée, comptes approuvés, sauvegarde actuelle et
nouveau préflight restent des préconditions. Une partie humaine complète et les
performances de MyBoxPerf 8 à dix-sept connexions restent non validées.

## Périmètre audité et règles conservées

La source est le candidat V2.2 indépendant préparé le 23 novembre, jamais la
recette distante. La restauration géologique et sa provenance sont détaillées
dans [le rapport du terrain](V22_VANILLA_UNDERGROUND_20261123.md).

Sont conservés : Paper 26.3-244, Java 25 / image MineStrator Java 25 Performance,
FallenKingdom officiel inchangé 2.24.9, quatre royaumes Rouge/Bleue/Verte/Jaune,
1 à 4 membres officiels chacun, 16 participants maximum et arbitre indépendant.
Vingt places techniques, whitelist/authentification strictes, jeu et Query 22880,
`restart-on-crash=false`, watchdog actif, vue 8 et simulation 6 restent prévus.

La partie conserve les phases manuelles : J1 préparation, J2 PvP hors bases
protégées et Nether activable, J3 assauts après validation des objectifs. Les
morts individuelles n'éliminent pas une équipe ; la capture de son coffre le fait.
Capture : 60 secondes de ticks continus, rayon 2,5 ; un attaquant pour un roster
solo, deux pour un roster de deux, trois ou quatre. Les absents restent membres
officiels. Défenseur, troisième équipe, distance, mort ou présence insuffisante
interrompent selon les protections existantes. Aucun changement de règle.

Les spawns d'équipe servent au départ et au rassemblement administratif. Après
une mort, lit/ancre Vanilla valide est respecté ; sinon la réapparition utilise
le centre naturel sûr. La grâce de cinq secondes protège contre le PvP, pas contre
les mobs. Un éliminé reste Spectator après mort/reconnexion. Les blocs ordinaires
ennemis ne deviennent pas librement constructibles/minables en J3 : les permissions
de bloc et règles TNT existantes restent appliquées, et l'accès au coffre doit
être réellement inspecté. Les protections des monuments et ravitaillements restent
actives ; le retrait des cavernes ne les désactive pas.

Le code de jeu FKAmis ne lit aucun ancien chantier de cavernes. Il protège les
monuments, ravitaillements, centre et portails enregistrés. Le validateur de
maintenance sélectionne explicitement `mapVersion: 2.2`, `vanilla-restored` et une
liste de cavernes vide ; les exigences V2.1 restent pour les anciennes références.
Le profil `v21-minestrator` garde son nom historique : il décrit les paramètres
d'hébergement, pas une obligation de quatre cavernes.

## Guidage vers sa base : verdict et fonctionnement

**L'indicateur existe et ses paquets ActionBar sont fonctionnels sur Paper local.**
Le calcul tient compte de la position horizontale et du yaw : huit flèches, nom
de sa propre équipe et distance en mètres. Les tests vérifient les huit secteurs,
les rotations au-delà de 360°, les changements de distance et les quatre équipes.
Les paquets NMS sortants sont lus ; aucune coordonnée ni équipe adverse n'y figure.

L'affichage automatique est rafraîchi toutes les deux secondes pendant une partie
active. `/fka base` le demande immédiatement, y compris au jour 0 pour un
participant déjà affecté. En pause, le rafraîchissement automatique est suspendu.
L'arbitre sans équipe et les éliminés n'ont pas de guidage compétitif. Dans le
Nether, un message indique que la direction vers l'Overworld est indisponible ;
aucune flèche interdimensionnelle artificielle n'est produite.

La protection de réapparition utilise prioritairement l'ActionBar ; le guidage
automatique attend son expiration. Les captures utilisent une BossBar ; les
notifications territoriales restent dans le chat. Le guidage est recalculé après
téléportation, réapparition et reconnexion. La Locator Bar Vanilla reste désactivée,
avec portées de transmission/réception de waypoints à zéro.

**Le rendu réel reste à confirmer avec un client authentifié** : lisibilité des
flèches, durée visible, rotation, latence et cohabitation des affichages ne sont
pas prouvées par l'inspection des paquets seule.

## Portail Nether officiel : anomalie corrigée et garanties

La campagne a reproduit un défaut de reprise : `Frame.load()` appelait
`World.getChunkAt(x,z,false)`. Le bytecode du Paper figé montre que cet appel
crée un wrapper `CraftChunk`, sans charger le chunk. Quand les chunks d'un cadre
n'étaient pas déjà chargés, la reprise pouvait annoncer le service ouvert avec
une surface absente, et le retour échouait. Lire les blocs pour diagnostiquer
pouvait masquer ce défaut en les chargeant. Trois tentatives conservées ont
permis de distinguer ce problème d'une perte d'inventaire ou de permissions.

Le correctif charge réellement les seuls chunks préalablement vérifiés comme
déjà générés. Il ne modifie ni les phases ni les autorisations. La désactivation
persiste d'abord l'état fermé, charge les deux cadres et retire leurs surfaces,
y compris sans joueur proche. Aucun ticket permanent ni recherche Vanilla
d'un nouveau portail n'est ajouté. Le nouveau JAR doit remplacer celui de `ded565d`
dans tout futur candidat ; les archives précédentes restent conservées.

Un second défaut a été reproduit sur le JAR intermédiaire : l'autorisation de
voyage était vérifiée avant chargement asynchrone, mais pas juste avant le départ.
Une élimination pendant ce délai permettait encore au spectateur de traverser.
Le callback revérifie maintenant rôle actif/arbitre et mode non Spectator avant
toute téléportation. Une nouvelle assertion reproduit l'élimination entre demande
et callback, constate le refus, puis vérifie qu'un voyage ultérieur autorisé reste
possible. L'OP sans rôle est également testé comme participant actif, et pas
seulement comme compte hors roster. Aucun rôle ou droit de jeu n'est ajouté.

La première campagne `V22-FINAL-20261123-01`, son candidat intermédiaire, ses
archives et l'essai révélant ce défaut restent conservés. La campagne `02`
reprend toutes les suites sur le même nouveau JAR ; seul son candidat est retenu.

Les contrôles portent sur : enregistrement réel d'un cadre visé par l'arbitre,
refus participant/OP, refus d'activation J1, activation J2, blocage des créations
Vanilla `FIRE`/`NETHER_PAIR`, cadre non officiel inutilisable, aller-retour vers les
sorties enregistrées, inventaire conservé, pause/reprise, redémarrage et fermeture.
Les essais existants ajoutent briquet, charge de feu, distributeur, cadre endommagé
et refus des contournements. La plateforme de l'End reste distincte.

Il s'agit d'**une route officielle à deux extrémités**, pas d'un cadre unique
pour les deux dimensions. Les téléportations administratives et le suivi
spectateur validé constituent des outils d'arbitrage distincts, sans autoriser
de portail de jeu supplémentaire.

### Ce que l'arbitre devra faire en jeu

1. **Construire physiquement**, en Creative, un cadre complet d'obsidienne dans
   chaque dimension, coins compris. Intérieur accepté : largeur 2 à 4 et hauteur
   3 à 5. Prévoir le sol et une sortie sûre hors de la surface, sans lave ni
   obstruction. Le cadre Overworld doit être neutre, à moins de 64 blocs du centre,
   hors des volumes protégés. Ne pas inventer une position approuvée : l'inspecter.
2. **Enregistrer** les deux cadres éteints : les viser à six blocs maximum et
   exécuter `/fka nether portal register overworld`, puis
   `/fka nether portal register nether`. L'enregistrement exige l'arbitre en jeu,
   pas seulement OP ; désactiver avant tout remplacement. L'accès technique de
   l'arbitre au Nether pour construire relève de la console/administration,
   pas d'une traversée de participant J1.
3. Contrôler `/fka nether portal status`. L'enregistrement ne signifie pas ouverture.
4. **Activer** à partir de J2, partie active hors pause :
   `/fka nether portal activate`. Le service crée les deux surfaces officielles ;
   ne pas les allumer au briquet. La console accepte status/activate/deactivate.
5. Tester avec deux vrais comptes approuvés l'aller-retour, l'inventaire et la
   sortie ; fermer avec `/fka nether portal deactivate` au moindre problème.

Le candidat propre ne contient aucun cadre de recette ni identité synthétique.
Le portail réellement choisi pour MineStrator reste donc à construire, enregistrer
et inspecter après autorisation, avant son ouverture aux participants.

## Campagne automatique et limites

| Validation retenue | Résultat |
|---|---|
| Java | 60 tests réussis, dont deux nouveaux tests couvrant les huit directions et leurs limites |
| Python | 148 tests réussis, dont trois nouveaux contrôles du confinement de campagne |
| Guidage / permissions / portail / reprise | 90 assertions, deux démarrages |
| Affectations réelles par commandes, seize corps serveur synthétiques | 47 assertions |
| Partie simulée à 1 membre par royaume | 96 assertions, trois démarrages, victoire Rouge |
| Partie simulée à 2 membres par royaume | 102 assertions, trois démarrages, victoire Rouge |
| Partie simulée à 3 membres par royaume | 109 assertions, trois démarrages, victoire Rouge |
| Partie simulée à 4 membres par royaume | 115 assertions, trois démarrages, victoire Rouge |
| Portails, pause, spectateurs et ignitions physiques | 55 assertions, deux démarrages |
| Ravitaillements | 47 assertions, deux démarrages |
| Configuration, statistiques, export et reprise finale | 102 assertions, trois démarrages |
| Notifications/protections territoriales avec le nouveau JAR | 51 assertions, un démarrage |
| Physique PvE/PvP réelle côté serveur | 15 cas, un démarrage |
| Terrain dans Paper | 22 219 états de blocs, 47 chunks chargés sans génération, quatre territoires/spawns |
| Maintenance initiale | 160 SHA, 37 128 cellules naturelles, sept monuments, huit ravitaillements, six inventaires de butin |
| Partie terminée sauvegardée/restaurée puis démarrée | 318 fichiers, J3, 16 membres, trois éliminations et victoire/statistiques conservées |

Soit **814 assertions d'événements/mécanismes et 26 phases Paper réussies retenues**,
en plus des 15 cas physiques, vérifications de terrain et de restauration. Les
essais de diagnostic antérieurs ne sont pas comptés comme réussis dans ce bilan.
Les erreurs des phases retenues sont nulles ; trois WARN de sauvegarde manuelle
sont conservés. Les assertions de capture utilisent les effectifs officiels,
y compris les déconnectés ; elles ne réduisent pas le seuil pour faciliter un test.

La restauration de partie terminée compare **76 régions, 21 847 chunks et
996 emplacements d'inventaire ou butin**, sans ajout/retrait de chunk ni changement
de leurs enregistrements d'inventaire. Sa copie de contrôle et la source restent
identiques. Le démarrage s'effectue sur une seconde copie : 23 fichiers existants
diffèrent ensuite, avec journaux, sauvegardes natives et métadonnées/régions du
monde ; quatre chemins sont créés et le JAR de fixture initial est conservé dans
un autre dossier. Le port Query et la sonde de restauration sont des adaptations
volontaires de cette seule copie, pas des écritures normales attribuées à Paper.
La liste SHA avant/après est privée, dans
`finished-match-boot-file-differences-private.json`.

Ce contrôle est fonctionnel sous Windows. Il ne reproduit pas les ACL, UID/GID
ou autres propriétés Linux de MineStrator. Leur application et les permissions
d'exécution devront être contrôlées pendant la future installation autorisée.
La sauvegarde historique de novembre à dix places n'a pas servi de fixture et
ses archive/manifeste restent inchangés.

Le reçu donne chaque suite, phase, nombre d'assertions, empreinte du JAR, du journal
privé et les avertissements. Les fixtures partent de la vraie V2.2 ; seules leurs
copies reçoivent plateformes, coffres d'objectif, joueurs simulés et états de jeu.
Les simulations de captures avancent les ticks du moteur : elles ne représentent
pas des heures de jeu humain ou un chronomètre de 60 s observé en client.

Les contrôles couvrent les effectifs 1/2/3/4, refus du cinquième, seize affectations
par commande, arbitre hors roster/statistiques, J1/J2/J3, PvE/PvP/protections,
réapparitions, captures contestées, absences/morts/reconnexions, élimination des
quatre membres d'un royaume, victoire et statistiques finales. Les redémarrages
reviennent en pause explicite ; les captures partielles ne reprennent pas.

Les ravitaillements vérifient huit sites, intervalle de 1 800 secondes actives,
deux lots au maximum, absence de rattrapage hors ligne, butins autorisés,
réservation durable unique et blocage entonnoirs/pistons. Les tests physiques
complètent les événements API par IA, projectiles, collisions et santé serveur.

Une première tentative de ravitaillement a terminé ses assertions mais échoué
sur le préfixe de rapport non reconnu par l'ancienne sonde. L'orchestrateur utilise
ensuite son préfixe autorisé dans le nouveau dossier privé ; aucun garde-fou de
la sonde ni fichier historique n'a été changé.

Les WARN de sauvegarde manuelle induits par les commandes de test sont conservés
dans le reçu ; ils ne sont pas masqués. Ils ne prouvent pas un problème de données,
mais les mesures de performance prises pendant ces écritures ne valent pas une
mesure stable. Les avertissements de compilation existants restent distincts.

La première finalisation a également arrêté la livraison sur une incompatibilité
d'encodage de sortie Python sous Windows. Le sous-processus de maintenance utilise
désormais explicitement UTF-8. La copie partielle a été conservée pour diagnostic,
puis une copie neuve a passé les contrôles et été archivée ; aucune validation
refusée n'a été ignorée et les anciennes archives n'ont pas été remplacées.

Les joueurs sont des doubles API ou des corps NMS synthétiques, sans session
Minecraft authentifiée. **Aucune partie humaine ni charge à dix-sept connexions
n'est validée.** Une visite réelle doit encore confirmer terrain, accès naturels,
sécurité des spawns/salles/portails, rendu, interactions et latence.

## Livraison et inspection locale

Le nouveau candidat comprend **309 fichiers gérés**, dont 121 fichiers du monde
strictement identiques à la première V2.2. Ses seules différences sont :
`plugins/FKAmis-1.0.0.jar`, `FKAmis.sha256`, `RUNTIME_LOCK.json` et
`DEPLOYMENT_MANIFEST.json`. Les références de terrain restent les mêmes ; aucun
monument, minerai, spawn, territoire, inventaire, whitelist ou règle n'est retouché.

| Artefact privé | SHA-256 |
|---|---|
| `fallenkingdom-v22-final-candidate-private.zip` | `75b192b294af5a62d966206014efe957ef6ecfe3926e4a1bfe00d2dea2b1e0ea` |
| `FKAmis-v22-final.jar` | `905b0f4b11192d26cd59b82b151525ad3b69f7f1803c65760589800404345ca5` |
| `finished-simulated-match-private.zip` — preuve de test uniquement, jamais une carte à déployer | `6cdf8fc34a48f91d89c8f43234c3c37b16ce997aac30260733a69288b7d1c15a` |

Les ZIP complets ont un manifeste de sauvegarde et une empreinte externe.
`SHA256SUMS.txt` accompagne la livraison. L'ancien candidat et ses cinq artefacts
sont recontrôlés inchangés ; la référence de rollback historique l'est également
pour son archive et son manifeste. Les ZIP de monde/maintenance de la première
V2.2 ne doivent pas être confondus avec les vieux ZIP de construction V2.1.

`visual-inspection/` est une copie propre arrêtée, sans sonde ni joueur synthétique.
Depuis le dépôt, la démarrer volontairement avec :

```powershell
.\.tools\ms-audit\Scripts\python.exe -B scripts/vanilla_delivery.py --work C:\Users\youne\FKBackups\V22-FINAL-20261123-02 --start-inspection
```

Se connecter à `127.0.0.1:25631` avec un compte déjà autorisé. Le jeu et Query sont
loopback seulement ; le candidat reste configuré pour 22880. Le guide privé
`VISITE_V22_PRIVEE.txt` contient les repères ; il ne constitue pas une preuve
d'inspection déjà faite. La whitelist n'est pas étendue. Ne pas lancer de partie
dans cette copie propre sans accord distinct ; une recette destructive exige
une autre copie et son point de restauration. Fermer proprement avec `stop`.

## Déploiement futur : préconditions et séquence

1. Obtenir une autorisation séparée et préparer un nouveau préflight V2.2 lié aux
   nouveaux artefacts. Ne pas réutiliser le plan V2.1 de 148 fichiers. Vérifier
   identité 513365, versions, état arrêté, accès, espace et relances éventuelles.
2. Prendre une sauvegarde **actuelle** complète, à froid, avec verrou partagé ou
   dérogation ponctuelle explicitement approuvée. La restaurer dans un dossier
   distinct et contrôler ses SHA et son fonctionnement. Conserver les précédentes
   sauvegardes et quarantaines, sans remplacer `MS-COLD-20261119-02`.
3. Comparer la recette réelle à V2.1. Intégrer le plan naturel bloc par bloc dans
   une copie actuelle, jamais par écrasement des quatre régions. Toute divergence
   légitime de recette bloque l'intégration automatique. Préserver inventaires,
   NBT, dimensions, accès et états ; aucune fusion avec une autre partie.
4. Faire approuver explicitement le choix de démarrer une **nouvelle partie test
   propre**. Le retour à un état initial est une opération distincte de la seule
   correction des cavernes ; archiver intégralement l'ancienne recette avant cela.
5. Après vérification des vrais comptes et de leur approbation, préparer les
   politiques définitives. Documenter toute différence de whitelist/rôle ; elle
   exige de nouvelles empreintes, pas la modification d'une ancienne preuve.
6. Générer le candidat intégré, son manifeste exact et le plan créer/remplacer/
   conserver/quarantainer, puis simuler le transfert et le rollback localement.
   Contrôler les règles et l'état initial avec les outils V2.2.
7. Après autorisation de bascule : staging, relecture SHA, quarantaine sans
   suppression, activation cohérente carte/JAR/marqueur/registre/traduction,
   démarrage restreint et recette. Surveiller l'API et arrêter immédiatement sur
   démarrage inattendu, divergence, erreur critique ou perte du contrôle.
8. Conserver `restart-on-crash=false`, watchdog, Query 22880 et paramètres panel.
   Contrôler MineBoard en présence de vrais joueurs ; son affichage n'a pas été
   revérifié par cette campagne locale. Aucun lancement de partie automatique.

La bascule doit avoir un rollback vers la sauvegarde **actuelle** de l'étape 2 :
serveur arrêté, tentative V2.2 conservée en quarantaine, restauration de toute
l'instance dans une destination neuve, relecture SHA, contrôle fonctionnel puis
activation autorisée. Aucun retour au seul JAR, aucune fusion d'inventaires.

## Première partie test avec les amis

La [procédure d'identités](MINESTRATOR_RECETTE_ET_WHITELIST_20261120.md) reste
applicable à la vérification nom/UUID et à l'approbation. Ses références aux
cavernes, ancien JAR et manifeste V2.1 ne s'appliquent pas à V2.2. Ne calculer
aucun UUID offline et n'ajouter aucun compte de sonde. Conserver la liste réelle
hors Git ; au maximum seize participants et un arbitre approuvés, sans OP joueur.

Avant départ, après autorisations de déploiement, whitelist et partie test :

```text
fka status
fka config validate
fka info phases
fka admin uuid <compte_connecte_verifie>
fka admin grant <UUID_arbitre_verifie> confirm
fka info teams
fka admin list
```

Vérifier les quatre spawns, limites inclusives 40/exclusives 41 et sous-sols
naturels avec de vrais clients. Des affectations temporaires peuvent servir à
vérifier guidage et `fka teams tpall` ; les retirer ensuite explicitement avec
`fka unassign <pseudo>` avant le scellement initial. Configurer les cadres officiels
éteints avec l'arbitre. Aucune visite automatisée ne remplace cette inspection.

Faire sortir les visiteurs. Arrêter proprement et sceller une **référence initiale
propre de cette partie test**, avec le JAR corrigé, les politiques finales, monde
et inventaires initiaux ; vérifier la restauration. Le validateur initial exige
jour 0, aucun objectif et **roster/membres natifs vides** : ne pas contourner ce
contrôle pour sceller une partie déjà affectée. Ce scellement n'a pas été exécuté
sur MineStrator. Redémarrer restreint, contrôler les empreintes politiques, jour 0
et absence de partie, puis affecter les vrais joueurs connectés :

```text
fka assign <participant_connecte_verifie> <Rouge|Bleue|Verte|Jaune>
fka info teams
fka terrain <equipe_inspectee> confirm
fka teams tpall
```

Chaque équipe doit avoir 1 à 4 membres ; ajuster uniquement avant lancement avec
`unassign` puis `assign`. Répéter la confirmation pour les quatre terrains réellement
inspectés ; tous les participants doivent être connectés. Une sauvegarde complète
supplémentaire du pré-départ affecté peut être conservée séparément de la référence
initiale scellée ; elle ne doit pas être présentée comme ce même état vide.

L'arbitre lance ensuite volontairement `fka start`, sans `override` pour contourner
une précondition. J1 : récolte, construction, protections, PvE, respawns, guidage
et PvP/Nether fermés. Chaque équipe choisit son propre coffre objectif dans son
territoire et l'enregistre en le visant avec `/fka room register`. L'arbitre
inspecte l'accès et valide avec `fka room validate <équipe>` avant J3.

À l'heure décidée par les joueurs, l'arbitre passe J2 avec `fka nextday` ; contrôler
PvP et activer volontairement le portail officiel. Avant J3, les quatre objectifs
doivent être valides. Passer avec `fka nextday`, puis jouer les assauts normaux :
capturer réellement pendant 60 s à portée, contester, tester déconnexion et
élimination sans donner de droits compétitifs aux spectateurs. La dernière équipe
restante gagne. Ne pas utiliser `win` pour présenter cette victoire comme naturelle.

`fka pause`/`resume` servent aux incidents ; `teams tpall confirm` uniquement en
pause avec accord des joueurs, jamais pour changer un combat. Un redémarrage
conserve la progression en pause : contrôler avant `resume`, ne pas lancer
`start` une seconde fois. Ne pas accélérer les phases ou les règles pour présenter
un scénario technique comme une partie normale.

## Performances et collecte des incidents

Paliers humains proposés : repos, quatre participants (un par équipe), huit
(deux par équipe), seize (quatre par équipe), puis seize et l'arbitre. Si le groupe
dispose de moins de comptes, inscrire les autres paliers **non mesurés**. Prévoir
5 minutes au repos puis 3 minutes d'échauffement et 10 à 15 minutes de mesure par
palier, avec déplacements, combats, captures et exploration Nether. Faire les
mesures de charge dans une recette approuvée et restaurable, sans changer les
rosters d'une partie déjà commencée. Une partie normale garde ses effectifs.

Chaque minute : TPS 1/5/15 min, MSPT moyen/p95, heap et limite, RAM processus/
conteneur et marge, compte/temps/pauses GC, ping médian/p95, chunks et entités.
Le [modèle CSV](../tests/results/v22-partie-test-performance-template.csv) est vide,
pas une preuve de mesure. Les valeurs issues des sondes locales ne certifient
pas l'offre MyBoxPerf 8.

En console autorisée, vérifier l'aide disponible puis employer `tps`, `mspt`,
`spark tps`, `spark ping`, `spark health show --memory` et `spark gcmonitor`.
Pour diagnostiquer une charge, `spark profiler start`, puis
`spark profiler stop --save-to-file` pour conserver le résultat localement.
Ces outils sont décrits dans les documentations primaires
[Paper](https://docs.papermc.io/paper/reference/commands/) et
[spark](https://spark.lucko.me/docs/Command-Usage), consultées le 23 novembre.
Leur présence exacte et leurs droits doivent être vérifiés sur le serveur figé ;
aucun profil public n'est téléversé par cette préparation.

Critères de recette proposés : TPS durable ≥19,5, MSPT moyen <40 ms/p95 <50 ms,
pas d'OOM/watchdog, pas de croissance mémoire durable après GC et marge conteneur
d'environ 15 %. Repérer ping p95 >200 ms ou hausse >50 ms par rapport au repos.
Ces seuils ne sont pas une garantie MineStrator ; arrêter le palier suivant en
cas de dégradation et documenter la cause. Ne pas forcer un GC ni augmenter les
allocations panel pour masquer le problème.

Pour chaque anomalie : heure UTC, phase, rôle/mode/équipe, action attendue/réelle,
reproduction, extrait de log et preuve visuelle privés. Protéger les coordonnées
des objectifs, UUID et inventaires ; ne pas les publier dans Git. Sauvegarder
les journaux complets et statistiques JSON/CSV de `plugins/FKAmis/history/`.

## Retour propre après la partie test

Après victoire ou interruption, préserver la partie terminée, ses données,
historiques et journaux par une sauvegarde complète à froid, vérifiée et restaurée.
Ne pas employer un reset logique seul : il ne remet pas les minerais, butins ou
inventaires à leur état initial. Préparer une restauration complète de la
référence initiale approuvée, dans un nouveau dossier, avec contrôles SHA,
politiques, terrain et démarrage isolé avant activation autorisée.

Conserver séparément les résultats de test hors de l'instance propre. Une future
partie officielle exige sa liste d'identités/équipes approuvée et une nouvelle
référence si ses politiques diffèrent. Aucun remplacement de politique ni fusion
des inventaires de test ne doit être automatique. Les sauvegardes V2.1,
`MS-COLD-20261119-02`, les anciennes variantes et quarantaines restent intactes.
