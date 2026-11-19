# Diagnostic du refus SFTP — 19 novembre 2026

Conclusion : **défaut du comparateur face aux attributs SFTP optionnels**, reproduit
en lecture seule. Aucune preuve d'écriture concurrente dans ce diagnostic. Aucun
fichier distant, règle `AGENTS.md` ou configuration Minecraft n'a été modifié.
Aucune nouvelle sauvegarde complète ni restauration n'a été lancée.

## Fichier et étape

Le premier fichier régulier renvoyé par la liste racine dans la reproduction est
`start.sh` : 422 octets, type régulier, permissions `0755`, mtime `1794069845`.
L'ancien contrôle échoue à **`lstat_before`**, avant l'ouverture du fichier distant
et avant la création du fichier de copie local. Cela explique le résultat observé
« zéro fichier copié ». Le même défaut se reproduit sur `FKAmis.sha256` et
`server.properties`.

**Limite historique :** l'opération interrompue n'avait enregistré ni le nom du
fichier ni le point précis de comparaison. Il est impossible de certifier après
coup que son premier fichier était également `start.sh`. L'étape et le fichier
ci-dessus sont ceux de la reproduction observée, pas une trace historique inventée.

## Attributs effectivement retournés

| Attribut de `start.sh` | READDIR / `listdir_attr` | LSTAT | FSTAT |
|---|---|---|---|
| Flags SFTP | 13 (`0x0D`) | 15 (`0x0F`) | 15 (`0x0F`) |
| Type | Régulier, disponible | Régulier, disponible | Régulier, disponible |
| Taille | 422, disponible | 422, disponible | 422, disponible |
| Date de modification | 1794069845, disponible | 1794069845, disponible | 1794069845, disponible |
| Mode brut | `0100755` | `0100755` | `0100755` |
| Permissions | `0755`, disponibles | `0755`, disponibles | `0755`, disponibles |
| UID | Absent, flag UID/GID non positionné | Fourni | Fourni, identique à LSTAT |
| GID | Absent, flag UID/GID non positionné | Fourni | Fourni, identique à LSTAT |

Le rapport privé consigne les valeurs numériques UID/GID, chaque valeur brute,
les flags réseau, la présence de l'attribut Python et son indicateur de disponibilité
pour chaque observation. Aucun identifiant de connexion ou contenu de configuration
n'est affiché dans les logs. La différence `0x02` correspond aux champs UID/GID.

La [documentation officielle Paramiko](https://docs.paramiko.org/en/stable/api/sftp.html)
précise que les champs retournés par un serveur SFTP peuvent être incomplets.
L'absence de ces attributs dans READDIR n'est donc pas une modification de propriété
du fichier ni, à elle seule, une non-conformité du serveur.

Sur les trois fichiers examinés, deux séries de LSTAT/FSTAT avant et après lecture
ont fourni des tailles/dates/types/modes concordants. Les deux SHA-256 de chaque
petit fichier sont identiques. Les contenus ne sont pas conservés par le diagnostic.

## Défaut exact de l'ancien script

`metadata()` convertissait les UID/GID absents en `None`, puis `assert_same()`
comparait les dictionnaires entiers par égalité. READDIR donnait donc `uid=None`
et `gid=None`, tandis que LSTAT donnait des valeurs numériques. L'inégalité du
dictionnaire déclenchait `ConcurrentFileChange` malgré la concordance des champs
critiques. FSTAT aurait également échoué sur la même comparaison.

Le simulateur de comparaison historique a été figé séparément dans le diagnostic :
la modification du code de production ne peut pas transformer a posteriori l'ancien
comparateur en un comparateur réussi. Le défaut est reproduit douze fois
(deux comparaisons historiques × deux séries × trois fichiers).

## Correction et protections conservées

- Taille, mtime, type et permissions restent obligatoires et doivent concorder.
  Une valeur critique absente, même des deux côtés, fait échouer le contrôle.
- UID/GID sont comparés lorsqu'ils sont réellement disponibles des deux côtés.
  Une différence numérique, y compris avec zéro, reste bloquante.
- Une absence n'est jamais normalisée en zéro, et deux absences sont marquées
  **non vérifiées**, jamais « égales » ou preuves de stabilité.
- Les valeurs de LSTAT constituent une référence par fichier pour les FSTAT, le
  LSTAT après lecture, la seconde passe et un LSTAT final. Un changement d'UID/GID
  disponible ou une disparition sur une même source reste bloquant.
- Si un autre type de réponse omet UID/GID, les champs concernés sont déclarés non
  comparables ; cela ne les valide pas. Les attributs manquants restent visibles
  dans les preuves et les compteurs de vérification partielle.
- Le nombre d'octets lus reste vérifié ; le SHA-256 à la copie et la seconde lecture
  distante intégrale restent obligatoires. Un contenu changé de même taille et même
  mtime reste détectable par la comparaison des empreintes.
- Les réinventaires ne traitent plus l'égalité brute de `None` comme vérification
  des métadonnées. Ils vérifient les chemins et les champs critiques, et déclarent
  les champs optionnels non vérifiés.
- Le surveillant API, les interruptions de transport, les refus des liens/chemins
  dangereux et les contrôles archive/restauration restent en place.

Les futures traces sont écrites dans `sftp-attributes.jsonl`, à l'intérieur du
dossier privé de l'opération. Chaque événement porte le chemin, l'étape, les deux
observations brutes, leurs disponibilités et le résultat champ par champ. Les
rapports d'échec privés contiennent aussi `failureDetailsPrivate`. L'ordre de copie
et l'inventaire initial sont enregistrés avant la première lecture. Ces chemins et
valeurs privés ne sont pas reproduits dans la sortie console publique.

## Résultats des vérifications

- 18 tests locaux dédiés aux attributs et à la comparaison.
- 19 autres tests locaux du client d'inventaire et de la sauvegarde compensatoire.
- Cas couverts : flags 13/15, valeurs absentes, zéros réels, champs critiques absents,
  changement de taille/mtime/type/mode/UID/GID, perte de disponibilité, changement de
  contenu à métadonnées constantes, changement entre deux passes et détails d'erreur.
- Diagnostic distant corrigé : **24 comparaisons acceptées** sur les trois fichiers,
  avec une distinction explicite entre champs vérifiés et champs non comparables.
- API surveillée et serveur observé arrêté ; empreinte hôte vérifiée avant le mot
  de passe. Aucun appel API d'écriture ni opération SFTP d'écriture.

Commandes de tests sans réseau :

```powershell
./.tools/ms-audit/Scripts/python.exe -m unittest discover -s tests -p test_sftp_attributes.py
./.tools/ms-audit/Scripts/python.exe -m unittest discover -s tests -p 'test_minestrator_*.py'
```

Les observations détaillées restent dans `local/minestrator-secrets/sftp-diagnostic-*.json`,
ignoré par Git et protégé par ACL. La synthèse expurgée est
`tests/results/minestrator-sftp-diagnostic.json`. Les preuves originales de l'échec
hors dépôt n'ont pas été écrasées ou supprimées.

## Nouvelle tentative : proposition uniquement

La cause technique étant identifiée et le correctif testé, une nouvelle sauvegarde
peut être proposée avec un nouvel identifiant et une destination neuve. Le script
reste actuellement limité à l'identifiant ponctuel déjà consommé ; il n'a pas été
réarmé et refusera la destination existante. Aucune tentative n'a été déclenchée.

Une éventuelle reprise doit préciser son autorisation et son périmètre dérogatoire,
refaire le contrôle arrêté et le signalement des planifications non vérifiées,
conserver la surveillance API et les doubles lectures, puis valider l'archive et
la restauration. Le correctif ne supprime ni les risques sans verrou partagé ni
l'interdiction de déployer V2.1 sans accord séparé.
