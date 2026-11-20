# Plan de bascule après sauvegarde MS-COLD-20261119-02

**Plan remplacé le 20 novembre 2026**, sans exécution, par la préparation
[quatre membres par royaume](FOUR_PLAYERS_20261120.md) : 148 fichiers cibles,
20 places pour V2.1, rollback historique inchangé à 10. Ne plus utiliser le
nombre 146 ou les empreintes de ce plan comme autorisation de transfert.

**Plan local préparé pour revue, non exécuté et non autorisé.** Le déploiement
V2.1 est distinct de la dérogation -02, réservée à la sauvegarde/restauration.
L'[anomalie du marqueur source](MINESTRATOR_BACKUP_REPORT_20261119_02.md) doit être
examinée : la restauration est fidèle mais sa remise en service via les outils
de maintenance n'est pas validée sans réserve.

## Point de retour vérifié

- Archive privée : `C:\Users\youne\FKBackups\MS-COLD-20261119-02\instance.zip`.
- SHA-256 : `255fb82eeddb4b067313e8a6ce39ed012ada204f28d0a7bdb0b85ec2025663bf`.
- Manifeste externe : `manifest.json`, SHA-256
  `b54da288c8ad983c6bc35172ed1e0a697812b210dd7afe38ffb7e060f9ff81a1`.
- 305 fichiers restaurés et comparés ; observations API de l'opération toutes arrêtées.
- Le point inclut le marqueur historique périmé : il n'a pas été réécrit pour
  fabriquer une sauvegarde artificiellement cohérente.

## Manifeste de transfert concret

Le manifeste privé actualisé est
`C:\Users\youne\FKBackups\MS-COLD-20261119-02\bascule-plan-private.json`.
Il rattache les **146 fichiers cibles** du payload `.cache/ms15q/payload` aux
empreintes complètes du point source -02. Les hashes du payload ont été revérifiés ;
aucune dérive des anciennes préconditions connues ou des fichiers conservés n'est
constatée lors de la préparation du rapport. Aucun contenu n'a été transféré.

| Groupe cible | Nombre |
|---|---:|
| Nouveau `world/` V2.1, dimensions intégrées | 121 |
| Données initiales/configuration `plugins/FKAmis/` | 5 |
| Données initiales `plugins/FallenKingdom/` | 8 |
| Outils et références `maintenance/` | 7 |
| `FKAmis.sha256`, `RUNTIME_LOCK.json` | 2 |
| Métadonnées carte V2/V2.1 | 2 |
| Nouveau manifeste de déploiement | 1 |
| Total | **146** |

Les JAR Paper/FallenKingdom/FKAmis déjà conformes sont conservés. Le nouveau marqueur
préparé correspond au JAR VNext.1 : son remplacement fait partie de ce **futur** plan,
pas d'un correctif appliqué maintenant à l'ancienne instance. Le candidat reprend
les politiques d'accès réelles sans importer les anciens inventaires, états ou
compteurs de lots. Port 22880, Java **25 - Performance**, image `java/25_perf`,
allocations et mémoire du panel restent inchangés.

## Séquence proposée après accord séparé

1. Examiner/qualifier l'anomalie du marqueur source et les limites du rollback.
   Ne pas la corriger dans la sauvegarde ou dans l'instance sans accord explicite.
2. Revalider identité, état arrêté, réglages panel et tous les hashes source du
   point -02 avant toute écriture. En cas de dérive, arrêter et présenter un plan
   actualisé ; ne pas appliquer silencieusement un manifeste périmé.
3. Définir les conditions de maintenance de la bascule. La dérogation de sauvegarde
   ne constitue aucune permission de démarrage, arrêt, modification ou migration.
4. Conserver les anciens arbres dans une quarantaine distincte, et archiver les
   anciennes versions des autres fichiers remplacés, avant tout dépôt du candidat.
   Ne jamais superposer des régions neuves à des profils/états de l'ancien monde.
5. Déposer uniquement les 146 fichiers du manifeste approuvé, relire leur contenu
   distant et comparer chaque SHA-256 ; vérifier les fichiers déclarés conservés.
6. Démarrer seulement dans le cadre de l'accord de déploiement, en accès restreint,
   puis vérifier logs, versions, jour 0, 4 rayons 40, spawns, rôles et protections.
7. Inspecter en jeu les quatre cavernes, configurer la paire officielle de portails,
   effectuer la recette humaine et sceller la référence initiale V2.1 appropriée.
   Ne pas lancer automatiquement une partie officielle.

L'inventaire source actuel utilise `world/` pour ses dimensions. Les dossiers
séparés éventuels doivent être réévalués au contrôle final. Sauvegardes précédentes,
références, EULA, bans et paramètres du panel ne sont pas supprimés.

## Rollback complet avec réserve connue

Sous l'autorisation correspondante : arrêter la nouvelle instance, conserver son
état pour diagnostic, puis restaurer tout le point -02 dans un espace vide. Comparer
chaque fichier avec le manifeste ancien et remettre les métadonnées et réglages
du panel appropriés ; ne jamais restaurer le seul JAR ni fusionner des profils.

Le point -02 contient déjà le JAR VNext.1 et un état historique de rayon 80. Le
rollback revient à **ce point réel**, pas à une ancienne révision arbitraire.
Son `FKAmis.sha256` annonce encore `83e721...`, alors que le JAR et le registre
sont `46703f...`. Les outils de maintenance peuvent refuser le point pour cette
raison. Toute décision de correction de ce marqueur après une restauration doit
être explicitement autorisée, documentée et distinguée de la restauration fidèle.
Aucun démarrage fonctionnel du rollback n'est prétendu validé ici.

Le [plan détaillé précédent](MINESTRATOR_DEPLOYMENT_PLAN.md) reste la description
des groupes à conserver et des protections. Ce complément le rattache au nouveau
point de sauvegarde, sans autoriser aucune exécution.
