# Compatibilité et provenance

Les corrections de gameplay conservent Paper 26.2 build 135, Java 25 et FallenKingdom
2.24.9, sans modification du JAR tiers ni dépendance de jeu supplémentaire. Le JAR
FKAmis corrigé est identifié par son empreinte dans `v2-fixes-delivery.json`.
Les outils de nettoyage et de recette sont retirés de la candidate après usage.

## Contrôle carte v2 — 7 novembre 2026

La copie v2 utilise les mêmes Paper 26.2 build 135, FallenKingdom 2.24.9 et Java 25.
Le complément est recompilé contre la même API fixe. Aucun WorldEdit, FAWE, générateur
ou plugin de ravitaillement tiers n'est ajouté au profil de jeu. Les formats JSON de
structures sont des créations originales, chargées par l'outil Paper séparé et
contrôlées sur les blocs réels après placement. Ce ne sont pas des fichiers `.schem`.

Les compatibilités **déclarées** des solutions alternatives et leurs licences sont
référencées dans [MAP_V2.md](MAP_V2.md) et [LOOT_SYSTEM.md](LOOT_SYSTEM.md) ; elles ne
sont pas présentées comme des chargements locaux effectués. Le statut non maintenu
de Paper 26.2 et la nécessité d'une recette de migration restent ceux indiqués ci-dessous.

Vérification du **6 novembre 2026**. Les versions exactes installables sont enregistrées
dans `configs/artifacts.lock.json`, avec liens officiels et empreintes. Ne pas remplacer
les numéros par `latest` dans les scripts d'installation.

| Composant | Version retenue | Vérification |
|---|---|---|
| Minecraft / Paper | 26.2, build 135 STABLE, commit e4d6dfd | Métadonnées API Paper officielles et JAR vérifié SHA-256 |
| API Paper de compilation | 26.2.build.135-stable | Résolue et compilée par Maven, version fixe |
| FallenKingdom | 2.24.9, publication 24 août 2026 | API GitHub et Spigot, tag source v2.24.9 (d3d5b00), JAR officiel SHA-256 |
| Java portable Windows x64 | Eclipse Temurin 25.0.5+8, HotSpot | Archive proposée par l'API Adoptium au moment de la vérification ; SHA-256 dans le verrou |
| Maven | 3.9.11 | Archive Apache/Maven Central, SHA-512 officiel vérifié |
| FKAmis | 1.0.0 | Sources de ce dépôt, compilation Java 25 |
| Python | 3.11+ requis ; 3.14 présent sur ce poste | Scripts sans dépendance Python tierce |
| JUnit Jupiter | 5.11.4 | Tests de progression et capture ; aucune dépendance d'exécution du serveur |

Paper propose aussi 26.3. La fiche publique de FallenKingdom 2.24.9 annonce une
compatibilité jusqu'à 26.2 ; la branche principale contient des adaptations plus
récentes mais n'est pas utilisée comme release. **26.2 n'est donc pas présenté comme
la dernière version Paper ni comme une branche encore maintenue.** Ce profil est
figé pour la recette privée. Une migration vers une branche Paper maintenue exige
de revérifier FallenKingdom et les API avant déploiement durable.

L'API officielle interrogée confirme `support.status: UNSUPPORTED` et la fin de support
de 26.2 au **3 novembre 2026**, avec Java minimum 25. Le profil fonctionne pour les
tests décrits mais n'est pas présenté comme une production durable sur une branche
maintenue. Le relevé de compatibilité est conservé dans `tests/results/compatibility.json`.

La compilation et un chargement réel sont des contrôles différents de la recette
multijoueur. Le bilan exact est dans [TEST_PLAN.md](TEST_PLAN.md), jamais inféré d'un
simple téléchargement réussi.

## Changements d'API pris en compte

- Java 25 pour les versions Paper 26.1 et suivantes.
- API publiée avec version `26.2.build.135-stable`, sans ancien `R0.1-SNAPSHOT`.
- Certaines dimensions n'ont pas d'horloge : `World#setFullTime` y lève une exception.
  Seuls les mondes normaux ont leur temps préservé lors de la synchronisation native.
- Règle `GameRules.ADVANCE_TIME` pour le cycle naturel et API du tick manager pour la pause.
- Organisation des dimensions 26.x : sauvegarde récursive de tout le dossier du serveur.
- Aucun appel NMS de l'extension ; FallenKingdom conserve ses propres adaptations de versions.

## Licences

FallenKingdom est publié sous **CC BY-NC-ND 4.0**, par Etrenak, fabulacraft et syldium.
Usage privé non commercial ; JAR officiel intact, attribution conservée. Aucun code
modifié du plugin n'est distribué. Le complément est un plugin séparé et ne contient
pas les classes de FallenKingdom. Ne pas vendre une version modifiée du plugin tiers.

Paper relève de ses licences open source, le logiciel serveur Minecraft de son EULA.
Temurin utilise GPLv2 avec exception Classpath ; Maven est Apache-2.0. Le bootstrap
conserve les archives complètes de Java/Maven et leurs notices. Le code propre à ce
dépôt est sous MIT ; cela ne modifie aucune licence des logiciels téléchargés.

## Sources officielles

- [Téléchargements Paper](https://papermc.io/downloads/paper)
- [API Paper : version 26.2](https://fill.papermc.io/v3/projects/paper/versions/26.2)
- [API Paper : build 135](https://fill.papermc.io/v3/projects/paper/versions/26.2/builds/135)
- [Service de téléchargement Paper](https://docs.papermc.io/misc/downloads-service/)
- [Exigences Java Paper](https://docs.papermc.io/paper/getting-started/)
- [FallenKingdom Spigot](https://www.spigotmc.org/resources/fallenkingdom.38878/)
- [Release officielle 2.24.9](https://github.com/syldium/FallenKingdom/releases/tag/v2.24.9)
- [Sources exactes et licence](https://github.com/syldium/FallenKingdom/tree/v2.24.9)
- [API Adoptium](https://api.adoptium.net/v3/assets/latest/25/hotspot?architecture=x64&image_type=jdk&os=windows&vendor=eclipse)
- [Archive Maven 3.9.11](https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.11/)
- [EULA Minecraft](https://www.minecraft.net/eula)
