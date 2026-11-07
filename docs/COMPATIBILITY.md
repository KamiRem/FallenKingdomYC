# Compatibilité et provenance — profil Paper 26.3

Profil courant autorisé : **Paper 26.3 build 244 STABLE**, Java 25, FallenKingdom
officiel 2.24.9, FKAmis 1.0.0 compilé contre `26.3.build.244-stable` et descripteur
`api-version: 26.3`. Les versions/hashes sont figés dans `configs/artifacts.lock.json`
et le profil `configs/paper-26.3/`. Les anciennes instances conservent leurs propres
JAR et verrous 26.2 ; aucune mise à jour n’y est appliquée.

| Vérification | Résultat / limite |
|---|---|
| Paper 244 | Téléchargement officiel revalidé, SHA-256 9601f9a26a2a52a0f2c807cf1abf691f96ee4fb287878313b601cebc2c51eabf |
| Java | Local Temurin 25.0.5+8 ; panel annoncé Java 25 Performance |
| FallenKingdom | 2.24.9 dernière release vérifiée, JAR officiel intact |
| FKAmis | 25 classes de production inchangées ; POM et descripteur mis à jour |
| Dépendances serveur | Deux JAR de plugins seulement ; outils Maven/JUnit/probes exclus de l’export |
| Exécution | Démarrages, reprise, restauration et 217 assertions sur Paper 26.3 réel réussis |
| Format monde | NBT 26.3 à palettes abrégées/defaults omis ; lecteur hors ligne adapté, aucun bloc réécrit |
| Clients | Aucun connecté ; interfaces, chat réseau et charge à huit à valider humainement |

La compatibilité **déclarée par FallenKingdom 2.24.9 reste 26.2**. Le profil 26.3
est désormais celui du projet à la demande du propriétaire, avec compatibilité
technique constatée dans notre recette ; cela ne constitue pas un engagement de
support de syldium. Une incompatibilité majeure empêcherait la promotion, sans
modification du JAR tiers. Aucun problème majeur n’a été détecté dans les essais finaux.

Les warnings de compilation signalent notamment PotionEffectTypeCategory et les
constructeurs d’événements des fixtures dépréciés, systemPath Maven et Guice/Unsafe.
Ils ne justifient pas de réécrire des mécaniques fonctionnelles dans cette livraison.
Les deux WARN du probe gameplay sont des refus de téléportation dangereuse attendus.
Les démarrages du candidat et de la restauration finale sont contrôlés séparément.

Les données converties ne doivent **jamais** être rouvertes en 26.2. Pour retrouver
26.2, restaurer l’archive antérieure dans un espace distinct avec ses JAR d’origine,
sans écraser les copies 26.3. Le paquet courant est décrit dans
`tests/results/preproduction-package-26.3.json` ; le détail est dans
[PREPRODUCTION_AUDIT.md](PREPRODUCTION_AUDIT.md).

FallenKingdom de syldium/Etrenak/fabulacraft : **CC BY-NC-ND 4.0**, usage privé non
commercial, JAR inchangé et attribution conservée. Aucun code tiers modifié n’est
distribué. FKAmis et les structures propres au projet restent indépendants, sous MIT.
Paper conserve ses licences ; Minecraft relève de son EULA, déjà acceptée explicitement
par le propriétaire pour les tests locaux, sans nouvelle acceptation automatique.
Java du fournisseur remplace le JDK Windows, non livré dans le paquet.

Sources : [Paper 244 officiel](https://fill.papermc.io/v3/projects/paper/versions/26.3/builds/244),
[Java requis](https://docs.papermc.io/paper/getting-started/),
[descripteur api-version](https://docs.papermc.io/paper/dev/plugin-yml/),
[release FK](https://github.com/syldium/FallenKingdom/releases/tag/v2.24.9),
[évolution Minecraft 26.3](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-3).
Historique documentaire pré-migration : `COMPATIBILITY_26_2.md`.
