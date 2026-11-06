"""Tests des sauvegardes et garde-fous, sans démarrer Minecraft."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/server.py"
spec = importlib.util.spec_from_file_location("fkserver", SCRIPT)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        temporary_root = server.ROOT / ".cache/test-temp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        server.confined(Path(self.temp.name), temporary_root)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.source = self.path / "original"
        (self.source / "world/playerdata").mkdir(parents=True)
        (self.source / "plugins/FKAmis").mkdir(parents=True)
        (self.source / "world/level.dat").write_bytes(b"world-fixture")
        (self.source / "world/playerdata/player.dat").write_bytes(b"inventory-fixture")
        (self.source / "plugins/FKAmis/state.yml").write_text("day: 3\n", encoding="utf-8")
        (self.source / ".fk-managed").write_text("FallenKingdomYC", encoding="utf-8")

    def test_backup_restores_world_plugin_and_inventory_byte_for_byte(self):
        archive = self.path / "backup.zip"
        server.create_archive(self.source, archive)
        target = self.path / "restored"
        server.restore(target, archive)
        for original in server.iter_files(self.source):
            self.assertEqual(original.read_bytes(), (target / original.relative_to(self.source)).read_bytes())
        self.assertTrue(archive.with_suffix(".zip.sha256").is_file())

    def test_archive_tampering_is_detected(self):
        archive = self.path / "altered.zip"
        server.create_archive(self.source, archive)
        with zipfile.ZipFile(archive, "r") as original:
            files = {name: original.read(name) for name in original.namelist()}
        files["world/level.dat"] = b"tampered"
        with zipfile.ZipFile(archive, "w") as output:
            for name, value in files.items(): output.writestr(name, value)
        with self.assertRaisesRegex(ValueError, "altérée"):
            server.verify_archive(archive)

    def test_zip_slip_is_rejected_before_extraction(self):
        archive = self.path / "unsafe.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("../escape", "bad")
            output.writestr("BACKUP_MANIFEST.json", json.dumps({"schema": 1, "files": {}}))
        with self.assertRaises(ValueError): server.verify_archive(archive)
        self.assertFalse((self.path.parent / "escape").exists())

    def test_symlink_in_archive_is_rejected(self):
        archive = self.path / "symlink.zip"
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr(info, "/etc/passwd")
        with self.assertRaisesRegex(ValueError, "symboliques"): server.verify_archive(archive)

    def test_restore_refuses_existing_data(self):
        with self.assertRaisesRegex(RuntimeError, "nouveau nom"): server.restore(self.source, self.path / "absent.zip")
        self.assertEqual(b"world-fixture", (self.source / "world/level.dat").read_bytes())

    def test_control_lock_excludes_other_processes(self):
        code = (
            "import importlib.util,sys; from pathlib import Path; "
            "spec=importlib.util.spec_from_file_location('server',sys.argv[1]); "
            "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
            "context=m.maintenance(Path(sys.argv[2])); context.__enter__(); "
            "print('locked',flush=True); sys.stdin.readline(); context.__exit__(None,None,None)"
        )
        process = subprocess.Popen([sys.executable, "-c", code, str(SCRIPT), str(self.source)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual("locked", process.stdout.readline().strip())
            with self.assertRaises(RuntimeError):
                with server.maintenance(self.source): self.fail("Le verrou n'a pas été respecté.")
        finally:
            process.communicate("release\n", timeout=10)
        with server.maintenance(self.source): pass

    def test_minecraft_session_lock_is_checked_even_without_control_wrapper(self):
        lock = self.source / "world/session.lock"
        lock.write_bytes(b"snowman")
        with server.file_lock(lock):
            with self.assertRaises(RuntimeError):
                with server.maintenance(self.source): self.fail("Le monde ouvert devrait bloquer la copie.")

    def test_server_name_and_path_traversal_refused(self):
        for name in ("../prod", "C:/prod", "a/b", "..", "", "local;stop"):
            with self.assertRaises(ValueError): server.server_dir(name)
        with self.assertRaises(ValueError): server.confined(self.path / "../escape", self.path)

    def test_eula_requires_explicit_flag(self):
        with self.assertRaisesRegex(RuntimeError, "explicitement"): server.accept_eula(self.source, False)
        self.assertFalse((self.source / "eula.txt").exists())
        server.accept_eula(self.source, True)
        self.assertEqual("true", server.properties(self.source / "eula.txt")["eula"])

    def test_manifest_requires_every_file(self):
        archive = self.path / "untracked.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("surprise.jar", b"bad")
            output.writestr("BACKUP_MANIFEST.json", json.dumps({"schema": 1, "files": {}}))
        with self.assertRaisesRegex(ValueError, "incomplet"): server.verify_archive(archive)

    def test_windows_case_collision_is_rejected(self):
        archive = self.path / "case-collision.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("world/data.dat", b"a")
            output.writestr("WORLD/data.dat", b"b")
        with self.assertRaisesRegex(ValueError, "dangereux"): server.verify_archive(archive)

    def test_windows_alternate_stream_is_rejected(self):
        archive = self.path / "ads.zip"
        with zipfile.ZipFile(archive, "w") as output: output.writestr("world/data.dat:payload", b"bad")
        with self.assertRaisesRegex(ValueError, "dangereux"): server.verify_archive(archive)


if __name__ == "__main__": unittest.main()
