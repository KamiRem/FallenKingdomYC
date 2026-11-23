import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from minestrator_v22_backup import active_hashes,preconditions,deep_checks,Unsafe

class Guard:
    def check(self):pass

class CurrentBackupTests(unittest.TestCase):
    def test_technical_files_only_excluded_from_active_comparison_not_full_backup(self):
        files={'paper.jar':'a','.fk-quarantine/old/world/level.dat':'b','.fk-stage/old/a':'c','world/.fk-quarantine/a':'d'}
        self.assertEqual(active_hashes(files),{'paper.jar':'a','world/.fk-quarantine/a':'d'})
        self.assertEqual(len(files),4)

    def test_fresh_audit_difference_blocks_before_destination_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'fresh';b=root/'old';a.mkdir();b.mkdir()
            (a/'fingerprint-private.json').write_text(json.dumps({'passed':True,'apiGameState':'offline','doubleReadHashes':{'file':'new'}}))
            (b/'fingerprint-private.json').write_text(json.dumps({'doubleReadHashes':{'file':'old'}}))
            with patch('minestrator_v22_backup.FRESH',a),patch('minestrator_v22_backup.PREVIOUS',b):
                with self.assertRaisesRegex(Unsafe,'FreshAuditDiverges'):preconditions()

    def test_corrupt_region_in_quarantine_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);f=root/'.fk-quarantine/old/world/region/r.0.0.mca';f.parent.mkdir(parents=True);f.write_bytes(b'broken')
            with self.assertRaises(ValueError):deep_checks(root,Guard())

    def test_empty_technical_region_is_decoded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);f=root/'.fk-quarantine/old/world/region/r.0.0.mca';f.parent.mkdir(parents=True);f.write_bytes(bytes(8192))
            self.assertEqual(deep_checks(root,Guard())['technicalRegionFilesDecoded'],1)

if __name__=='__main__':unittest.main()
