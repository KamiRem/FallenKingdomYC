# Recette avec huit comptes Minecraft authentifiés

**À exécuter avec les huit personnes.** Aucun test de cette préparation ne constitue
une connexion de client authentifié ni une mesure de charge à huit. Les anciens
probes emploient des interfaces Player simulées. Leur succès ne coche aucune ligne
de cette recette humaine.

## Préparer la session

Prévoir 2 à 3 heures, huit clients Java **26.3** et une préproduction issue du ZIP initial **26.3**, un point de sauvegarde
à froid, huit clients Java de la version choisie, deux comptes par équipe Rouge,
Bleue, Verte, Jaune. L’un des huit peut piloter la console du panel depuis son navigateur ;
aucun compte de jeu ne reste OP. Garder une feuille privée avec pseudos réels,
horaires, captures et signatures ; utiliser seulement J1…J8 dans les comptes rendus Git.
Les secrets des salles restent entre chaque équipe et l’administrateur.

Whitelist vide au départ : ajouter les huit comptes via console, vérifier
`online-mode=true`, refuser un compte hors liste. Attribuer les binômes connectés par
`fka assign`, confirmer les quatre terrains inspectés. Prévisualiser la téléportation
avec `fka teams tpall`, vérifier les destinations puis confirmer. Aucun contournement
`start override`. Sur cette copie **de recette**, lancer manuellement `fka start`.

## Scénarios et preuves attendues

Chaque ligne doit recevoir date UTC, exécutants J1…J8, résultat, preuve privée et
numéro d’anomalie si échec. Ne pas cocher « réussi » à partir d’un ancien rapport technique.

| Cas | Manipulation à huit / par binômes | Critère d’acceptation |
|---|---|---|
| Accès | Connexion des huit officiels, tentative hors whitelist, vérification OP | 8 authentifiés, quatre binômes, accès refusé au neuvième, participants non OP |
| Téléportation | Prévisualisation puis confirmation, cas temporaire hors ligne | Tous aux bons spawns sûrs ; avertissement explicite pour absent, pas de téléportation silencieuse dangereuse |
| Chat/interfaces | Chaque binôme échange un message privé ; vérifier les six non-destinataires, puis le préfixe `!` global ; afficher aide, règles, équipes et tableau de bord | Livraison privée aux alliés seulement, global reçu, interfaces lisibles sans exception ; preuve réseau réelle |
| Spawns | Chaque binôme meurt en recette puis réapparaît ; essayer lit personnel | Réapparition conforme à la règle au royaume, sans suffocation ni chute |
| Carte/butin | Visiter bases, drapeaux, sept monuments, six coffres ; prendre un lot puis revenir/redémarrer | Carte intacte, butin initial exact, lot retiré non recréé automatiquement |
| J1 PvE | Chaque équipe combat un zombie/squelette ; vérifier dégâts de chute/feu | Mobs actifs et dégâts reçus dès J1 |
| J1 PvP | Attaque directe, projectile et TNT entre ennemis en zone neutre | Aucun dommage PvP ; pas de contournement par attribution de TNT/projectile |
| J1 territoires | Deux alliés construisent, deux ennemis tentent de miner/poser/ouvrir les accès protégés | Droits alliés attendus, protections adverses conservées |
| J2 | Console `fka nextday` une fois ; mêlée/projectiles hors puis dans royaume ennemi | PvP neutre autorisé, assaut protégé ; feu allié interdit ; Nether selon règle J2 |
| J3 TNT | `fka nextday`, chaque binôme prépare défense et attaque adverse à la TNT | Murs adverses endommagés par explosion en phase d’assaut, PvP conforme |
| Minage adverse | Essayer pioche/main/outils à J1, J2, J3 et après pause/reconnexion | Minage manuel ennemi refusé dans toutes les phases, aucun succès après J3 |
| Objets interdits | Sur copie de recette seulement, fournir par console netherite, débris, modèle, élytres, pomme enchantée ; tester ramassage/inventaire/équipement/coffre | Usage prohibé selon le règlement ; pomme dorée ordinaire autorisée ; vérifier toutes dimensions accessibles |
| Salles secrètes | Construire quatre salles légitimes ; chaque équipe cible son coffre et `/fka room register` ; admin inspecte/valide en privé | Aucun secret en chat général, coffre accessible par chemin légitime, seuil de validation respecté |
| Capture | Un attaquant, puis deux de même équipe à portée ; interrompre avant 60 s ; sortir/revenir | Pas de capture à un ; progression interrompue correctement ; capture à deux après durée complète |
| Élimination/victoire | Faire capturer successivement trois royaumes en gardant le dernier vivant | Éliminés sans capacité de combat/contournement après reconnexion ; victoire annoncée une seule fois au dernier royaume |
| Ravitaillements | Sur une autre copie fraîche si partie terminée : jouer 30 minutes actives ; visiter les huit sites, ouvrir à plusieurs et vider un lot | Zones annoncées, maximum deux charges, tables prévues, pas de double distribution, expiration à 10 minutes |
| Pause/reprise | `fka pause`, attendre au moins 2 minutes, observer timer/capture/dégâts ; `fka resume` | Chronomètres de jeu/approvisionnement suspendus, reprise cohérente, pas de double événement |
| Déconnexions | Quitter/revenir à un puis deux membres pendant combat/capture et à proximité d’un coffre | Roster conservé, aucun doublon ni gain de progression indue, reconnexion des éliminés cohérente |
| Redémarrage | Pause/save/stop pendant état représentatif, redémarrer même version | Jour, équipes, objectifs, éliminations, inventaires et délai de ravitaillement conservés |
| Restauration | Après lot consommé et construction témoin, sauvegarder à froid ; modifier puis restaurer entièrement dans espace neuf | Retour exactement au point sauvegardé, témoins/inventaires cohérents, aucune duplication ; ancienne copie arrêtée |

La victoire termine la partie : les scénarios qui exigent une partie active doivent
précéder la victoire ou se dérouler sur **une deuxième copie initiale**, pas après
une édition improvisée de `state.yml`. N’ajouter aucun plugin de fixture à l’hôte.

## Mesure de performances réelle

Relever l’offre, CPU/nœud annoncé, Java complet, versions/hash des deux plugins,
limite RAM, heap, vue 8/simulation 6, version des clients et réseau des huit joueurs.
Après 5 minutes de chauffe, garder **les huit connectés simultanément pendant au moins
30 minutes** : 10 minutes répartis entre bases/monuments, 10 de combat/TNT/capture,
10 d’exploration/ravitaillements. Inclure un trajet Nether si ouvert. Ne pas générer
un immense territoire hors de la bordure pour artificiellement charger le serveur.

Toutes les 60 secondes : console `tps`, `mspt`, capture des métriques RAM totale du
panel, heap/GC si exposés et ping de chaque client. Conserver les sorties brutes
avec horodatage ; si `mspt` ne fournit pas de percentile exploitable, inscrire « non
mesuré » pour p95. Ne pas déduire un p95 de quelques moyennes. Spark intégré peut
fournir un profil si un problème le justifie, mais l’envoi externe d’un profil reste
une décision de l’administrateur ; aucune publication automatique de données privées.

Gabarit `deployment/acceptance-metrics.example.csv` : recopier dans un fichier privé.
Cibles proposées pour accepter l’offre, **aucune valeur mesurée à ce stade** :

| Mesure | Cible et décision |
|---|---|
| TPS | 20 visés ; pas de chute durable sous 19,5 en jeu normal |
| MSPT | Budget de 50 ms/tick à 20 TPS ; moyenne nettement sous 50, p95 sous 50 si mesurable ; expliquer les pics TNT |
| Mémoire | Aucune OOM/relance, pas de dérive continue, garder une marge native de 1–2 Go sur un service 8 Go |
| Réseau | Relever médiane/max par joueur ; cible indicative <60 ms pour joueurs en France, pas de pertes/déconnexions répétées |
| Ressenti | Aucun retour arrière récurrent, coffre retardé ou bloc qui réapparaît ; associer heure et scénario à chaque incident |

Si échec : conserver logs et point de sauvegarde, identifier CPU, RAM ou réseau avant
de changer l’offre ou les réglages. Refaire seulement les scénarios concernés plus
les invariants touchés. Signer avec les huit joueurs ; le lancement reste suspendu
tant qu’un défaut bloquant de règles, sécurité, restauration ou performances subsiste.
