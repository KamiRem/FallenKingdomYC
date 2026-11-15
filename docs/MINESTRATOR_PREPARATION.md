# Préparation MineStrator — 15 novembre 2026

Cette préparation s'arrête avant E. Aucun arrêt, transfert, écriture distante,
snapshot distant ou démarrage n'est autorisé par cette procédure préparatoire.
La construction locale ne change aucune version Paper/Java/FallenKingdom.

## A — accès et audit

Les guides VNext.1, déploiement, sauvegarde/restauration et le rapport de livraison
ont été examinés. Les trois livrables doivent conserver leurs empreintes dans
`tests/results/vnext1-delivery.json`. Les archives de livraison restent inchangées.
L'API officielle `https://mine.sttr.io` est joignable depuis cet environnement :
GET sans authentification sur `/server/0/live` renvoie HTTP 401. Cela ne prouve
aucun accès au serveur de jeu. Source : [documentation officielle](https://api.minestrator.com/).

OpenSSH/SFTP sont disponibles. Aucun paramètre MineStrator, clé API ou configuration
SSH n'était présent lors de l'audit ; Paramiko n'est pas installé. Le port de jeu
22880 n'est pas un port SFTP à déduire. Les paramètres fournis ensuite par l'utilisateur
ont été relevés uniquement dans un fichier local ignoré par Git. Une connexion TCP
au SFTP indiqué sur 2022 et la réception d'une bannière SSH réussissent ; aucune
authentification n'a eu lieu et l'identité de la clé hôte reste à valider. État, versions, fichiers,
espace disponible, paramètres du panel et sauvegardes réels restent NON VÉRIFIÉS.

Dans un terminal PowerShell local sans transcription, renseigner des paramètres
réels non secrets puis exécuter :

```powershell
./scripts/minestrator_secrets.ps1 -ServerId <ID> -SftpHost <HOTE> -SftpPort <PORT> -SftpUser <UTILISATEUR> -IdentityFile <CLE_PRIVEE> -KnownHostsFile <KNOWN_HOSTS>
./scripts/minestrator_audit.ps1
```

Les chevrons sont des placeholders à remplacer. La clé API est demandée par saisie
masquée, protégée par DPAPI Windows, dans `local/minestrator-secrets` ignoré par Git
et limité au compte Windows par ACL. Ne jamais la coller dans le chat, une commande,
le code ou un log. Le fichier est lié à ce compte Windows et à cette machine.
Une clé SSH protégée doit être déverrouillée dans l'agent local ; son chemin seul
est enregistré. Valider la clé hôte via une empreinte indépendante du panel/support ;
ne pas utiliser l'acceptation automatique de nouvelles clés. Aucun scan de clé ne
constitue à lui seul une preuve d'identité.

Pour les paramètres effectivement fournis et enregistrés localement, le raccourci
`./scripts/minestrator_configure_local.ps1` évite de retaper les identifiants : il
demande la clé API et le mot de passe SFTP en saisie masquée, sans connexion réseau.
Puis `./scripts/minestrator_audit.ps1` permettra la sonde API en lecture seule ;
l'accès SFTP par mot de passe restera à vérifier dans le client local.

Le script d'audit est une sonde de connexion : GET API bornés (informations, live,
sauvegardes et snapshots du compte), puis `pwd`/`ls` SFTP. Il ne sauvegarde ni
réponse brute ni listing pouvant contenir des informations privées. Il ne constitue
pas encore un inventaire distant complet. L'audit précis doit ensuite télécharger
en lecture seule les JAR, registres et configurations utiles dans un dossier privé,
calculer les SHA-256 et vérifier Java 25 dans le panel/logs. Une lecture de fichiers
actifs est un relevé d'audit, jamais une sauvegarde cohérente.

Si l'hôte impose un mot de passe SFTP, OpenSSH BatchMode ne l'automatise pas :
utiliser WinSCP/FileZilla localement avec saisie masquée, vérification de la clé hôte,
journalisation désactivée et aucun mot de passe dans une URL ou une ligne de commande.
L'option `-StoreSftpPassword` du script de configuration permet aussi de conserver
le mot de passe dans `sftp.clixml`, chiffré par DPAPI, pour un futur client automatisé.
Le script d'audit actuel ne consomme pas ce mot de passe ; le stockage ne prouve
aucune authentification. Ne pas installer ou faire confiance à un client improvisé
pour contourner cette limite. La connexion interactive d'un client SFTP reste la
solution manuelle ciblée, sans transfert avant E.
L'API n'implique ni accès SSH shell ni capacité d'exécuter Python sur l'hôte.

## B — nouvelle carte

`python scripts/prepare_minestrator.py --work .cache/mp15a` construit une nouvelle
sortie `runtime/map-v21-candidate` sous ce dossier privé. Ne pas réexécuter sur un
dossier existant : choisir un chemin court neuf sous `.cache`.
Référence d'entrée connue : `dist/fallenkingdom-preproduction-26.3.zip`, SHA-256
`8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de`.
L'approbation visuelle humaine reste à obtenir ; la référence est contrôlée
techniquement, sans profils, roster ni objectifs déclarés.

Le ZIP de construction fournit le constructeur et les références. Le ZIP de mise
à jour sert uniquement à une partie VNext existante ; il ne contient aucune carte.
La sortie initiale reçoit directement le JAR VNext.1 contrôlé, quatre rayons 40,
quatre cavernes et les outils de maintenance V2.1. Aucun état, inventaire, statistique,
historique ou progression de l'ancienne partie n'est importé.

## C — sauvegarde et simulation

La recette locale conserve une ancienne fixture synthétique VNext entière, la
sauvegarde sous verrou à froid, restaure le candidat dans un autre dossier, compare
son manifeste, démarre sur localhost, puis restaure et démarre le rollback complet.
Le diff fichier par fichier est privé : `.cache/mp15a/transfer-diff-private.json`.
Cette fixture n'est PAS une copie du serveur MineStrator actuel.

La sauvegarde du serveur réel attend E si le serveur est actif. Après autorisation :
pause/save/stop, preuve de fin Java et état arrêté dans le panel, neutralisation
temporaire de l'auto-redémarrage, snapshot complet si disponible. Si Python distant
est disponible, utiliser les verrous partagés/natifs et `maintenance/host_ops.py backup`.
Sinon télécharger toute l'instance arrêtée par SFTP, revérifier l'état arrêté avant
et après, relire les fichiers distants et comparer les SHA-256 de chaque fichier
avec la copie locale. Refuser liens symboliques, fichiers instables ou manquants.
Créer l'archive avec manifeste et SHA-256 externe localement et conserver les deux
hors instance, puis faire une restauration complète dans un dossier neuf.
Un verrou local ne démontre pas l'arrêt distant. Ne jamais nommer une copie active
« sauvegarde vérifiée ». La liste de sauvegardes API n'en prouve pas la cohérence.

## D — plan de transfert soumis à revue

Le diff réel et ses SHA restent à calculer après accès puis à revalider sur le point
arrêté. Le plan ci-dessous est conditionnel et n'autorise aucun transfert.

| Groupe | Nouvelle instance V2.1 |
|---|---|
| `paper.jar`, FallenKingdom officiel | Conserver strictement 26.3-244 et 2.24.9, SHA vérifiés |
| Runtime Java/panel/port | Java 25, port 22880, allocations et mémoire du panel conservés |
| `plugins/FKAmis-1.0.0.jar`, `FKAmis.sha256`, `RUNTIME_LOCK.json` | Révision VNext.1 et registre cohérent |
| `world/` et éventuels dossiers de dimensions | Ensemble initial V2.1 complet, jamais fusionné avec l'ancien monde |
| `plugins/FKAmis/state.yml` | État initial VNext.1, jour 0, sans roster/objectifs/historique importés |
| Config, admins UUID, whitelist/ops/bans | Revue des politiques réelles, copie ciblée explicite avant scellement ; aucun UUID inventé |
| `supplies.yml` | Configuration de la référence V2.1, pas de lots/compteurs d'une ancienne partie |
| `server.properties` | Comparer toutes les clés, conserver paramètres MineStrator et port ; imposer seulement allow-flight=true, refuser level-name incompatible |
| Métadonnées et `maintenance/` | Référence cavernes V2.1, scripts, empreintes et métadonnées associés |
| Profils, inventaires, advancements, statistiques, objectifs et historiques anciens | Uniquement dans la sauvegarde/ancienne instance conservée, jamais injectés dans la nouvelle partie |

Après audit, figer les fichiers exacts dans un manifeste privé avec hash source et
cible, empreinte globale du candidat et du backup. Représenter tout changement
matériel du plan à l'utilisateur avant écriture distante. Privilégier une destination
serveur séparée et vide, sans créer de service payant sans accord. Un simple sous-dossier
SFTP n'est pas forcément sélectionnable comme racine de serveur dans MineStrator.
Si le panel ne sait pas basculer de racine/service, préparer une procédure de
remplacement complet arrêté, avec l'ancien ensemble déplacé seulement après backup
vérifié et accord spécifique. Ne pas superposer le nouveau monde à l'ancien.

Rollback : arrêt autorisé de la nouvelle instance, conservation de ses données,
restauration de TOUT le point précédent dans un espace vide, comparaison de chaque
hash, contrôle du JAR/registre/état ancien, paramètres panel et port 22880 restaurés,
démarrage isolé puis contrôle logs/inventaires/équipes. Ne jamais remettre le seul
ancien JAR. Ne jamais ouvrir simultanément deux copies de la partie.

Risques restant à lever : accès et place disque réels, snapshot incomplet, drift
pendant maintenance, permissions de fichiers Linux, paramètres panel non exportés,
politiques d'accès, erreur de racine, inspection visuelle des quatre cavernes,
enregistrement administratif de la paire de portails et recette humaine réseau.

E reste INTERDITE tant que l'utilisateur n'a pas approuvé explicitement l'arrêt,
le transfert selon le manifeste réel et le démarrage. Cette préparation n'est pas
une demande d'approbation anticipée sur des fichiers distants encore inconnus.
