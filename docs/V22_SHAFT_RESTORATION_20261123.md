# V2.2 — restauration locale du puits depuis l'archive initiale

**Statut : prêt pour inspection humaine locale. Déploiement encore NO-GO.**
La variante privée `V22-SHAFT-20261123-01` restaure les 33 cellules archivées et
quatre valeurs de hauteur de leur colonne. Aucune connexion MineStrator, aucune
écriture distante, sauvegarde distante, whitelist ou partie modifiée. Les
références, archives, restaurations et quarantaines historiques sont conservées.

Le [reçu expurgé](../tests/results/v22-shaft-restoration-20261123.json) et la
[liste des 17 fichiers et empreintes](MINESTRATOR_V22_SHAFT_FILES_20261123.tsv)
complètent le rapport. Coordonnées, données NBT, régions, archives et journaux
restent sous `C:\Users\youne\FKBackups\V22-SHAFT-20261123-01`, hors Git.

## 1. Origine du puits : ce qui est démontré

La référence géologique est directement
`dist/fallenkingdom-preproduction-26.3.zip`, SHA-256 :

`8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de`.

Les 33 cellules sont toutes solides dans cette archive. La référence V2.1 locale
contient exactement les mêmes états complets ; le SHA de sa région concorde avec
le manifeste réellement installé le 20 novembre. Le puits n'était donc pas présent
dans cette livraison V2.1. Deux cellules seulement figurent dans le plan historique
de la caverne ; elles n'étaient pas dans les 22 219 restaurations nécessaires.
Les 31 autres sont hors de son emprise contrôlée.

Le relevé distant du 23 novembre contient de l'air aux 33 positions. La conclusion
**fortement étayée** est un creusement postérieur à l'installation. Une modification
de recette est l'explication probable, sans certitude sur son intention, sa date
précise ou son auteur. Le dernier journal localement disponible ne contient pas
de commande `fill`/`setblock` ni de commande joueur permettant l'attribution ;
il ne couvre pas nécessairement tout l'historique. Aucune nouvelle connexion
n'a été effectuée pour rechercher des journaux supplémentaires.

## 2. Comparaison des 33 cellules et proximité

| État complet d'origine | Nombre |
|---|---:|
| `minecraft:stone` | 26 |
| `minecraft:diorite` | 4 |
| `minecraft:dirt` | 2 |
| `minecraft:grass_block[snowy=false]` | 1 |

Le tableau individuel contient coordonnées exactes, état courant, état r2, état
archivé complet et appartenance à l'emprise historique :
`shaft-33-cells-private.csv`. Il est également repris dans
`INSPECTION_CLIENT_PRIVATE.md`. Les données d'environnement et de proximité sont
dans `analysis-private.json`. Aucun emplacement sensible n'est publié dans Git.

Le puits est dans un territoire, à environ **2,83 blocs du centre de base** et
**9,22 blocs du spawn** en projection horizontale. Les monuments et ravitaillements
les plus proches sont à environ 229 et 173 blocs. Aucun objectif n'est enregistré
dans l'état de partie précédemment relevé. Aucun block entity ne se trouve dans
les 33 cellules. Les briques de pierre moussues voisines appartiennent au cadre
existant et ne sont pas remplacées.

## 3. Correction justifiée et conservation du voisinage

La correction n'est pas un remplissage uniforme déduit du danger : **chaque état
provient de l'archive**, propriétés comprises, et concorde avec V2.1 livrée.
Elle vise uniquement cette colonne de 33 cellules actuellement en air. Elle ne
génère pas de terrain, ne dessine pas de caverne, ne déplace pas de structure et
ne modifie ni dimensions, ni centres, ni rayons de territoire.

Les états complets d'un voisinage de 5 × 5 colonnes, du dessous du puits à
l'air au-dessus de la surface, sont comparés avant/après : aucun bloc hors des
33 cibles n'est modifié. Les accès horizontaux observés dans ce volume ne sont
pas élargis ; la colonne restaurée retrouve exactement la roche, la terre et
le gazon archivés. Les approches immédiates restent au même niveau que le sol
restauré, avec deux blocs d'air pour les pieds et la tête.

Une dépendance NBT a été détectée : les quatre heightmaps conservaient une
hauteur au fond du puits. Remettre seulement les blocs aurait laissé ces caches
incorrects. Après confirmation que **les 384 états de toute la colonne** correspondent
à l'archive, seules ses quatre valeurs `MOTION_BLOCKING`,
`MOTION_BLOCKING_NO_LEAVES`, `WORLD_SURFACE` et `OCEAN_FLOOR` sont restaurées.
Les 255 autres valeurs de chaque carte, leurs bits inutilisés, les horodatages
des chunks et les autres métadonnées NBT restent préservés. L'éclairage du chunk
modifié est invalidé pour recalcul par Paper.

Les block entities, inventaires, biomes et autres données du chunk ne sont pas
réécrits. Les fichiers d'entités/POI ne sont pas ciblés. Les positions d'entités
actuelles et les profils courants ne sont toutefois pas tous disponibles dans
les copies locales : leur contrôle devra être repris sur une future sauvegarde
complète, sans supposer qu'une géométrie statique prouve l'absence d'une entité.

## 4. Référence renforcée, sans exception de terrain

La référence r2 n'est pas approuvée ni modifiée en place. La nouvelle proposition
part de la référence initiale :

- **37 128 points historiques**, tous à nouveau conformes, avec leur empreinte
  initiale inchangée ; aucune réduction de l'ancien contrôle.
- Un complément nommé `archiveRestorations`, mode strict `shaft-column-33`,
  documente les **33 états archivés**, dont deux points déjà dans l'emprise et
  **31 points supplémentaires**. Soit **37 159 positions uniques contrôlées**.
- **Zéro exception de terrain conservée.** Les 22 219 restaurations précédentes
  sont préservées ; le total de restaurations est **22 252**.
- La référence demeure `proposed_pending_human_inspection`. Cela n'est ni une
  approbation de production ni une autorisation de sauvegarde/déploiement distante.

Le validateur conserve les contrôles historiques et ajoute ce complément :
source SHA imposée, schéma, 33 positions uniques contiguës, 31 positions nouvelles,
états complets et empreinte du terrain. Une métadonnée exige explicitement ce
complément dans la nouvelle variante : son omission est refusée. Les profils et
références historiques restent compatibles ; aucun contrôle général n'est désactivé.

## 5. Vérifications effectuées

| Vérification locale | Résultat |
|---|---|
| Comparaison à l'archive initiale | 46 chunks, 1 150 sections, **4 710 400 états de blocs**, tous conformes après correction |
| Cibles précédentes | **22 219 conservées** ; 33 cellules supplémentaires restaurées exactement |
| Région du puits | Sections et NBT vérifiés ; 1 023 corps compressés de chunks non ciblés identiques dans cette région |
| Heightmaps | Quatre valeurs de la seule colonne corrigées ; autres valeurs et NBT conservés |
| Référence de carte | Quatre bases, sept monuments, **6 689 blocs de monuments**, huit ravitaillements et six coffres de butin contrôlés |
| Tests Python | **178 réussis**, dont 11 nouveaux tests de complément de référence et de heightmaps |
| Démarrage Java/Paper isolé | Java 25, Paper 26.3-244 ; FK officiel 2.24.9 et JAR FKAmis retenu inchangés ; sortie propre, **0 ERROR/SEVERE, 0 WARN** |
| Sonde moteur privée | **22 252 blocs**, 47 chunks de contrôle chargés sans demande de génération, quatre territoires de rayon 40 et quatre spawns sûrs |
| Surface moteur | Cinq points contrôlés : bloc, hauteur Bukkit et espace de passage corrects |
| Réseau de test | Commande liée à `127.0.0.1:25630`, Query journalisé sur ce même endpoint local |
| Partie | J0 non lancé, aucun client authentifié ; aucune visite humaine ni partie multijoueur revendiquée |

La sonde Java est ajoutée uniquement à une seconde copie jetable de validation.
Elle ne figure ni dans les 17 fichiers ni dans la copie d'inspection humaine.
Les deux plugins de production gardent leurs versions et empreintes approuvées.
Le premier essai d'orchestration a refusé une action de maintenance CLI inexistante
**avant tout démarrage Paper** ; ses preuves restent conservées. L'essai suivant
utilise les commandes documentées et réussit les validations.

Ces contrôles démontrent la suppression du puits dans la variante et la conformité
géométrique immédiate. Ils ne remplacent pas l'inspection humaine, les essais de
passage avec clients réels ou une preuve de performances multijoueurs. Les règles
et protections de jeu ne sont pas modifiées ; leurs validations antérieures du
JAR retenu restent les preuves applicables, sans nouvel essai d'assaut revendiqué.

## 6. Plan de transition et simulations

Le plan conserve **17 fichiers : 12 remplacements et cinq créations**, et un
manifeste de **157 entrées**. Six cibles évoluent depuis r2 : la région du puits,
les deux références, leur validateur, les métadonnées de restauration et le
manifeste. Les onze autres fichiers restent identiques à la proposition précédente.
Le marqueur, le registre et le JAR restent cohérents ; SHA FKAmis :
`905b0f4b11192d26cd59b82b151525ad3b69f7f1803c65760589800404345ca5`.

La [liste exacte](MINESTRATOR_V22_SHAFT_FILES_20261123.tsv) remplace celle de r2
pour la prochaine revue. Aucun ancien plan à 148 fichiers n'est utilisé.

Deux niveaux de simulation sont distingués :

1. Le modèle des **311 chemins/SHA** du relevé distant conserve ses préconditions,
   teste staging/activation et un échec avec rollback hypothétique. Le drapeau de
   sauvegarde vérifiée de ce modèle est une hypothèse de test, pas une nouvelle
   sauvegarde réellement créée.
2. Une répétition physique utilise les **265 fichiers** dont les octets actuels
   sont disponibles et conformes au relevé. Les 12 anciennes cibles et le fichier
   historique à déplacer sont tous disponibles. Les 17 cibles sont installées,
   **13 fichiers mis en quarantaine**, 252 conservés ; la restauration dans un
   dossier neuf reconstitue les **265 fichiers à SHA identiques**, plus le
   `session.lock` technique disponible, vérifié séparément : **266 fichiers**.
   Installation et
   quarantaine de test restent conservées.

Les **45 fichiers courants indisponibles** ne sont ni inventés ni reconstitués
depuis des données anciennes en prétendant obtenir leur état réel. Cette répétition
est partielle. Le test Paper part d'une copie complète de la livraison locale avec
le terrain intégré, pas d'une restauration complète de la partie courante. Le
manifeste de cette fixture est recalculé et marqué local ; il n'est pas substitué
au manifeste de transfert. Le rollback actuel complet reste à valider après la
future sauvegarde complète autorisée.

Espace supplémentaire proposé recalculé : **2 858 981 188 octets**, dont
46 779 595 octets de staging. Ce calcul conserve les volumes distants observés
au préflight ; ce n'est pas une nouvelle mesure d'espace libre.

## 7. Artefacts et inspection humaine

Archive privée proposée, **pas une sauvegarde complète** :
`v22-shaft-transition-PROPOSED-private.zip`, 39 679 868 octets.

SHA-256 : `523e3d0d3eb21063ed4549d19a364c825cf6bd81be83f45e29632b3637c7ab38`.

| Fichier | SHA-256 |
|---|---|
| `DEPLOYMENT_MANIFEST.json` | `f1b876f699ca6c3908d989b0a0695a94561fb5391ffc953ee6025e55366bcd50` |
| `maintenance/new-match-reference-v2.2.json` | `b932654b693c098be1580e6b720ca0f04033c1366cdf7f316181efce86dd261e` |
| `maintenance/terrain_reference.py` | `1546ae120fa7e6eb04be7f4dfd45c86939d57618663a14dab29406361bcaa153` |

ZIP relu par CRC et par les 17 SHA ; `UPDATE_MANIFEST.json` est une enveloppe
de contrôle, pas un fichier à installer. Les archives initiale, historique
`MS-COLD-20261119-02`, candidat final et proposition r2 ont été recontrôlées sans
changement d'empreinte. Les restaurations originales n'ont reçu aucune écriture.

La copie `inspection-candidate` est prête, **non démarrée**, avec seulement les
deux plugins de production, sans compte synthétique, sans modification de whitelist
et sans partie lancée. Le guide privé `INSPECTION_CLIENT_PRIVATE.md` donne les
33 coordonnées, les commandes locales de visite et les critères de validation.
Le lanceur manuel `start-inspection-local.ps1` utilise `127.0.0.1:22880` ; il
n'exécute aucune commande MineStrator et aucune sauvegarde automatique.

L'arbitre déjà autorisé doit vérifier le gazon, les quatre approches, les fondations
de base, le spawn et le sous-sol sans casser de blocs, puis les quatre bases et
frontières. Conserver captures et décision en privé. Ne pas ajouter un compte ou
désactiver la whitelist pour contourner un refus d'accès.

**Après inspection seulement :** approbation de la nouvelle proposition, puis
autorisation de reprise des contrôles distants et de la sauvegarde complète. Les
observations utilisées restent celles du 23 novembre à 11:19:49, heure de Paris.
Une future bascule doit être reconstruite/revérifiée depuis une sauvegarde fraîche
et reste soumise à une autorisation distincte. Aucun déploiement n'est effectué.
