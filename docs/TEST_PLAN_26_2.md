# Tests et recette

## Corrections de la v2 — 7 novembre 2026

Candidate : `runtime/map-v2-fixes`. Les deux sources `local` et `map-v2` sont
conservées. Le nettoyage a retiré 6 547 blocs naturels invalides, avec comptage par
type/zone, comparaison des monuments et drapeaux et dernier passage à zéro.
Voir `tests/results/v2-fixes-cleanup-total.json`.

```powershell
.\scripts\build.ps1 -Corrections -MapV2 -Probe
python -m unittest discover -s tests -v
python -u scripts/gameplay_probe.py --name probe-v2-fixes-recette-neuve
python -u scripts/map_v2.py verify --name map-v2-fixes
python -u scripts/map_v2_qa.py --source map-v2-fixes --name map-v2-qa-fixes-recette-neuve
```

La suite Java comprend maintenant **19 tests**, dont six politiques supplémentaires :
PvE pendant toutes les phases, PvP J2 hors base, friendly fire, pause/élimination,
minage adverse permanent et rassemblement confirmé. Les **12 tests Python** restent
réussis. La recette existante des phases a aussi passé 23 contrôles et 5 au redémarrage
sur `probe-v2-fixes-regression` avec le JAR corrigé.

`v2-fixes-gameplay.json` décrit la recette des listeners Paper/FallenKingdom/FKAmis :
fleurs/herbes/buissons flottants, feuilles orphelines, arbre et plante suspendue valides,
idempotence ; zombie, flèche de squelette, creeper naturel, environnement J1 ; attaques
attribuées et pièges identifiés ; PvP J2/J3 et friendly fire ; casse adverse des trois
jours, casse propriétaire, **véritables explosions** sans brèche J1/J2 et avec brèche J3,
coffre objectif préservé ; objets et pommes ordinaires ; destinations, permissions,
déconnectés, sans équipe, spectateurs, pause, spawn invalide et annulation externe.

Les huit `Player` de cette recette sont des **interfaces de fixture**, jamais des
comptes connectés. Les annulations passent par la chaîne réelle des listeners, mais
le mouvement réseau, les inventaires d'un véritable client et la santé d'un joueur
authentifié restent à tester. Les blocs, mobs et explosions sont réels dans la copie
de recette. Un marqueur SUCCESS accompagné d'une ERROR n'est pas accepté par le script.

| Contrôle final des corrections | Résultat |
|---|---|
| Gameplay sur `probe-v2-fixes-8` | 112 contrôles, zéro ERROR/SEVERE ; aucun client authentifié |
| Monde corrigé après redémarrage | 22 contrôles ; 21 aménagements préexistants conservés ; six butins fixes exacts |
| Ravitaillements avec tickets partagés | 42 contrôles initiaux, puis 6 dans la restauration complète |
| Mesures ravitaillement initial / restauration | 19,77 / 19,93 TPS ; 0,80 / 0,82 ms par tick ; zéro joueur, attente de 200 ticks |
| Sources conservées | local : 268 fichiers identiques ; map-v2 : 278 identiques |
| Archive de la candidate | 284 fichiers, manifeste et SHA-256 vérifiés ; `v2-fixes-delivery.json` |

Incidents conservés : première copie de nettoyage interrompue après une passe,
restaurée depuis la sauvegarde initiale sous le nom de livraison ; hauteur de balayage
corrigée pour inclure les fleurs ; chunks de téléportation désormais retenus jusqu'au
transfert. Les premières interfaces de fixture manquaient `getEyeLocation` et leur
retrait provoquait une résolution de profils sur le thread de jeu ; ces problèmes
de recette sont corrigés. Les journaux des essais ne sont pas déclarés sans erreur.
Le contrôle des plans a également relevé 21 différences déjà présentes dans les
escaliers de la source. Leur origine n'est pas déduite : elles sont consignées par
lecture des régions, puis préservées et vérifiées au lieu d'être reconstruites.

À faire en jeu : visite visuelle du nettoyage, huit comptes authentifiés, dégâts
réels et morts PvE, inventaires pleins/curseur lors du rassemblement, combat/siège et
captures complètes. Voir [V2_CORRECTIONS.md](V2_CORRECTIONS.md) et le carnet de visite.

## Refonte v2 — recette du 7 novembre 2026

La candidate est `runtime/map-v2` ; les tests de ravitaillement modifient uniquement
sa copie `runtime/map-v2-qa-final`. Aucun compte authentifié n'est simulé comme preuve
de test multijoueur. Les compteurs sont accélérés par la recette technique, pas par
une modification du profil livré de 1 800 secondes.

```powershell
.\scripts\build.ps1 -MapV2 -Probe
python -m unittest discover -s tests -v
python -u scripts/map_v2.py verify
python -u scripts/map_v2_qa.py --name map-v2-qa-final
python scripts/map_v2_delivery.py
```

Ne pas réexécuter la recette sur une copie ayant déjà servi : son état de test a été
conservé pour examen. Choisir un nouveau nom commençant par `map-v2-qa`.

Les 13 tests Java couvrent les 7 règles antérieures et 6 tests de ravitaillement :
1 800 secondes actives, gel avant partie/pause/victoire/sans participant, compteur
conservé, 100 000 catégories tirées, plafonds sur 10 000 événements, catalogue interdit.
Les 12 tests Python de sauvegarde/restauration restent réussis.

| Contrôle v2 exécuté | Résultat |
|---|---|
| Monde réel après redémarrage | 21 contrôles réussis, dont drapeaux, surfaces centrales, sept monuments et six butins fixes exacts |
| Ravitaillements sur Paper | 42 contrôles initiaux réussis ; état de partie simulé, événements API, aucun client |
| Après restauration complète à froid | 6 contrôles réussis ; lot réservé non réattribuable, lot actif et minuteur conservés |
| Mesure initiale / reprise | 19,93 / 19,85 TPS ; 0,83 / 1,17 ms par tick ; 0 joueur, attente de 200 ticks par phase |
| Journaux finaux monde et deux phases de ravitaillement | Chargement des deux plugins confirmé, aucune ERROR/SEVERE ; avertissement Paper ancien toujours présent |
| Conservation de local | 268 fichiers comparés, tous identiques à l'empreinte initiale |
| Export privé de la candidate | 277 fichiers, manifeste interne et SHA-256 vérifiés ; `map-v2-delivery.json` |

Les rapports réels sont `tests/results/map-v2-world.json`, `map-v2-supply-initial.json`,
`map-v2-supply-restart.json`, `map-v2-supply-restoration.json` et `map-v2-preservation.json`.
La phase de redémarrage utilise une restauration complète à froid dans un nouveau
dossier, avec un lot déjà réservé et un autre actif. Les mesures TPS/MSPT y sont
explicitement associées au nombre de joueurs et à la durée ; elles ne prouvent pas
une charge à huit joueurs. La recette existante des phases a également été exécutée
sur `runtime/probe-v2-regression` : 23 contrôles initiaux et 5 au redémarrage réussis.
Le code de capture n'a pas été modifié.

Incidents de chantier corrigés et conservés : un sondage synchrone initial a dépassé
le watchdog ; le chargement est désormais asynchrone et les opérations de chantier
découpées. La première construction plaçait plusieurs lieux dans des dépressions
proches de l'eau ; elle est conservée sous `runtime/map-v2-build-1`, puis remplacée
comme candidate par un nouveau chantier sur des points secs mesurés. Aucun monde
n'a été supprimé. Les journaux finaux sont contrôlés séparément de ces essais.
Le contrôle renforcé du contenu a ensuite détecté que l'actualisation d'un état de
coffre effaçait le lot ajouté à son inventaire réel : l'écriture utilise désormais
l'inventaire du snapshot avant `update`. Les six coffres encore vides ont fait
l'objet d'une réparation ciblée après sauvegarde, sans reconstruire le terrain.

Restent à exécuter avec clients : inspection esthétique, ressources et temps de trajet,
entrée réelle de la crypte et échelle de la tour, clic droit sur lots, double clic,
inventaire plein, déconnexion pendant attribution, permissions de joueurs non OP,
assauts/captures et TPS/MSPT à huit joueurs. Le carnet `MAP_V2_INSPECTION.md` fournit
les vraies téléportations et la liste des vérifications. Les confirmations de terrain
restent décochées jusqu'à cette inspection.

Les résultats de ce document concernent les commandes réellement exécutées. Les
contrôles de code, tests unitaires, événements déclenchés sur serveur et essais de
vrais joueurs sont distingués. Une compilation ne prouve pas la sécurité de tous
les événements multijoueurs.

## Automatisation disponible

```powershell
.\scripts\build.ps1
python -m unittest discover -s tests -v

# Sur une instance neuve dédiée, après acceptation explicite de son EULA :
.\scripts\server.ps1 install -Name smoke
.\scripts\server.ps1 accept-eula -Name smoke -Accept
python -u scripts/smoke_test.py --pregen

# Plugin de recette séparé ; ne jamais l'installer sur la partie :
.\scripts\build.ps1 -Probe
.\scripts\server.ps1 install -Name probe
.\scripts\server.ps1 accept-eula -Name probe -Accept
python -u scripts/probe_test.py
```

Le smoke test écoute sur `127.0.0.1:25575`, la recette technique sur `127.0.0.1:25576`.
Ils conservent `online-mode=true`, whitelist et EULA explicite. Aucun faux compte
offline n'est créé. Le JAR `FKRuntimeProbe` provient des sources de test et n'est pas
inclus dans le JAR FKAmis distribué. Les petites salles de fixture de `runtime/probe`
ne doivent jamais être transférées comme carte de la partie.

## Résultats exécutés le 6 novembre 2026

| Contrôle | Résultat observé |
|---|---|
| Résolution API Paper exacte et compilation Java 25 | Réussie |
| Tests unitaires Java | 7 réussis : limites d'effectif, dérogation explicite, progression, objectifs avant assauts, victoire, capture continue et interruptions |
| Tests Python maintenance | 12 réussis : restauration octet pour octet, empreintes, chemins dangereux, liens, verrou interprocessus, verrou Minecraft, refus d'écrasement, EULA explicite, manifeste complet, collisions de casse Windows et flux NTFS |
| Recette sur Paper réel | 23 contrôles initiaux et 5 au redémarrage réussis : phases, inventaires, commandes console, pause, victoire, visibilité du coffre et persistance ; `tests/results/probe.json` |
| Vérification des phases natives | Jour 1 fermé ; jour 2 PvP/Nether ouverts et assauts fermés ; jour 3 refusé sans objectifs puis ouvert avec quatre objectifs de fixture validés |
| Objets interdits sur API réelle | Débris, lingots et modèle retirés ; diamants conservés ; shulker et bundle filtrés sans supprimer leur contenu autorisé ; transfert d'entonnoir interdit |
| Pause/reprise sur API réelle | Gel puis dégel du tick confirmé |
| Élimination/victoire sur API réelle | Deux éliminations sans victoire ; troisième donnant la victoire à Verte ; fichier atomique vérifié |
| Redémarrage de l'instance de recette | Jour, vainqueur, trois éliminations conservés, partie gelée, reprise d'une partie finie refusée |
| Premiers démarrages serveur | Erreur d'horloge Nether découverte puis corrigée ; chargement des deux plugins confirmé après correction |
| Sélection de graine | Première graine rejetée après mesure ; six graines supplémentaires sondées, 216 points réels, graine 123456789 retenue ; voir `maps/seed-survey.csv` |
| Prégénération naturelle 1 800 × 1 800 | Terminée sur la graine 123456789 : 13 689 chunks demandés, fin de tâche confirmée, sauvegarde et restauration réussies ; `tests/results/pregeneration.json` |
| Démarrage final du JAR livré | Bonne graine confirmée par commande native ; 14 contrôles smoke réussis, journal final sans ERROR/SEVERE, serveur arrêté ; `tests/results/smoke.json` |
| Journaux de génération | Une erreur upstream de sculk a été observée, décrite ci-dessous ; le journal n'est pas déclaré sans erreur |
| Clients authentifiés / huit joueurs | Non exécuté : comptes et joueurs indisponibles dans cette session |

Preuves locales : rapports JSON dans `tests/results`, rapports JUnit dans
`plugins-custom/fk-amis/target/surefire-reports`, journaux dans les instances `runtime`.
Les logs bruts sont exclus de Git pour éviter de publier des données de joueurs.

## Incident de génération observé

Sur la carte finale, **27 messages ERROR** ont été relevés ; les 27 concernent ce
défaut précis de génération du sculk. La prégénération s'est terminée. Le redémarrage
final du même monde, après installation du dernier JAR, ne contient aucune ERROR/SEVERE.
Les deux résultats sont conservés séparément, sans effacer le bilan de génération.

Paper 26.2 build 135 a journalisé `Detected unsafe terrain read during worldgen`
avec `minecraft:sculk_patch_deep_dark`. Le serveur a continué son exécution. Le
[signalement officiel Paper #13995](https://github.com/PaperMC/Paper/issues/13995)
décrit le même défaut vanilla, sans exception interrompant le code. Cela n'atteste
pas l'absence d'irrégularités locales : inspecter les zones générées avant recette.
Le contrôle `check-logs` continue volontairement à échouer sur un tel journal.
Ne pas masquer ces lignes ni déclarer l'ensemble « sans erreur ».

La migration vers une branche Paper maintenue est à réévaluer après une publication
compatible de FallenKingdom et une nouvelle recette, sans rétrograder les mondes.

## Recette multijoueur obligatoire avant partie officielle

Préparer huit comptes officiels, quatre terrains inspectés, une copie de sauvegarde
et un arbitre en console. Remplir les résultats dans un carnet privé ; garder les
positions des objectifs hors de Git et hors des captures d'écran publiques.

| Domaine | Actions à tester | Attendu | État |
|---|---|---|---|
| Équipes | Attribuer huit comptes, essayer un troisième, retirer/réattribuer avant départ | Deux maximum, bonnes couleurs et composition persistante | À exécuter avec clients |
| Apparitions | Démarrer, mourir dans chaque équipe | Terrain sûr et point propre à l'équipe | À exécuter |
| Départ | Essayer un départ incomplet puis avec huit comptes non OP | Refus puis départ ; override uniquement explicite | Garde logique testée, clients à exécuter |
| Carte | Parcourir bordure et territoires sur toute hauteur | 1 800 blocs ; aucun fort donné ; terrains et ressources comparables | Inspection humaine requise |
| Construction | Construire/creuser dans sa base, poser hors base | Liberté propriétaire, restrictions FK documentées ailleurs | À exécuter |
| Protection J1/J2 | Casser, poser, TNT, lits, ancres, coffres doubles, minecarts et cadres adverses | Aucun vol ni sabotage avant assauts | À exécuter |
| Contournements | Pistons depuis les deux côtés, seaux, flèches enflammées, entonnoirs, distributeurs, arbres/bonemeal | Pas d'accès indirect ni déplacement d'objectif | À exécuter |
| PvP J1/J2 | Mêlée, arc, arbalète, trident, potions, nuages et animaux apprivoisés | J1 interdit ; J2 seulement terrain neutre ; friendly fire interdit | À exécuter |
| Confidentialité | Depuis chaque équipe : commandes /fk, alias/namespaces, tabulation, scoreboard et messages | Aucune position de salle adverse ; centre général de base public autorisé | À exécuter |
| Salle | Déclarer hors territoire, dans une salle sans place, puis une vraie salle cachée | Refus des cas invalides ; inspection privée pour l'accès légal | Contrôle technique testé sur fixture, usage joueur à exécuter |
| Capture | Deux attaquants même équipe, défenseur, troisième équipe, sortie rapide, mort et déconnexion | 60 secondes continues ; interruption et remise à zéro ; une seule élimination | Horloge unitaire testée ; capture réelle à exécuter |
| Pause | Ouvrir inventaire puis pause, jet/ramassage, craft/forge, faim, projectiles, redstone, mobs | Aucun gameplay influant sur le résultat ; reprise sans duplication | Gel API testé, scénarios clients à exécuter |
| Dimensions | Portail/téléportation/chorus, reconnexion depuis dimension fermée, retour Nether | Fermetures appliquées à toutes les voies ; aucune sortie de bordure | Caps API testés ; scénarios clients à exécuter |
| Netherite | Miner, exploser, craft, forge, commande console, loot, échange, créatif, offhand, équipement, shulker, bundle | Objets interdits inutilisables/retirés, contenu autorisé conservé | Inventaires imbriqués/transfert testés ; parcours complet à exécuter |
| Élimination | Capturer une équipe puis reconnexion de ses deux membres | Spectateurs, aucune interaction, état conservé | État testé ; modes clients à exécuter |
| Victoire | Capturer trois royaumes | Un seul vainqueur annoncé et partie gelée | Logique et API testées ; capture réelle à exécuter |
| Persistance | Remplir coffres/inventaires, pause, arrêt, redémarrage | Monde/objets/équipes/jour/objectifs identiques, reprise explicite | État logique testé ; inventaires réels à exécuter |
| Restauration | Restaurer une archive complète sous un autre nom/port | Même état cohérent, original conservé | Fichiers testés ; recette d'une partie peuplée à exécuter |
| Performance | Huit joueurs explorant et combattant sur monde prégénéré | TPS proches de 20 et MSPT stables, pas de saturation mémoire | À mesurer chez l'hébergeur |

## Opérations manuelles restantes

1. Inspecter réellement les quatre terrains et les structures ; ajuster ou changer
   la graine dans une nouvelle instance si nécessaire. Définir territoires et apparitions.
2. Ajouter les huit pseudos réels à la whitelist, connecter et attribuer les comptes.
3. Valider les salles construites par les équipes avant le jour 3.
4. Effectuer la recette ci-dessus avec clients authentifiés et corriger tout défaut observé.
5. Choisir/commander l'hébergement selon son total TTC et sa disponibilité Europe ; aucun achat effectué.
6. Transférer le paquet privé, tester les sauvegardes du panel, puis autoriser le lancement officiel.
