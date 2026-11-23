# Préparation V2.1 → V2.2 — MineStrator 513365

**Verdict : NO-GO pour une bascule immédiate. Préparation locale effectuée.**

**Suite de la revue :** l'approbation conditionnelle a déclenché une
[vérification géométrique supplémentaire](MINESTRATOR_V22_CELL_REVIEW_20261123.md).
Un puits dangereux a été identifié : la condition de sécurité échoue, la référence
r2 reste non approuvée et la sauvegarde actuelle autorisée sous condition n'a pas
été engagée. Les mesures et propositions ci-dessous restent la preuve du préflight.

**Suite locale :** la [restauration ciblée du puits](V22_SHAFT_RESTORATION_20261123.md)
est techniquement validée et prête pour inspection humaine. Sa nouvelle liste de
17 fichiers et ses empreintes remplacent la proposition r2 pour la revue ; aucune
bascule ni sauvegarde distante n'a été effectuée. Les observations distantes de ce
rapport n'ont pas été renouvelées pendant cette correction locale.

Deux préconditions restent ouvertes : approbation de la référence proposée qui
préserve deux cellules de recette, puis autorisation/réalisation/vérification
d'une nouvelle sauvegarde complète actuelle avec restauration de contrôle.
Une autorisation distincte sera nécessaire avant toute écriture, arrêt,
démarrage, modification de whitelist ou partie. Aucun de ces actes n'a été réalisé.

La base de code est `2759630`, le candidat retenu `V22-FINAL-20261123-02`.
Le [reçu expurgé](../tests/results/minestrator-v22-preflight-20261123.json)
et la [liste exacte des actions et SHA](MINESTRATOR_V22_FILES_20261123.tsv)
complètent ce rapport. Les fichiers de monde, données, accès et preuves détaillées
restent privés dans `C:\Users\youne\FKBackups\MS-V22-PREFLIGHT-20261123-01`.

## 1. Audit distant réellement effectué

API officielle authentifiée, uniquement GET ; SFTP avec empreinte hôte déjà
vérifiée, uniquement liste/attributs/lectures. Aucun exec SSH, PUT/PATCH/POST,
commande console, création de snapshot, renommage, chmod ou suppression distante.
Les secrets DPAPI passent par stdin et ne figurent ni dans les arguments ni dans
les journaux. Les réponses complètes du panel sont chiffrées localement par DPAPI.

Trois fenêtres le 23 novembre, heure de Paris : découverte 11:09:39–11:10:36,
empreintes complètes 11:12:15–11:17:12, régions 11:18:44–11:19:49. Respectivement
13, 60 et 14 observations API, toutes `offline`, intervalle maximal 5,129 s.
La surveillance concerne ces fenêtres ; elle ne constitue pas un verrou partagé
ni une surveillance permanente entre les étapes. Le reçu donne aussi le dernier
checkpoint API avant clôture de la préparation.

Ce dernier checkpoint, à **14:50:11 heure de Paris**, confirme encore `offline`,
la même image Java et le même fichier de startup. Il ne remplace pas une nouvelle
lecture des fichiers après 11:19:49 : les préconditions de contenu devront être
recontrôlées avant sauvegarde et bascule.

| Contrôle actuel | Résultat / portée |
|---|---|
| Identité | API authentifiée : 513365, adresse et port attendus |
| État | Arrêté durant les trois lectures ; aucune action d'alimentation envoyée |
| Offre | MyBoxPerf 8 ; API : 2 CPU, 8 Go de RAM, quota disque 50 Go |
| Java | Réglage 61, image `reg.sttr.io/java/25_perf:latest` ; dernier démarrage journalisé en Java 25.0.5+8-LTS |
| Paper | JAR SHA approuvé, dernier journal : 26.3-244 |
| FallenKingdom | JAR officiel SHA approuvé, dernier journal : 2.24.9 |
| FKAmis distant | Ancien JAR V2.1 `38180caa…fb31a`, version affichée 1.0.0 ; V2.2 pas installée |
| Réseau | Propriétés : jeu 22880, Query activé sur 22880, capacité 20 |
| Query / MineBoard | Dernier boot journalise Query ; pas de test réseau de service en fonctionnement puisque le serveur est arrêté |
| Accès | Authentification et whitelist strictes ; deux comptes, whitelist/OP inchangés depuis installation |
| Partie | J0, non lancée, roster et objectifs vides ; quatre équipes sans membre officiel |
| Carte | Quatre rayons 40, centres et spawns identiques au candidat approuvé |
| Règles | Capacité 4/équipe, capture 60 s et 2,5 blocs ; PvP/Nether J2, assauts J3 |
| Redémarrage jeu | Spigot `restart-on-crash=false`, timeout 60 s ; `max-tick-time=60000`, watchdog Paper conservé |
| Scripts | Startup sans boucle détectée ; aucun script exécuté par l'audit |
| Journal courant lu | Boot terminé, arrêt journalisé, fermeture des I/O ; zéro ERROR/SEVERE et zéro WARN dans cet extrait complet lu |

Les versions des JAR sont vérifiées par empreinte ; le journal décrit le dernier
processus exécuté, pas une JVM actuellement en marche. Deux plugins de production
uniquement. Aucun JAR ni joueur synthétique n'est prévu dans le transfert.

## 2. Écarts depuis l'installation V2.1

La comparaison utilise les empreintes des **302 fichiers activés avant le premier
boot du 20 novembre**, reconstituées depuis les preuves d'installation. Ce n'est
pas un ancien plan réutilisé pour transférer V2.2. Les différences incluent donc
les réécritures du premier démarrage ; leur datation exacte après ce boot n'est
pas démontrée par cette seule référence.

**311 fichiers actifs, 38 différents, neuf ajoutés, aucun manquant.** Les 311
contenus ont chacun été lus deux fois et sont restés stables pendant la lecture.

- 34 fichiers du monde diffèrent : 32 sous les dimensions, `level.dat` et sa copie.
- Deux états de plugins, `server.properties` et `usercache.json` diffèrent.
- Les propriétés effectives de `server.properties` sont identiques : sa différence
  binaire n'est pas une modification de politique de capacité ou de Query.
- Les ajouts comprennent journaux, audit arbitre, verrou et quatre fichiers d'un
  profil joueur existant. Ce profil appartient à la whitelist et à l'arbitre ;
  aucune identité ni inventaire n'est publié dans Git.
- Les JAR, accès, règles et métadonnées de carte V2.1 restent conformes aux
  empreintes de leur installation. La progression n'a pas été réinitialisée.

Une différence de monde n'est pas qualifiée automatiquement de normale : les
quatre régions concernées par la restauration ont été relues puis comparées
bloc par bloc. Les autres fichiers du monde seront conservés, pas remplacés par
la copie initiale locale. Leurs inventaires et états devront être vérifiés lors
de la sauvegarde complète autorisée.

## 3. Quarantaine et espace disque

Lecture de métadonnées seulement :

- `.fk-stage/MS-DEPLOY-V21-20261120-01` : zéro fichier.
- `.fk-quarantine/MS-DEPLOY-V21-20261120-01` : **152 fichiers, 182 616 866 octets**,
  environ 174,16 Mio. Identifiant et volume correspondent à la quarantaine créée
  pendant le déploiement V2.1 autorisé. Elle n'a pas été créée par cet audit.

La ressemblance avec la taille du monde est attendue : l'ancien arbre de monde
y a été conservé. Aucun de ses contenus n'a été relu par SHA dans ce préflight ;
la concordance de taille ne prouve pas son intégrité. Ne pas le supprimer.

Les fichiers actifs représentent **470 697 815 octets**. Avec la quarantaine,
le périmètre complet observé par métadonnées représente **463 fichiers et
653 314 681 octets**. La future sauvegarde complète doit inclure les espaces
techniques existants, pas seulement les 311 fichiers actifs. Recalculer ce
périmètre avant copie : ce nombre n'est pas une limite figée de sauvegarde.

Relevé récent fourni par le propriétaire : quota 50 Go, utilisation brute environ
625 Mo, reste estimé largement supérieur à 49 Go. Le total de 124,5 Mo avec
`overhead_applied` n'est **pas** interprété comme espace libre. L'API ne fournit
pas d'utilisation disque exploitable ici et SFTP statvfs n'est pas disponible.

Le plan propose :

| Réserve supplémentaire | Octets |
|---|---:|
| Staging des 17 fichiers | 46 746 720 |
| Quarantaine par renommage sur le même filesystem | 0 octet de duplication |
| Restauration complète parallèle, historique compris | 653 314 681 |
| Plus gros fichier temporaire | 11 403 264 |
| Marge de fonctionnement | 2 147 483 648 |
| **Total** | **2 858 948 313**, environ 2,86 Go / 2,66 Gio |

Aucune archive distante n'est prévue. **Espace estimé suffisant selon les relevés
du propriétaire**, pas une mesure indépendante de libre exact sous quota.
Recontrôler le quota juste avant maintenance et après une partie qui génère
de nouveaux chunks. La marge ne remplace pas le contrôle d'un échec quota réel.

## 4. Planifications et concurrence

Le propriétaire confirme une liste de plannings vide et aucun calendrier de
fonctionnement ; aucune action en cours observée, serveur `offline`. La file
interne des actions et le réglage de redémarrage après crash de la plateforme
restent inaccessibles. L'API lue n'expose pas de mécanisme vérifié permettant de
les désactiver. Les messages d'annonce de restart ne sont pas une telle preuve.

La [documentation officielle API](https://api.minestrator.com/) décrit les lectures
utilisées ; aucune mutation de réglage ou d'alimentation n'a été appelée. La
politique de relance de l'hébergeur n'est pas déduite de `restart-on-crash=false`.

La [page publique de statut](https://minestrator.com/statut) consultée annonce la
plateforme/API opérationnelles. Sa vue accessible ne fournit pas de preuve sur
les interventions propres à ce compte ou à cet hôte ; elle ne certifie donc pas
l'absence de maintenance future pendant notre opération.

L'absence de verrou de maintenance exclusif reste un risque résiduel : une action
humaine, une automatisation ou un service fournisseur peut intervenir entre
deux observations. Les doubles lectures ne démontrent pas l'absence d'écritures
transitoires remises à l'état initial. La prochaine sauvegarde doit respecter
[AGENTS.md](../AGENTS.md) : « Sauvegardes uniquement serveur arrêté, avec verrou
de processus partagé », ou faire l'objet d'une **nouvelle dérogation ponctuelle
explicitement approuvée**. L'accord du 20 novembre n'est pas réutilisé.

## 5. Restauration des sous-sols et réserve des deux cellules

Les quatre régions réelles sont différentes des régions de livraison initiale :
les remplacer aveuglément effacerait des écritures de recette. La simulation
part de leurs octets actuels, relus deux fois, et applique seulement les cellules
dont l'état correspond encore à l'avant V2.1 connu.

**22 219 restaurations prévues, 22 219 applicables, zéro conflit sur ces cellules.**
Quatre régions, 46 chunks concernés. Vérifications : **4 710 400 cellules** des
chunks ciblés, **4 050 corps compressés de chunks non ciblés identiques** ; NBT
hors éclairage, biomes, structures, block entities et inventaires conservés.
Seul l'éclairage des chunks modifiés est invalidé pour recalcul par Paper.

Le contrôle élargi des 37 128 cellules révèle toutefois **deux pierres devenues
de l'air**, hors de ces 22 219 restaurations. Elles sont stables dans les lectures
actuelles ; la cause et le caractère volontaire ne sont pas établis. La référence
initiale stricte refuse correctement la sortie qui les préserve. Cet échec a
arrêté la première construction locale du payload.

La proposition r2 :

- ne rebouche pas ces deux cellules ;
- conserve la référence V2.2 initiale et les artefacts approuvés inchangés ;
- inscrit explicitement deux exceptions de terrain actuel, leurs coordonnées et
  états dans une nouvelle référence **privée et non approuvée** ;
- distingue **37 126 cellules conformes à la référence initiale** et deux écarts
  conservés, sur 37 128 contrôlées ;
- porte `approvalStatus: proposed_only_not_approved` et une demande d'approbation
  dans le manifeste/plan ; ne modifie aucun validateur général pour ignorer un échec.

La proposition échoue volontairement si une exception tente de masquer une
restauration ratée sur l'une des 22 219 cellules. Elle nécessite une validation
explicite du propriétaire avant toute bascule. Le rapport privé
`natural-reference-differences-private.json` permet la revue des deux emplacements.
Leur conservation est recommandée pour respecter la consigne de préservation,
sans la présenter comme une restauration strictement identique de toute l'emprise.

## 6. Fichiers proposés et simulation de bascule

La [liste TSV](MINESTRATOR_V22_FILES_20261123.tsv) contient **17 fichiers cibles**,
leur action, taille, SHA avant/après et mode attendu : **12 remplacements et cinq
créations**. Un 18e enregistrement décrit le déplacement du seul ancien fichier
de métadonnées encore actif : `map-v21-caverns.json`.

Les cibles sont : JAR/marqueur/registre ; quatre traductions dans le fichier
français existant ; outils/références naturelles ; métadonnées de carte préservées
en UTF-8 ; quatre régions reconstruites à partir du réel ; manifeste installé
en dernier. Le nouveau manifeste gère **157 empreintes**, pas les 148 transferts
V2.1 ni une copie des 309 fichiers du candidat initial.

Seul `map-v21-caverns.json` existe réellement en racine. Il sera conservé dans
la nouvelle quarantaine et copié à l'identique sous `reference/history-v21/`.
Les trois autres anciens rapports présents seulement dans le candidat local
ne sont pas ajoutés au serveur. La carte de ravitaillements actuelle est conservée,
y compris ses libellés UTF-8 ; elle n'est pas remplacée en bloc depuis le candidat.

**298 fichiers actifs conservés** : états de partie, rôles, règles, accès,
inventaires/profils, autres régions, Nether/End, JAR Paper et FK officiel,
Spigot/watchdog et scripts. Aucun état initial local n'est importé dans la recette.
Après activation : 315 fichiers actifs attendus, hors espaces techniques.
Treize anciens fichiers iront en nouvelle quarantaine ; les 152 historiques restent
à leur emplacement. Aucun fichier n'est supprimé.

Les simulations locales de chemins/SHA réussissent : staging vérifié avant
quarantaine, activation avec manifeste en dernier, fichiers inconnus conservés,
échec injecté après début d'activation et reconstruction du modèle complet des
311 fichiers actifs d'origine. Le test refuse un rollback sans sauvegarde vérifiée.
**Il s'agit d'un modèle de chemins/empreintes, pas d'une restauration réelle de
l'instance courante.** Les droits Linux, l'atomicité des renommages, les écritures
distantes et le boot de cette intégration ne sont pas testés par cette simulation.

Les 162 tests Python passent, dont 14 nouveaux contrôles de lecture seule,
changement d'état, conflits de blocs, référence proposée et rollback. Le JAR
de jeu n'est pas recompilé : les validations Java/Paper du commit `2759630`
restent les preuves de son fonctionnement. Aucun démarrage local de partie
supplémentaire ni client authentifié n'est revendiqué ici.

## 7. Procédure d'exécution à faire autoriser

Emplacements proposés, non créés : sauvegarde PC
`C:\Users\youne\FKBackups\MS-COLD-V22-20261123-01`, staging distant
`.fk-stage/MS-V22-SWITCH-20261123-01`, nouvelle quarantaine
`.fk-quarantine/MS-V22-SWITCH-20261123-01/files/`. Ils doivent être absents lors
du contrôle frais ; ne jamais réutiliser un dossier d'essai existant.
Les exécuteurs V2.1 figés sur les 148 fichiers ne doivent pas être lancés pour
cette opération. Les nouveaux outils de cette préparation restent en lecture
seule ou en simulation locale.

1. **Revue et autorisation** : faire accepter ou rejeter explicitement les deux
   écarts conservés, le manifeste r2 et le périmètre de maintenance. Définir une
   nouvelle opération, de nouveaux dossiers de sauvegarde/staging/quarantaine.
   Confirmer les risques non levés et la procédure d'arrêt en cas de divergence.
2. **Préconditions fraîches** : identité 513365, état arrêté, versions/accès/règles,
   quota suffisant, planning et actions en attente. Toute modification de contenu
   depuis les empreintes actuelles impose une nouvelle comparaison ; ne pas
   utiliser aveuglément le payload préparé aujourd'hui.
3. **Sauvegarde complète à froid autorisée séparément** : inclure tous les fichiers
   et dossiers du root, y compris quarantaines et espaces techniques existants.
   Ne pas employer le script ancien figé sur `MS-COLD-20261119-02` avec un autre
   accord supposé. Télécharger dans un nouveau dossier privé hors Git/instance.
   Conserver serveur arrêté, verrou ou dérogation, surveillance API régulière.
4. Lire attributs listdir/lstat/FSTAT avec le comparateur corrigé ; double lecture
   SHA distante, manifeste complet, archive locale et relecture intégrale.
   Restaurer dans un second dossier neuf, vérifier chaque SHA, mondes/NBT,
   inventaires, états, plugins, politiques et permissions réellement restituables.
   Tester fonctionnellement une **autre copie locale isolée**, jamais la restauration
   originale, sans lancement de partie. Arrêter si un contrôle critique échoue.
5. Recréer l'intégration depuis cette sauvegarde actuelle vérifiée. Refaire le
   contrôle voxel, les exceptions approuvées, les 157 empreintes et les contrôles
   de partie initiale réellement applicables. Des butins consommés, un roster,
   un objectif ou une progression inattendue doivent bloquer un scellement initial,
   pas conduire à effacer les données pour passer le validateur.
6. Simuler localement le transfert concret et le rollback avec la restauration
   complète courante. Relever la liste définitive et son SHA ; aucune extension
   de fichier ou de politique ne doit être ajoutée après approbation sans revue.
7. Après autorisation de bascule : créer des dossiers neufs, transférer les 17
   fichiers en staging, lire chaque SHA et vérifier modes/propriétaires accessibles.
   Recontrôler l'état API et tous les SHA source avant tout renommage.
8. Déplacer chaque ancienne cible vers la nouvelle quarantaine, jamais l'arbre
   `world` complet. Déplacer l'ancien `map-v21-caverns.json` hors racine active.
   Activer les fichiers vérifiés, le manifeste en dernier. Vérifier la liste active,
   tous les SHA cibles, les 298 fichiers conservés, données d'accès/progression
   comprises, ainsi que les historiques. Aucun dossier de test n'est transféré.
9. Démarrer **seulement après autorisation**, accès restreint. Recette ci-dessous ;
   pas de `fka start`. Garder les versions, Query/port 22880, vingt places,
   `restart-on-crash=false`, watchdog et paramètres panel.

À chaque étape : état inattendu, mutation concurrente, disparition, quota,
permission ou SHA critique incorrect → **arrêt immédiat**. Avant activation,
conserver staging et rapports sans poursuivre. Après activation, ne restaurer
qu'après vérification des préconditions du rollback et de son autorisation.

La frontière « activation commencée » doit être journalisée **avant le premier
renommage d'un fichier actif vers la quarantaine**, pas seulement après la pose
du premier fichier neuf. Une anomalie à partir de ce point peut nécessiter le
rollback ; ne jamais démarrer une instance partiellement mise en quarantaine.

## 8. Rollback complet de cette opération

Le retour doit utiliser **la nouvelle sauvegarde actuelle du point 3**, à vingt
places et avec ses vrais profils, pas la sauvegarde historique à dix places.
Ne pas revenir au seul JAR et ne pas mélanger deux progressions.

Serveur confirmé arrêté ; sauvegarde/archive/manifeste courants revalidés ;
ancienne restauration de contrôle conservée ; destination de restauration neuve.
Préserver la tentative V2.2 en quarantaine de diagnostic. Restaurer l'intégralité
du root sauvegardé dans une zone distincte et vérifier tous les SHA, droits et
états avant activation cohérente des fichiers actifs. Les quarantaines historiques
existantes sont comparées et conservées ; aucune copie restaurée ne doit les
écraser ni remplacer une ancienne sauvegarde. Conserver également les copies
de diagnostic, même après réussite.

Contrôler les 311 fichiers actifs d'origine (ou le nombre frais de la sauvegarde),
les profils/inventaires, état de partie, mondes, JAR et accès. Un redémarrage
restreint n'est permis qu'avec autorisation et contrôles réussis ; la partie revient
en pause selon sa logique, jamais en lancement automatique. Si les préconditions
de restauration sont perdues, conserver les données et demander une intervention
ciblée ; ne pas effectuer de suppression forcée.

## 9. Recette réelle après installation autorisée

| Domaine | Contrôle réel attendu |
|---|---|
| Boot / intégrité | Versions exactes, JAR FKAmis `905b0f4b…345ca5`, deux plugins, aucun ERROR/SEVERE critique ; SHA statiques et contrôles fonctionnels après le manifeste vérifié à froid |
| Notifications | Compte Survival et arbitre Creative, quatre frontières 41→40 puis sorties, couleurs/noms, téléportations, absence de répétitions |
| Guidage | Chaque équipe voit sa seule base ; tourner/se déplacer, dimensions, mort/grâce de respawn, reconnexion ; pas de Locator Bar Vanilla |
| Carte | Quatre rayons 40, spawns sûrs, sous-sols naturels ; aucune caverne préfabriquée ; revoir les deux cellules conservées sans publier leurs positions |
| Effectifs | Formats disponibles de 1 à 4, refus du cinquième, arbitre hors roster ; pas d'obligation de seize participants |
| UI | BossBar capture et progression, ActionBar, scoreboards, chat sans conflit ni fuite de positions |
| Partie | Captures 60 s / 2,5 blocs, seuil officiel 1 ou 2, contestation, absences, élimination et Spectator, victoire |
| Query / panel | Réponse Query UDP 22880 et MineBoard : vingt places, connexions/déconnexions des vrais comptes et mise à jour des informations |
| Reprise | Arrêt/boot autorisés sur protocole restaurable ; progression en pause, inventaires et statistiques conservés, pas de reset |

La visite et les essais destructifs/partie complète nécessitent leurs autorisations
propres. Le [guide pratique](GUIDE_PARTIE_TEST_V22.md) donne les commandes exactes,
le portail, la collecte des mesures et le retour à une référence propre. Les
preuves à dix-sept connexions restent à produire si ces comptes sont disponibles.

Les SHA de monde/états sont ceux de l'installation à froid. Après le boot, Paper
peut écrire les lumières, métadonnées/compteurs, journaux et sérialisations natives ;
ne pas interpréter toute différence binaire attendue comme une anomalie. Vérifier
les propriétés effectives et la conservation des inventaires/progression, puis
analyser toute différence non expliquée. Les JAR, références et autres éléments
statiques restent soumis à leurs SHA. Les écritures normales ne constituent pas
une autorisation de reset ou de remplacement d'un état de partie.

## 10. Livraison de préparation

Le dossier privé contient le payload `proposed-payload-preserve-current-r2`, le
plan détaillé, les différences avant/après, la proposition de référence et ses
deux écarts, les traces d'attributs et observations API. L'archive proposée r2 et
son SHA sont indiqués dans le reçu. Elle contient 17 cibles et un manifeste
d'emballage `UPDATE_MANIFEST.json` **non destiné à être installé**.

Archive proposée : `v22-transition-PROPOSED-r2-private.zip`, SHA-256
`8b9b0feabd9aa569e75d87a18629882926d691ebf0158badf694a4bd98d8bb4b`.
Le JAR qu'elle contient est exactement celui retenu :
`905b0f4b11192d26cd59b82b151525ad3b69f7f1803c65760589800404345ca5`.

Ce paquet n'est ni le ZIP complet initial V2.2, ni le ZIP de construction V2.1,
ni une sauvegarde de l'instance actuelle. Les premières propositions locales
échouée/intermédiaire restent conservées. Les sauvegardes historiques, le candidat
retenu et ses archives n'ont reçu aucune écriture.
