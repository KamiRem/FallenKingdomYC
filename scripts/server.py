"""Gestion locale Windows/Linux, bibliothèque standard Python 3.11+ uniquement.

Toutes les opérations se limitent à runtime/, backups/ et dist/ du dépôt.
Les sauvegardes acquièrent un verrou commun et les verrous session.lock Minecraft.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LOCKFILE = ROOT / "configs/artifacts.lock.json"
PLUGIN = ROOT / "plugins-custom/fk-amis/target/fk-amis-1.0.0.jar"
EULA_URL = "https://www.minecraft.net/eula"


def confined(path: Path, parent: Path) -> Path:
    path, parent = path.resolve(), parent.resolve()
    if path == parent or not path.is_relative_to(parent):
        raise ValueError(f"Chemin hors du dossier autorisé : {path}")
    return path


def server_dir(name: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}", name):
        raise ValueError("Nom de serveur : lettres, chiffres, tiret, underscore (40 caractères maximum).")
    return confined(ROOT / "runtime" / name, ROOT / "runtime")


def digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm.lower())
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


@contextmanager
def file_lock(path: Path, create: bool = True):
    """Verrou OS, libéré même après un crash ; jamais de suppression du verrou d'un autre processus."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b" if create else "r+b") as handle:
        if create and path.stat().st_size == 0:
            handle.write(b"\0")
            handle.flush()
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.lockf(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, PermissionError) as exc:
            raise RuntimeError(f"Serveur actif ou opération concurrente : {path}") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.lockf(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def maintenance(root: Path, check_worlds: bool = True):
    root.mkdir(parents=True, exist_ok=True)
    with file_lock(root / ".control.lock"), ExitStack() as stack:
        if check_worlds:
            for lock in root.rglob("session.lock"):
                stack.enter_context(file_lock(lock, create=False))
        yield


def verified_artifacts() -> dict[str, Path]:
    lock = json.loads(LOCKFILE.read_text(encoding="utf-8-sig"))
    artifacts = {}
    for item in lock["artifacts"]:
        path = confined(ROOT / item["path"], ROOT)
        if not path.is_file() or digest(path, item["algorithm"]) != item["hash"]:
            raise RuntimeError(f"Archive absente ou empreinte incorrecte : {item['name']} ; exécuter scripts/bootstrap.ps1")
        artifacts[item["name"]] = path
    return artifacts


def install(root: Path):
    artifacts = verified_artifacts()
    if not PLUGIN.is_file():
        raise RuntimeError("Compiler le complément avec scripts/build.ps1 au préalable.")
    with maintenance(root):
        (root / "plugins/FallenKingdom").mkdir(parents=True, exist_ok=True)
        (root / "plugins/FKAmis").mkdir(parents=True, exist_ok=True)
        # Ne jamais réinitialiser les données ou configurations d'une partie existante.
        if (root / "plugins/FKAmis/state.yml").exists() or (root / "world/level.dat").exists():
            raise RuntimeError("Installation existante : sauvegarder, puis mettre à jour les JAR explicitement serveur arrêté.")
        shutil.copy2(artifacts["paper"], root / "paper.jar")
        shutil.copy2(artifacts["fallenkingdom"], root / "plugins/FallenKingdom-2.24.9.jar")
        shutil.copy2(PLUGIN, root / "plugins/FKAmis-1.0.0.jar")
        (root / "FKAmis.sha256").write_text(digest(PLUGIN) + "\n", encoding="ascii")
        templates = {
            ROOT / "configs/server/server.properties": root / "server.properties",
            ROOT / "configs/fallenkingdom/config.yml": root / "plugins/FallenKingdom/config.yml",
            ROOT / "plugins-custom/fk-amis/src/main/resources/config.yml": root / "plugins/FKAmis/config.yml",
        }
        for source, target in templates.items():
            if not target.exists():
                shutil.copy2(source, target)
        if not (root / "eula.txt").exists():
            (root / "eula.txt").write_text(f"# Lire {EULA_URL} puis accepter explicitement.\neula=false\n", encoding="utf-8")
        (root / ".fk-managed").write_text("FallenKingdomYC\n", encoding="utf-8")
        (root / "artifacts.lock.json").write_bytes(LOCKFILE.read_bytes())
    print(f"Installation préparée : {root}. EULA inchangée ; whitelist vide.")


def accept_eula(root: Path, accepted: bool):
    if not accepted:
        raise RuntimeError(f"Lire {EULA_URL}, puis utiliser accept-eula --accept explicitement.")
    with maintenance(root):
        if not (root / ".fk-managed").is_file():
            raise RuntimeError("Installation gérée absente.")
        (root / "eula.txt").write_text("# Acceptation explicite par l'administrateur.\neula=true\n", encoding="utf-8")
        (root / "eula-acceptance.json").write_text(json.dumps({
            "accepted": True, "url": EULA_URL, "atUtc": datetime.now(timezone.utc).isoformat()
        }, indent=2), encoding="utf-8")
    print("Acceptation explicite de l'EULA enregistrée pour ce serveur.")


def properties(path: Path) -> dict[str, str]:
    output = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            output[key.strip()] = value.strip()
    return output


def validate(root: Path):
    config = properties(root / "server.properties")
    required = {"online-mode": "true", "white-list": "true", "enforce-whitelist": "true",
                "enable-rcon": "false", "enable-command-block": "false"}
    for key, expected in required.items():
        if config.get(key) != expected:
            raise RuntimeError(f"Configuration refusée : {key} doit être {expected}.")
    if config.get("max-players") not in ("8", "10"):
        raise RuntimeError("Profil privé : 8 places historiques ou 10 places pour huit participants et un arbitre.")
    if properties(root / "eula.txt").get("eula") != "true":
        raise RuntimeError("EULA non acceptée. Aucune modification automatique.")
    for path in [root / "paper.jar", root / "plugins/FallenKingdom-2.24.9.jar", root / "plugins/FKAmis-1.0.0.jar"]:
        if not zipfile.is_zipfile(path):
            raise RuntimeError(f"JAR absent ou invalide : {path.name}")
    lock = json.loads((root / "artifacts.lock.json").read_text(encoding="utf-8-sig"))
    for item in lock["artifacts"]:
        if item["name"] in ("paper", "fallenkingdom"):
            path = root / "paper.jar" if item["name"] == "paper" else root / "plugins/FallenKingdom-2.24.9.jar"
            if digest(path, item["algorithm"]) != item["hash"]:
                raise RuntimeError(f"JAR modifié : {item['name']}")
    with zipfile.ZipFile(root / "plugins/FKAmis-1.0.0.jar") as jar:
        if "fr/fkamis/FKAmis.class" not in jar.namelist():
            raise RuntimeError("Classe principale FKAmis absente.")
    custom_hash = root / "FKAmis.sha256"
    if custom_hash.exists() and digest(root / "plugins/FKAmis-1.0.0.jar") != custom_hash.read_text(encoding="ascii").strip():
        raise RuntimeError("JAR FKAmis différent de celui enregistré à l'installation.")
    print("Configuration privée et JAR vérifiés. Cela ne valide pas le gameplay multijoueur.")


def java_path() -> Path:
    candidates = list((ROOT / ".tools/jdk").glob("*/bin/java.exe"))
    if not candidates:
        java = shutil.which("java")
        if java:
            return Path(java)
        raise RuntimeError("Java 25 absent ; exécuter scripts/bootstrap.ps1.")
    return candidates[0]


def start(root: Path, memory: int, public: bool, port: int, auto_backup: bool):
    if not 2 <= memory <= 12 or not 1024 <= port <= 65535:
        raise ValueError("Mémoire 2..12 Go et port 1024..65535 requis.")
    with maintenance(root, check_worlds=False):
        validate(root)
        # Conserver le verrou parent pendant toute la vie du processus enfant.
        command = [str(java_path()), "-Xms2G", f"-Xmx{memory}G", "-jar", "paper.jar", "--nogui",
                   "--host", "0.0.0.0" if public else "127.0.0.1", "--port", str(port)]
        process = subprocess.Popen(command, cwd=root)
        try:
            result = process.wait()
        except KeyboardInterrupt:
            # SIGINT est également transmis à Java dans cette console Windows.
            print("Attente de l'arrêt propre de Java ; ne pas fermer la fenêtre.")
            result = process.wait()
        if result:
            raise RuntimeError(f"Paper s'est arrêté avec le code {result}. Consulter logs/latest.log.")
        if auto_backup:
            # L'arrêt a fermé les mondes et terminé les écritures natives/plugins.
            with ExitStack() as stack:
                for lock in root.rglob("session.lock"):
                    stack.enter_context(file_lock(lock, create=False))
                backup_locked(root)


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Lien symbolique non pris en charge : {path}")
        if path.is_file() and path.name not in (".control.lock", "session.lock"):
            yield path


def create_archive(root: Path, output: Path, excluded_roots: tuple[Path, ...] = ()):
    if output.exists():
        raise RuntimeError("L'archive cible existe déjà.")
    # Les sauvegardes portables peuvent résider dans un dossier réservé du serveur.
    # Elles ne doivent jamais embarquer les sauvegardes précédentes.
    excluded = tuple(path.resolve() for path in excluded_roots)
    files = [path for path in iter_files(root)
             if path.relative_to(root).as_posix() != "BACKUP_MANIFEST.json"
             and not any(path.resolve().is_relative_to(folder) for folder in excluded)]
    manifest = {str(path.relative_to(root)).replace("\\", "/"): digest(path) for path in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".zip.part")
    with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
        archive.writestr("BACKUP_MANIFEST.json", json.dumps({"schema": 1, "files": manifest}, indent=2))
    # Relire les données avant de publier une sauvegarde comme utilisable.
    verify_archive(temporary)
    temporary.replace(output)
    output.with_suffix(".zip.sha256").write_text(digest(output) + "\n", encoding="ascii")


def verify_archive(path: Path):
    with zipfile.ZipFile(path) as archive:
        seen = set()
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            parts = name.split("/")
            if (name.startswith("/") or ":" in name or ".." in parts or name.casefold() in {n.casefold() for n in seen}
                    or any(part.endswith((" ", ".")) for part in parts) or "" in parts):
                raise ValueError("Archive avec chemin dangereux ou dupliqué.")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Liens symboliques interdits dans une archive.")
            seen.add(name)
        manifest = json.loads(archive.read("BACKUP_MANIFEST.json"))
        if manifest.get("schema") != 1 or set(manifest["files"]) != seen - {"BACKUP_MANIFEST.json"}:
            raise ValueError("Manifeste incomplet ou incompatible.")
        for name, expected in manifest["files"].items():
            hasher = hashlib.sha256()
            with archive.open(name) as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    hasher.update(block)
            if hasher.hexdigest() != expected:
                raise ValueError(f"Archive altérée : {name}")
    return manifest


def backup_locked(root: Path, destination: Path | None = None) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = destination or ROOT / "backups" / root.name / f"fk-{timestamp}.zip"
    create_archive(root, destination)
    print(f"Sauvegarde cohérente vérifiée : {destination}")
    return destination


def backup(root: Path):
    with maintenance(root):
        if not (root / ".fk-managed").is_file():
            raise RuntimeError("Serveur géré absent.")
        return backup_locked(root)


def restore(root: Path, archive: Path):
    archive = archive.resolve()
    if root.exists() and any(root.iterdir()):
        raise RuntimeError("Restaurer dans un nouveau nom de serveur vide ; l'original est conservé.")
    verify_archive(archive)
    with maintenance(root):
        with zipfile.ZipFile(archive) as source:
            for item in source.infolist():
                if item.filename == "BACKUP_MANIFEST.json":
                    continue
                target = confined(root / item.filename, root)
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source.open(item) as src, target.open("xb") as dst:
                        shutil.copyfileobj(src, dst)
    print(f"Restauration terminée : {root}. État d'origine conservé ; isoler le réseau avant vérification.")


def import_world(root: Path, source: Path):
    source = source.resolve()
    if not (source / "level.dat").is_file():
        raise RuntimeError("Le dossier source doit contenir level.dat. Ne pas importer de monde ouvert dans Minecraft.")
    if root.is_relative_to(source) or source.is_relative_to(root):
        raise RuntimeError("La carte source doit être séparée du serveur cible.")
    with maintenance(root), ExitStack() as stack:
        if (root / "world").exists() or (root / "plugins/FKAmis/state.yml").exists():
            raise RuntimeError("Importer uniquement avant le premier démarrage dans une installation neuve.")
        for lock in source.rglob("session.lock"):
            stack.enter_context(file_lock(lock, create=False))
        list(iter_files(source))  # Refuser les liens avant copie.
        shutil.copytree(source, root / "world", ignore=shutil.ignore_patterns("session.lock", ".control.lock"))
    print("Carte copiée. Ne pas changer de version ; inspecter les terrains et dimensions au premier démarrage.")


def export(root: Path):
    with maintenance(root):
        validate(root)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = ROOT / "dist" / f"fallenkingdom-{root.name}-{timestamp}.zip"
        backup_locked(root, destination)
    print("Archive PRIVÉE pour SFTP. Contient mondes, whitelist, objectifs et EULA ; ne pas publier.")


def update_plugin(root: Path):
    if not PLUGIN.is_file():
        raise RuntimeError("Compiler le complément avant la mise à jour.")
    with maintenance(root):
        validate(root)
        backup_locked(root)
        destination = root / "plugins/FKAmis-1.0.0.jar"
        temporary = destination.with_suffix(".jar.new")
        shutil.copy2(PLUGIN, temporary)
        temporary.replace(destination)
        (root / "FKAmis.sha256").write_text(digest(PLUGIN) + "\n", encoding="ascii")
    print("Complément mis à jour après sauvegarde ; configurations et progression conservées.")


def check_logs(root: Path):
    log = root / "logs/latest.log"
    data = log.read_text(encoding="utf-8", errors="replace")
    failures = [line for line in data.splitlines() if re.search(r"\b(ERROR|SEVERE)\b|Could not load|Error occurred", line)]
    if failures:
        print("\n".join(failures))
        raise RuntimeError("Erreurs détectées dans les journaux.")
    for expected in ["Done (", "FKAmis prêt", "Enabling FallenKingdom"]:
        if expected not in data:
            raise RuntimeError(f"Preuve de démarrage absente : {expected}")
    print("Démarrage des deux plugins confirmé ; aucune ERROR/SEVERE détectée. Vérifier aussi les WARN.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "accept-eula", "validate", "start", "backup", "restore", "import-world", "export", "update-plugin", "check-logs"])
    parser.add_argument("--name", default="local")
    parser.add_argument("--accept", action="store_true", help="Acceptation explicite de l'EULA par l'utilisateur")
    parser.add_argument("--memory", type=int, default=4)
    parser.add_argument("--port", type=int, default=25565)
    parser.add_argument("--public", action="store_true", help="Écoute réseau, whitelist et authentification restent obligatoires")
    parser.add_argument("--no-auto-backup", action="store_true")
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    root = server_dir(args.name)
    if args.action == "install": install(root)
    elif args.action == "accept-eula": accept_eula(root, args.accept)
    elif args.action == "validate": validate(root)
    elif args.action == "start": start(root, args.memory, args.public, args.port, not args.no_auto_backup)
    elif args.action == "backup": backup(root)
    elif args.action == "restore":
        if args.source is None: parser.error("restore exige --source <archive.zip>")
        restore(root, args.source)
    elif args.action == "import-world":
        if args.source is None: parser.error("import-world exige --source <dossier-monde>")
        import_world(root, args.source)
    elif args.action == "export": export(root)
    elif args.action == "update-plugin": update_plugin(root)
    elif args.action == "check-logs": check_logs(root)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        sys.exit(1)
