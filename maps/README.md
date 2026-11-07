# Carte et confidentialité

`manifest.json` référence la candidate corrigée dans `runtime/map-v2-fixes`.
La v2 initiale est conservée dans `runtime/map-v2`.
`v2-corrections/preexisting-differences.json` consigne les aménagements
de monuments déjà présents dans la source et préservés par les corrections.
Les fichiers de monde restent exclus de Git. `v1-manifest.json` conserve le descriptif
de la carte historique de `runtime/local`, restée intacte.

Aucun château d'équipe, mur défensif, salle ou objectif n'est fourni. Les quatre terrains
et drapeaux sont construits, les territoires définis mais leur inspection humaine reste
à confirmer. Sept monuments neutres possèdent des plans de blocs JSON originaux dans
`v2/structures` ; ils sont lus par l'outil de chantier Paper, pas par WorldEdit.
`monuments.json` et `supply-locations.json` contiennent les positions après placement.
Les objectifs seront posés et cachés par les équipes. Ne jamais copier leur état ici.

Consulter [la v2](../docs/MAP_V2.md), [le carnet de visite](../docs/MAP_V2_INSPECTION.md)
et [le guide de carte](../docs/MAP_GUIDE.md) pour prégénérer, importer et contrôler
les terrains. La génération vanilla conserve quelques structures naturelles ; il
faut sélectionner les territoires pour ne pas donner une forteresse ou un village
défendable à une seule équipe.
