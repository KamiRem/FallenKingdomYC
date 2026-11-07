# Ravitaillement et récompenses — carte v2

Le système est intégré à FKAmis. Il ne remplace pas les objectifs secrets et ne crée
pas un deuxième mode de capture. Aucun plugin de coffres tiers n'est installé.

## Choix technique vérifié le 7 novembre 2026

| Solution examinée | Fonctions attestées | Écart avec ce projet |
|---|---|---|
| [RandomChest](https://modrinth.com/plugin/randomchest) | Paper 26.2 déclaré, coffres enregistrés, tables et délai de remplissage, licence MPL-2.0 | Le fonctionnement documenté repose sur l'ouverture et le délai de recharge par coffre ; aucune liaison documentée avec la pause, victoire et sauvegarde atomique FKAmis |
| [Chest Spawn](https://modrinth.com/plugin/chest-spawn/) | Événements, lots, butins, protections et gardiens, licence MIT | La fiche s'arrête à 26.1.x ; intégration FKAmis non attestée ; plusieurs fonctionnalités légendaires inutiles pour cette partie |
| FKAmis | Même état de partie, même fichier atomique, API Paper déjà compilée pour 26.2 et Java 25 | Développement ciblé et tests supplémentaires nécessaires, réalisés dans la copie de recette |

L'absence d'intégration documentée n'est pas présentée comme la preuve d'une
impossibilité technique de ces plugins. Le complément existant permet ici un seul
compteur et un seul état de sauvegarde, sans dépendance de production supplémentaire.

## Déroulement

Toutes les **1 800 secondes de ticks actifs**, deux emplacements au maximum reçoivent
un lot virtuel. Un tick du compteur représente 20 ticks serveur : un serveur ralenti
retarde l'événement en temps réel. Aucun rattrapage selon l'horloge système.

Le compteur s'arrête avant le départ, en pause, après la victoire, sans participant
actif connecté et lorsque le système est désactivé. Le temps restant est sauvegardé
chaque seconde active et à chaque mutation de partie. Une coupure peut faire reculer
le compteur d'au plus une seconde ; aucun lot n'est réémis par rattrapage hors ligne.

Les **huit supports physiques** sont préparés avant la partie. Ce sont des coffres
vides identifiés par une donnée persistante, placés hors des royaumes et monuments.
L'événement ne remplace aucun bloc ni conteneur et ne détruit aucun objet au sol.
Un clic droit sur un support actif remet le lot complet dans l'inventaire, si le joueur
dispose d'assez de cases libres. Le coffre physique reste vide et en place.

Les lots non récupérés expirent après **600 secondes actives**. Il n'y a jamais plus
de deux lots actifs simultanément. Les sites précédents sont écartés lorsqu'il existe
assez d'autres candidats ; les deux sites d'un événement sont distants d'au moins
200 blocs. Le message indique seulement des zones générales. Les emplacements de
ravitaillement sont publics ; aucune coordonnée d'objectif secret n'est consultée
pour les annonces.

Huit chunks sont retenus par des tickets Paper pour que les sites restent disponibles.
Ils sont chargés de manière asynchrone sans génération de nouveaux chunks. Un site
manquant, occupé, mal identifié, dans un royaume, hors bordure ou contenant des objets
est inéligible ; son contenu n'est pas effacé.

## Probabilités et limites

Configuration corrigée : `runtime/map-v2-fixes/plugins/FKAmis/supplies.yml`.
Le profil livré figure dans `configs/map-v2-fixes/supplies.yml` ; le profil du premier
chantier reste conservé dans `configs/map-v2/supplies.yml`.
Le fichier source par défaut est `plugins-custom/fk-amis/src/main/resources/supplies.yml`.
Il est désactivé par défaut dans les installations historiques ; le chantier v2 produit
un profil activé et renseigne les coordonnées après placement.

**Chaque tirage** choisit une catégorie : commune 65 %, inhabituelle 28 %, rare 7 %.
Chaque coffre effectue au plus trois tirages. Ce ne sont pas les probabilités qu'un
coffre entier soit « rare ». Dans la catégorie, l'entrée est choisie uniformément,
puis sa quantité dans l'intervalle configuré.

Les budgets limitent ensuite le résultat : 48 unités de valeur par coffre, 96 par
événement, et un plafond par matériau partagé entre les deux coffres. Un tirage
devenu impossible est réduit ou ignoré, sans retirage compensatoire. Les probabilités
de réception peuvent donc différer des poids bruts lorsqu'un plafond est atteint.

| Catégorie | Contenu initial |
|---|---|
| Commune | Nourriture, bois, pierre, flèches, charbon, torches, 2–4 lingots de fer |
| Inhabituelle | Un peu d'or ou de fer, obsidienne, une perle, un bouclier, une pioche en fer ou des livres |
| Rare | 1–2 diamants ou un livre Efficacité II / Protection I |

Plafonds par événement, notamment : **2 diamants, 12 fers, 6 ors, 2 perles, 1 livre
enchanté**, 1 bouclier et 1 outil de chaque type. Aucun équipement complet n'est donné.
Le coût des diamants et livres rares consomme une part importante du budget.

Le catalogue accepté est fermé aux matériaux de survie prévus. Netherite, débris
antiques, élytres, totems, pommes dorées enchantées, objets administratifs et
enchantements supérieurs au niveau II sont refusés à la lecture de la table.
Les paramètres incohérents font échouer la configuration plutôt que produire un lot
imprévisible. Les autres mécanismes d'interdiction de la netherite restent actifs.

## Persistance et duplication

Le compteur, numéro d'événement, derniers sites, lots, statuts `ACTIVE`, `CLAIMED`,
`EXPIRED` et historique borné à 50 lignes sont sérialisés dans la section `supplies`
du **même `state.yml` atomique** que la progression FKAmis. Les objets ne sont jamais
recopiés dans les coffres du monde.

Une récupération marque d'abord le lot `CLAIMED` et écrit l'état sur disque, puis
remet les objets au joueur et demande la sauvegarde de son inventaire. Une seconde
réservation, y compris après redémarrage, est refusée. Un arrêt brutal exactement
entre l'écriture et la remise peut faire perdre le lot : cette préférence pour une
attribution au plus une fois évite une duplication. Il n'existe pas de transaction
globale entre le fichier du plugin et les inventaires Minecraft. L'arbitre peut
compenser un incident après contrôle des journaux, sans réactiver le même lot.

Les pistons, explosions, ouvertures d'inventaire et transferts d'entonnoirs ne peuvent
déplacer ou exploiter les supports. La protection concerne uniquement le bloc coffre,
pas un mur invulnérable autour de lui. Les joueurs ne peuvent pas y déposer leurs
propres objets. Un coffre de ravitaillement ne peut pas être déclaré comme objectif.

Restaurer une archive **complète à froid**, jamais seulement la section des lots ou
un inventaire individuel. Les sites et tables font partie de l'archive de serveur.

## Commandes réelles

| Commande | Autorisation / effet |
|---|---|
| `/fka supply status` | Tous : activation, secondes actives restantes et nombre de lots |
| `/fka supply list` | Admin : sites publics enregistrés et états |
| `/fka supply enable` | Admin : reprend le compteur conservé |
| `/fka supply disable` | Admin : suspend le compteur et expire les lots actifs ; garde l'historique des récupérations |
| `/fka supply reload` | Admin, partie en pause ou avant départ, aucun lot actif : valide et recharge la table ; préserve le temps restant, plafonné au nouvel intervalle |
| `/fka supply add <id> <zone_sans_espace>` | Admin avant départ, en visant un coffre neutre vide à cinq blocs maximum |
| `/fka supply remove <id>` | Admin avant départ, lot inactif ; conserve le coffre physique et retire son identification |
| `/fka supply test confirm` | Admin, `test-mode: true` **et partie jamais démarrée** ; refuse le profil livré où `test-mode: false` |

Toutes les commandes sensibles demandent `fkamis.admin`. Une commande de test est
refusée sur une partie officielle même si elle est en pause. Pour tester, utiliser une
copie distincte ; ne pas modifier le compteur d'une partie par édition de fichiers.

## Éviter la domination par camping

Huit sites, deux choix espacés, exclusion des sites précédents, expiration courte et
petits lots rendent la surveillance permanente coûteuse. Certains emplacements restent
naturellement plus proches d'un royaume : les probabilités ne garantissent pas une
distance identique à chaque tirage. Ne pas augmenter les récompenses pour compenser
une domination ; mesurer d'abord les temps de parcours à quatre équipes et déplacer
un support avant le départ si nécessaire.

Pendant la recette multijoueur, vérifier clic droit, inventaire plein, double clic,
déconnexion pendant la remise, interactions en pause, tir à distance et affrontement
près d'un support. Les événements sans clients et les simulations d'horloge ne
remplacent pas ces essais.
