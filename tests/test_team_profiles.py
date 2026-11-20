"""Profils de capacité et protections de maintenance, sans réseau ni donnée historique."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import server
sys.modules['serverlib']=server
sys.path.insert(0,str(ROOT/'deployment'))
import host_ops
from vnext1_tests import run_probe


class ProbeLifecycle(unittest.TestCase):
    def test_probe_stops_cleanly_on_timeout_without_closed_stdin(self):
        command=[sys.executable,'-c',"import sys; value=sys.stdin.readline(); print('received='+value.strip(),flush=True)"]
        code,log,expired,forced=run_probe(command,ROOT,timeout=.2,stop_timeout=5)
        self.assertEqual(0,code);self.assertIn('received=stop',log)
        self.assertTrue(expired);self.assertFalse(forced)

    def test_successful_probe_exits_without_stop(self):
        code,log,expired,forced=run_probe([sys.executable,'-c',"print('fixture success')"],ROOT,timeout=5)
        self.assertEqual(0,code);self.assertIn('fixture success',log)
        self.assertFalse(expired);self.assertFalse(forced)


class CapacityProfiles(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.cache/test-temp');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'instance';(self.root/'plugins').mkdir(parents=True)
        for name in ('paper.jar','plugins/FallenKingdom-2.24.9.jar','plugins/FKAmis-1.0.0.jar'):
            with zipfile.ZipFile(self.root/name,'w') as z:z.writestr('fr/fkamis/FKAmis.class',b'fixture')
        lock={'artifacts':[{'name':name,'algorithm':'sha256','hash':server.digest(self.root/file)} for name,file in [('paper','paper.jar'),('fallenkingdom','plugins/FallenKingdom-2.24.9.jar')]]}
        (self.root/'artifacts.lock.json').write_text(json.dumps(lock))
        (self.root/'FKAmis.sha256').write_text(server.digest(self.root/'plugins/FKAmis-1.0.0.jar'))
        (self.root/'eula.txt').write_text('eula=true\n') # Fixture, aucun vrai serveur.

    def configure(self,capacity=20,query='false',whitelist='true'):
        text=f'max-players={capacity}\nonline-mode=true\nwhite-list={whitelist}\nenforce-whitelist=true\nenable-rcon=false\nenable-command-block=false\nenable-query={query}\npvp=true\ndifficulty=normal\n'
        (self.root/'server.properties').write_text(text)

    def test_historical_ten_and_new_twenty_pass_without_changing_config(self):
        for capacity in (10,20):
            self.configure(capacity);before=(self.root/'server.properties').read_bytes()
            host_ops.check(self.root)
            self.assertEqual(before,(self.root/'server.properties').read_bytes())

    def test_query_and_whitelist_guards_remain_enforced(self):
        self.configure(10,query='true')
        with self.assertRaisesRegex(RuntimeError,'enable-query'):host_ops.check(self.root)
        self.configure(20,whitelist='false')
        with self.assertRaisesRegex(RuntimeError,'white-list'):host_ops.check(self.root)

    def test_capacity_and_artifact_guards(self):
        for invalid in (4,21):
            self.configure(invalid)
            with self.assertRaises(RuntimeError):host_ops.check(self.root)
        self.configure();(self.root/'FKAmis.sha256').write_text('0'*64)
        with self.assertRaisesRegex(RuntimeError,'FKAmis'):host_ops.check(self.root)

    def test_both_profiles_roundtrip_with_state_and_inventory(self):
        for capacity in (10,20):
            self.configure(capacity)
            (self.root/'world/playerdata').mkdir(parents=True,exist_ok=True)
            (self.root/'world/playerdata/fixture.dat').write_bytes(b'inventory-preserved')
            (self.root/'state-fixture.yml').write_text('schema: 1\nplayers-per-team: 4\n')
            archive=self.root.parent/f'{capacity}.zip'
            with server.maintenance(self.root):server.create_archive(self.root,archive)
            restored=self.root.parent/f'restored-{capacity}';server.restore(restored,archive)
            self.assertEqual(str(capacity),server.properties(restored/'server.properties')['max-players'])
            self.assertEqual(b'inventory-preserved',(restored/'world/playerdata/fixture.dat').read_bytes())
            self.assertEqual((self.root/'state-fixture.yml').read_bytes(),(restored/'state-fixture.yml').read_bytes())
            host_ops.check(restored)

if __name__=='__main__':unittest.main()
