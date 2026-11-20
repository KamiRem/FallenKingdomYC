# Audit final avant bascule V2.1 — 20 novembre 2026

**Recommandation : DÉPLOIEMENT ENCORE BLOQUÉ.** Les fichiers et le candidat sont
conformes. L'espace réellement libre sous quota et la neutralisation des
redémarrages concurrents restent à confirmer. Aucune écriture distante, commande
console, alimentation, modification de whitelist ou bascule n'a été effectuée.

Base Git : `93fd580`, avant ajout des présents outils/rapports d'audit. Candidat :
`C:\Users\youne\FKBackups\V21-QUERY-20261120-01`.
Audit privé : `C:\Users\youne\FKBackups\MS-PREFLIGHT-20261120-01`.

## Bilan constaté

Fenêtre du 20 novembre : **21:06:04–21:12:17 UTC**, soit **22:06:04–22:12:17
Europe/Paris**. Ces observations ne garantissent pas l'état à une date ultérieure.

| Vérification | Résultat |
|---|---|
| Authentification API et identité | ID 513365, port 22880 ; accès authentifié à l'instance attendue |
| SFTP | Authentifié après vérification de la clé hôte épinglée, avant transmission du mot de passe |
| Serveur arrêté | 74 observations API, toutes offline ; intervalle maximal 5,131 s ; aucun démarrage détecté |
| Arborescence source | 305 fichiers, 321 dossiers ; aucun ajout/suppression détecté |
| Contenu distant | 305 SHA-256 identiques au point -02, sur **deux lectures**, soit 610 comparaisons réussies |
| Stabilité SFTP | READDIR/LSTAT/FSTAT, tailles, mtime, types et modes contrôlés avant/après lectures et sur les relevés d'arbre |
| Propriétaires Linux | Baselines LSTAT contrôlées lorsqu'elles sont disponibles ; UID/GID absents ne sont jamais une preuve d'égalité |
| Réglages MineBoard | Aucun changement détecté par rapport à la capture du point -02 ; ports et commande de lancement identiques |
| Java | ID API 61, image `reg.sttr.io/java/25_perf:latest`, compatible avec Java 25 Performance ; version du processus non mesurée, serveur arrêté |
| Entrée de démarrage | `paper.jar` ; les alias paper.jar/server.jar correspondent au Paper officiel 26.3-244 vérifié |
| Query/jeu | server.properties identique à la sauvegarde : Query actif, query.port et server-port 22880, historique à 10 places |
| Versions/fichiers | Paper 26.3-244 et FallenKingdom 2.24.9 inchangés ; FKAmis distant historique intact, différent du nouveau JAR selon le plan prévu |
| Candidat local | Archive et 148 cibles vérifiées ; manifeste complet de 152 empreintes cohérent avec la copie préparée |
| Sauvegardes historiques | Archive, manifeste et les 305 fichiers restaurés originaux confirmés inchangés après l'audit |
| Whitelist | Deux comptes conservés ; aucune identité ajoutée, aucun pseudo/UUID inventé |
| Espace disponible | API offline : aucun usage disque ; SFTP statvfs non disponible ; contrôle non conclusif |
| Planifications et verrou | Pas de liste de tâches vérifiable ni de verrou partagé fourni par ces accès ; risque non résolu pour la bascule |

Les deux passes comparent **l'état distant à la sauvegarde historique**, pas aux
fichiers futurs de la nouvelle carte. Les différences prévues par le plan sont
donc distinguées d'une dérive distante. **Aucune divergence inattendue détectée.**

Les protections SFTP du correctif `0d7877a` sont réutilisées. Le contrôle refuse
liens/fichiers spéciaux, attribut critique absent, changement de disponibilité
pertinent, taille/mtime/mode différent ou SHA différent. Il s'arrête au premier
écart et ferme le transport ; aucune sauvegarde complète supplémentaire n'a été
créée. Le contenu distant est lu pour hachage, sans être écrit dans une instance.
98 tests Python locaux passent, dont trois tests avec faux SFTP vérifiant les
deux lectures et l'arrêt avant le fichier suivant en cas de divergence.

Le marqueur FKAmis distant périmé est **celui déjà présent dans la sauvegarde**,
pas une nouvelle divergence : JAR historique `46703f...`, ancienne valeur déclarée
`83e721...`. Il n'a pas été corrigé à distance. Le rollback local fonctionnel a
réconcilié uniquement le marqueur d'une copie et utilisé le profil historique.

## Empreintes et liste exacte

| Objet | SHA-256 |
|---|---|
| Archive historique instance.zip | `255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf` |
| Manifeste historique | `b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1` |
| Manifeste cible V2.1 | `bc99993cf2796991a97adf92c12091bea86e5b5166c503258d1311aa227948e6` |
| Plan privé V2.1 | `7896bd00c34aa50602f779db00b2a178556050c8396dd3ccadf9e0af5b59296a` |
| Archive privée de transfert | `d6ca64ed0e1d05adfc05aab21387cb050cae148fa3a31acd7cf8645a3507c9f2` |

La [liste exacte des 148 fichiers](MINESTRATOR_148_FILES_20261120.tsv) indique
chaque chemin, taille, SHA cible et action de contenu. Elle ne contient ni monde
binaire, ni configuration sensible, ni profil joueur. Les détails des anciens
fichiers, dont les noms de profils, restent dans `operation-plan-private.json`
du répertoire d'audit privé, hors Git.

| Groupe cible | Nombre |
|---|---:|
| world/ et dimensions intégrées | 121 |
| plugins/FKAmis/ | 5 |
| plugins/FallenKingdom/ | 8 |
| maintenance/ | 7 |
| JAR FKAmis indépendant | 1 |
| Fichiers racine | 6 |
| Total | **148** |

Par rapport au point source : **46 contenus remplacés, 6 créations et 96 contenus
identiques**. Les fichiers identiques situés dans les arbres neufs sont réinstallés
depuis le candidat ; cela ne fusionne aucun inventaire/état ancien. Le staging
contient la totalité des 148 cibles approuvées, avec vérification avant activation.

Créations exactes : `maintenance/map_reader.py`,
`maintenance/new-match-reference-v2.1.json`, `maintenance/new-match-reference.json`,
`maintenance/new_match.py`, `maintenance/territory_migration.py`,
`map-v21-caverns.json`.

## Conservation et quarantaine proposées

Après autorisation seulement, renommer les anciens arbres **entiers**, sans
superposer les nouvelles régions à une partie jouée : `world`,
`plugins/FKAmis`, `plugins/FallenKingdom`. La procédure réserve aussi le traitement
de `world_nether`/`world_the_end` s'ils apparaissent lors du précontrôle, mais ces
arbres séparés sont actuellement absents ; leur apparition constituerait une
divergence à réexaminer. Les dimensions actuelles sont intégrées à world/.
**142 anciens fichiers** appartiennent aux arbres remplacés.

Conserver séparément neuf anciennes versions hors de ces arbres :

```text
BACKUP_MANIFEST.json
DEPLOYMENT_MANIFEST.json
FKAmis.sha256
RUNTIME_LOCK.json
maintenance/host_ops.py
maintenance/serverlib.py
map-v2-construction.json
plugins/FKAmis-1.0.0.jar
server.properties
```

Ne pas réutiliser ou écraser une quarantaine. Prévoir des chemins neufs
`.fk-stage/<operation_approuvee>` et `.fk-quarantine/<operation_approuvee>`,
avec traces de chaque renommage. Les dossiers temporaires/quarantaines sont
explicitement distincts des 148 chemins applicatifs finaux.

Les **154 autres fichiers du point -02** ne sont pas remplacés par ce plan.
Les cinq contrôles conservés du manifeste sont `paper.jar`, `server.jar`,
`plugins/FallenKingdom-2.24.9.jar`, `whitelist.json`, `ops.json`. Préserver aussi
les autres fichiers inchangés : configurations Paper/Bukkit/Spigot, bibliothèques,
caches, EULA, bans, références, sauvegardes et lanceurs. Aucun nettoyage automatique.
Les écritures normales du premier démarrage sont contrôlées séparément de l'étape
d'installation binaire ; elles ne sont pas présentées comme des transferts.

## Dimensionnement disque et contrôle manuel ciblé

| Poste | Octets |
|---|---:|
| Instance historique complète déjà présente | 464 871 862 |
| 148 fichiers à stager | 188 380 952 |
| Réserve pour une restauration entière en parallèle | 464 871 862 |
| Plus grand fichier temporaire/reprise de transfert | 11 747 328 |
| Marge opérationnelle proposée | 2 147 483 648 |
| **Libre supplémentaire requis par ce plan** | **2 812 483 790**, environ **2,62 Gio** |

Le renommage sur le même filesystem conserve les anciens arbres sans dupliquer
leurs octets. Cette hypothèse doit être vérifiée ; en cas de copie de quarantaine,
ajouter sa taille réelle. La réserve permet de conserver le candidat raté et de
restaurer le point complet sans effacer l'historique. La marge de 2 Gio est une
hypothèse de planification, pas une garantie pour une exploration prolongée.

Le ZIP de transfert pèse 140 900 300 octets ; le ZIP historique externe 413 245 391.
Le plan prévoit des fichiers SFTP, **pas** une extraction ZIP sur l'hôte. Si une
archive est aussi téléversée ou si une seconde copie est nécessaire, recalculer
les besoins avant approbation.

L'API live offline ne retourne que son état dans stats ; l'extension SFTP
`statvfs@openssh.com` n'est pas disponible. Une allocation d'offre ne prouve pas
l'espace libre sous quota. **Ne pas déduire le libre en soustrayant cette instance
du quota MyBox : d'autres données/instances peuvent l'utiliser.**

Action manuelle à préparer, sans rien changer : relever dans MineBoard/MyBox
l'usage réel et la capacité effectivement disponible sous quota, pour toutes les
données concernées, avec date/heure. Il faut au moins 2 812 483 790 octets libres
supplémentaires sous les hypothèses ci-dessus. Le champ API brut `java_memory=30`
est inchangé, mais son unité/allocation effective n'a pas été établie par cette
lecture : relever aussi la mémoire réellement allouée, sans la modifier.

## Redémarrages et concurrence

L'[API officielle](https://api.minestrator.com/) donne l'identité, les réglages et
l'état live. Les lectures utilisées ne fournissent pas de liste vérifiable de
tâches planifiées ou de verrou de processus partagé. Le message de notification
`poweraction_message.restart` ne prouve pas la désactivation d'un redémarrage.

MineBoard propose des [tâches planifiées](https://minestrator.com/blog/article/tache-planifiee-minestrator-automatiser-serveur)
et un [calendrier de fonctionnement](https://minestrator.com/blog/article/minenews-9-google-apple-passkeys-panel-plus-rapide).
Inspection manuelle ciblée à préparer : tâches/commandes, calendrier, relance
après crash, actions en attente et interventions des autres opérateurs. Relever
leur état, les mécanismes à neutraliser et la fenêtre de maintenance ; ne pas
les désactiver dans le cadre de cet audit. Demander au fournisseur la procédure
si l'un de ces états n'est pas accessible dans le panel.

Une observation offline toutes les cinq secondes n'exclut pas toute écriture
concurrente ni tout cycle entre deux observations. La dérogation du point -02
concernait sa sauvegarde/restauration ; elle n'autorise pas une bascule. L'accord
futur devra préciser les conditions de maintenance de cette opération et le
traitement du risque résiduel, sans changer silencieusement AGENTS.md. Aucun
verrou exclusif n'est revendiqué ici.

## Bascule proposée, non exécutée

1. Lever les réserves d'espace et de maintenance, puis faire approuver ce plan,
   les empreintes et le périmètre de restauration. La whitelist reste inchangée
   dans les 148 fichiers ; toute extension demande une autorisation distincte.
2. Juste avant écriture, répéter identité/offline, réglages et préconditions des
   305 fichiers. À toute dérive : arrêter, conserver le point -02 intact et
   réauditer ; une nouvelle sauvegarde éventuelle requiert son cadre autorisé.
3. Garder archive/manifeste/restauration -02 sur PC privé hors instance. Vérifier
   leurs empreintes et l'accès au point fonctionnel de rollback. Conserver la
   fenêtre de maintenance et la surveillance API durant toute l'opération.
4. Préparer staging et quarantaine neufs. Déposer les seuls 148 fichiers depuis
   le payload V2.1 approuvé ; relire chaque SHA distant. Ne pas utiliser le ZIP
   de construction de carte ou un ancien ZIP de mise à jour FKAmis.
5. Renommer les arbres/fichiers anciens listés en quarantaine, puis activer les
   arbres neufs et fichiers cibles. Ne jamais fusionner l'ancienne progression,
   les profils ou états. Vérifier permissions/propriétaires accessibles, absence
   de restes anciens dans les arbres neufs, les 148 SHA et les 5 fichiers conservés.
6. Garder Java 25 Performance, Paper 26.3-244, FallenKingdom 2.24.9, mémoire et
   paramètres panel. Port 22880, Query actif, capacité 20, whitelist stricte.
   Le JAR seul ne remplace pas les données de carte/état prévues.
7. Démarrer seulement après l'accord couvrant cette action. Contrôler logs,
   versions, plugins et jour 0 non lancé. Aucun `fka start` automatique, aucun
   `/reload`. Appliquer le protocole de recette ci-dessous avant partie officielle.
8. Au contrôle critique échoué : ne pas ouvrir la partie, conserver les preuves
   et appliquer le rollback uniquement dans le périmètre autorisé. Ne pas
   poursuivre les transferts si un démarrage ou une écriture concurrente apparaît.

## Rollback complet proposé

Le point de retour est **toute l'instance réelle -02**, pas seulement son JAR.
Son test fonctionnel a réussi dans `RB-QUERY-20261120-02` avec dix places et Query
actif, sur Windows ; les permissions Linux restent à vérifier sur l'hôte.

Après autorisation couvrant l'arrêt/restauration : arrêter proprement V2.1,
maintenir l'absence de redémarrage et préserver son état raté dans une nouvelle
quarantaine ou sauvegarde autorisée. Ne pas supprimer l'ancienne quarantaine.
Vider l'espace **applicatif** par renommage de tous ses arbres/fichiers dans la
quarantaine dédiée, en conservant les conteneurs de sauvegarde/quarantaine hors
des chemins actifs. Restaurer les 305 fichiers et 321 dossiers du point -02 dans
un espace applicatif neuf : mondes, profils, tous plugins, états, réglages,
politiques, références et historiques. Ne jamais superposer aux fichiers V2.1.

Comparer les 305 SHA au manifeste original avant toute adaptation, puis réconcilier
**uniquement le marqueur de l'instance restaurée** avec son JAR historique
`46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442`.
L'archive et la restauration originale restent inchangées. Utiliser les outils
externes actuels avec `historical-rollback` ; les anciens outils embarqués du point
imposent un profil obsolète et ne doivent pas être remplacés silencieusement.

Rétablir dix places, Query actif sur 22880 et les réglages panel historiques.
Les territoires historiques reviennent à rayon 80, la capacité historique à deux
par équipe, au jour 0 non lancé de ce point précis. Ce n'est pas une récupération
de progression nouvelle ni une fusion d'inventaires. Restaurer/contrôler les modes,
UID/GID Linux avec les permissions disponibles ; recourir à l'opérateur/support
si SFTP ne permet pas de réappliquer les métadonnées. Démarrer seulement après
validation, contrôler logs/plugins/état et garder les preuves du retour arrière.

Si la restauration de l'espace actif ne peut être garantie avec SFTP, l'étape
manuelle ciblée est une restauration complète dans le panel/support, depuis le
point vérifié, puis relecture SFTP des empreintes. Aucun shell SSH, déplacement
atomique de racine ou mécanisme fournisseur non disponible n'est prétendu exécuté.

## Whitelist, recette et décision

Le [protocole détaillé](MINESTRATOR_RECETTE_ET_WHITELIST_20261120.md) couvre les
identités Java vérifiées/approuvées, les quatre équipes, cavernes/territoires,
commandes, captures, morts/éliminations, spectateurs, portails, Query/MineBoard et
TPS/MSPT/RAM/GC/ping à 4/8/16 participants puis 17 connexions réelles. Les modèles
CSV sont vides ; aucune identité ni mesure n'a été inventée.

La compatibilité Query avec l'affichage joueurs est [documentée par MineStrator](https://minestrator.com/blog/article/minenews-5-mineboard-nouveautes-serveur-2026),
mais le rendu réel du panel et la charge humaine restent à tester après
installation autorisée, sans confondre recette et partie officielle.

**Décision finale : DÉPLOIEMENT ENCORE BLOQUÉ**, en attente de confirmation du libre
sous quota, des conditions de maintenance/redémarrage et d'une autorisation
explicite de bascule. L'audit de fichiers et la préparation du candidat sont
réussis ; ils n'autorisent aucune modification distante.
