# Déploiement de la version approuvée

La préparation du **7 novembre 2026** remplace les anciens conseils de transfert et
les comparaisons tarifaires du 6 novembre. `runtime/map-v2-fixes` reste une référence
intacte, visuellement approuvée par le propriétaire. Ne pas la démarrer pour la recette.

- [Audit : versions, maintenance, sécurité et résultats réellement exécutés](PREPRODUCTION_AUDIT.md).
- [Hébergement : MyBox Perf 8 à 23,99 € TTC/mois, alternative MyBox 8 à 13,99 €](HOSTING_COMPARISON.md).
- [Installation pas à pas : Java 25, JAR custom, SFTP, mémoire, whitelist et console](HOST_INSTALLATION.md).
- [Recette avec huit comptes authentifiés et mesures de charge](MULTIPLAYER_ACCEPTANCE.md).
- [Sauvegarde et restauration intégrales à froid](BACKUP_RESTORE.md).
- [Lancement propre depuis une nouvelle restauration de l’archive initiale](OFFICIAL_LAUNCH.md).
- [Checklist avant lancement humain](PRODUCTION_CHECKLIST.md).

Le paquet privé exact, son SHA-256 et le contrôle des fichiers sont dans
[preproduction-package.json](../tests/results/preproduction-package.json). Il contient
les mondes/dimensions, deux plugins de production, configurations, état initial,
coordonnées de ravitaillement, références de butin et maintenance portable. Les accès
administrateur et comptes de visite sont exclus ; aucun monde n’est publié dans Git.

Le ZIP de référence reste **Paper 26.2-135**, hors maintenance. La branche de test
`test/paper-26.3-preprod` vérifie Paper 26.3-244 sur des copies indépendantes ; ses
fixtures ne doivent pas être transférées sur l’hébergement. Aucun downgrade d’un
monde converti, aucune mise à jour automatique du JAR. La recette à huit et la
validation de version restent requises avant une partie officielle.

Aucun abonnement commandé, aucun fichier de serveur distant modifié, aucune partie
officielle lancée pendant cette préparation.
