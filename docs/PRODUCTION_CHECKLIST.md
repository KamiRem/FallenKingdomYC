# Checklist finale — validation humaine avant lancement

État au 7 novembre 2026 : préparation technique locale ; **hébergeur non commandé,
recette à huit non exécutée, partie officielle non lancée**. Reporter les résultats
de la livraison dans `tests/results/preproduction-package.json` et ceux des démarrages
dans `tests/results/preproduction-smoke.json` / `paper-26.3-migration.json`.

- [x] Sauvegarde intégrale privée de `runtime/map-v2-fixes` vérifiée à froid.
- [x] Carte visuellement approuvée par le propriétaire dans sa demande ; aucun chantier reconstruit.
- [x] Contrôle technique local : source et fichiers de monde conservés, paquet restaurable, deux JAR seuls.
- [ ] Lire l’audit : décider de la version retenue ; traiter le risque Paper 26.2 hors maintenance.
- [ ] Choisir l’hôte, confirmer prix final TTC mensuel ≤25 €, localisation, Java 25, JAR custom et marge mémoire.
- [ ] Commander personnellement ; conserver accès panel/SFTP en privé et sécuriser le compte.
- [ ] Transférer dans une instance de préproduction vide/arrêtée, vérifier les empreintes.
- [ ] Configurer le port réel, l’écoute, Java 25, heap et sauvegardes ; désactiver les mises à jour automatiques.
- [ ] Authentification officielle et whitelist imposées ; huit comptes, participants non OP, console réservée à l’admin.
- [ ] Logs propres, deux plugins actifs, jour 0, carte/dimensions/butin/sites conformes.
- [ ] Exécuter tous les scénarios de recette avec huit comptes authentifiés, joindre preuves et signatures privées.
- [ ] Mesurer TPS/MSPT/RAM/ping à huit ; aucune anomalie bloquante restante.
- [ ] Prouver une sauvegarde et une restauration complètes sur l’hébergement choisi.
- [ ] Arrêter/archiver la recette ; restaurer le ZIP initial dans un espace neuf, même version.
- [ ] Réattribuer les binômes, confirmer terrains/spawns, contrôler absence de données de recette et de secrets publiés.
- [ ] Sauvegarder la préparation officielle à froid et vérifier le point de reprise.
- [ ] Accord humain final avec les huit connectés ; saisir `fka start` uniquement à ce moment.

Signatures privées : responsable, date UTC, huit participants, version retenue,
empreinte de l’archive initiale et de la sauvegarde précédant le lancement.
