# Corrections gameplay et nettoyage de la v2

La variante corrigée se trouve dans **`runtime/map-v2-fixes`**. `runtime/local` et
`runtime/map-v2` sont conservés. Le JAR officiel FallenKingdom 2.24.9 reste intact ;
les corrections portent sur FKAmis et un outil de nettoyage séparé.

Archive privée vérifiée : `dist/fallenkingdom-map-v2-fixes-20261107T023228Z.zip`
(369 577 744 octets, 284 fichiers). SHA-256 :
`ca112b60e94751ae1c2c96bb64270cadd32c747ade760db30f538b07bd442713`.
Le bilan `tests/results/v2-fixes-delivery.json` confirme que les **268 fichiers de
local et 278 fichiers de map-v2 sont inchangés**. La partie corrigée reste au jour 0,
sans objectif déclaré et avec les validations de terrain encore vides.

## Nettoyage sans reconstruction

Une sauvegarde complète de la v2 a été vérifiée avant sa copie :
`backups/map-v2/fk-20261107T013518704466Z.zip`. L'outil ne rappelle ni la terraformation,
ni les fonctions de construction des monuments, ni le remplissage des coffres.
Il refuse un monde ayant commencé sa partie ou contenant des objectifs déclarés.

Le balayage couvre les quatre cœurs, les transitions jusqu'à 88 blocs des centres,
les sentiers et leurs lisières, les rives, les abords des monuments et des supports.
Il utilise la hauteur `WORLD_SURFACE`, qui inclut les plantes sans collision.
`TerrainCleanup` sélectionne les plantes via les tags Minecraft et un catalogue
complémentaire de végétation 26.2, puis interroge le support réel du bloc.
Les plantes bisectées exigent deux moitiés cohérentes et un support valide.

Les feuilles naturelles doivent rejoindre, à six faces et sur six blocs au maximum,
un tronc relié à un bloc solide. Les grands cas ambigus ou débordant des chunks chargés
sont conservés. Les troncs ne sont pas supprimés et les feuilles décoratives persistantes
sont préservées. Les blocs exacts des plans de monuments sont exclus du nettoyage.
La source contenait déjà **21 différences** avec les plans initiaux, dans les escaliers
de mine et de crypte. Elles ont été lues directement dans les régions, consignées dans
`maps/v2-corrections/preexisting-differences.json` et conservées. La vérification compare
ces positions à la source, afin de ne pas annuler des aménagements préexistants.
Les mâts, laines et socles ne font pas partie du catalogue naturel supprimable.

Le travail est découpé sur plusieurs ticks après chargement asynchrone sans génération.
Les suppressions n'émettent aucun drop et n'appliquent pas de physique en chaîne.
Une passe complète sans modification termine le traitement. Les empreintes des
monuments, drapeaux et contenus des coffres sont comparées avant/après.
Les rapports `tests/results/v2-fixes-cleanup*.json` donnent les nombres par matériau
et par zone ; le bilan cumulé figure dans `v2-fixes-cleanup-total.json`.

**6 547 blocs naturels invalides ont été retirés** : notamment 3 431 feuilles,
1 223 pétales roses, 791 herbes courtes, 775 litières de feuilles et 153 blocs
d'herbe haute. Le dernier balayage couvre 186 149 colonnes et termine par une passe
à zéro modification. Aucun tronc ni drapeau n'a été supprimé ; les butins fixes des
monuments sont préservés, sans régénération.

```powershell
# Seulement pour une nouvelle copie, refuse de remplacer l'existante :
python scripts/map_v2_fixes.py prepare
.\scripts\build.ps1 -Corrections
# Sauvegarde puis nettoyage ponctuel, sans renouvellement du butin :
python -u scripts/map_v2_fixes.py clean
```

Le constructeur de terrain existant appelle également ce contrôle de supports après
ses futurs chantiers. Il n'a pas été réexécuté pour corriger cette carte.
La première copie interrompue est conservée sous `runtime/map-v2-fixes-interrupted-1`
pour diagnostic ; elle n'est pas la livraison. Le premier calcul synchrone de zones
a provoqué un avertissement watchdog ; ce calcul se fait désormais hors du thread de jeu.

## Dégâts et protections

| Source / phase | Jour 1 | Jour 2 | Jour 3+ |
|---|---|---|---|
| Joueur contre adversaire | Refusé | Autorisé hors royaumes protégés | Autorisé |
| Joueur contre coéquipier | Refusé | Refusé | Refusé |
| Mob hostile, creeper naturel, chute, noyade, faim, feu/lave naturels | Actif | Actif | Actif |
| Casse directe d'un bloc de base adverse, TNT comprise | Refusée | Refusée | Refusée |
| Explosion contre une défense adverse | Défense protégée | Défense protégée | Brèche possible |
| Destruction du coffre objectif | Refusée | Refusée | Refusée |

La difficulté reste normale. Les restrictions de pause et de spectateur restent
actives. Un joueur peut combattre les mobs hostiles, même dans une base protégée.
Les distributeurs restent fermés avant les assauts conformément aux protections
existantes. Les extractions par pistons à travers les limites territoriales restent
interdites après le jour 3 ; endermen et withers ne deviennent pas des outils de minage.

FKAmis ne bloque plus une catégorie entière comme `FIRE`, `LAVA`, `POISON` ou
`ENTITY_EXPLOSION` au seul motif que le jour vaut 1. Il consulte la source Paper,
les tireurs de projectiles, propriétaires d'animaux apprivoisés, TNT, nuages et objets
explicitement attribués à un joueur. Les potions nocives attribuées respectent les
restrictions PvP ; les soins restent possibles.

Les blocs dangereux, liquides posés et blocs solides posés sont attribués dans les
données persistantes du chunk. L'attribution suit les écoulements de liquide, le feu,
les TNT amorcées et les entités concernées. Les creepers allumés volontairement et les
cristaux posés/frappés par un joueur sont attribués ; un creeper naturel ne l'est pas.
Une noyade ou suffocation n'est reliée à un joueur que si le bloc exact est identifié.
La suppression du support exact sous un joueur peut attribuer la chute pendant dix
secondes de ticks du monde. Le feu conserve son auteur pendant sa combustion ; son
horloge reste gelée en pause et arrêt. Aucune attribution ne vient de la simple proximité
d'un joueur. Les pièges qui échappent à une attribution fiable restent interdits par
le règlement et doivent être vérifiés pendant la recette avec clients.

Ces comportements s'appuient sur l'API [DamageSource Paper 26.2](https://jd.papermc.io/paper/26.2/org/bukkit/damage/DamageSource.html)
et sur la source d'[EntityPotionEffectEvent](https://jd.papermc.io/paper/26.2/org/bukkit/event/entity/EntityPotionEffectEvent.html).
Les listeners natifs ont été examinés dans le tag FallenKingdom 2.24.9 déjà présent
dans le cache source. Les nouveaux listeners annulent les actions interdites sans
réautoriser un événement annulé par un autre composant.

## Objets interdits

Le filtre `ItemBan` existant reçoit, via la configuration de la copie :

```yaml
ban-netherite-family: true
extra-banned: [ELYTRA, ENCHANTED_GOLDEN_APPLE]
```

`GOLDEN_APPLE` reste autorisée. Le catalogue netherite demeure interdit. Inventaires,
équipement, loot, conteneurs imbriqués, ramassage, recettes, commandes et transferts
continuent d'utiliser le même filtre. Le vol en élytre et l'équipement par distributeur
ont aussi un garde immédiat. Les tables de ravitaillement refusaient déjà ces objets ;
les six lots fixes de monuments n'en contiennent aucun.

Les profils livrés sont dans `configs/map-v2-fixes/`. Les fichiers des deux anciennes
instances ne sont pas migrés en place.

## Rassemblement administrateur

```text
/fka teams tpall
/fka teams tpall confirm
```

Permission : `fkamis.admin`, console ou administrateur. Avant le début de partie,
la première forme suffit. Après le début, la partie doit être en pause et `confirm`
est obligatoire. La commande refuse une partie active ou terminée.

Les joueurs connectés, vivants, encore participants et non spectateurs rejoignent
le spawn enregistré de leur équipe. Déconnectés, sans équipe et éliminés sont ignorés.
Aucune coordonnée n'est codée en dur. Les quatre destinations sont contrôlées avant
le premier transfert : monde, territoire, bordure, coordonnées finies, chunks chargés,
volume entier du joueur libre et sol portant non dangereux. Les chunks voisins requis
par ce volume sont chargés aussi. Un spawn invalide annule tout le lot.
Le yaw/pitch enregistré est utilisé ; la vitesse et la distance de chute sont remises
à zéro uniquement après un transfert réussi.

Les chunks sont retenus pendant l'opération, puis libérés. `ChunkLeases` partage les
tickets avec le ravitaillement pour qu'un service ne décharge pas les chunks de l'autre.
Les équipes et inventaires ne sont pas réécrits. Les opérations et refus sont journalisés.

FallenKingdom refuse les téléportations survival en pause profonde. Le transfert
autorisé utilise une exemption synchrone limitée au joueur, à la destination enregistrée
et à la cause `PLUGIN`, avec passage temporaire en spectateur puis restauration du mode
dans `finally`. Aucun tick de monde n'est dégelé, aucune phase n'est reprise et aucun
joueur éliminé n'entre dans ce chemin. Les téléportations ordinaires restent refusées
en pause. Toute autre annulation de listener est respectée.

## Recette et visite humaine

Les six nouveaux tests Java de politique couvrent les phases, le PvE, le friendly
fire, le minage et les conditions de rassemblement. La recette Paper distincte crée
des mobs et de véritables explosions ; ses événements visant des joueurs utilisent
des interfaces `Player` de fixture, **pas des comptes connectés**.
Les résultats détaillés figurent dans `tests/results/v2-fixes-gameplay.json` et
[TEST_PLAN.md](TEST_PLAN.md). Les essais avec huit comptes authentifiés restent requis.

Résultats finaux : **19 tests Java, 12 tests Python, 112 contrôles gameplay sur API
Paper et 22 contrôles du monde réussis**. Les 21 différences préexistantes sont toutes
conservées. La recette de ravitaillement passe 42 contrôles initiaux et 6 après
restauration complète. Les journaux finaux de ces quatre instances ne comportent
aucune ERROR/SEVERE ; l'avertissement de version Paper ancienne reste visible.
Mesures de recette sans joueur : 19,77 / 19,93 TPS et 0,80 / 0,82 ms par tick,
sur une attente de 200 ticks par phase. Aucune charge à huit clients n'est attestée.

```powershell
.\scripts\server.ps1 start -Name map-v2-fixes -Port 25579
```

Utiliser le carnet [MAP_V2_INSPECTION.md](MAP_V2_INSPECTION.md) : les centres et monuments
gardent leurs coordonnées. Inspecter particulièrement les lisières et pentes de chaque
territoire, le pied des drapeaux, les plantes hautes, les arbres conservés, les sentiers
et les décorations des monuments. Aucune capture d'écran ni validation esthétique n'est
présentée comme réalisée. Confirmer les terrains seulement après cette visite.
