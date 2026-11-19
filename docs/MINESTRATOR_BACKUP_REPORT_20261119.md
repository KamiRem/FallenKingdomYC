# Rapport de sauvegarde dérogatoire — 19 novembre 2026

**Résultat : opération interrompue, aucune sauvegarde ni restauration validée.**
Dérogation : [MS-COLD-20261119-01](MINESTRATOR_BACKUP_DEROGATION_20261119.md),
acceptée explicitement par l'utilisateur pour cette seule opération.
La règle générale d'`AGENTS.md` n'a pas été modifiée.

## Déroulement réel

- Début : `2026-11-19T19:19:47.640392Z` (20:19:47 à Paris).
- Arrêt : `2026-11-19T19:20:10.151328Z` (20:20:10 à Paris).
- API authentifiée, identité du serveur vérifiée ; six observations `offline`,
  dont la dernière à `2026-11-19T19:20:10.075842Z`.
- Empreinte hôte SFTP vérifiée avant transmission du mot de passe ; authentification
  et inventaire réussis : 305 fichiers, 321 dossiers, 464 871 862 octets inventoriés.
- Espace privé créé hors dépôt :
  `C:\Users\youne\FKBackups\MS-COLD-20261119-01`.
- Le contrôle de stabilité a refusé la première phase de lecture avec
  `ConcurrentFileChange`. Aucune nouvelle tentative n'a été effectuée.

## Anomalie et portée du constat

Le code compare le type de fichier, la taille, la date de modification, le mode
et les attributs propriétaire/groupe entre l'inventaire, `lstat` et les attributs
du fichier ouvert (`FSTAT`). Il vérifie aussi le nombre d'octets effectivement lus.
Le code de refus générique ne consigne malheureusement pas quel attribut a divergé
ni à quel point précis de cette séquence.

**Il n'est donc pas établi qu'une écriture concurrente réelle ait eu lieu.**
Une différence de représentation ou de disponibilité d'attributs entre les réponses
SFTP est aussi possible. Il ne faut ni supprimer ce contrôle ni affirmer que le monde
est corrompu sur cette seule base. Le constat certain est le refus du contrôle, sans
preuve suffisante pour continuer, tandis que toutes les observations API indiquaient
le serveur arrêté.

L'examen local après arrêt confirme : zéro fichier d'instance enregistré, zéro
octet dans les fichiers de copie, absence de `instance.zip` et absence de dossier
de restauration. Les dossiers de copie vides et les éléments de diagnostic sont
conservés ; aucun nettoyage n'a été réalisé.

## Contrôles réussis et non réalisés

| Contrôle | Résultat |
|---|---|
| Documentation ciblée de la dérogation et signalement préalable du risque | Faits |
| Vérification de l'état arrêté avant copie et surveillance API | Réussies, 6 observations |
| Tâches/calendrier MineBoard désactivés, verrou distant partagé | Non démontrés ; risque accepté et déclaré avant opération |
| Clé hôte et authentification SFTP | Réussies |
| Inventaire complet et espace local disponible | Réussis |
| Stabilité d'une lecture de fichier | **Refusée** ; origine exacte non établie |
| Copie complète et double passe SHA-256 distante | Non réalisées |
| ZIP, manifeste complet et empreinte externe | Non produits |
| Restauration de contrôle | Non réalisée |
| Cohérence restaurée des mondes, inventaires, plugins, états, configurations | Non vérifiée |
| Démarrage de Minecraft, inspection visuelle ou multijoueur | Non exécutés |
| Écriture distante, commande console/alimentation, modification de Java ou carte | Aucune opération de ce type envoyée |

Les vérifications locales de l'outil (13 tests factices, chiffrement DPAPI de
métadonnées factices et lecture YAML d'un candidat de recette) ont réussi avant
l'opération. Elles ne constituent pas une validation de sauvegarde réelle.

## Éléments conservés sur le PC

Dans le dossier privé extérieur au dépôt :

- `report.json` : résultat original de l'opération, statut `aborted`.
- `api-observations.json` : les six observations API expurgées.
- `panel-settings.dpapi` : réglages du panel chiffrés pour ce compte Windows ;
  ce fichier n'est pas une sauvegarde du monde ou des joueurs.
- `download.partial/` : arborescence incomplète, sans fichier d'instance copié.

Synthèse sans identifiants dans le dépôt :
`tests/results/minestrator-cold-backup-20261119.json`.
Ne pas utiliser le dossier partiel comme point de restauration ou prérequis de
déploiement. La présence d'un dossier de destination ne vaut pas succès.

## Suite proposée, sans exécution automatique

Un diagnostic ciblé, exclusivement en lecture, devra comparer les attributs renvoyés
par `listdir`, `lstat` et `FSTAT`, en consignant le point de contrôle et les champs
divergents dans le stockage privé, sans identifiant ni secret dans les logs publics.
Ce diagnostic n'a pas été exécuté après l'arrêt demandé.

Selon le résultat, il faudra soit traiter une modification réelle, soit distinguer
les attributs indisponibles de ceux réellement modifiés sans affaiblir les contrôles
critiques taille/date/contenu. Toute reprise complète utilisera un nouvel identifiant
d'opération et une destination neuve, après revue de l'anomalie ; aucune reprise
automatique n'est effectuée sous le même identifiant.

Le [plan de bascule V2.1](MINESTRATOR_DEPLOYMENT_PLAN.md) reste documentaire.
La sauvegarde/restauration n'étant pas validée, la bascule n'est pas débloquée.
Aucun des 146 fichiers n'a été transféré et aucune autorisation de déploiement
n'est déduite de l'autorisation de sauvegarde.

## Diagnostic ultérieur autorisé séparément

Le [diagnostic ciblé du comparateur SFTP](MINESTRATOR_SFTP_DIAGNOSTIC_20261119.md)
a ensuite reproduit le refus : les UID/GID absents de READDIR sont fournis par
LSTAT/FSTAT. La comparaison brute du script confondait disponibilité et différence
de valeur. Le fichier initial de la reproduction est `start.sh`, à `lstat_before` ;
le journal original ne permet toujours pas de certifier rétrospectivement son nom.
Ce constat et le correctif n'altèrent pas le résultat historique ci-dessus :
la sauvegarde du 19 novembre reste interrompue et non validée.
