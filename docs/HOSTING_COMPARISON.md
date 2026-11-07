# Hébergement — relevé public du 7 novembre 2026

**Recommandation : MineStrator MyBox Perf 8 en France, 23,99 € TTC par mois,
cycle d’un mois.** Le CPU plus rapide laisse davantage de marge pour les ticks,
explosions et captures. C’est une estimation de dimensionnement pour huit joueurs,
deux plugins et carte prégénérée ; aucune performance à huit n’a été mesurée.
Alternative économique : MyBox 8 à **13,99 € TTC/mois**, sous la fourchette prévue,
à retenir si sa recette de charge réussit. Plus de RAM sur un CPU moins rapide
ne résout pas nécessairement une saturation du thread principal.

## Caractéristiques publiées

| Offre mensuelle | CPU annoncé / allocation | RAM | Stockage | Localisation | Prix mensuel public |
|---|---|---|---|---|---|
| MineStrator MyBox Perf 8 — choix principal | Ryzen 9 9900X OC, 2 cœurs + 1 FlexCore temporaire | 8 Go DDR5 | 50 Go NVMe Gen5 | France, Toulouse | **23,99 € TTC**, un mois |
| MineStrator MyBox 8 — économie | EPYC 7543p, 2 cœurs + 1 FlexCore temporaire | 8 Go DDR4 | 50 Go NVMe Gen4 | France, Toulouse | **13,99 € TTC**, un mois |
| DedicatedMC Budget — autre hébergeur étudié | Ryzen 7600/9600X, cœur partagé | 6 Go | 50 Go NVMe | Amsterdam ou Royaume-Uni notamment | **14 USD/mois affichés** ; total France TTC/euros non établi |
| DedicatedMC Premium | Ryzen 7900/9900X, cœur dédié annoncé | 8 Go DDR5 | 70 Go NVMe | Amsterdam ou Royaume-Uni notamment | **24 USD/mois affichés** ; total France TTC/euros non établi |

Les deux lignes MineStrator viennent des [offres mensuelles officielles](https://minestrator.com/hebergeur/minecraft).
La [FAQ tarifaire](https://minestrator.com/foire/aux/questions) précise TTC, absence de frais
de mise en service et remise liée à la durée. Les prix retenus n’utilisent ni engagement
long, ni coupon, ni tarif de premier mois. Vérifier le total et le renouvellement au
récapitulatif avant paiement, sans ajouter d’options. Le FlexCore ne vaut pas un troisième
cœur permanent. Les chiffres sont des annonces commerciales, pas des benchmarks locaux.

Les lignes DedicatedMC viennent du [catalogue officiel](https://portal.dedicatedmc.io/index.php?rp=%2Fstore%2Fgame-server-hosting-plans).
La TVA applicable, le change et les éventuels frais de paiement français ne sont pas
prouvés par ce catalogue USD ; aucun prix TTC en euros n’est inventé. Ces offres ne
sont donc pas retenues devant un total public TTC connu. Aucune commande, simulation
de panier avec identité, création de compte ni activation d’essai n’a été effectuée.

## Fonctions nécessaires

| Critère | MineStrator, commun aux deux recommandations | DedicatedMC, réserve de comparaison |
|---|---|---|
| Java 25 | Sélection documentée pour Minecraft 26.1+ | Sélecteur Java documenté, page ancienne ne prouvant pas Java 25 : confirmation requise |
| JAR Paper personnalisé | Oui, fichier choisi dans Paramètres → Hébergement | Guide custom JAR disponible ; Java 25 à confirmer avant achat |
| SFTP / console | SFTP, WebSFTP et console MineBoard | SFTP et panel documentés |
| Sauvegardes / restauration | SmartBackup inclus : horaire en France, historique 30 jours, restauration panel | Site annonce snapshots hors site toutes les 15 minutes, conservation jusqu’à trois mois |
| DDoS | Protection incluse annoncée | Protection annoncée par le site, périmètre/limites à confirmer |
| Ping France | France disponible ; estimation commerciale 10–25 ms | Non mesuré, dépend de la route vers Amsterdam/UK ; pas de valeur garantie |
| Heap / limite conteneur | Viser 6 Go heap sur 8 Go service ; possibilité exacte de réglage à confirmer au panel/support | Même vérification nécessaire ; sur 6 Go viser au départ 4 Go heap |

La documentation [MineStrator custom JAR et Java](https://minestrator.com/blog/article/installer-version-custom-minecraft-serveur-minestrator)
confirme Java 25 et le transfert SFTP. [MineBoard](https://minestrator.com/mineboard/panel)
décrit la console. [SmartBackup](https://minestrator.com/sauvegardes/smartbackup)
décrit cadence, conservation et restauration ; prévoir en plus les points à froid
du projet. Les [localisations](https://minestrator.com/localisations/serveurs) proposent
Toulouse et un test de latence. L’estimation 10–25 ms vient de la
[FAQ du fournisseur](https://minestrator.com/foire/aux/questions), pas d’une mesure depuis
les connexions des huit amis. Leur faire tester cette page, puis le serveur livré.
Les caractéristiques et disponibilités du nœud exact restent à contrôler à la commande.

Pour DedicatedMC : [SFTP](https://docs.dedicatedmc.io/server-setup/how-to-upload-and-manage-your-files-with-sftp/),
[sélecteur Java, document ancien](https://docs.dedicatedmc.io/server-setup/how-to-change-your-servers-java-version/),
[catalogue des guides custom JAR](https://docs.dedicatedmc.io/),
[sauvegardes et services annoncés](https://dedicatedmc.io/).
L’absence de preuve publique actuelle de Java 25 et de total TTC suffit à ne pas le
recommander comme achat immédiat pour ce projet. Les cases inconnues restent inconnues.

## Vérifications avant commande personnelle

Choisir un mois en France, vérifier Java 25 + `paper.jar` custom, accès SFTP/console,
espace libre après sauvegardes et disponibilité réelle. Demander si nécessaire :
« Sur MyBox Perf 8 Minecraft, puis-je utiliser mon Paper custom Java 25 et limiter
la heap à 6 Go en gardant 8 Go au service ? Comment faire une restauration complète
serveur arrêté et exporter mes sauvegardes ? Le total mensuel est-il bien 23,99 € TTC
sans option ni engagement long ? » Ce texte n’a été envoyé à personne.

Le choix de l’offre ne résout pas le statut hors maintenance de Paper 26.2 : prendre
la décision de version après [l’audit](PREPRODUCTION_AUDIT.md), puis appliquer
[l’installation](HOST_INSTALLATION.md) et mesurer les performances à huit.
