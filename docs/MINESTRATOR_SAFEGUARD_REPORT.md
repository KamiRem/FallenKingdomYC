# Sécurisation préalable — 15 novembre 2026

Résultat : **arrêt au contrôle 2, avant toute sauvegarde**. L'autorisation reçue
porte seulement sur la sécurisation et la restauration de contrôle, pas sur la
bascule V2.1. Aucun fichier distant n'a été modifié et aucune action d'alimentation
ou commande console n'a été envoyée.

## Contrôle 1 : état arrêté confirmé

À `2026-11-15T18:01:28.3700899Z` (19:01:28 à Paris), les lectures authentifiées
`GET /server/{id}` et `GET /server/{id}/live` renvoient un code API 200. L'identité
correspond à la configuration locale ; `state` et `stats.state` sont `offline`.
Le port reste 22880. C'est une observation d'état à cet instant, pas une garantie
de maintien à l'arrêt pendant une copie.

## Contrôle 2 : exclusion du redémarrage non démontrée

Les données retournées ne donnent pas de liste vérifiable des tâches planifiées,
des actions d'alimentation en attente, ni de preuve d'un verrou de maintenance
exclusif. Le champ `poweraction_message.restart` est un message de notification :
il ne renseigne pas l'activation ou l'absence de redémarrage automatique.

La [documentation REST consultée](https://api.minestrator.com/) ne fournit pas de
mécanisme documenté permettant à cet audit d'acquérir ce verrou. C'est une limite
des accès et preuves actuellement disponibles, pas une affirmation qu'aucune
solution n'existe chez le fournisseur.

Le [guide officiel des tâches planifiées](https://minestrator.com/blog/article/tache-planifiee-minestrator-automatiser-serveur)
indique que leurs actions ne sont pas lancées quand le serveur est arrêté. Cette
règle ne prouve pas l'absence d'autres actions déjà en cours, d'une relance externe
ou d'une intervention d'un autre opérateur. Elle ne remplace pas un verrou partagé.

L'accès SFTP authentifié permet la lecture des fichiers, mais ne démontre pas la
possibilité d'exécuter un outil de verrouillage de processus sur l'hôte. Aucun
verrou distant n'a été acquis ou prétendu acquis. Aucun redémarrage n'a été détecté ;
c'est la garantie préventive demandée qui manque.

`AGENTS.md` impose : « Sauvegardes uniquement serveur arrêté, avec verrou de
processus partagé. » L'utilisateur a aussi demandé l'arrêt dès l'échec d'un
contrôle. Les observations API répétées ou un verrou local sur le PC ne suffisent
pas à satisfaire cette exigence distante.

## Opérations non exécutées

| Opération autorisée sous conditions | État |
|---|---|
| Création de la sauvegarde complète actuelle | Non commencée |
| Téléchargement hors du dépôt et de l'instance | Non commencé |
| SHA-256 complets de ce nouveau point | Non calculés |
| Restauration locale de ce nouveau point | Non exécutée |
| Cohérence monde/inventaires/états de cette restauration | Non vérifiée |
| Transfert des 146 fichiers, carte ou territoires | Non autorisé et non effectué |

Les empreintes et l'inventaire établis auparavant restent des preuves d'audit,
pas une nouvelle sauvegarde complète ni une restauration validée. Aucun fichier
de sauvegarde ou de restauration n'a été créé hors du dépôt pendant cette phase.
Le présent document et sa synthèse JSON sont uniquement des rapports locaux.

## Condition nécessaire pour reprendre la sécurisation

Obtenir une garantie de maintenance exclusive du fournisseur, ou un accès
permettant d'exécuter sur l'hôte les outils de maintenance avec verrou partagé et
verrous natifs, pendant que le serveur reste arrêté. Vérifier dans le panel les
tâches/actions en attente et les mécanismes de redémarrage ; préserver la liste des
réglages temporairement neutralisés afin de les rétablir ensuite. Une simple
confirmation de tâches désactivées ne prouve pas, à elle seule, le verrou partagé.

Demande manuelle ciblée possible au support, à envoyer par l'utilisateur :

> Je prépare une sauvegarde complète à froid de mon serveur. Pouvez-vous garantir
> une fenêtre de maintenance exclusive empêchant tout démarrage et toute écriture
> concurrente pendant la copie, ou fournir un moyen d'exécuter un outil de sauvegarde
> avec verrou partagé et verrous natifs ? Merci de préciser la procédure et sa durée.

Aucun message n'a été envoyé au support par l'agent. Une fois cette preuve obtenue,
la sauvegarde et sa restauration pourront reprendre dans le cadre de l'autorisation
de sécurisation déjà donnée ; aucune nouvelle autorisation de déploiement n'en
découle.

La destination proposée, à créer seulement lors de la reprise, est un dossier privé
hors dépôt tel que `C:\Users\youne\Documents\FallenKingdom-Backups`, avec une archive,
un manifeste par fichier et une empreinte externe. La restauration sera dans un
autre dossier local neuf ; ses fichiers et inventaires devront être comparés avant
tout démarrage éventuel isolé.

Le [plan de bascule](MINESTRATOR_DEPLOYMENT_PLAN.md) est conservé. Il ne sera présenté
comme validé par la sauvegarde/restauration qu'après réussite de ces opérations.
