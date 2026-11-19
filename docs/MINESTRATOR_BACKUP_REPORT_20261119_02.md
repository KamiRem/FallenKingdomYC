# Sauvegarde MS-COLD-20261119-02 — rapport final

**Intégrité de la sauvegarde et restauration binaire vérifiées sous dérogation.**
**Réserve applicative : marqueur `FKAmis.sha256` incohérent dans l'instance source.**
Aucune autorisation de déploiement ; arrêt après constat de cette anomalie lors du
contrôle local complémentaire. Aucun correctif n'a été appliqué aux données.

La [dérogation -02](MINESTRATOR_BACKUP_DEROGATION_20261119_02.md) est explicitement
autorisée par l'utilisateur pour cette opération seulement. `AGENTS.md` est inchangé.
Le comparateur corrigé de `0d7877a` a été utilisé ; ses 37 tests locaux passent.

## Opération et destination

- Début : 19 novembre 2026, `20:13:54.355975Z` (21:13:54 à Paris).
- Fin de l'outil : `20:20:54.764604Z` (21:20:54 à Paris), environ sept minutes.
- Destination privée : `C:\Users\youne\FKBackups\MS-COLD-20261119-02`.
- **305 fichiers et 321 dossiers**, 464 871 862 octets source, sans exclusion des
  fichiers cachés, anciennes sauvegardes, `session.lock` ou manifestes historiques.
- Archive : `instance.zip`, 413 245 391 octets.
- Restauration neuve : `restore/` ; les 305 fichiers sont identiques au manifeste.
- Dossier `MS-COLD-20261119-01` préservé : tous ses fichiers et son arborescence
  ont été comparés au relevé de conservation pris avant -02. Aucun écrasement/nettoyage.

## État distant et stabilité

L'identité et l'arrêt du serveur ont été vérifiés par GET authentifiés avant copie.
Pendant l'opération, **86 observations API sont toutes `offline`**, avec un intervalle
maximal observé de 5,140322 secondes. Un GET supplémentaire après la restauration,
à `20:22:30.6983612Z`, confirme encore `offline`. Aucune commande de console,
alimentation, migration ou écriture SFTP n'a été envoyée.

Les réglages API ne donnent pas de preuve vérifiable de désactivation des tâches,
du calendrier ou des relances externes. Ce risque a été annoncé avant la copie ;
aucune désactivation distante n'a été prétendue ou effectuée. Le risque résiduel
sans verrou partagé reste expressément accepté pour -02, sans étendre cette
autorisation au déploiement.

La clé hôte a été vérifiée avant le mot de passe. Chaque fichier a été contrôlé
par LSTAT/FSTAT avant/après lecture, puis relu intégralement une seconde fois avec
comparaison SHA-256. Les inventaires initial/intermédiaires/final sont concordants
sur leurs chemins et champs critiques. Aucun changement de contenu, taille, date,
type ou mode n'a été détecté par ces contrôles.

UID/GID : 305 références de fichiers connues via LSTAT, aucune référence de fichier
sans UID/GID ; les champs manquants de READDIR ne sont jamais déclarés égaux. Les
propriétaires de 321 dossiers restent non vérifiés par le listing. Les traces
privées `sftp-attributes.jsonl` distinguent valeurs, disponibilité et comparabilité.

## Archive, manifeste et restauration

Le manifeste **externe** `manifest.json` référence chaque fichier et dossier,
ses métadonnées relevées et chaque SHA-256 de contenu. Le `BACKUP_MANIFEST.json`
historique présent sur l'hôte est conservé comme un fichier source ordinaire,
pas réutilisé comme preuve du nouveau point. Les éventuelles anciennes archives
sont copiées intégralement ; leur contenu interne n'est pas restauré récursivement.

La liste du ZIP est comparée au manifeste, chaque contenu est relu avec contrôle
CRC/SHA-256 lors de la restauration, puis chaque fichier restauré est de nouveau
haché. Les listes de fichiers et de dossiers sont identiques, dossiers vides compris.
Les empreintes finales et leurs sidecars ont également été relus et comparés.

```text
instance.zip
255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf

manifest.json
b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1
```

Les fichiers `instance.zip.sha256` et `manifest.json.sha256` sont adjacents. Les
rapports, journaux API, traces SFTP, inventaire initial et ordre de téléchargement
sont aussi conservés dans le dossier privé. Les réglages de panel sont dans
`panel-settings.dpapi`, chiffrés pour le compte Windows local. Ni sauvegarde, ni
profil, ni configuration privée ne sont placés dans Git.

## Contrôles structurels réellement réussis

| Contrôle | Résultat |
|---|---:|
| Régions Anvil vérifiées (en-têtes, bornes, secteurs, décompression) | 76 fichiers |
| Chunks NBT décodés | 21 865 |
| Autres fichiers NBT du monde | 46 |
| Fichiers de profils NBT, variantes historiques comprises | 4 fichiers, pas 4 joueurs annoncés |
| Enregistrements NBT contenant des listes d'inventaire | 1 549, listes vides comprises |
| JSON analysés | 26 |
| YAML analysés par SnakeYAML SafeConstructor | 19 |
| JAR contrôlés par CRC, dont Paper et plugins | 3 |
| Empreintes attendues Paper, server.jar, FallenKingdom et FKAmis | Conformes |
| Registre RUNTIME_LOCK et JAR actifs | Cohérents |
| État FKAmis | Schéma 1, structure native et 4 spawns présents |

Les inventaires et données de partie ont été préservés octet par octet. Ce contrôle
ne prétend pas vérifier leurs effets en jeu. Minecraft n'a été démarré ni localement
ni à distance ; seul le lecteur YAML sûr a utilisé la JVM locale.

## Anomalie source révélée au contrôle complémentaire

Le fichier source **`FKAmis.sha256` est périmé** :

```text
Valeur annoncée par FKAmis.sha256 :
83e721d8ac12feefdb590976747f88d6825b3243976c7e9f10b1cc35fac5239d

SHA-256 du JAR réellement sauvegardé/restauré :
46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442
```

Le second correspond bien à VNext.1 et à `RUNTIME_LOCK.json`. L'anomalie ne vient
pas du transfert : le marqueur a exactement le contenu vérifié lors des deux
lectures distantes. La sauvegarde et sa restauration reproduisent donc fidèlement
cette incohérence préexistante.

Le `maintenance/serverlib.py` sauvegardé compare ce marqueur au JAR (lignes
170–172) et peut refuser sa validation/démarrage contrôlé. Cela ne prouve pas que
le lancement direct par MineBoard échouerait ; aucun démarrage n'a été testé.
Il est interdit de déclarer le point prêt à redémarrer sans réserve applicative.

L'opération a été arrêtée à ce constat complémentaire : aucun fichier distant,
archive, marqueur sauvegardé ou fichier restauré n'a été corrigé. Le rapport brut
de l'outil est conservé tel quel (`verified_under_derogation` pour ses contrôles),
et `verification-supplement.json` consigne ce contrôle supplémentaire non validé.
Le statut consolidé distingue **intégrité vérifiée** et **préparation applicative
non validée**. La réserve doit être examinée avant toute bascule ou reprise.

## Limites et risques non éliminés

- Aucun verrou partagé distant : pas de capture atomique ni garantie totale. Un
  démarrage/une écriture très bref, puis annulé entre observations, peut échapper
  aux contrôles. Les dates SFTP ont une précision limitée.
- Planifications/redémarrages non démontrés désactivés ; observation API périodique,
  pas surveillance continue de chaque événement de l'hôte.
- Dates/modes/propriétaires source sont enregistrés dans le manifeste. La restauration
  Windows vérifie chemins et octets, pas une remise à l'identique des horodatages,
  propriétaires et permissions POSIX. Le manifeste devra guider leur remise en place
  sur Linux avec le bon compte, lors d'un rollback autorisé.
- Pas de validation fonctionnelle Paper, multijoueur, de salles ni d'inspection visuelle.
- Une sauvegarde fidèle peut contenir une configuration source incohérente : c'est
  le cas du marqueur périmé, conservé et signalé, non réparé silencieusement.

## Statut et suite

Sauvegarde et restauration **vérifiées selon les contrôles compensatoires -02**,
avec réserve applicative bloquante pour déclarer une remise en service validée.
Aucune nouvelle action distante après le contrôle final, aucune suppression et
aucun des 146 fichiers V2.1 transféré.

Le [plan de bascule rattaché à ce point](MINESTRATOR_BASCULE_PLAN_AFTER_BACKUP_02.md)
est présenté pour revue, avec l'anomalie et le rollback complet. Toute bascule
attend une autorisation séparée. Ce rapport n'en constitue pas une.
