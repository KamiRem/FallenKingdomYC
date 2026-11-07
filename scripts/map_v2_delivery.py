"""Produit le carnet de visite depuis le chantier réel et vérifie l'original à froid."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from server import ROOT, digest, iter_files, maintenance, server_dir, verify_archive


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    index=json.loads((ROOT/'maps/manifest.json').read_text(encoding='utf-8'))
    if index.get('candidate')=='runtime/map-v2-fixes':
        raise RuntimeError('La variante corrigée utilise scripts/map_v2_fixes_delivery.py ; ne pas réécrire son carnet avec le générateur historique.')
    built_path = ROOT / "maps/v2/built-manifest.json"
    built = json.loads(built_path.read_text(encoding="utf-8"))
    if built["status"] != "BUILT" or built["visualValidation"]:
        raise RuntimeError("Chantier construit et validation visuelle distincte requis.")
    baseline = json.loads((ROOT / ".cache/map-v2-baseline.json").read_text(encoding="utf-8"))
    original = server_dir("local")
    with maintenance(original):
        actual = {str(p.relative_to(original)): digest(p) for p in iter_files(original)}
        if actual != baseline["files"]:
            raise RuntimeError("L'original diffère de l'empreinte initiale ; conserver toutes les copies pour examen.")
    archive = ROOT / baseline["archive"]
    if digest(archive) != baseline["sha256"]:
        raise RuntimeError("L'archive initiale diffère de son empreinte.")
    archived = verify_archive(archive)
    root = server_dir("map-v2")
    with maintenance(root):
        plugins = sorted(p.name for p in (root / "plugins").glob("*.jar"))
        if any("Builder" in p or "Probe" in p for p in plugins):
            raise RuntimeError("Outil temporaire présent dans les plugins de livraison.")
        jar = root / "plugins/FKAmis-1.0.0.jar"
        if digest(jar) != digest(ROOT / "plugins-custom/fk-amis/target/fk-amis-1.0.0.jar"):
            raise RuntimeError("JAR livré différent du JAR compilé.")
        config_dir = ROOT / "configs/map-v2"
        config_dir.mkdir(exist_ok=True)
        shutil.copy2(root / "plugins/FKAmis/supplies.yml", config_dir / "supplies.yml")
        # Profil complet, sans progression ni données de joueurs.
        shutil.copy2(root / "plugins/FKAmis/config.yml", config_dir / "fkamis.yml")
        world_files = {p.relative_to(root).as_posix(): digest(p) for p in iter_files(root / "world")}
    old_manifest = ROOT / "maps/v1-manifest.json"
    if not old_manifest.exists():
        shutil.copy2(ROOT / "maps/manifest.json", old_manifest)
    write_json(ROOT / "maps/manifest.json", {
        "schema": 2, "activeInstanceUnchanged": "runtime/local", "candidate": "runtime/map-v2",
        "minecraft": "26.2", "seed": built["seed"], "borderSize": built["border"],
        "constructed": True, "visualValidation": False, "officialGameStarted": False,
        "builtManifest": "maps/v2/built-manifest.json", "survey": "maps/v2/terrain-survey.json",
        "worldChecks": "tests/results/map-v2-world.json", "historicalMap": "maps/v1-manifest.json",
        "inspection": "docs/MAP_V2_INSPECTION.md", "prebuiltForts": 0,
    })
    write_json(ROOT / "tests/results/map-v2-preservation.json", {
        "checkedAtUtc": datetime.now(timezone.utc).isoformat(),
        "originalInstance": "runtime/local", "unchanged": True,
        "comparedFiles": len(actual), "initialBackup": baseline["archive"],
        "backupSha256": baseline["sha256"], "backupManifestFiles": len(archived["files"]),
        "candidateWorldFiles": len(world_files),
        "candidateLevelDatSha256": world_files["world/level.dat"],
        "candidateJarSha256": digest(jar), "plugins": plugins,
        "note": "Empreintes intégrales comparées à froid ; verrous natifs exclus par iter_files. Aucune bascule de local.",
    })

    lines = [
        "# Visite de la carte v2 — coordonnées réellement placées", "",
        "Ce carnet provient de `maps/v2/built-manifest.json`, écrit par Paper après le chantier.",
        "La présence technique des blocs est testée ; **l'inspection visuelle et l'équilibre à huit joueurs restent à valider**.",
        "Aucune capture d'écran Minecraft n'a été réalisée. Les coordonnées ci-dessous sont publiques ; aucun objectif secret n'est défini.", "",
        "## Ouvrir la candidate", "", "```powershell",
        r".\scripts\server.ps1 start -Name map-v2 -Port 25577", "```", "",
        "Se connecter avec Minecraft Java 26.2 à `127.0.0.1:25577`. Depuis la console :",
        "`whitelist add PseudoArbitre`, puis `op PseudoArbitre`. Avant toute partie, passer l'arbitre",
        "en créatif avec `/gamemode creative`. Les vues aériennes ci-dessous supposent le vol créatif activé.",
        "Ne pas lancer la partie pendant cette visite. Préférer une copie supplémentaire pour tester les commandes de butin.", "",
        "## Terrains et drapeaux", "",
        "| Royaume | Centre X/Z | Pied du mât Y | Téléportation au spawn vérifié |", "|---|---|---|---|",
    ]
    for base in built["bases"]:
        spawn = base["spawn"]
        lines.append(f'| {base["team"]} | {int(base["x"])} / {int(base["z"])} | {base["flagY"]} | `/tp @s {spawn["x"]} {spawn["y"]} {spawn["z"]}` |')
    lines += ["", "Chaque territoire a un rayon carré de 80 blocs. Inspecter tout le périmètre, pas seulement le spawn :",
              "surface de construction, transitions de pente, arbres, accès aux grottes et bois, eau, absence de fort vanilla donnant un avantage.",
              "Les mâts font neuf blocs, sans effet sur les captures. Aucun château d'équipe n'a été ajouté.", "",
              "Voisins : Rouge–Bleue 442, Rouge–Verte 482, Bleue–Jaune 408, Verte–Jaune 482 blocs à vol d'oiseau.",
              "Diagonales : Rouge–Jaune 681 et Bleue–Verte 595. Chronométrer au moins deux parcours à pied entre voisins.", "",
              "## Monuments", "", "Les téléportations aériennes permettent d'observer l'intégration avant de descendre en vol créatif.", "",
              "| Lieu | Ancrage X Y Z | Vue aérienne |", "|---|---|---|"]
    for monument in built["monuments"]:
        x, y, z = (monument[key] for key in ("x", "y", "z"))
        lines.append(f'| {monument["id"]} | {x} {y} {z} | `/tp @s {x} {y + 18} {z}` |')
    crypt = next(m for m in built["monuments"] if m["id"] == "crypte-des-veilleurs")
    lines += ["", f'Entrée de la crypte : `/tp @s {crypt["x"]} {crypt["y"] + 3} {crypt["z"] + 25}` en vol créatif.',
              "Descendre l'escalier à pied ; vérifier la hauteur libre, les marches, l'absence d'eau et les deux squelettes persistants.",
              "Vérifier l'échelle de la tour, la galerie de mine, les six coffres fixes et leurs petits lots avant toute exploration officielle.",
              "Le cercle central n'a pas de coffre. Les butins fixes ne se régénèrent pas.", "",
              "## Ravitaillements", "", "Les coffres physiques restent vides : les lots sont virtuels et remis au clic droit pendant la partie active.",
              "Le profil livré refuse `/fka supply test confirm`. Vérifier les chemins d'accès et le support sous chaque coffre.", "",
              "| Site | Zone | Bloc coffre X Y Z | Vue en vol |", "|---|---|---|---|"]
    for site in built["supplies"]:
        x, y, z = (site[key] for key in ("x", "y", "z"))
        lines.append(f'| {site["id"]} | {site["zone"]} | {x} {y} {z} | `/tp @s {x} {y + 4} {z}` |')
    lines += ["", "## Paysage et fin de visite", ""]
    for feature in built["landscape"]:
        if feature["type"] in ("lac", "cascade_rocaille"):
            lines.append(f'- {feature["type"]} : `/tp @s {feature["x"]} {feature["y"] + 12} {feature["z"]}` en vol créatif.')
    lines += ["", "Inspecter les passerelles et leurs piliers, les rives, les arbres autour des sentiers et les éventuelles ruptures de pente.",
              "Comparer les ressources accessibles autour des quatre terrains ; les minerais profonds n'ont pas été rééquilibrés artificiellement.",
              "Faire ensuite la recette multijoueur de `TEST_PLAN.md` : huit comptes authentifiés, captures, protections, inventaire plein, pause et reprise.",
              "Mesurer TPS/MSPT avec les huit joueurs répartis sur la carte ; les mesures automatisées sans joueurs ne suffisent pas.", "",
              "Après inspection seulement : `/fka terrain Rouge confirm`, `/fka terrain Bleue confirm`,",
              "`/fka terrain Verte confirm`, `/fka terrain Jaune confirm`. Retirer OP aux participants avant lancement.",
              "Sauvegarder puis exporter l'installation complète arrêtée. Conserver `runtime/local` et l'archive initiale.", ""]
    (ROOT / "docs/MAP_V2_INSPECTION.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Original inchangé : {len(actual)} fichiers ; archive initiale vérifiée ; carnet et profils produits.")


if __name__ == "__main__":
    main()
