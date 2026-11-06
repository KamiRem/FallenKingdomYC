"""Démarrage réel, contrôles console, arrêt propre, sauvegarde et restauration.

Ce script n'accepte jamais l'EULA. Une instance `smoke` neuve déjà acceptée est requise.
Le compte-rendu ne couvre ni clients authentifiés ni événements multijoueurs.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

spec = importlib.util.spec_from_file_location("server", Path(__file__).with_name("server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def smoke(name: str, pregen: bool):
    root = server.server_dir(name)
    report = {"atUtc": datetime.now(timezone.utc).isoformat(), "server": name,
              "configuredSeed": server.properties(root / "server.properties").get("level-seed"),
              "checks": [], "multiplayer": "non exécuté"}
    log_dir = server.ROOT / "tests/results"
    log_dir.mkdir(parents=True, exist_ok=True)
    with server.maintenance(root, check_worlds=False):
        server.validate(root)
        process = subprocess.Popen([str(server.java_path()), "-Xms1G", "-Xmx4G", "-jar", "paper.jar", "--nogui",
                                    "--host", "127.0.0.1", "--port", "25575"], cwd=root,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace", bufsize=1)
        lines = queue.Queue()
        full_log = []

        def read_output():
            for line in process.stdout:
                full_log.append(line)
                lines.put(line)

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

        def wait_for(marker, timeout=180):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try: line = lines.get(timeout=.5)
                except queue.Empty:
                    if process.poll() is not None: raise RuntimeError(f"Paper arrêté avant {marker}")
                    continue
                if marker in line:
                    report["checks"].append({"marker": marker, "passed": True})
                    print(f"PASS : {marker}", flush=True)
                    return
            raise RuntimeError(f"Délai dépassé : {marker}")

        def command(value):
            process.stdin.write(value + "\n")
            process.stdin.flush()

        try:
            wait_for("Done (")
            command("seed"); wait_for(report["configuredSeed"])
            command("fka status"); wait_for("Jour 0")
            command("fk game start"); wait_for("commandes natives verrouillées")
            command("fka start"); wait_for("Inspecter et confirmer les quatre terrains naturels")
            command("fka nextday"); wait_for("Aucune partie en cours")
            command("fka room inspect Rouge"); wait_for("Aucun objectif enregistré")
            command("fka survey"); wait_for("Rapport terrain privé écrit")
            command("fka save"); wait_for("Opération enregistrée")
            try:
                server.backup(root)
                raise AssertionError("Une sauvegarde concurrente aurait dû être refusée.")
            except RuntimeError as error:
                if "concurrente" not in str(error) and "actif" not in str(error): raise
                report["checks"].append({"marker": "backup refuses running server", "passed": True})
            if pregen:
                command("fka pregen")
                wait_for("Prégénération naturelle lancée")
                wait_for("Prégénération terminée", timeout=1800)
            command("stop")
            result = process.wait(timeout=120)
            thread.join(timeout=5)
            if result: raise RuntimeError(f"Code de sortie Paper : {result}")
            report["checks"].append({"marker": "clean stop", "passed": True})
        finally:
            if process.poll() is None:
                command("stop")
                process.wait(timeout=120)
            (log_dir / "smoke-console.log").write_text("".join(full_log), encoding="utf-8")
    try:
        server.check_logs(root)
        report["checks"].append({"marker": "plugin startup and no ERROR/SEVERE", "passed": True})
    except RuntimeError as error:
        report["checks"].append({"marker": "plugin startup and no ERROR/SEVERE", "passed": False, "detail": str(error)})
        print("Journal à examiner ; la génération et la sauvegarde restent vérifiées séparément.", flush=True)
    archive = server.backup(root)
    report["checks"].append({"marker": "real world backup verified", "passed": True})
    restored = server.server_dir(name[:20] + "-restore-" + datetime.now(timezone.utc).strftime("%H%M%S"))
    server.restore(restored, archive)
    server.validate(restored)
    report["checks"].append({"marker": "restore world and plugin state", "passed": True})
    report["worldGenerated"] = (root / "world/level.dat").exists()
    report["pregenerated"] = pregen
    (log_dir / "smoke.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Rapport : tests/results/smoke.json", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="smoke")
    parser.add_argument("--pregen", action="store_true")
    args = parser.parse_args()
    smoke(args.name, args.pregen)
