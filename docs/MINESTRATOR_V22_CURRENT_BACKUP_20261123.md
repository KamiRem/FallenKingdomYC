# Sauvegarde actuelle complète — MS-COLD-V22-20261123-01

**Sauvegarde vérifiée sur le plan binaire, structurel et fonctionnel en local.**
Il s'agit de l'instance V2.1 actuelle à vingt places, avant bascule V2.2, et non
de la sauvegarde historique à dix places. La dérogation et ses limites sont
décrites [ici](MINESTRATOR_V22_DEPLOY_DEROGATION_20261123.md).

## Périmètre et intégrité

Destination privée neuve hors Git et instance :
`C:\Users\youne\FKBackups\MS-COLD-V22-20261123-01`.

- **463 fichiers, 366 dossiers, 653 314 681 octets** dans le relevé complet.
- 311 fichiers actifs et 152 fichiers techniques/historiques ; les namespaces
  de staging et de quarantaine sont inclus, y compris les dossiers vides.
- Tous les profils, configurations, rôles, inventaires, mondes, états et journaux
  présents dans le relevé sont copiés. Le `session.lock` technique est inclus.
- Les fichiers indisponibles lors de la répétition partielle précédente sont
  désormais présents ; aucune reconstruction de leurs données n'est supposée.

| Artefact privé | SHA-256 |
|---|---|
| `instance.zip` | `18b387d5c824c5a892c98dcf1c009ce22666c09228ab2df42bd8434692656684` |
| `manifest.json` | `758654db5341f361b0bcb7125eb94e1671275fab34b47f17fb71776f4a33e21d` |

Les deux lectures SFTP de chaque fichier concordent. Les contrôles corrigés
listdir/lstat/FSTAT, tailles, dates, modes, disponibilité d'attributs et arbres
avant/après sont conservés. Les valeurs optionnelles absentes ne sont pas utilisées
comme preuve d'égalité. Clé hôte vérifiée avant authentification, secrets DPAPI
transmis par stdin, aucune écriture applicative distante pendant la sauvegarde.

Le nouveau relevé des 311 contenus actifs correspond au dernier audit. L'API
authentifiée confirme serveur 513365 arrêté, Java 25 Performance et paramètres
approuvés. La surveillance poursuit ses observations pendant copie, relecture,
archive et restauration : **115 observations API** sur cette opération, arrêtées
proprement après le dernier contrôle à froid. Aucun démarrage ni arrêt distant
n'est commandé par la sauvegarde.

## Restauration et contrôles structurels

L'archive est extraite dans `restore`, dossier neuf. Tous les fichiers et dossiers
sont comparés au manifeste ; chaque fichier extrait est relu et vérifié par SHA.
Cette restauration originale est conservée intacte.

- **152 fichiers de régions, 43 711 chunks décodés**, quarantaines comprises.
- Dans les mondes actifs : 76 régions, 21 846 chunks et 44 fichiers NBT.
- CRC des **111 JAR** du périmètre complet ; JSON et **33 YAML** analysés.
- Schéma de partie 1 et quatre spawns présents ; JAR/registre runtime cohérents.
- Propriétaires et modes SFTP conservés comme métadonnées de preuve. Windows
  ne démontre pas l'application de propriétaires ou permissions POSIX Linux.

## Validation fonctionnelle indépendante

Une seconde copie complète est créée sous
`MS-DEPLOY-V22-20261123-01/rollback-local/instance` ; elle ne remplace pas `restore`.
La maintenance accepte explicitement le profil MineStrator à vingt places et
Query activé. Démarrage réel en Java 25.0.5, Paper 26.3-244, FK officiel 2.24.9
et ancien JAR FKAmis V2.1, puis arrêt propre : **zéro erreur, zéro avertissement**.

Les écoutes TCP et UDP sont vérifiées sur localhost ; Query répond à vingt places
avec zéro joueur. Aucun client authentifié, aucune partie démarrée, aucun accès
API/SFTP distant utilisé par cette validation locale.

Conservation après le boot :

- 76 régions et 21 846 chunks : aucun ajout ou retrait ;
- inventaires et butins comparés sur **996 emplacements** ;
- équipes natives, territoires, spawns, objectifs et état historique conservés ;
- **quatre fichiers joueur** protégés par SHA ;
- **152 fichiers techniques/historiques** strictement inchangés ;
- politiques d'accès et JAR conservés ; maintenance réussie avant et après.

Les différences normales de session, journaux, sérialisation, caches et métadonnées
de monde sont relevées dans `rollback-local/runtime-differences-private.json`.
Elles restent sur la copie de test. L'archive, le manifeste et tous les fichiers
de la restauration originale restent identiques. Ce test valide le retour vers
la sauvegarde actuelle ; il ne constitue pas une restauration distante effectuée.

## Limites et conservation

Le propriétaire confirme actuellement 50 Go disponibles sous quota. Il s'agit
d'un relevé déclaré : l'API ne fournit pas de libre sous quota exploitable et
SFTP statvfs n'est pas supporté. Planifications internes, file d'alimentation et
politique de relance fournisseur restent inaccessibles par ces accès ; la
poursuite est explicitement demandée après signalement de ces limites.

Sans verrou partagé, l'absence de toute écriture transitoire ne peut être prouvée.
Le résultat est **vérifié selon les contrôles compensatoires autorisés**, pas un
snapshot atomique totalement garanti. La surveillance périodique ne constitue
pas un verrou de maintenance exclusif.

Les sauvegardes historiques, leurs manifestes/restaurations, les anciens candidats
et quarantaines ne sont pas modifiés. Le rollback doit utiliser cette nouvelle
archive complète ; ne pas lui substituer l'archive historique à dix places ni
les copies de démarrage modifiées par Paper.
