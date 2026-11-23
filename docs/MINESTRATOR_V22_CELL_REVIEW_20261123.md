# V2.2 — contrôle conditionnel des deux cellules, sauvegarde suspendue

**Verdict : NO-GO. La condition préalable de sécurité échoue.** La référence r2
n'est pas validée et la nouvelle sauvegarde complète n'a pas été engagée.
Aucune écriture ni commande d'alimentation distante, aucun déploiement, aucune
modification de whitelist ou de partie. Aucun bloc n'a été rebouché.

Cette revue suit le commit `824bc39` et l'autorisation conditionnelle du
propriétaire. Elle s'arrête au premier contrôle bloquant, conformément à sa
demande. Les contrôles distants et tests dépendant de la sauvegarde ne sont pas
présentés comme réalisés.
Le [reçu expurgé](../tests/results/minestrator-v22-cell-review-20261123.json)
consigne les résultats et les empreintes des preuves privées.

## Résultat géométrique

Les deux cellules sont **superposées dans une même colonne**, à l'intérieur d'un
territoire d'équipe. Dans la source distante relevée, elles sont bien de l'air.
Dans la référence initiale approuvée, elles sont de la pierre.

La vérification ne montre pas une poche fermée et isolée :

- Dans les régions distantes relevées avant restauration, la colonne est ouverte
  vers le ciel, avec **43 blocs de chute sur du minerai de charbon** depuis les
  quatre bords adjacents.
- Après les 22 219 restaurations prévues, le payload r2 laisse une colonne ouverte
  vers le ciel et **33 blocs de chute sur de la pierre** depuis les quatre bords.
- Ces bords comprennent des blocs d'herbe et des briques de pierre moussues. La
  colonne est entièrement composée d'air : aucune eau ni interruption qui amortisse
  la chute. L'accès n'est pas couvert par un bloc au sommet.
- Les deux exceptions approfondissent ce puits de deux blocs. Les reboucher seules
  laisserait encore une chute de **31 blocs** : ce n'est pas une correction suffisante.

Il existe donc un **danger de chute non maîtrisé dans le terrain conservé**. La
condition « pas de danger anormal ou de modification critique » n'est pas satisfaite.
La cause, la date et l'intention de ce creusement ne sont pas établies. Le contrôle
ne prétend pas qu'une brèche de protection ou un exploit en jeu a été reproduit ;
ce danger géométrique suffit à interrompre la procédure.

Les emplacements, l'équipe concernée, le fond et les blocs environnants sont dans
la preuve **privée**, hors Git :
`C:\Users\youne\FKBackups\MS-V22-CELL-REVIEW-20261123-02\cell-safety-review-private.json`
et sa note `REVIEW_CELL_SHAFT_PRIVATE.md`. Aucune coordonnée n'est publiée ici.
Aucune visite en client Minecraft n'a été effectuée.

## Contrôles de référence réellement réussis

| Contrôle local | Résultat |
|---|---|
| Archive initiale V2.2 approuvée | SHA-256 conforme à `75b192b2…b1e0ea` ; référence et quatre régions de la copie de travail comparées aux octets du ZIP |
| Preuves du préflight | Huit empreintes privées conformes au reçu du commit `824bc39` |
| Régions distantes relevées | SHA conformes aux deux lectures distantes antérieures et au relevé des régions |
| Plan de restauration | Empreinte approuvée inchangée, 22 219 positions uniques |
| Source des 22 219 restaurations | Chaque état est encore l'état « avant » connu dans les régions relevées |
| Sortie des 22 219 restaurations | Chaque état du payload r2 correspond à l'état naturel attendu |
| Appartenance des deux exceptions | Aucune ne concerne une des 22 219 restaurations |
| Empreinte élargie | 37 128 cellules uniques, dont **37 126 conformes** à la référence initiale |
| Deux différences | Exactement les deux exceptions pierre → air déjà documentées ; aucune exception supplémentaire masquée |
| Référence r2 proposée | Empreinte calculée cohérente avec le terrain proposé, **sans approbation de sécurité** |
| Payload | Les 17 fichiers correspondent aux SHA du plan existant ; aucune réécriture de leur contenu ou manifeste |

La revue de la colonne explique une limite importante du seul contrôle des
37 128 points : **31 autres cellules au-dessus des deux exceptions** diffèrent de
la référence initiale, hors de cette emprise contrôlée. Elles étaient préservées
par le rebasage sur l'état courant. Le résultat « 37 126 conformes + deux exceptions »
reste exact pour cette emprise ; il ne certifie pas la sécurité de tout le voisinage.
Ces 31 cellules ne sont ni modifiées ni ajoutées silencieusement aux exceptions.

## Portée et fraîcheur des preuves

La revue est **strictement locale**, sur les quatre régions relues à distance le
23 novembre jusqu'à **11:19:49, heure de Paris**. Les données d'entrée et les 17
fichiers proposés ont été recontrôlés par SHA. Le diagnostic privé retenu est daté
du 23 novembre à **16:17:23, heure de Paris**.

Ce n'est pas un nouveau relevé distant à 16 h : aucune connexion API ou SFTP n'a
été effectuée pendant cette mission. L'état
actuel du serveur et l'absence de changements depuis la fenêtre du préflight ne
sont donc pas certifiés de nouveau. Il serait incorrect de poursuivre une copie
conditionnelle pour lever ce doute alors que sa condition de sécurité échoue déjà.

## Sauvegarde et validations dépendantes

| Opération demandée | Statut après le blocage |
|---|---|
| Nouvelle confirmation serveur arrêté / identité / accès | Non exécutée dans cette mission |
| Planifications, actions en attente, quota libre | Non recontrôlés ; limites du préflight conservées |
| Nouvelle dérogation au verrou partagé | [Documentée](MINESTRATOR_V22_COLD_DEROGATION_20261123.md), accord conditionnel non mis en œuvre |
| Nouvelle sauvegarde distante complète | **Non commencée : aucun fichier sauvegardé, aucune archive créée** |
| SHA-256 de nouvelle archive / manifeste | **Sans objet : ces fichiers n'existent pas** |
| Nouvelle restauration binaire complète | Non effectuée |
| Démarrage Paper d'une seconde copie | Non effectué |
| Nouvelle simulation complète depuis cette sauvegarde | Non effectuée |
| Préparation précédente des 17 fichiers | Conservée inchangée, reste proposée et non autorisée au déploiement |

Le dossier de sauvegarde proposé `MS-COLD-V22-20261123-01` n'a pas été créé.
Le périmètre estimé au préflight était de **463 fichiers**, dont 311 actifs et
152 en quarantaine, pour 653 314 681 octets, plus les dossiers techniques vides.
Ce nombre n'est **pas** le périmètre d'une sauvegarde réalisée ; il devra être
réinventorié intégralement lors d'une reprise autorisée.

Les archives historiques, restaurations originales, manifestes, quarantaines et
artefacts V2.2 existants ne reçoivent aucune écriture. Seuls de nouveaux rapports
privés et les documents/outils de diagnostic locaux sont créés.

## Outil et tests

`scripts/v22_cell_review.py` reproduit le contrôle local avec vérification des SHA,
de l'emprise et des cellules de restauration, puis mesure les colonnes d'air et
leurs bords. Il n'appelle aucun service distant, n'approuve aucune référence et
ne peut engager de sauvegarde. Un danger produit `BLOCKED_TERRAIN_SAFETY` et un
code de sortie non nul ; même une absence de ce danger précis ne constitue pas
une certification générale de sécurité.

**167 tests Python réussis**, dont cinq nouveaux cas : puits ouvert, poche fermée,
exception qui n'est pas de l'air, échec sur cellule à restaurer et point de
référence dupliqué. Les validateurs généraux de maintenance et les règles
`AGENTS.md` ne sont pas modifiés. Aucun test multijoueur ou démarrage Paper
supplémentaire n'est revendiqué.

## Condition de reprise

Présenter le puits complet à une revue privée et décider explicitement de son
traitement. Une visite en jeu, si retenue, doit se faire sur une copie locale
indépendante, avec des contrôles adaptés ; aucune inspection humaine n'est
présumée déjà réussie. Ne pas réduire cette décision au rebouchage des deux
cellules ou à l'élargissement silencieux du manifeste d'exceptions.

Toute correction de terrain ou adaptation supplémentaire de référence exige une
revue et une validation explicites avant modification. Ensuite seulement : nouveau
précontrôle distant, sauvegarde complète sous la dérogation accordée dans son
périmètre, restauration et boot local, nouveau plan de transition. Une autorisation
distincte restera indispensable pour toute bascule distante.

**La sauvegarde conditionnelle et le déploiement sont suspendus ; aucune garantie
de rollback actuel n'est ajoutée par cette revue.**
