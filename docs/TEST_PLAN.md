# Tests et recette

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
