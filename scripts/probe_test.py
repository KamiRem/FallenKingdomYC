"""Recette Paper avec un plugin de test séparé, exclusivement dans runtime/probe.

Préparer et accepter l'EULA pour --name probe auparavant. Aucune connexion de joueur
ni authentification simulée. Les petites salles de fixture ne sont pas la carte livrée.
"""
import importlib.util
import argparse
import json
from pathlib import Path
import shutil
import subprocess

spec = importlib.util.spec_from_file_location("server", Path(__file__).with_name("server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="probe")
    args = parser.parse_args()
    if not args.name.startswith("probe"):
        raise ValueError("Recette de fixture réservée aux instances nommées probe...")
    root = server.server_dir(args.name)
    server.validate(root)
    output = server.ROOT / "tests/results"
    output.mkdir(parents=True, exist_ok=True)
    with server.maintenance(root, check_worlds=False):
        shutil.copy2(server.ROOT / ".cache/FKRuntimeProbe.jar", root / "plugins/FKRuntimeProbe.jar")
        checks = []
        for phase in ("initial", "restart"):
            command = [str(server.java_path()), "-Xms1G", "-Xmx3G", "-Dfkamis.probe=true"]
            if phase == "restart": command.append("-Dfkamis.probe.restore=true")
            command += ["-jar", "paper.jar", "--nogui", "--host", "127.0.0.1", "--port", "25576"]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=240)
            (output / f"probe-{phase}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
            passed = [line.split("PROBE PASS ", 1)[1] for line in result.stdout.splitlines() if "PROBE PASS " in line]
            if result.returncode or "PROBE SUCCESS" not in result.stdout or "PROBE FAILED" in result.stdout:
                print(result.stdout[-12000:], flush=True)
                raise RuntimeError(f"Recette {phase} échouée, consulter tests/results/probe-{phase}.log")
            checks.append({"phase": phase, "passed": passed})
            print(f"PASS {phase} : {len(passed)} contrôles sur Paper réel", flush=True)
    (output / "probe.json").write_text(json.dumps({"checks": checks, "multiplayer": "non exécuté"}, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__": main()
