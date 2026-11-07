"""Garde-fous du paquet portable, sans Java ni monde réel."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import server
import preproduction

sys.modules['serverlib'] = server
spec = importlib.util.spec_from_file_location('host_ops', ROOT / 'deployment/host_ops.py')
host_ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host_ops)


class PortableTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT / '.cache/test-temp'
        folder.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=folder)
        server.confined(Path(self.tmp.name), folder)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'instance'
        self.root.mkdir()

    def test_backup_does_not_embed_previous_backups(self):
        (self.root / 'world').mkdir()
        (self.root / 'world/level.dat').write_bytes(b'world')
        saved = self.root / '.fk-backups'
        saved.mkdir()
        (saved / 'old.zip').write_bytes(b'old backup')
        # Une extraction par le panel peut conserver le manifeste du ZIP initial.
        (self.root / 'BACKUP_MANIFEST.json').write_text('{"old": true}')
        target = saved / 'new.zip'
        server.create_archive(self.root, target, excluded_roots=(saved,))
        manifest = server.verify_archive(target)
        self.assertEqual(set(manifest['files']), {'world/level.dat'})
        restored = self.root.parent / 'restored'
        with patch.object(host_ops, 'ROOT', self.root):
            host_ops.restore(target, restored)
        self.assertEqual((restored / 'world/level.dat').read_bytes(), b'world')
        with patch.object(host_ops, 'ROOT', self.root):
            with self.assertRaises(RuntimeError): host_ops.restore(target, restored)

    def test_external_digest_required_and_tampering_rejected(self):
        (self.root / 'file').write_bytes(b'fixture')
        target = self.root.parent / 'backup.zip'
        server.create_archive(self.root, target)
        target.with_suffix('.zip.sha256').write_text('0' * 64)
        with self.assertRaisesRegex(RuntimeError, 'externe'):
            host_ops.restore(target, self.root.parent / 'new')

    def test_initial_manifest_detects_changed_and_missing_files(self):
        data = self.root / 'file'
        data.write_bytes(b'initial')
        (self.root / 'DEPLOYMENT_MANIFEST.json').write_text(json.dumps({'files': {'file': server.digest(data)}}))
        host_ops.verify(self.root)
        data.write_bytes(b'changed')
        with self.assertRaises(RuntimeError): host_ops.verify(self.root)
        data.unlink()
        with self.assertRaises(RuntimeError): host_ops.verify(self.root)

    def test_profile_filter_keeps_world_regions_and_plugin_state(self):
        for name in ('world/players/data/account.dat', 'world/playerdata/account.dat',
                     'ops.json', '.paper/console_history', 'logs/latest.log', 'usercache.json'):
            self.assertIsNotNone(preproduction.excluded(name))
        for name in ('world/dimensions/minecraft/the_nether/region/r.0.0.mca',
                     'plugins/FKAmis/state.yml', 'plugins/FKAmis/supplies.yml', 'world/level.dat'):
            self.assertIsNone(preproduction.excluded(name))


if __name__ == '__main__': unittest.main()
