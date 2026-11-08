# Règlement de la partie

## Révision gameplay courante

Voir [GAMEPLAY_UPDATE.md](GAMEPLAY_UPDATE.md) pour la livraison ciblée, les causes,
les limites de preuve, l'installation et le rollback. Le rapport définitif est
`tests/results/gameplay-update-delivery.json`. Paper 26.3-244 / Java 25 / FK 2.24.9
inchangé ; 1 à 4 membres par équipe (défaut 2), arbitre UUID indépendant, lit valide
ou centre sûr pour les morts, construction neutre libre, capture sans condition de
regard, locator bar désactivée, mobs suspendus au jour 0 et `/fka announce <message>`.
Les guides des anciennes livraisons restent historiques.

## Priorité : morts illimitées et élimination par capture

Aucune limite de vies. Tant que le royaume reste actif, toute mort individuelle
(PvE, environnement, PvP, défense ou assaut) laisse le joueur dans son équipe, avec
réapparition SURVIVAL au lit/ancre valide ou au centre sûr. Seule la capture
complète de son objectif provoque l'élimination persistante et le mode SPECTATOR.
Entrer dans un château ou commencer une capture ne suffit pas. Le moteur reste :
min(2, effectif officiel) attaquants de même équipe, 2,5 blocs, proximité accessible sans regard, 60 secondes consécutives,
contestation par un défenseur et interruptions existantes.

Quatre à seize participants et un arbitre supplémentaire en CREATIVE : l'arbitre UUID n'a
aucune équipe, aucun poids de capture, présence active ou victoire. Son départ et
celui d'un spectateur ne doivent pas interrompre le combat des participants.
Les protections de jeu restent imposées aux OP ordinaires. Les corrections
destructives d'objectifs/sites exigent une intervention administrative explicite
et journalisée, en pause ; voir [le guide](ADMIN_UPDATE.md).

## Compléments de la carte v2

La carte compacte mesure 1 200 blocs de côté. Les quatre zones de rayon 80 sont
aménagées et portent un drapeau décoratif ; les forts et salles secrètes restent
entièrement construits par les équipes. Le drapeau n'est pas un objectif de capture.

Sept monuments neutres offrent des récompenses fixes à usage unique, sans recharge
automatique. La crypte contient deux gardiens créés une seule fois, masqués/suspendus à J0 puis réactivés au départ. Les ressources
des monuments peuvent être récoltées selon les règles normales de la zone neutre.

Toutes les 30 minutes actives, jusqu'à deux supports de ravitaillement reçoivent des
lots. Clic droit pour récupérer tout le lot, avec des cases libres ; aucune récupération
pendant une pause. Les coffres fixes ne servent pas de stockage personnel et ne peuvent
pas être déplacés. Les sites tournent lorsque possible et les lots expirent après
dix minutes actives. Les règles détaillées et budgets figurent dans [LOOT_SYSTEM.md](LOOT_SYSTEM.md).

Les jours, PvP, assauts, éliminations et interdiction de la netherite gardent les
mêmes règles que ci-dessous. Ni les monuments ni les ravitaillements ne révèlent les objectifs.

## Royaumes et construction

Quatre royaumes de un à quatre joueurs, configurés avant partie (défaut deux). Les emplacements et ressources sont inspectés avant
le départ. Aucun château, mur, tour ou salle n'est donné. Les joueurs récoltent leurs
matériaux, construisent leurs forts, creusent et aménagent leur propre territoire sur
toute la hauteur du monde. Sur la v2, rayon de 80 blocs, carré inclusif.

La construction et les coffres ordinaires sont libres en zone neutre dès J1. La TNT
reste soumise aux assauts J3 ; les objectifs et supports de ravitaillement restent
protégés. Les exceptions natives autorisées dans une base ennemie sont conservées. Le minage chez l'adversaire reste interdit même après le jour 3 :
les brèches se font par TNT, accès existants et stratégies autorisées. Les tunnels
peuvent être creusés en terrain neutre ; ne pas miner la partie du tunnel dans une
base adverse. Les joueurs peuvent librement creuser et construire leur propre base.

Les restrictions natives de seaux et de portails du Nether dans une base adverse
restent actives : ne pas compter sur ces voies pour entrer pendant un assaut.

Pas de duplication, triche, X-ray, abus de bugs ou exploitation des permissions.
Les dommages indirects destinés à contourner un jour d'interdiction sont interdits.

## Phases

Les jours sont des phases administratives. Le soleil et la nuit continuent à leur
rythme vanilla pendant la session. Dormir ou attendre ne débloque jamais le PvP.

- Jour 1 : exploration, récolte et construction ; aucun PvP, aucun vol ou sabotage
  dans une base adverse ; Nether fermé.
- Jour 2 : PvP en terrain neutre ; royaumes protégés, aucun assaut ni vol ; Nether ouvert.
- Jour 3 et suivants : PvP et assauts ouverts, TNT contre les défenses, coffres de
  stockage pillables, captures des objectifs validés possibles.

Le friendly fire est interdit, y compris les projectiles et effets de potions
attribuables. Au jour 1, certains dégâts sans attribution fiable (lave, feu, poison,
explosions) ne sont plus bloqués globalement : le **PvE et les dangers naturels sont
entièrement actifs dès J1**, y compris zombies, squelettes, creepers naturels, chute,
noyade, feu, lave, faim et effets de mobs. Les attaques et pièges attribués à un joueur
respectent les restrictions PvP. Les soins entre joueurs restent possibles.
Avant les assauts, les distributeurs sont désactivés par prudence ; les transferts
de conteneurs ne traversent pas les limites territoriales.

La difficulté est normale. Les morts n'éliminent pas un royaume. Les pistons ne
permettent pas d'extraire les murs à travers les frontières, même après J3. Les mains,
outils et TNT non amorcée ne donnent aucune exception au refus de casse adverse.

## Salle secrète et capture

Chaque royaume choisit et cache un coffre objectif ordinaire dans son territoire.
La salle doit être accessible légalement, permettre à deux attaquants de se tenir
près du coffre et offrir un espace debout relié aux faces du coffre, sans condition de regard. Pas de salle scellée sans
issue, coque invulnérable, protection extérieure permanente ou exploitation de la bordure.

Les autres coffres ne sont pas des objectifs. Ne pas déplacer le coffre déclaré.
L'emplacement reste secret et doit être enregistré avec `/fka room register`, puis
inspecté et validé avant le jour 3. L'administrateur gère cette inspection en privé.

Min(2, effectif officiel) membres **de la même équipe**, en survie, vivants et connectés, doivent rester
dans un rayon de 2,5 blocs autour de l'objectif dans un espace accessible adjacent au même niveau pendant 60 secondes
de ticks serveur. Un défenseur dans cette zone conteste la capture. Un second royaume
attaquant dans la zone, une sortie, une mort, une déconnexion ou une pause remet la
progression à zéro. Une baisse de TPS allonge le temps réel : elle ne raccourcit pas la capture.

Une capture annonce l'élimination du royaume. Tous les membres deviennent spectateurs,
y compris après reconnexion. Ils n'interagissent plus et ne doivent pas transmettre
d'informations aux survivants. Après la troisième élimination, le dernier royaume gagne.

## Dimensions et objets

Nether fermé au jour 1, ouvert au jour 2. Sa bordure est proportionnelle à celle de
l'Overworld pour limiter les contournements par les portails. End fermé jusqu'à décision
administrative. Les téléportations vers une dimension fermée sont refusées ; un joueur
reconnecté dans une dimension fermée est ramené dans l'Overworld.

Netherite interdite partout : débris antiques, fragments, lingots, blocs, armes, outils,
armures et modèle d'amélioration. Les recettes, table de forge, butins, inventaires,
shulkers, bundles, équipement de mobs, ramassages et transferts sont filtrés. Les
conteneurs non ouverts ne sont pas tous parcourus au démarrage ; ils sont filtrés
avant usage ou transfert. Les objets autorisés sont conservés.
Les **élytres (`ELYTRA`) et pommes dorées enchantées (`ENCHANTED_GOLDEN_APPLE`)** sont
également interdites. Les pommes dorées ordinaires (`GOLDEN_APPLE`) restent autorisées.

## Sessions

On joue ensemble. La déconnexion d'un participant actif met la partie en pause ;
l'administrateur décide de la reprise. La pause bloque les actions de jeu et gèle
les mondes. Le jour ne progresse pas en l'absence des joueurs. Après redémarrage,
la partie reste en pause jusqu'à `/fka resume`.

Les litiges et la validité d'une entrée sont arbitrés avant l'ouverture des assauts.
Toute dérogation doit être annoncée aux quatre équipes avant la reprise.
