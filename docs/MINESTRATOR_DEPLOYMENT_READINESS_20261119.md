# Disponibilité au déploiement V2.1 — après RB-20261119-01

**Statut : non validé pour bascule. Aucun déploiement autorisé ou effectué.**

| Prérequis | État |
|---|---|
| Sauvegarde MS-COLD-20261119-02 et restauration binaire | Vérifiées sous dérogation |
| Archive, manifeste et restauration originaux | Inchangés après le test |
| Marqueur SHA de la copie indépendante | Corrigé et cohérent avec le JAR / registre |
| Outils de maintenance de l'ancienne instance | Validation refusée : exigence de 8 places, configuration réelle à 10 |
| Rollback Paper local fonctionnel | Non testé après le refus critique |
| Conservation de l'état historique après démarrage | Non démontrée par cette opération |
| Candidat V2.1 et plan des 146 fichiers | Préparés précédemment, aucun transfert |
| Inspection humaine de la carte / recette réseau | Restent nécessaires |
| Autorisation explicite de bascule distante | Non reçue |

La réserve du marqueur est levée **dans la copie de test seulement**. L'archive
reproduit toujours fidèlement le point historique et ses anciens outils. Il reste
à vérifier le rollback avec des outils compatibles, sans réduire artificiellement
les places ni modifier les données pour obtenir une validation.

Le [rapport local](MINESTRATOR_ROLLBACK_LOCAL_REPORT_20261119.md) précise le refus.
Le [plan rattaché à la sauvegarde](MINESTRATOR_BASCULE_PLAN_AFTER_BACKUP_02.md) reste
une proposition documentaire ; il ne sera pas exécuté sur la base de cette tentative.
Aucune nouvelle validation ni bascule n'est déduite du présent rapport.
