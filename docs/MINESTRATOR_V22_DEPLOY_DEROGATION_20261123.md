# Autorisation ponctuelle — sauvegarde actuelle et bascule V2.2

Opérations réservées à MineStrator 513365 : sauvegarde
`MS-COLD-V22-20261123-01`, préparation/bascule `MS-DEPLOY-V22-20261123-01`.
Sources : mission jointe explicitement autorisée par le propriétaire après le
commit `d837416`, puis confirmation actuelle de 50 Go disponibles dans MineBoard.
Cette valeur est une déclaration du propriétaire, pas une mesure API indépendante.

La règle [AGENTS.md](../AGENTS.md) « Sauvegardes uniquement serveur arrêté, avec
verrou de processus partagé » reste inchangée. L'utilisateur accorde une dérogation
pour cette seule sauvegarde à froid et ce déploiement, accepte l'absence de verrou
exclusif fourni par l'hôte et sa politique de relance non vérifiée. Les mécanismes
de planification sont contrôlés dans la mesure accessible ; les informations
inaccessibles restent signalées. Aucune garantie de snapshot atomique n'est ajoutée.

L'utilisateur valide les 33 états archivés du puits et ses quatre valeurs de
hauteur. Il dispense explicitement d'inspection humaine préalable, sans prétendre
qu'une visite a eu lieu et sans autoriser d'autre changement imprévu de terrain.

Conditions : identité, état arrêté et versions contrôlés à nouveau ; comparaison
des fichiers avec le dernier audit ; pin SFTP avant authentification ; secrets
DPAPI transmis par stdin ; surveillance API périodique avec interruption des
lectures/écritures en cas de démarrage inattendu ou de perte de surveillance.
Taille/date/mode/disponibilité d'attributs et doubles SHA restent obligatoires.
Tout échec critique bloque la phase suivante, sans suppression des preuves.

La sauvegarde couvre tout le root, y compris fichiers cachés, profils, inventaires,
quarantaines et verrous techniques. Destination privée neuve hors Git/instance,
archive et manifeste vérifiés, restauration originale intacte, second exemplaire
pour démarrage fonctionnel local isolé. Aucun déploiement avant réussite complète.

La reconstruction repart de cette sauvegarde, applique seulement les 22 219
restaurations et les 33 cellules approuvées avec leurs heightmaps. Règles, accès,
inventaires et structures légitimes conservés. Dix-sept fichiers prévus ; toute
extension substantielle du périmètre impose un arrêt et une nouvelle approbation.
Staging et quarantaine neufs, SHA vérifiés, activation journalisée avant le premier
renommage actif, manifeste en dernier ; aucune suppression irréversible.

Un démarrage distant unique est autorisé après installation conforme : recette
technique, J0, aucune partie, aucune création/activation effective de portail.
Query 22880, vingt places, whitelist et versions approuvées inchangées,
`restart-on-crash=false` et watchdog conservés. Aucun autre réglage panel modifié.

En cas d'échec critique après activation, arrêt propre si nécessaire et rollback
complet vers la **nouvelle** sauvegarde actuelle, après contrôles, en conservant la
tentative et tous les historiques. Aucune restauration partielle forcée. Si les
préconditions sont perdues, laisser le serveur arrêté et documenter l'intervention.
