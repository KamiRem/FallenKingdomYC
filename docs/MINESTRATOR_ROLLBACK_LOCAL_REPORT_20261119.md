# Rollback local RB-20261119-01 — contrôle interrompu

**Statut : réserve SHA levée dans la copie ; rollback fonctionnel non validé.**
La validation de maintenance historique a échoué avant tout lancement de Paper.
L'arrêt demandé au premier contrôle critique refusé a été respecté.

## Originaux préservés

Source : `C:\Users\youne\FKBackups\MS-COLD-20261119-02`.
Une preuve privée prise avant le test contient les hashes de l'archive, du manifeste,
des 305 fichiers restaurés, l'arborescence et tailles/mtime des fichiers. La même
vérification après arrêt confirme leur conservation. Aucun outil n'a été exécuté
dans la restauration originale ; aucun fichier cache Python n'y a été créé.

| Original | SHA-256 inchangé |
|---|---|
| `instance.zip` | `255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf` |
| `manifest.json` | `b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1` |
| `restore/` | 305 fichiers identiques au manifeste ; liste des dossiers et mtime des fichiers inchangés |

Les archives, manifestes et rapports antérieurs n'ont été ni réécrits ni nettoyés.
La comparaison est une preuve de contenu/arborescence et métadonnées relevées,
pas une promesse concernant les métadonnées d'accès NTFS liées aux lectures.

## Copie indépendante et correction autorisée

Destination neuve : `C:\Users\youne\FKBackups\RB-20261119-01\preproduction`.
La copie a d'abord été comparée aux 305 fichiers de l'original. Puis **seul**
`FKAmis.sha256` a été modifié manuellement, pour y inscrire :

```text
46703f7bbb5a6368b52cbac13f606857f6a9a619892e35c6c2d90b1777610442
```

Cette empreinte correspond au JAR réellement copié et à `RUNTIME_LOCK.json`.
Le marqueur ancien `83e721...` reste inchangé dans l'archive et la restauration
originales. Aucun JAR, monde, inventaire, état, rôle ou réglage n'a été remplacé.

## Validation refusée : cause précise

Commande locale exécutée dans la copie, avec bytecode Python désactivé :

```text
python -B maintenance/host_ops.py check
```

L'outil historique appelle `maintenance/serverlib.py:validate` et refuse :

```text
RuntimeError: Configuration refusée : max-players doit être 8.
```

La copie et l'original contiennent tous deux **`max-players=10`**. Le validateur
embarqué dans la sauvegarde exige littéralement `8` dans sa table `required`.
Le validateur courant du dépôt accepte pour sa part le profil privé de 5 à 20
places avec authentification et whitelist imposées. L'écart vient donc d'un outil
de maintenance historique non adapté au profil actuel, et non d'une modification
de `server.properties` par le test ou d'une nouvelle erreur de SHA.

Ce refus n'est pas une preuve de corruption des mondes/inventaires, ni une preuve
que Paper refuserait directement de démarrer. Il bloque toutefois la chaîne de
validation demandée. Il n'a pas été ignoré, et le nombre de places n'a pas été
abaissé à huit pour contourner le contrôle.

## Ce qui a été exécuté ou arrêté

| Contrôle | Résultat |
|---|---|
| Originaux et comparaison intégrale de la copie | Réussis |
| Correction du seul marqueur de la copie | Réussie |
| SHA réel du JAR / `RUNTIME_LOCK.json` | Cohérents |
| Validation par les outils sauvegardés | Refus sur la contrainte historique de 8 places |
| Démarrage local Paper, sockets et plugins chargés | **Non exécutés après le refus** |
| État historique après démarrage / contrôle de reprise | Non vérifié, puisque Paper n'a pas été lancé |
| Réinitialisation, attribution d'équipe, départ de partie | Aucun |
| Connexion API/SFTP/Minecraft vers MineStrator | Aucune initiée par l'outil |
| Transfert V2.1 ou modification distante | Aucun |

Les journaux et preuves sont privés dans `RB-20261119-01/` :
`original-preservation.json`, `maintenance-before.log`, `failure-private.log`,
`report.json`. La synthèse expurgée est `tests/results/minestrator-rollback-local.json`.

Le programme de test prépare un lancement explicite sur `127.0.0.1`, un port local
disponible, les commandes de consultation et le contrôle des sockets TCP/UDP. Il
prévoit de comparer les données historiques après arrêt. **Ces étapes n'ont pas
été atteintes** et ne sont pas présentées comme validées. Le compte local ne
dispose pas du privilège administrateur pour imposer un pare-feu sortant global ;
une éventuelle suite doit distinguer l'écoute locale d'un véritable réseau coupé.

## Limites Windows et portée fonctionnelle

La restauration conserve les octets et les métadonnées source dans son manifeste.
Le test Windows ne valide ni la remise en place des propriétaires/permissions
POSIX Linux, ni leurs effets sur le lancement sous MineStrator. Aucune validation
multijoueur, visuelle ou fonctionnelle Paper n'a eu lieu ici.

Une réussite binaire et un marqueur corrigé ne suffisent donc toujours pas à
affirmer que le rollback est fonctionnel. Le [rapport de disponibilité](MINESTRATOR_DEPLOYMENT_READINESS_20261119.md)
reste bloquant avant toute bascule.

## Étape proposée, sans reprise automatique

Qualifier puis tester la restauration avec la version courante compatible des
outils de maintenance VNext.1, depuis l'extérieur de la copie ou dans une autre
copie de test autorisée. Préserver les propriétés réelles, dont les dix places et
les protections, au lieu de les adapter à un garde-fou obsolète. Documenter la
différence d'outils, puis refaire les contrôles et le lancement local isolé seulement
dans le cadre autorisé. Aucun correctif d'outil embarqué ou nouvel essai n'a été
appliqué après le refus critique de cette opération.
