# V2.2 — terrain d'origine et notifications de territoire

**Prêt pour inspection locale. Aucun déploiement, aucune connexion à MineStrator.**

La révision `V2.2-vanilla-underground` supprime les quatre chantiers de cavernes
en restaurant les états de blocs de la référence antérieure approuvée. Elle
ajoute un repli indépendant de notification dans FKAmis pour l'arbitre.
Les résultats détaillés sont dans le
[reçu technique](../tests/results/vanilla-underground-20261123.json).

Tous les mondes, archives, plans avec coordonnées et journaux restent privés :
**`C:\Users\youne\FKBackups\V22-VANILLA-20261123-01`**.
Les données de recette actuelles de MineStrator n'ont pas été téléchargées,
fusionnées ni modifiées pendant cette mission.

## 1. Référence retrouvée et restauration fidèle

La source est `dist/fallenkingdom-preproduction-26.3.zip`, SHA-256 :

```text
8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de
```

Cette archive approuvée contient le monde converti en 26.3, les constructions
légitimes antérieures, et aucune métadonnée des cavernes V2.1. Ses blocs ont été
comparés aux valeurs « avant » du plan historique : **37 128 cellules, zéro
divergence de matériau**. Les propriétés complètes des blocs proviennent de
l'archive, pas des seuls noms consignés dans le plan.

**22 219 états de blocs sont restaurés dans 46 chunks et quatre régions.**
La restauration inclut les anciens escaliers, accès et minerais ajoutés pour les
cavernes, en leur rendant l'état archivé : roche, minerai naturel, terre, air,
fluide et propriétés correspondantes. Aucune génération aléatoire, aucun nouveau
dessin de caverne. Les cavités naturelles retrouvent leurs blocs d'air d'origine.

La comparaison complète des 46 chunks, sur **1 150 sections / 4 710 400 cellules**,
confirme leur terrain identique à celui de l'archive initiale, avec normalisation
des propriétés par défaut du registre réel Paper 26.3. Dans les quatre régions,
les corps compressés de **4 050 chunks non ciblés** restent identiques à V2.1.
Les horodatages de chunks non ciblés restent identiques.

Les quatre fichiers de terrain concernés sont :

```text
world/dimensions/minecraft/overworld/region/r.-1.-1.mca
world/dimensions/minecraft/overworld/region/r.-1.0.mca
world/dimensions/minecraft/overworld/region/r.0.-1.mca
world/dimensions/minecraft/overworld/region/r.0.0.mca
```

Le plan exact cellule par cellule est `restoration-plan-private.json`.
`file-differences-private.json` donne tous les chemins et SHA avant/après.
Le reçu public contient les quatre empreintes de région, sans publier le plan
des sous-sols ni les coordonnées des objectifs.

`baseline-v21-world.zip` n'a **pas** été utilisé comme référence de terrain :
il contient les premières cavernes. Le nouveau `before-v22-local.zip` conserve
l'instance locale V2.1 complète comme point de retour, avec ces anciennes
cavernes ; son rôle est celui d'un rollback, pas d'une référence géologique.

## 2. Éléments conservés

La copie de départ est la référence V2.1 initiale approuvée
`V21-QUERY-20261120-01/preproduction-candidate`. Elle est restée inchangée.
La variante `V2.1-natural-caverns-r2` est **abandonnée**, mais ses archives,
candidat et preuves ont été conservés et recontrôlés. Elle n'est pas une entrée
de cette reconstruction.

Contrôles réussis sur V2.2 :

- quatre bases, spawns et territoires natifs de rayon 40 ;
- sept monuments et 6 689 blocs de référence ;
- huit sites de ravitaillement et six inventaires de coffres de référence ;
- biomes, structures, block entities, inventaires et autres champs NBT des
  chunks, conservés par rapport à V2.1 ;
- fichiers des dimensions Nether et End, entités, points d'intérêt et métadonnées
  persistantes du monde inchangés ;
- `state.yml`, configurations FKAmis, rôles arbitre, whitelist et OP identiques ;
- règles de capture, effectifs et progression inchangés, jour 0 non lancé.

L'éclairage des seuls chunks restaurés est invalidé explicitement puis recalculé
par Paper. Les verrous temporaires `.control.lock` et `session.lock` sont exclus
des copies/archives et recréés pour chaque instance. Les archives historiques et
la restauration originale `MS-COLD-20261119-02` n'ont reçu aucune écriture ; les
empreintes de l'archive et de son manifeste sont recontrôlées.

Versions et paramètres conservés : Java 25, Paper 26.3-244, FallenKingdom
**officiel inchangé** 2.24.9, FKAmis 1.0.0 révisé, quatre équipes de 1 à 4,
maximum 16 participants et arbitre hors effectifs, vingt places, jeu/Query 22880,
whitelist stricte, capture 60 s / 2,5 blocs. Le candidat reprend le correctif
Spigot approuvé `restart-on-crash=false`, avec watchdog conservé. Aucun paramètre
du panel MineStrator ou de l'image Java 25 Performance n'a été modifié.

## 3. Cause exacte de l'absence des notifications

La chaîne historique est `MoveListener` → `RegionChange` →
`GlobalDisplayService.dispatch` → canal chat du plugin officiel.
Le canal `notification.region-change: chat` est actif dans la référence.

**Cause reproduite :** le pont FKAmis `NativeAdminBridge` exempte les comptes
arbitres des handlers natifs de protection, dont `MoveListener`. Il retourne
avant d'appeler ce listener pour l'arbitre. La notification, produite dans ce
même listener, disparaît donc avec lui. Le filtre porte sur le rôle UUID de
l'arbitre, pas sur le seul mode Creative ou le statut OP.

Une autre branche native retourne avant les notifications lorsque la partie
est en pause profonde et qu'un joueur Creative/Spectator se déplace à hauteur
constante. Cette branche concerne la pause, pas un blocage général du jour 0 :
le natif est en `BEFORE_STARTING` au jour 0, et les comptes Survival/OP de la
sonde reçoivent déjà leur notification.

La réduction 80 → 40 n'est pas la cause : la détection utilise les bases natives
avec leur rayon réel. Les frontières 41/40 sont confirmées. Aucune régression
d'API d'envoi n'est observée sur Paper 26.3 : les paquets chat natifs sont bien
produits. Les BossBars, Titles et ActionBars de FKAmis n'effacent pas ce chat.

Le diagnostic combine lecture du pont FKAmis, sources locales du plugin officiel,
contrôle du bytecode du JAR figé et reproduction sur ce JAR. Il ne prétend pas
constituer un nouvel audit de la configuration distante du 23 novembre.

## 4. Correction indépendante et présentation

Le JAR officiel n'est ni modifié ni recompilé. Les exemptions de protection de
l'arbitre restent en place, y compris les gardes de pause, TNT et spectateurs.

`TerritoryNotifications` observe les destinations finales aux événements de
mouvement/téléportation, après les protections. Il réutilise `Base.contains`,
le canal de notification et les couleurs natifs. Lorsque le listener officiel
a déjà produit son `RegionChange`, aucun repli supplémentaire n'est envoyé.
Une mémoire transitoire par joueur supprime les répétitions dans un même
territoire ; elle est retirée au départ et à l'arrêt du plugin.

Le repli fonctionne au jour 0, en jeu, pour l'arbitre Creative et lors des
téléportations autorisées. Les changements de dimension et arrivées sont
synchronisés sans doublons. Un événement annulé n'actualise pas la position.
Les éliminés et spectateurs ordinaires n'obtiennent pas de repli supplémentaire.
Les éventuelles notifications publiques du natif déjà présentes en jeu pour
ces comptes restent inchangées dans leur portée ; aucun coffre, objectif ou
position cachée n'est révélé. Le statut OP ne crée aucun droit d'arbitre.

Quatre clés françaises configurables du plugin officiel sont adaptées :

```properties
player.base.enter=&7Entrée dans le territoire %team%&7.
player.base.exit=&7Sortie du territoire %team%&7.
player.base.self.enter=&7Entrée dans le territoire %team%&7.
player.base.self.exit=&7Sortie du territoire %team%&7.
```

`%team%` reçoit le nom et la couleur native, y compris pour sa propre équipe.
Le fichier de surcharge contient ces seules clés ; le fichier livré
`messages_fr.properties` conserve toutes les autres traductions. Les options
de jeu et d'accès n'en sont pas changées.

## 5. Références et validateurs

La carte active porte `mapVersion: 2.2`. Les quatre enregistrements de chantier
`map-v21-*.json` sont déplacés **dans la copie uniquement** vers
`reference/history-v21/`, sans perte d'octets. Les anciennes références V2.1 et
les outils historiques restent conservés.

La référence courante `maintenance/new-match-reference-v2.2.json` déclare
`caverns: []` et `underground.mode: vanilla-restored`. Elle contrôle 37 128
cellules via leurs états complets normalisés et l'empreinte de l'archive approuvée.
Une référence incomplète, un registre altéré ou un terrain miné sont refusés.

Le validateur V2.1 exige toujours ses quatre cavernes ; le profil historique
reste compatible avec ses données. La nouvelle politique V2.2 est explicite,
et une ancienne référence de cavernes y est refusée. **160 empreintes** du
manifeste V2.2 sont vérifiées.

Les anciens manifestes de livraison et leurs empreintes d'outils n'ont pas été
réécrits. Les scripts de déploiement figés sur l'ancien candidat de 148 fichiers
ne sont pas adaptés à V2.2. Leur refus éventuel sur empreinte d'outil périmée doit
conduire à préparer un nouveau préflight fondé sur le présent reçu, jamais à
supprimer les contrôles ou retoucher une preuve historique.

## 6. Tests et limites

- **58 tests Java**, dont cinq nouveaux tests de transitions : succès.
- **145 tests Python**, dont dix pour les références naturelles et la compatibilité
  des anciennes politiques : succès.
- Sonde Paper historique, **29 assertions** : absence reproduite pour l'arbitre
  au jour 0, une notification native pour Survival et OP.
- Sonde Paper corrigée, **51 assertions** : une notification pour chacun, couleurs
  des quatre équipes, frontière 41/40, sortie, changement d'équipe de destination,
  téléportations, dimensions, jour 0, état de jeu simulé, pause et absence de spam.
  Les restrictions des éliminés, OP et participants restent actives.
- Événements de minage testés sur quatre territoires en J1 simulé : sa propre
  équipe autorisée, les autres protégées, OP sans exemption, arbitre exempté.
  Aucun bloc n'est détruit par ces événements de test.
- Sonde du terrain : **22 219 états de blocs** contrôlés dans Paper, 47 chunks de
  l'emprise historique chargés, spawns et bornes verticales des quatre bases vérifiés.
- Restauration locale complète V2.1 : **305 fichiers** comparés ; une copie de
  cette restauration a ensuite démarré, validé son jour 0/configuration et fermé
  proprement. Le dossier de restauration de contrôle est resté inchangé.

Les sondes réussies et le démarrage de rollback ont zéro ERROR/SEVERE et zéro
WARN, code de sortie 0, sur loopback uniquement. Les premières tentatives de sonde
restent conservées pour diagnostic ; les résultats retenus sont baseline `03`,
correctif `02` et la sonde de terrain. Les avertissements de dépréciation existants
de Maven/Paper à la compilation ne sont pas des erreurs de ces démarrages.

Les joueurs de sonde sont des corps serveur synthétiques sans authentification.
Les paquets sortants sont contrôlés ; **aucun rendu client réel, test multijoueur
authentifié ou mesure de charge à 17 connexions n'est revendiqué**. Les états
commencés ne concernent que les instances de test ; aucune partie officielle
n'a été lancée. Le candidat livré n'a jamais été démarré.

## 7. Livrables et empreintes

Tous les artefacts se trouvent dans `V22-VANILLA-20261123-01`, hors dépôt :

| Artefact | Usage | SHA-256 |
|---|---|---|
| `fallenkingdom-v22-world-private.zip` | 121 fichiers de monde et sept références/outils courants | `167a34838d81ebb7ffc66fca7563240aa09356dfc2217890183a8fb880c086d0` |
| `fallenkingdom-v22-fkamis-update-private.zip` | JAR, marqueur, registre et traduction française ; aucun monde | `b8be1448fcb06fee7213bdcd200285fa792c39e049561ec14e447d29b71a0738` |
| `fallenkingdom-v22-candidate-private.zip` | Instance initiale complète, 309 fichiers gérés | `ff3882af21b9477af89670198708612215357d2c705cf225290e42a7e0e090b9` |
| `FKAmis-v22-notifications.jar` | JAR indépendant, nom cible `plugins/FKAmis-1.0.0.jar` | `271cf678f3c817624b4c9cb580307d8b0d706864f40dcea0975dd1a010207a2d` |
| `before-v22-local.zip` | Point V2.1 local complet avant modification | `3639174d89308ec6d9462f89632c6e3a53ded6788c0bad813d2d8d683e92e761` |

Chaque ZIP possède un `BACKUP_MANIFEST.json`, a été relu et validé par SHA-256.
Les comptes de fichiers ci-dessus excluent ce manifeste généré. Les fichiers
`.sha256` et `SHA256SUMS.txt` accompagnent la livraison.

La liste complète des différences est dans le reçu public et
`file-differences-private.json` : **13 fichiers existants modifiés, huit chemins
créés, quatre chemins actifs déplacés en historique**. Aucune région ni donnée
de joueur n'est supprimée. Le `prepared-private.json` indique tous les chunks,
sections et SHA ; le plan privé contient chaque état avant/après.

## 8. Visite humaine locale

La copie `visual-inspection/` est préparée et arrêtée, avec seulement les deux
plugins de jeu. Les copies `territory-*` et `vanilla-paper-validation` sont des
fixtures de test, pas des livrables à déployer.

Depuis le dépôt :

```powershell
.\.tools\ms-audit\Scripts\python.exe -B scripts/vanilla_delivery.py --work C:\Users\youne\FKBackups\V22-VANILLA-20261123-01 --start-inspection
```

Se connecter en Minecraft Java 26.3 à **`127.0.0.1:25631`** avec un compte déjà
autorisé. Query utilise aussi 25631 sur cette copie seulement, pour éviter le
port 22880 déjà occupé localement. Le candidat destiné à MineStrator conserve
22880. Aucun rôle ni compte n'est ajouté.

`VISITE_V22_PRIVEE.txt` contient les spawns et les repères 41/40, pour l'arbitre
Creative en vol. Parcourir réellement chaque frontière et vérifier une seule
entrée/sortie, le nom et la couleur, puis absence de répétition à l'intérieur.
Pour un compte Survival, partir du spawn sûr et marcher sur le terrain existant.
Vérifier également une téléportation, un aller-retour de dimension autorisé et
l'absence de gain de droits pour OP.

Les sous-sols n'ont plus d'accès manufacturé : l'exploration suit les grottes
Minecraft et le minage naturel. Pour une inspection sans creuser, l'arbitre peut
passer temporairement en Spectator par la console **locale**, puis rétablir
Creative. Cela ne donne aucun droit supplémentaire aux éliminés. Le minage
Survival reste soumis aux phases et protections de partie existantes ; il n'est
pas déverrouillé artificiellement au jour 0 pour les visiteurs.

Ne pas lancer de partie officielle. Arrêter avec `stop`. Seule la copie de
visite reçoit les écritures normales ; `candidate/` et les archives restent la
référence de livraison. La présentation réelle du chat doit être validée ici.

## 9. Intégration MineStrator future et rollback

**Aucun fichier n'est prêt à être transféré sans nouveau contrôle de la recette
réelle et autorisation explicite.** Le candidat provient de l'instance initiale
approuvée, pas d'une sauvegarde fraîche de la recette du 23 novembre.

Après inspection acceptée :

1. Faire autoriser une nouvelle opération précise ; relever identité, état,
   versions, Query, accès, planifications et risques de concurrence. Respecter
   `AGENTS.md` ou une dérogation ponctuelle explicitement approuvée, sans réutiliser
   automatiquement l'accord d'une ancienne opération.
2. Obtenir et vérifier une **sauvegarde complète actuelle à froid**, hors instance,
   avec manifeste/SHA et restauration de contrôle. Préserver les anciennes
   sauvegardes et quarantaines.
3. Préparer une copie de cette sauvegarde. Pour chaque cellule du plan de
   restauration, comparer l'état réel à l'état V2.1 connu ; traiter comme conflit
   toute valeur différente non déjà restaurée. Ne pas effacer une construction
   légitime, un coffre, son NBT ou une modification de recette pour forcer le plan.
4. Intégrer les seuls changements validés **bloc par bloc** dans cette copie,
   en préservant tous les autres chunks, inventaires, joueurs, données de partie,
   biomes et dimensions. Ne jamais remplacer directement les quatre `.mca` de
   livraison sur l'instance courante.
5. Préparer les références et empreintes correspondant à ce vrai candidat
   d'intégration. Refaire les contrôles de terrain, de butin et de règles.
   **Ne pas importer le `state.yml`, les rôles ou les accès de l'instance initiale**
   sur une recette qui a évolué.
6. Après autorisation de bascule, staging, comparaison SHA, quarantaine sans
   suppression, puis activation cohérente du JAR/marqueur/registre/traduction et
   de la carte validée. Garder les versions, 20 places, Query 22880,
   `restart-on-crash=false` et watchdog actif.
7. Démarrer en accès restreint et vérifier logs, état de partie, spawns, rayons,
   butins et messages via un client réel. Arrêter sur divergence critique.

Le rollback de cette future opération doit restaurer **toute la sauvegarde
actuelle prise à l'étape 2**, avec ses états et inventaires, après préservation
de la tentative V2.2 en nouvelle quarantaine. Ne pas revenir au seul JAR ni
fusionner deux mondes. Conserver la politique de relance choisie ; ne pas réactiver
`restart-on-crash=true` implicitement.

Le point `before-v22-local.zip` et son test fonctionnel démontrent le retour de
la **référence locale initiale V2.1**. Ils ne remplacent pas une sauvegarde de la
recette actuelle. `MS-COLD-20261119-02`, à dix places, reste un autre point
historique conservé intact et ne doit pas être confondu avec ce rollback récent.
