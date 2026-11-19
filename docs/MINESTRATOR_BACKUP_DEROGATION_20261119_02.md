# Dérogation ponctuelle MS-COLD-20261119-02

L'utilisateur autorise explicitement le 19 novembre 2026 une **nouvelle** sauvegarde
à froid de son instance MineStrator et une restauration de contrôle locale, après
validation du comparateur corrigé du commit `0d7877a`.

La dérogation ne vaut que pour l'opération `MS-COLD-20261119-02`. L'utilisateur
accepte le risque résiduel lié à l'absence de verrou partagé distant, selon les
[limites précédemment documentées](MINESTRATOR_BACKUP_DEROGATION_20261119.md).
`AGENTS.md` et ses règles générales restent inchangés. Aucune autorisation de
suppression, migration, modification distante ou déploiement n'est donnée.

## Destination et conservation

Nouvelle destination exclusive :
`C:\Users\youne\FKBackups\MS-COLD-20261119-02`.
La copie, l'archive, les empreintes et la restauration restent hors du dépôt Git
et hors de l'instance distante, avec ACL limitées au compte Windows courant.
Le script refuse toute destination préexistante. Le dossier `MS-COLD-20261119-01`
et ses preuves ne sont ni réutilisés, ni écrasés, ni nettoyés.

## Contrôles obligatoires

1. GET authentifiés avant la copie : identité du serveur, état `offline`, paramètres
   utiles au rollback. Aucun ordre distant d'arrêt ou de démarrage.
2. Vérification des informations de planification exposées. Si la désactivation des
   tâches/calendriers/redémarrages ne peut pas être confirmée, le signaler avant
   copie. Ce risque non résolu est expressément accepté dans cette autorisation.
   Aucun réglage distant n'est modifié pour le contourner.
3. Surveillance API toutes les cinq secondes et contrôles après copie/restauration,
   délai réseau de trois secondes. État non sûr, erreur API ou trou de surveillance
   critique : fermeture du transport SFTP et interruption, sans tentative automatique.
4. Empreinte hôte vérifiée avant le mot de passe ; SFTP uniquement en lecture.
   Copie complète, y compris fichiers cachés, verrous présents et anciennes archives.
   Liens, chemins dangereux et fichiers spéciaux refusés.
5. Comparateur corrigé : champs critiques type/taille/mtime/permissions obligatoires ;
   UID/GID manquants déclarés non vérifiés, jamais assimilés à des valeurs égales.
   Référence LSTAT par fichier, contrôle FSTAT avant/après, LSTAT après et final,
   référence conservée entre les deux passes, traces privées champ par champ.
6. SHA-256 à la copie puis **seconde lecture distante intégrale**, réinventaires,
   refus de toute différence détectée. Les valeurs absentes ne constituent pas une
   preuve de stabilité ; les limites d'observation restent explicites.
7. ZIP sans perte des fichiers originaux, manifeste externe complet et empreintes ;
   restauration dans un autre dossier local neuf, comparaison de tous les octets,
   contrôle structurel NBT/régions/JSON/YAML/JAR/état de partie.
8. Aucun démarrage de Minecraft pour cette vérification structurelle. Aucune
   prétention de test multijoueur, d'inspection visuelle ou de garantie atomique.

## Qualification du résultat

En cas de réussite : « sauvegarde et restauration vérifiées selon les contrôles
compensatoires de MS-COLD-20261119-02 ». Jamais « totalement garantie » : un
démarrage ou une écriture transitoire entre deux observations peut échapper aux
contrôles. Les permissions/propriétaires POSIX sont relevés quand disponibles ;
leur application Linux n'est pas démontrée par une restauration Windows.

En cas de contrôle critique non validé : arrêt immédiat de la copie, conservation
des données partielles privées et rapport. Aucun relancement ou affaiblissement
automatique du contrôle. La précédente opération interrompue reste non validée.

Le rapport final présentera l'état de la sauvegarde/restauration et le plan de
bascule à examiner. Même en cas de réussite, aucun des 146 fichiers V2.1 ne sera
transféré et aucune bascule ne sera effectuée sans autorisation séparée.
