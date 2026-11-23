# Dérogation conditionnelle — sauvegarde actuelle avant V2.2

## Autorisation et périmètre

Le propriétaire autorise explicitement une nouvelle sauvegarde complète de
MineStrator 513365 et ses vérifications/restaurations locales, **uniquement après
réussite du contrôle de sécurité des deux cellules**. Il accorde, pour cette seule
sauvegarde et sa vérification, une dérogation à la règle
[AGENTS.md](../AGENTS.md) : « Sauvegardes uniquement serveur arrêté, avec verrou
de processus partagé. » MineStrator ne fournit pas ce verrou via les accès
disponibles. La règle générale demeure inchangée.

**Statut : non mise en œuvre.** Le contrôle géométrique a identifié un puits
dangereux ; voir le [rapport](MINESTRATOR_V22_CELL_REVIEW_20261123.md).
La référence r2 n'est pas validée, aucune sauvegarde n'a commencé et le dossier
proposé `C:\Users\youne\FKBackups\MS-COLD-V22-20261123-01` n'est pas créé.
Ce document n'accorde ni déploiement, ni restauration distante, ni modification
de terrain. Les accords historiques ne sont pas réutilisés.

## Conditions conservées pour une éventuelle reprise

- Lever le blocage terrain avant toute copie complète.
- Recontrôler identité, serveur arrêté, versions, accès, planifications et actions
  accessibles ; déclarer les informations inaccessibles, notamment l'auto-restart
  de la plateforme et la file interne, sans inventer une garantie.
- Recontrôler quota et espace PC ; conserver le risque d'absence de verrou exclusif.
- SFTP à clé hôte épinglée avant authentification ; secrets locaux DPAPI transmis
  par stdin, aucune valeur secrète dans les arguments ou journaux.
- API toutes les cinq secondes avec échec fermé ; fermer la lecture SFTP si le
  serveur démarre, si la surveillance est perdue ou si un contrôle critique échoue.
- Inventorier et copier tout le root, y compris fichiers cachés, quarantaines et
  données techniques ; ne pas exclure `.fk-quarantine` ou `.fk-stage`.
- Conserver les contrôles listdir/lstat/FSTAT corrigés, disponibilité des attributs,
  tailles, dates, modes et double lecture distante SHA-256, puis réinventaires.
- Destination privée neuve hors Git et instance ; aucune suppression ni réutilisation
  des copies précédentes, même après échec.
- Archive et manifeste complets vérifiés, restauration distincte et comparaison
  intégrale ; démarrage isolé uniquement sur une seconde copie locale, sans partie.
- Relever permissions/propriétaires Linux, sans prétendre que Windows les applique ;
  documenter les écritures normales du boot et refuser les pertes de progression.

La surveillance périodique et les doubles lectures ne constituent pas un snapshot
atomique : une intervention entre deux observations reste possible. Une éventuelle
sauvegarde réussie sera qualifiée selon les contrôles réellement exécutés, jamais
totalement garantie en l'absence de verrou partagé.

Les opérations distantes d'écriture, renommage, suppression, alimentation,
whitelist, restauration et lancement de partie restent interdites. Aucun ancien
outil de déploiement V2.1 à 148 fichiers ne doit être exécuté.
