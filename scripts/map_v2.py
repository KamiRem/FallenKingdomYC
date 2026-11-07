"""Chantier isolé ; ne lit l'original qu'au travers du manifeste de contrôle déjà sauvegardé."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import queue
import time
from server import ROOT, server_dir, maintenance, java_path, digest, validate, backup, restore, iter_files, file_lock


def prepare():
    source, target = server_dir("local"), server_dir("map-v2")
    if target.exists(): raise RuntimeError("map-v2 existe : aucune donnée ne sera remplacée.")
    import re
    if not re.search(r"^started: false$", (source / "plugins/FKAmis/state.yml").read_text(encoding="utf-8"), re.M):
        raise RuntimeError("La partie originale a commencé ; ne pas créer une nouvelle carte depuis sa progression.")
    archive = backup(source)
    report = {"archive": str(archive.relative_to(ROOT)), "sha256": digest(archive),
              "files": {str(p.relative_to(source)): digest(p) for p in iter_files(source)}}
    (ROOT / ".cache/map-v2-baseline.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    restore(target, archive)


def run(mode, name="map-v2"):
    if name!="map-v2" and not (name=="map-v2-fixes" and mode=="verify"):
        raise RuntimeError("Seule la vérification est autorisée sur map-v2-fixes.")
    root = server_dir(name)
    if mode == "repair-loot": backup(root)
    with maintenance(root, check_worlds=False):
        for session in root.rglob("session.lock"):
            with file_lock(session, create=False): pass
        validate(root)
        # Seule l'instance indépendante reçoit le JAR nouvellement compilé.
        companion = ROOT / "plugins-custom/fk-amis/target/fk-amis-1.0.0.jar"
        shutil.copy2(companion, root / "plugins/FKAmis-1.0.0.jar")
        (root / "FKAmis.sha256").write_text(digest(companion) + "\n", encoding="ascii")
        shutil.copy2(ROOT / ".cache/FKMapV2Builder.jar", root / "plugins/FKMapV2Builder.jar")
        config = root / "plugins/FKAmis/config.yml"
        content = config.read_text(encoding="utf-8").replace("border-size: 1800", "border-size: 1200")
        config.write_text(content, encoding="utf-8")
        properties = root / "server.properties"
        content = properties.read_text(encoding="utf-8").replace("server-port=25565", "server-port=25577")
        properties.write_text(content, encoding="utf-8")
        log_path = ROOT / ".cache" / f"map-v2-{mode}.log"
        command = [str(java_path()), "-Xms1G", "-Xmx4G", "-Dfk.mapv2.authorized=true", f"-Dfk.mapv2.mode={mode}",
                   "-jar", "paper.jar", "--nogui", "--host", "127.0.0.1", "--port", "25577"]
        process = subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
        lines = queue.Queue()
        text = []
        def reader():
            for line in process.stdout:
                text.append(line)
                lines.put(line)
        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        deadline = time.monotonic() + 1500
        try:
            while process.poll() is None:
                if time.monotonic() > deadline:
                    process.stdin.write("stop\n"); process.stdin.flush()
                    raise RuntimeError("Délai de chantier dépassé ; arrêt propre demandé.")
                try:
                    line = lines.get(timeout=1)
                    if "MAP V2" in line: print(line.strip(), flush=True)
                except queue.Empty: pass
            process.wait(timeout=120)
        finally:
            if process.poll() is None:
                process.stdin.write("stop\n");process.stdin.flush();process.wait(timeout=120)
            thread.join(timeout=5)
            log_path.write_text("".join(text), encoding="utf-8")
        expected = f"MAP V2 {mode.upper()} SUCCESS"
        if process.returncode or expected not in "".join(text) or "MAP V2 FAILED" in "".join(text):
            raise RuntimeError(f"Chantier {mode} échoué : {log_path}")
        # Déplacer l'outil hors des plugins, pas de suppressions ni de constructeur en production.
        saved = ROOT / ".cache" / f"FKMapV2Builder-{mode}-{datetime.now(timezone.utc).strftime('%H%M%S')}.jar"
        (root / "plugins/FKMapV2Builder.jar").replace(saved)
    print(f"Chantier {mode} terminé ; serveur arrêté.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "survey", "build", "verify", "repair-loot"])
    parser.add_argument("--name",default="map-v2")
    args = parser.parse_args()
    if args.mode == "prepare":
        if args.name!="map-v2":raise RuntimeError("La préparation de chantier garde son instance réservée.")
        prepare()
    else: run(args.mode,args.name)
