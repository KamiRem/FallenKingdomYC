# Passer de la recette à la partie officielle

La préparation n’a lancé aucune partie officielle. Ne pas nettoyer un monde déjà
joué par suppression de fichiers d’inventaire ou édition des seuls compteurs FKAmis :
coffres pillés, constructions, entités, états natifs et progression divergeraient.

Profil courant : `fallenkingdom-preproduction-26.3.zip`, MineStrator MyBox Perf 8,
Java 25 Performance, mémoire panel environ 6154M, `server-ip=` vide et port 22880.
Le ZIP 26.2 et la référence restent conservés ; ils ne sont pas la source de cette
préparation officielle 26.3. Ne pas effectuer de downgrade de monde.

## Repartir de l’archive initiale validée

1. Terminer et signer la recette à huit, traiter les anomalies et mesurer les performances
   sur l’hôte choisi. Le profil retenu est désormais Paper 26.3-244 / Java 25 ;
   conserver exactement les versions et empreintes du nouveau paquet, sans mélange 26.2/26.3.
2. Mettre la préproduction en pause, sauvegarder à froid et conserver cette archive comme
   preuve de recette. Arrêter le service et désactiver son redémarrage automatique.
3. Restaurer **le ZIP initial scellé Paper 26.3**, identifié dans `preproduction-package-26.3.json`,
   dans un espace neuf « officiel-prêt ». Employer la procédure de restauration complète.
   Ne pas restaurer la dernière sauvegarde de recette pour obtenir un état vierge.
   Ne pas modifier `runtime/map-v2-fixes` ni les historiques.
4. Vérifier le manifeste initial **avant configuration**. Cette restauration retrouve
   exactement les régions de la carte validée, terraformations, quatre territoires et
   drapeaux, sept monuments, six coffres de butin initial et les huit sites fixes.
   Les constructions, objets jetés, inventaires, captures et stocks consommés pendant
   les tests n’existent pas dans cette copie. Aucun réapprovisionnement de coffre dans
   un monde joué n’est nécessaire : on évite ainsi la duplication.
5. Configurer uniquement les paramètres d’hébergement du nouveau service arrêté,
   même version de Java/JAR ; remettre les huit pseudos officiels dans la whitelist
   via la console, puis reconnecter les joueurs. Le paquet ne contient aucun OP.
6. Vérifier `fka status` : **jour 0, installation**, pas de vainqueur ni éliminé,
   aucun objectif ni roster de recette. Ravitaillements : événement 0, délai initial
   1 800 secondes actives, aucune charge active/historique ; mode test désactivé.
   Le temps Minecraft du décor est celui de la référence, le jour FK passe à 1 lors
   du lancement. Ne pas modifier les compteurs manuellement.
7. Attribuer les quatre binômes connectés avec `fka assign <pseudo> <équipe>`.
   Les territoires et points d’apparition sont déjà enregistrés : les inspecter sans
   employer `fka territory`, qui déplacerait la base et invaliderait ses réglages.
   La validation visuelle de la carte a été donnée par le propriétaire ; enregistrer
   les confirmations nécessaires : `fka terrain Rouge confirm`, puis Bleue, Verte,
   Jaune. Contrôler deux blocs libres et un sol sûr à chaque spawn.
8. Les salles secrètes restent à construire/enregistrer par les équipes pendant la
   partie : ne pas recopier leurs objectifs de recette. Pas de coordonnées secrètes
   dans un message public ou un fichier Git. Aucun joueur ne doit être OP.
9. Réaliser `fka teams tpall` pour prévisualiser puis `fka teams tpall confirm` pour
   placer les huit joueurs aux bases, encore en installation. Contrôler l’intégrité
   des inventaires et l’absence d’équipement de recette. Annuler en cas de destination
   dangereuse plutôt que d’utiliser un contournement.
10. Sauvegarder à froid cette préparation officielle, puis redémarrer en vérifiant le
    jour 0 et les huit comptes. Faire signer la checklist : version/compatibilité,
    huit joueurs, terrains, règles, whitelist, sauvegarde restaurable, performances.

## Lancement humain uniquement

Quand tout est validé et les huit joueurs connectés, l’administrateur utilise
**`fka start` depuis la console**, sans `override`. Le passage attendu est au jour 1,
PvE actif, PvP fermé. La commande native `fk game start` est volontairement bloquée.
Après une reconnexion ou un redémarrage, utiliser les états enregistrés et la pause,
jamais un second lancement ni une restauration partielle pour « synchroniser ».

Le retour arrière après incident consiste à arrêter puis restaurer un point complet
dans un autre espace avec sa version d’origine. Un monde de test migré en 26.3 reste
en 26.3 ; retrouver 26.2 exige une copie du ZIP 26.2 **antérieur à la conversion**.
