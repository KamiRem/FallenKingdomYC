# Validation finale du profil Paper 26.3

## Campagne VNext courante

Voir [FKAMIS_VNEXT.md](FKAMIS_VNEXT.md) et `tests/results/vnext-delivery.json`.
`build.ps1 -VNext -Physics -Probe -Corrections -MapV2 -Migration -Administration -Features`
compile les outils séparés et exécute les tests Java ; `python -m unittest discover -s tests`
exécute les tests Python. `scripts/vnext_tests.py` reprend les neuf recettes Paper,
les quatre formats et les nouveaux services sur des copies conservées. Le paramètre
`--attempt` exige une destination neuve. Les anciennes recettes fixent la grâce à
zéro pour isoler leurs hypothèses ; la nouvelle recette vérifie son comportement.

`vnext_physics.py` compare l'ancien binaire au correctif : IA naturelle, tirs,
collisions, événements et santé réelle d'un corps NMS sans client authentifié.
`vnext_restore_tests.py` vérifie reset à froid, politiques incompatibles refusées,
référence initiale de fixture et restauration entière. `vnext_delivery.py` contrôle
mise à jour et rollback complet. Les rapports précisent le SHA du JAR exécuté.
Les micro-mesures locales ne prouvent pas la charge de seize clients sur l'hôte.
La checklist réseau, visuelle, sonore et multijoueur reste humaine.

## Campagne gameplay précédente

Voir [GAMEPLAY_UPDATE.md](GAMEPLAY_UPDATE.md) pour la livraison ciblée, les causes,
les limites de preuve, l'installation et le rollback. Le rapport définitif est
`tests/results/gameplay-update-delivery.json`. Paper 26.3-244 / Java 25 / FK 2.24.9
inchangé ; 1 à 4 membres par équipe (défaut 2), arbitre UUID indépendant, lit valide
ou centre sûr pour les morts, construction neutre libre, capture sans condition de
regard, locator bar désactivée, mobs suspendus au jour 0 et `/fka announce <message>`.
Les guides des anciennes livraisons restent historiques.

## Résultats gameplay courants

- Java : 32 tests JUnit, zéro échec/erreur.
- Python : 28 tests, zéro échec.
- Paper 26.3-244, même JAR : 654 assertions (formats solo 96, binômes 96,
  trios 97, quatuors 97, arbitre 51, phases 28, gameplay 112, ravitaillements 49,
  intégration native 28), zéro échec final.
- Comparaison distincte du précédent JAR : cinq assertions PvE/PvP/pause passent,
  l'événement de flèche squelette signalé n'y est pas bloqué non plus.
- Capacité : deux démarrages refusés volontairement, capacité changée en cours de
  partie et diminution sous roster, avec state.yml byte pour byte préservé.
- Seuls avertissements des suites normales : deux spawns dangereux volontaires
  du probe gameplay. Les logs d'erreurs des refus de capacité sont attendus.

Les premiers essais ont détecté une ambiguïté Comparator à la compilation, un
chemin de fixture non normalisé et un chemin de restauration trop long sous Windows.
Ils ont été corrigés ; leurs traces restent privées dans .cache et ne sont pas
présentées comme une recette réussie. Aucun de ces probes n'est livré en production.
La nouvelle réinitialisation sélective évite les captures annulées par un troisième
allié éloigné et par la mort d'un défenseur hors salle.

Les appels Player restent des doubles ; ils vérifient le moteur et les callbacks
serveur, pas une session réseau. La checklist de GAMEPLAY_UPDATE.md est obligatoire
pour le rendu client, les lits/impacts réels, les permissions authentifiées et la
performance à seize participants. L'installation réelle du paquet et son rollback
sont consignés dans le rapport définitif, sans contact avec MineStrator.

## Historique — mise à jour arbitre/survie/tips

La recette de cette précédente livraison figure dans `tests/results/admin-update-delivery.json`.
Construction : `./scripts/build.ps1 -Probe -MapV2 -Corrections -Migration -Administration`.
Tests purs : **24 Java** et **24 Python**. `scripts/admin_tests.py` crée des copies
neuves de l'archive 26.3, jamais une recette sur les références. Les tentatives sont
conservées ; choisir un nouveau numéro pour les rejouer.

Le probe dédié vérifie visiteurs en survie, UUID/confirmation/console, dix places,
neutralité de neuf acteurs, quatre territoires, OP ordinaire refusé, vol, pause,
TP dimension fermée, protection objectif/site et autorisation sensible à usage
unique, morts répétées, lit, capture/élimination et persistance des rôles/modes.
Les probes de gameplay, phases/captures/victoire, ravitaillements et intégration
native sont également rejoués. Le premier acteur de fixture manquait de PDC ;
cette donnée a été ajoutée au probe, sans corriger le plugin pour un faux joueur.

**Aucune connexion authentifiée** : les neuf Player du probe restent des interfaces.
À valider humainement : huit participants + arbitre simultanés, permissions réelles,
respawn après mort effective, chat/interfaces, statut éliminé après reconnexion et
redémarrage, absence de tips après trois minutes, annonces et performances sur l'hôte.
Le paquet ciblé est appliqué puis démarré dans une copie locale avec comparaison
monde/state.yml avant-après ; la restauration complète du backup est aussi vérifiée.
Les sections de migration ci-dessous constituent des résultats antérieurs.

Le profil courant est Paper **26.3-244 STABLE / Java 25**, avec le FKAmis final
compilé contre **26.3.build.244-stable**. Les tests anciens du worktree
`test/paper-26.3-preprod` ont été analysés et conservés. La recette définitive porte
sur le nouveau binaire et une restauration du ZIP 26.2 initial, jamais sur la référence.

## Résultats de promotion

| Couverture | Résultat |
|---|---|
| Java/JUnit | 19 tests, zéro échec/erreur |
| Python | 21 tests, dont palettes 26.2/26.3, défauts du registre et perte de contenu détectée |
| Native FK + intégration | 28 assertions : chargement, équipes/territoires, dimensions, affichage côté serveur, commandes/complétion/permissions, chat événementiel |
| Règles/captures natives | 23 assertions initiales + 5 après reprise |
| Gameplay corrigé | 112 assertions, événements/listeners réels, mobs/TNT réels, huit interfaces Player |
| Ravitaillements | 43 assertions initiales + 6 après reprise |
| Monde converti | Aucun chunk nouveau/perdu, aucun écart de blocs/biomes/conteneurs/inventaires ; six butins et huit sites vérifiés |
| Sauvegarde/restauration candidat | 291 fichiers identiques avant redémarrage dans une instance distincte |
| Paquet final | Manifeste/SHA, restauration neuve, démarrage des deux plugins, jour 0, contrôle monde et arrêt propre ; rapport final dédié |

Total technique Paper : **217 assertions**. Les deux avertissements de téléportation
du probe gameplay correspondent aux spawns volontairement dangereux des cas négatifs.
Les essais finaux ne comportent pas d’ERROR/SEVERE. Les mesures console TPS/MSPT
sont à vide ; elles ne décrivent pas la charge sur MyBox Perf 8.

Rapports : `promotion-26.3-restore-initial.json`, `promotion-26.3-world.json`,
`promotion-26.3-probes.json`, `promotion-26.3-smoke.json`,
`promotion-26.3-recovery.json`, `promotion-26.3-restart.json`,
`promotion-26.3-package-smoke.json`, `promotion-26.3-package-world.json`,
`preproduction-package-26.3.json`. Les logs complets restent privés/ignorés par Git.

## Reproduction contrôlée

```powershell
./scripts/build.ps1 -Probe -MapV2 -Corrections -Migration
python -m unittest discover -s tests -p 'test_*.py'
```

Ces options compilent séparément les probes et outils ; elles ne les exécutent pas
et ne construisent pas la carte. Aucun probe ne doit être installé sur l’hébergement.
`scripts/promote_26_3.py` propose `prepare`, `probes`, `candidate`, `seal`, `final-test`.
Les destinations existantes sont refusées. Ce workflow est déjà exécuté ici : ne pas
le relancer dans ses noms actuels et ne supprimer aucun résultat pour contourner un refus.
Pour un nouvel essai technique après correction de fixture, `probes --attempt N`
crée des noms distincts ; il utilise le binaire final et l’archive fixe vérifiée.
La comparaison du monde exige les défauts de blocs exportés par le probe natif ;
ils sont disponibles dans le dossier local de recette.

Pour un nouveau smoke sans partie sur la copie 26.3 existante :

```powershell
python scripts/preproduction_smoke.py --root runtime/preproduction-26-3 --port 25583 --report tests/results/promotion-26.3-smoke.json
```

Ne pas exécuter de constructeur/nettoyage, `pregen`, de mise à jour de plugin sur
les instances historiques, ni une rétrogradation du monde converti.

## Vérifications humaines restantes

**Zéro client authentifié connecté pendant la migration.** Le probe chat vérifie
le filtrage des destinataires et le préfixe global, sans livraison réseau réelle.
Les services/interfaces sont exercés côté serveur, sans rendu de client vérifié.
Faire inspecter la carte convertie, recevoir les messages entre vrais alliés et
vérifier leur confidentialité face aux adversaires, tester les commandes et affichages
sur les huit clients Java 26.3. Ajouter explicitement ces preuves à la feuille privée.

Suivre [la recette complète](MULTIPLAYER_ACCEPTANCE.md) : quatre binômes, J1 PvE/PvP,
J2 neutre, J3 assauts/TNT, minage adverse permanent interdit, objets interdits,
salles/captures, éliminations/victoire, pause/déconnexion, téléportations,
ravitaillements, restauration et mesures TPS/MSPT/RAM/ping avec les huit connectés.
Lancer uniquement la recette sur une copie ; la partie officielle attend sa validation.

Le plan d’essai et les résultats 26.2 sont conservés dans `TEST_PLAN_26_2.md`.
Ils décrivent un historique, pas une invitation à retester les références protégées.
