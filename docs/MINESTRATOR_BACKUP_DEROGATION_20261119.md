# Dérogation ponctuelle MS-COLD-20261119-01

Autorisation explicite de l'utilisateur du 19 novembre 2026 : sauvegarde de
l'instance MineStrator actuelle et restauration de contrôle, avec acceptation du
risque résiduel lié à l'absence de verrou de processus partagé sur l'hôte.

`AGENTS.md` conserve sa règle générale : « Sauvegardes uniquement serveur arrêté,
avec verrou de processus partagé. » Ce fichier documente une exception pour
**cette seule opération**, et ne modifie pas cette règle pour les autres sauvegardes,
serveurs, migrations ou déploiements. L'acceptation est celle de l'utilisateur,
pas une garantie technique ajoutée par l'agent.

Le serveur a été observé arrêté par GET authentifiés le 19 novembre à
`2026-11-19T19:10:59.4104688Z`. Un nouveau contrôle doit réussir avant toute copie.
Les accès API/SFTP disponibles n'exposent pas de preuve complète des tâches,
du calendrier MineBoard, d'actions en attente ou de leur désactivation. Le risque
a été signalé avant la copie ; il est couvert par l'acceptation résiduelle donnée
dans cette demande. Aucun paramètre distant de planification ne sera modifié.

## Contrôles compensatoires obligatoires

- API live avant copie, toutes les cinq secondes et après les opérations, avec
  délai réseau de trois secondes. Tout état autre que `offline`, réponse invalide,
  échec d'accès ou trou de surveillance critique annule l'opération.
- La clé hôte SFTP est comparée à l'empreinte fournie avant l'authentification.
- Inventaire complet des fichiers et dossiers, y compris fichiers cachés et fichiers
  de verrou présents : aucune exclusion des sauvegardes antérieures. Liens,
  fichiers spéciaux, chemins dangereux et collisions Windows entraînent un arrêt.
- Contrôle taille/date/mode avant et après chaque lecture ; SHA-256 à la copie,
  puis seconde lecture distante intégrale de chaque fichier et comparaison.
- Réinventaire pour détecter les ajouts, suppressions et changements de métadonnées,
  avant et après la relecture et en fin d'opération.
- Un état serveur non sûr détecté par le surveillant ferme le transport SFTP pour
  interrompre les lectures ; les copies partielles sont conservées et non validées.
- Copie privée, ZIP, manifeste externe et restauration dans des dossiers neufs
  hors du dépôt et hors de l'instance. Aucun ancien fichier local n'est écrasé.
- Relecture intégrale du ZIP et de la restauration, comparées au manifeste ;
  vérifications structurelles Minecraft sans démarrer Paper.

La destination de cette opération est un sous-dossier privé
`C:\Users\youne\FKBackups\MS-COLD-20261119-01`. Le script refuse sa réutilisation.
La disponibilité d'espace et les ACL utilisateur doivent être vérifiées avant copie.
Les secrets sont lus depuis DPAPI et passent au client par son entrée standard,
jamais en arguments, variables d'environnement ou journaux. Les réglages du panel
nécessaires au rollback sont conservés séparément, chiffrés avec DPAPI.

## Limites assumées

La surveillance est périodique, pas instantanée : jusqu'à cinq secondes plus le
délai de réponse réseau peuvent précéder une détection. Une écriture puis son
annulation entre deux lectures, ou un démarrage très bref entre deux observations,
peuvent échapper aux contrôles. Les dates SFTP ont une précision limitée. Deux
lectures identiques renforcent la confiance sans constituer une capture atomique.
Le service SFTP peut mettre à jour des métadonnées d'accès du système : aucune
opération applicative d'écriture n'est envoyée par le client.

Les permissions POSIX et propriétaires sont relevés, mais une restauration sur
Windows ne démontre pas leur application sur Linux. L'analyse structurelle et
l'identité des octets ne remplacent pas un démarrage fonctionnel de Paper, une
inspection visuelle ou un test multijoueur. Aucun de ces tests n'est prétendu fait.

Les scripts utilisent uniquement des GET API et des lectures/listes SFTP. Aucun
arrêt/démarrage distant, snapshot, suppression, migration, écriture de verrou sur
l'hôte, changement de Java ou transfert des 146 fichiers n'est autorisé ici.
En cas d'anomalie, arrêt de la copie et rapport ; aucune nouvelle tentative complète
automatique. Même en cas de réussite, le résultat sera qualifié **vérifié selon les
contrôles compensatoires**, jamais totalement garanti sans verrou partagé.

Sources consultées : [API officielle](https://api.minestrator.com/),
[tâches planifiées](https://minestrator.com/blog/article/tache-planifiee-minestrator-automatiser-serveur),
[calendrier de fonctionnement MineBoard](https://minestrator.com/blog/article/minenews-9-google-apple-passkeys-panel-plus-rapide).
