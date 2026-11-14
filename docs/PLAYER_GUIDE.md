# Guide des participants

## Révision VNext.1 courante

Voir [le guide VNext.1](FKAMIS_VNEXT_1.md). Le guidage ActionBar et `/fka base`
indiquent seulement votre base ; aucune position ennemie ni objectif. Hors de son
monde, la direction est indisponible. Les territoires migrés ont un rayon 40.
Sur une nouvelle référence V2.1, une caverne thématique est préparée par royaume ;
les accès et coordonnées restent à inspecter en jeu avant approbation.

Les éliminés et arbitres peuvent utiliser `/fka spectate [pseudo]` pour rejoindre
un participant actif à une position sûre déjà chargée. Sans pseudo : menu privé.
Aucune interaction ni ouverture de coffre n'est accordée. La pause immobilise
également les spectateurs ; la commande attend alors la reprise, sauf arbitre.

## Survie, morts et arbitrage

Vous jouez avec un client **Minecraft Java 26.3**. Nouveau joueur au jour 0 :
SURVIVAL, sans participation avant attribution. Un participant d'équipe active
réapparaît en SURVIVAL après zombie, lave, chute, PvP ou assaut, sans limite de vies.
Le lit/ancre valide est respecté ; à défaut le centre sûr près de 0,0 est utilisé.
Une mort ne retire ni équipe ni progression.

Seule la capture complète du coffre élimine le royaume. Tous ses membres passent
en SPECTATOR et y restent après mort, reconnexion ou redémarrage. L'arbitre en
CREATIVE est un compte supplémentaire hors équipe : il ne capture/conteste pas, ne récupère
pas les lots et son départ ne met pas la partie en pause. Les conseils périodiques
sont supprimés, les annonces de jours, lots, captures et victoire sont conservées.

Sur la **carte v2**, les royaumes sont plus proches. Votre drapeau indique le centre
d'un terrain préparé ; il faut toujours construire votre fort et cacher votre objectif.
Les ruines, mine, camp, sanctuaire, tour et crypte se trouvent en zone neutre.
Leur butin fixe n'est pas rechargé.

Toutes les 30 minutes de partie active, un message annonce jusqu'à deux ravitaillements
et leur zone générale. Les supports sont des coffres fixes : faites un clic droit avec
plusieurs cases libres pour récupérer le lot entier. Le compteur s'arrête pendant les
pauses. Il continue sans joueur connecté. `/fka supply status` indique le temps restant. Le butin
reste modeste ; le minage et la construction demeurent essentiels.

Utilisez Minecraft Java **26.3**, sans mod obligatoire. Donnez votre pseudo à
l'administrateur, rejoignez une fois pour l'attribution du compte, puis attendez le départ.
Vous jouez en Rouge, Bleue, Verte ou Jaune, par équipes de un à quatre, selon le format choisi (deux par défaut).

Construisez tout vous-mêmes : terrain de départ naturel, aucun fort fourni. Vous pouvez
creuser et bâtir dans votre base et en zone neutre dès J1, installer des coffres ordinaires, établis et fours. Les bases ennemies, objectifs et sites de ravitaillement gardent leurs protections ; la TNT attend J3.

| Jour | À retenir |
|---|---|
| 1 | Construire, miner, explorer ; aucun PvP ; Nether fermé |
| 2 | PvP en terrain neutre ; les royaumes restent protégés ; Nether ouvert |
| 3+ | Assauts, TNT et capture des royaumes |

Le jour change seulement quand l'administrateur l'annonce. La netherite est toujours
interdite. L'End est fermé sauf annonce administrative. Pas de dégâts entre coéquipiers.
Les élytres et pommes dorées enchantées sont interdites ; les pommes dorées ordinaires
restent autorisées. **Les mobs et tous les dangers naturels restent actifs dès J1** :
le PvP fermé ne protège ni des creepers, ni de la lave, ni des chutes ou de la noyade.
Vous pouvez vous défendre contre les mobs. Aucun minage adverse n'est permis après J3 :
utilisez les brèches par TNT et les accès existants.

Cachez un coffre objectif ordinaire dans une salle construite par votre équipe, à
l'intérieur de votre territoire. Il faut pouvoir y entrer et se tenir à deux près du
coffre. En le visant, utilisez `/fka room register`, puis demandez une inspection privée.
Les coordonnées ne sont pas annoncées aux autres joueurs.

Pour capturer : deux membres de la même équipe (un en format solo) doivent rester
60 secondes à 2,5 blocs maximum du coffre, au même niveau dans un espace debout relié
à celui-ci. Vous pouvez regarder ailleurs ou tourner le dos. Ni murs ni étages
séparés ne permettent de capturer. Un défenseur conteste, un autre royaume attaquant
bloque ; si une sortie ou une mort laisse trop peu d'attaquants, la progression
repart de zéro. Une déconnexion ne déclenche plus de pause ; le seuil officiel reste inchangé.
Un allié supplémentaire qui se déplace loin de la salle n'interrompt pas la capture.
Ne minez pas les blocs adverses : utilisez la TNT au jour 3 et les accès du fort.

Une équipe capturée devient spectatrice. Aucun conseil ou repérage depuis le mode
spectateur pour les survivants. La dernière équipe active gagne.

`/fka status` montre le jour et les royaumes restants. `/fk team list` affiche les
équipes. Le chat FallenKingdom est en équipe par défaut ; préfixer un message par `!`
pour le chat global. La déconnexion ne suspend pas la partie. Seul l’arbitre décide des pauses.
