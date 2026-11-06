"""Échantillonner six graines réelles avec le plugin de recette, sans les valider pour le jeu."""
import importlib.util
from pathlib import Path
import shutil
import subprocess

spec = importlib.util.spec_from_file_location("server", Path(__file__).with_name("server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)

if __name__ == "__main__":
    root = server.server_dir("map-selection")
    server.validate(root)
    with server.maintenance(root, check_worlds=False):
        shutil.copy2(server.ROOT / ".cache/FKRuntimeProbe.jar", root / "plugins/FKRuntimeProbe.jar")
        result = subprocess.run([str(server.java_path()), "-Xms1G", "-Xmx4G", "-Dfkamis.probe=true", "-Dfkamis.probe.mapseeds=true",
                                 "-jar", "paper.jar", "--nogui", "--host", "127.0.0.1", "--port", "25576"],
                                cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        (server.ROOT / ".cache/seed-survey-console.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode or "PROBE SUCCESS" not in result.stdout:
            raise RuntimeError("Sondage de graines échoué : consulter .cache/seed-survey-console.log")
        target = server.ROOT / "maps/seed-survey.csv"
        shutil.copy2(root / "plugins/FKRuntimeProbe/seed-survey.csv", target)
        print(f"Sondage réel disponible : {target}", flush=True)
