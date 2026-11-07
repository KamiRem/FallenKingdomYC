# Visite de la carte v2 — coordonnées réellement placées

La visite de la variante corrigée utilise `runtime/map-v2-fixes`. Les coordonnées
ci-dessous sont conservées. Inspecter les quatre cœurs et lisières jusqu'à 88 blocs
des centres : fleurs/herbes en suspension, plantes à deux blocs, feuillages, troncs
conservés et végétation suspendue valide. Vérifier les drapeaux et les décorations
des monuments après nettoyage. Voir [le bilan](V2_CORRECTIONS.md).

Ce carnet provient de `maps/v2/built-manifest.json`, écrit par Paper après le chantier.
La présence technique des blocs est testée ; **l'inspection visuelle et l'équilibre à huit joueurs restent à valider**.
Aucune capture d'écran Minecraft n'a été réalisée. Les coordonnées ci-dessous sont publiques ; aucun objectif secret n'est défini.

## Ouvrir la candidate

```powershell
.\scripts\server.ps1 start -Name map-v2-fixes -Port 25579
```

Se connecter avec Minecraft Java 26.2 à `127.0.0.1:25579`. Depuis la console :
`whitelist add PseudoArbitre`, puis `op PseudoArbitre`. Avant toute partie, passer l'arbitre
en créatif avec `/gamemode creative`. Les vues aériennes ci-dessous supposent le vol créatif activé.
Ne pas lancer la partie pendant cette visite. Préférer une copie supplémentaire pour tester les commandes de butin.
Pour rassembler les participants avant départ : `/fka teams tpall`. Après départ,
mettre en pause et utiliser `/fka teams tpall confirm`. Tester avec huit vrais comptes,
dont un spectateur et un déconnecté lors des variantes de recette ; ne pas valider ces
essais sur la seule base des interfaces Player de test automatisé.

## Terrains et drapeaux

| Royaume | Centre X/Z | Pied du mât Y | Téléportation au spawn vérifié |
|---|---|---|---|
| Rouge | -240 / -240 | 113 | `/tp @s -246.5 112 -239.5` |
| Bleue | 200 / -200 | 66 | `/tp @s 193.5 65 -199.5` |
| Verte | -200 / 240 | 65 | `/tp @s -206.5 64 240.5` |
| Jaune | 280 / 200 | 70 | `/tp @s 273.5 69 200.5` |

Chaque territoire a un rayon carré de 80 blocs. Inspecter tout le périmètre, pas seulement le spawn :
surface de construction, transitions de pente, arbres, accès aux grottes et bois, eau, absence de fort vanilla donnant un avantage.
Les mâts font neuf blocs, sans effet sur les captures. Aucun château d'équipe n'a été ajouté.

Voisins : Rouge–Bleue 442, Rouge–Verte 482, Bleue–Jaune 408, Verte–Jaune 482 blocs à vol d'oiseau.
Diagonales : Rouge–Jaune 681 et Bleue–Verte 595. Chronométrer au moins deux parcours à pied entre voisins.

## Monuments

Les téléportations aériennes permettent d'observer l'intégration avant de descendre en vol créatif.

| Lieu | Ancrage X Y Z | Vue aérienne |
|---|---|---|
| cercle-des-quatre-vents | 80 68 -48 | `/tp @s 80 86 -48` |
| temple-des-racines | -80 105 -352 | `/tp @s -80 123 -352` |
| mine-des-brumes | 360 70 0 | `/tp @s 360 88 0` |
| tour-des-vents | 40 70 350 | `/tp @s 40 88 350` |
| camp-des-eclaireurs | -320 71 48 | `/tp @s -320 89 48` |
| sanctuaire-des-sources | 40 66 175 | `/tp @s 40 84 175` |
| crypte-des-veilleurs | -80 70 -223 | `/tp @s -80 88 -223` |

Entrée de la crypte : `/tp @s -80 73 -198` en vol créatif.
Descendre l'escalier à pied ; vérifier la hauteur libre, les marches, l'absence d'eau et les deux squelettes persistants.
Vérifier l'échelle de la tour, la galerie de mine, les six coffres fixes et leurs petits lots avant toute exploration officielle.
Le cercle central n'a pas de coffre. Les butins fixes ne se régénèrent pas.

## Ravitaillements

Les coffres physiques restent vides : les lots sont virtuels et remis au clic droit pendant la partie active.
Le profil livré refuse `/fka supply test confirm`. Vérifier les chemins d'accès et le support sous chaque coffre.

| Site | Zone | Bloc coffre X Y Z | Vue en vol |
|---|---|---|---|
| supply-1 | Carrefour nord-ouest | -100 67 -100 | `/tp @s -100 71 -100` |
| supply-2 | Carrefour nord-est | 140 65 -100 | `/tp @s 140 69 -100` |
| supply-3 | Carrefour sud-ouest | -100 70 100 | `/tp @s -100 74 100` |
| supply-4 | Carrefour sud-est | 60 71 100 | `/tp @s 60 75 100` |
| supply-5 | Lisière nord | 0 80 -480 | `/tp @s 0 84 -480` |
| supply-6 | Crête est | 400 64 0 | `/tp @s 400 68 0` |
| supply-7 | Vallon sud | 0 73 480 | `/tp @s 0 77 480` |
| supply-8 | Bois ouest | -520 74 0 | `/tp @s -520 78 0` |

## Paysage et fin de visite

- lac : `/tp @s 0 107 265` en vol créatif.
- cascade_rocaille : `/tp @s 24 81 175` en vol créatif.

Inspecter les passerelles et leurs piliers, les rives, les arbres autour des sentiers et les éventuelles ruptures de pente.
Comparer les ressources accessibles autour des quatre terrains ; les minerais profonds n'ont pas été rééquilibrés artificiellement.
Faire ensuite la recette multijoueur de `TEST_PLAN.md` : huit comptes authentifiés, captures, protections, inventaire plein, pause et reprise.
Mesurer TPS/MSPT avec les huit joueurs répartis sur la carte ; les mesures automatisées sans joueurs ne suffisent pas.

Après inspection seulement : `/fka terrain Rouge confirm`, `/fka terrain Bleue confirm`,
`/fka terrain Verte confirm`, `/fka terrain Jaune confirm`. Retirer OP aux participants avant lancement.
Sauvegarder puis exporter l'installation complète arrêtée. Conserver `runtime/local` et l'archive initiale.
