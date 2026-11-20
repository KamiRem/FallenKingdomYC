# Whitelist et recette V2.1 — procédure préparée, non exécutée

Cette procédure ne donne aucune autorisation d'écriture, de démarrage ou de
partie. Elle accompagne le manifeste des 148 fichiers du candidat
`V21-QUERY-20261120-01`, base `93fd580`. Les tests automatisés précédents ne
prouvent pas une charge à dix-sept connexions réelles.

## Identités approuvées et whitelist

La liste actuelle contient deux comptes. Ils ne sont ni retirés ni considérés
automatiquement comme les futurs seize participants et l'arbitre. Le propriétaire
doit revoir leurs identités et rôles avec ceux des nouveaux arrivants.

1. Recueillir les véritables noms Java Edition auprès des titulaires, puis
   vérifier les couples nom/UUID avec le service officiel de profils Mojang/
   Minecraft. Faire une vérification réciproque nom → UUID → nom actuel et noter
   la date et la source. Une capture officielle du profil peut appuyer le contrôle
   de possession ; ne jamais demander de mot de passe ou jeton Microsoft.
2. Pas de UUID calculé depuis un pseudo, pas de UUID offline, pas d'identité de
   test, pas de compte Bedrock/Floodgate. Un résultat de cache seul ne suffit pas.
   Si la vérification officielle est indisponible ou contradictoire, différer
   l'ajout. Aucun nom ou UUID n'est inventé dans cette préparation.
3. Conserver la liste de revue **hors Git**, en privé. Champs : nom actuel, UUID,
   rôle participant/arbitre, équipe éventuelle, source/date de vérification,
   approbation explicite du propriétaire. UUID uniques ; quatre royaumes exacts ;
   1 à 4 participants par royaume, maximum 16 ; arbitre distinct, sans équipe.
4. Soumettre la liste finale au propriétaire avant toute commande. Au maximum
   **17 identités compétitives/approuvées**, en comptant les deux entrées existantes
   si elles sont retenues. Les 20 places techniques n'autorisent pas trois comptes
   inconnus supplémentaires. Toute conservation d'un visiteur exige une décision
   séparée. Les suppressions d'anciennes entrées ne sont jamais automatiques.
5. Après autorisation dédiée, employer la console serveur :

```text
whitelist on
whitelist add <nom_Java_verifie_et_approuve>
whitelist list
```

Vérifier dans le fichier obtenu que l'UUID correspond exactement à celui approuvé.
Garder `online-mode=true`, `white-list=true`, `enforce-whitelist=true`. Au premier
login authentifié, utiliser en console `fka admin uuid <pseudo_connecte>` pour
confirmer l'UUID réellement présenté ; différer l'affectation au moindre écart.
La commande de lecture des UUID ne confère pas le rôle arbitre.

Attribuer ensuite le seul arbitre approuvé via `fka admin grant <UUID> confirm`.
Il doit être absent du roster. OP ne remplace pas ce rôle ; les participants
doivent être non OP avant départ. Affectations avant partie :
`fka assign <pseudo_connecte> <Rouge|Bleue|Verte|Jaune>` ; retrait explicite avec
`fka unassign <pseudo>` avant réaffectation. Vérifier `fka info teams` et
`fka admin list` en console privée.

La whitelist reste un **fichier conservé**, hors transfert des 148 cibles. Son
extension ultérieure constitue une modification distincte et approuvée des
politiques : archiver son état antérieur, tracer les changements et actualiser
les empreintes de politique/référence initiale. Ne pas prétendre que l'ancien
manifeste initial reste identique après ces ajouts. Si l'on veut inclure une
nouvelle whitelist dans un futur paquet, recalculer et faire approuver ce paquet ;
ne pas ajouter silencieusement une 149e cible.

Sources de gestion native : [Paper, étapes suivantes](https://docs.papermc.io/paper/next-steps/)
et [données Vanilla](https://docs.papermc.io/paper/reference/vanilla-data-files/).

## Environnement de recette

Les inspections sans destruction peuvent se faire en installation, jour 0.
Les tests de captures, éliminations, portails et statistiques doivent utiliser
une copie de recette isolée avec les mêmes versions, règles et politiques, ou
un protocole de restauration initiale V2.1 **explicitement approuvé avant les
essais**. Ne pas consommer les minerais/butins ni lancer une partie officielle
pour obtenir une preuve de recette. Ne jamais restaurer une ancienne progression
dans la nouvelle carte.

Si seule l'instance principale est disponible, préparer d'abord une référence
initiale V2.1 complète vérifiée, adaptée aux politiques finales, et les conditions
de sauvegarde/restauration à froid ; faire approuver le test et son retour au
point neuf. Aucun reset, `start`, changement de jour ou restauration n'est exécuté
par cette préparation. Sans environnement/protocole approuvé, la recette reste
en attente ; les assertions automatiques ne la remplacent pas.

## Contrôles après installation autorisée

| Domaine | Protocole et résultat attendu |
|---|---|
| Intégrité | Relire les 148 SHA cibles, les 5 fichiers conservés et le registre ; aucune ancienne région ou donnée de joueur dans les arbres neufs |
| Versions | Logs et `version` : Paper 26.3-244, Java 25, FallenKingdom 2.24.9 ; exactement les deux plugins de production, JAR FKAmis `38180c...` |
| Démarrage | Pas d'ERROR/SEVERE inattendue, avertissements examinés ; `fka status` jour 0 non lancé ; pas de `/reload` |
| Règles | `fka config list`, `fka config validate` : capacité 4, captures 60 s, rayon 2,5, deux attaquants sauf solo ; allow-flight n'accorde aucun vol aux participants |
| Équipes | Rouge/Bleue/Verte/Jaune, essais 1/2/3/4 membres et effectifs mixtes ; refus d'un cinquième sans mutation ; arbitre absent des effectifs ; changements avant départ seulement |
| Territoires | Inspecter centres/spawns et limites inclusives à ±40, refus à 41 ; quatre joueurs simultanés au rassemblement, sans suffocation ni chute ; ne pas déplacer/agrandir sans validation |
| Cavernes | Visiter les quatre accès, escaliers, éclairages et plafonds, circulation à quatre, absence de pièges artificiels ; vérifier thèmes et ressources sans extraire le budget de la référence |
| Commandes | Participant : status/info/base/stats et enregistrement de son objectif selon les règles ; refus des commandes arbitre ; arbitre UUID : commandes autorisées ; OP ordinaire sans rôle refusé |
| Téléportations/morts | `fka teams tpall` avant départ, confirmation en pause ; respawn lit sûr ou centre, protection prévue ; tous les quatre membres restent présents au roster après départ/reconnexion |
| Phases | En recette : départ manuel après confirmations, J1/J2/J3 et objectifs validés ; pas de début de partie automatique lors d'un redémarrage |
| Capture | Pour chacun des effectifs 1..4 : solo officiel capture seul, autres effectifs exigent deux présents ; 60 s continues, sortie de rayon/mort interrompent ; défenseur ou troisième équipe conteste |
| Déconnexion | Le roster officiel ne diminue pas ; départ d'un des deux attaquants interrompt si insuffisant ; départ d'un allié éloigné ne réduit pas le seuil et ne met pas toute la partie en pause |
| Élimination | Capture d'un royaume à quatre : les quatre passent spectateurs, morts/reconnexions ne les réintègrent pas ; troisième royaume éliminé => victoire du survivant |
| Statistiques/UI | Effectifs et agrégats jusqu'à 16, aucun crédit arbitre ; BossBars, scoreboards et ActionBar sans fuite de positions ; pause/fin cohérentes et état conservé au redémarrage |
| Spectateurs | Menu et suivi seulement pour éliminés/arbitre ; cibles actives, pas de coffres, retour SURVIVAL ou avantage compétitif ; pause respectée |
| Nether | Arbitre enregistre les deux cadres officiels après inspection ; status/activate/deactivate, J1 fermé, J2+ activable ; aller-retour sûr, inventaire conservé, briquet/portail supplémentaire refusé |
| MineBoard | Query UDP 22880 actif, capacité 20 et liste des seuls joueurs en ligne ; tester connexion/déconnexion, noms et délai de mise à jour ; console et whitelist restent protégées |
| Arrêt/reprise | Arrêt propre puis démarrage autorisé : aucune perte d'inventaire/statistiques/équipes ; une partie précédemment active revient en pause, pas en reprise automatique |

Le portail unique et les salles objectives exigent une configuration humaine
validée ; aucune coordonnée proposée n'est présentée comme inspectée. Conserver
les preuves privées : heures UTC, comptes approuvés, screenshots/logs, résultats
et anomalies. Tout contrôle critique échoué bloque l'ouverture officielle.

## Charge réelle et mesures

Maintenir Java 25 Performance, allocation panel, vue 8 et simulation 6. Ne pas
optimiser à l'aveugle ni augmenter la mémoire au-delà des paramètres attribués.
Les étapes ci-dessous supposent les identités réelles approuvées et connectées.

| Palier | Répartition | Échauffement / mesure minimale | Scènes |
|---|---|---|---|
| Repos | 0 participant | 5 / 5 minutes | Référence JVM, chunks et GC |
| 4 | 1 par royaume | 3 / 10 minutes | Bases/cavernes, déplacements, combat PvE |
| 8 | 2 par royaume | 3 / 10 minutes | Captures simultanées et morts/respawns |
| 16 | 4 par royaume | 3 / 15 minutes | Combat, exploration dispersée et Nether, génération normale de chunks |
| 17 | 16 participants + arbitre | 3 / 15 minutes | Même charge, arbitre en inspection/suivi ; aucun crédit compétitif pour lui |

À chaque minute : TPS 1/5/15 min, MSPT moyen et p95 si disponible, heap utilisé/
limite, mémoire processus/conteneur, compte/fréquence et pauses GC, ping médian/
p95 et par connexion problématique, chunks/entités chargés. Écarter les mesures
de démarrage du régime établi, mais conserver les pics comme observations.
Horodater tous les relevés ; ne pas confondre ping réseau et temps serveur.

La [documentation Paper](https://docs.papermc.io/paper/reference/commands/) indique
20 TPS comme cible et 50 ms/tick comme budget. `tps`/`mspt` donnent un complément
console ; utiliser spark intégré pour la mesure détaillée. D'après les
[commandes spark](https://spark.lucko.me/docs/Command-Usage), employer depuis la
console autorisée `spark tps`, `spark ping`, `spark gcmonitor` et, si nécessaire,
`spark profiler start` puis **`spark profiler stop --save-to-file`**. Vérifier
l'aide de la version installée et conserver les fichiers en privé ; ne pas
publier un profil par défaut. Ne pas forcer un GC pour améliorer artificiellement
la mesure. Si un outil n'est pas accessible par les droits du panel, noter la
mesure manquante et organiser sa lecture avec l'opérateur, sans prétendre l'avoir.

Critères proposés pour approbation : TPS durable ≥19,5, MSPT moyen <40 ms et p95
<50 ms, pas d'OOM/watchdog ni croissance mémoire durable après GC, marge mémoire
conteneur d'au moins 15 %, pas de pauses GC répétées perturbant le jeu. Repérer
ping p95 >200 ms ou hausse >50 ms par rapport au repos et en rechercher la cause ;
le réseau des joueurs peut être en cause. Ce sont des seuils de recette proposés,
pas une garantie contractuelle MineStrator. Toute dégradation à un palier bloque
le palier suivant ; conserver la preuve et diagnostiquer avant nouvel essai.

Le résultat à dix-sept connexions est **non mesuré** aujourd'hui. Aucun palier
n'est réputé réussi par les seuls corps NMS, TPS au repos ou tests unitaires.
