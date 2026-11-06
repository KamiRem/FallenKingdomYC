# Règlement de la partie

## Royaumes et construction

Quatre royaumes de deux joueurs. Les emplacements et ressources sont inspectés avant
le départ. Aucun château, mur, tour ou salle n'est donné. Les joueurs récoltent leurs
matériaux, construisent leurs forts, creusent et aménagent leur propre territoire sur
toute la hauteur du monde. Rayon initial proposé : 100 blocs, carré inclusif.

La pose hors de sa base suit les règles classiques du plugin : torches, feu, panneaux
et exceptions natives ; la TNT devient disponible au jour 3. Les expéditions doivent
donc être préparées. Le minage chez l'adversaire reste interdit même après le jour 3 :
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
explosions) sont aussi bloqués : les pièges indirects ne doivent pas contourner le PvP.
Avant les assauts, les distributeurs sont désactivés par prudence ; les transferts
de conteneurs ne traversent pas les limites territoriales.

Les dégâts environnementaux restants du survival (chutes, mobs, faim) restent en jeu
hors pause. La difficulté est normale. Les morts n'éliminent pas un royaume.

## Salle secrète et capture

Chaque royaume choisit et cache un coffre objectif ordinaire dans son territoire.
La salle doit être accessible légalement, permettre à deux attaquants de se tenir
près du coffre et offrir une ligne de vue sur celui-ci. Pas de salle scellée sans
issue, coque invulnérable, protection extérieure permanente ou exploitation de la bordure.

Les autres coffres ne sont pas des objectifs. Ne pas déplacer le coffre déclaré.
L'emplacement reste secret et doit être enregistré avec `/fka room register`, puis
inspecté et validé avant le jour 3. L'administrateur gère cette inspection en privé.

Deux membres **de la même équipe**, en survie, vivants et connectés, doivent rester
dans un rayon de 2,5 blocs autour de l'objectif avec une ligne de vue pendant 60 secondes
de ticks serveur. Un défenseur dans cette zone conteste la capture. Un second royaume
attaquant dans la zone, une sortie, une mort, une déconnexion ou une pause remet la
progression à zéro. Une baisse de TPS allonge le temps réel : elle ne raccourcit pas la capture.

Une capture annonce l'élimination du royaume. Les deux comptes deviennent spectateurs,
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

## Sessions

On joue ensemble. La déconnexion d'un participant actif met la partie en pause ;
l'administrateur décide de la reprise. La pause bloque les actions de jeu et gèle
les mondes. Le jour ne progresse pas en l'absence des joueurs. Après redémarrage,
la partie reste en pause jusqu'à `/fka resume`.

Les litiges et la validité d'une entrée sont arbitrés avant l'ouverture des assauts.
Toute dérogation doit être annoncée aux quatre équipes avant la reprise.
