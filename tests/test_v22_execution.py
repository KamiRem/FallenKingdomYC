import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_minestrator_deploy import Sftp,Monitor
import minestrator_v22_execute as d

class V22ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.scope=patch.object(d,'WORK',self.root);self.scope.start();self.addCleanup(self.scope.stop)
        self.client=Sftp();self.tx=d.Transaction(self.client,Monitor(),{})
        self.source=self.root/'payload';self.source.write_bytes(b'new');self.h=hashlib.sha256(b'new').hexdigest()

    def test_exclusive_upload_and_promotion(self):
        self.tx.upload(self.source,'stage/new',self.h,0o644,1,1)
        self.tx.move('stage/new','active',self.h)
        self.assertEqual(self.client.files['active'],b'new')
        self.assertIn(('stage/new','wx'),self.client.opened)

    def test_existing_target_never_overwritten(self):
        self.client.files['active']=b'old'
        with self.assertRaisesRegex(d.Unsafe,'DestinationAlreadyExists'):self.tx.upload(self.source,'active',self.h,0o644,1,1)
        self.assertEqual(self.client.files['active'],b'old');self.assertEqual(self.client.opened,[])

    def test_wrong_owner_blocks_before_promotion(self):
        with self.assertRaisesRegex(d.Unsafe,'OwnershipMismatch'):self.tx.upload(self.source,'stage/new',self.h,0o644,99,1)
        self.assertEqual(self.client.renamed,[])

    def test_local_hash_change_is_rejected(self):
        with self.assertRaisesRegex(d.Unsafe,'LocalPayloadChanged'):self.tx.upload(self.source,'new','0'*64,0o644,1,1)
        self.assertEqual(self.client.opened,[])

    def test_foreign_command_never_reaches_api(self):
        api=d.ExecutionApi('FAKE',513365)
        for command in ('fka start','fka nextday','whitelist add fake','fka nether portal activate','minecraft:fill 0 0 0 1 1 1 air'):
            with self.assertRaisesRegex(d.Unsafe,'ApiMutationForbidden'):api.put('/command',{'command':command})

    def test_start_is_not_repeatable(self):
        self.tx.report.update({'installationOfflineVerified':True,'startRequested':True})
        with self.assertRaisesRegex(d.Unsafe,'SingleStartPreconditionFailed'):d.startup(self.tx,Mock(),{})

    def test_rollback_is_restricted_to_failed_activation(self):
        with self.assertRaisesRegex(d.Unsafe,'RollbackScopeNotSatisfied'):d.rollback(self.tx,Mock(),{}, {})
        self.tx.report['activationStarted']=True
        with self.assertRaisesRegex(d.Unsafe,'RollbackScopeNotSatisfied'):d.rollback(self.tx,Mock(),{}, {})

    def test_status_protocol_signed_varint(self):
        self.assertEqual(d.varint(-1),b'\xff\xff\xff\xff\x0f')
        self.assertEqual(d.varint(0),b'\0');self.assertEqual(d.varint(128),b'\x80\x01')

    def test_parent_escape_refused(self):
        for p in ('../escape','/absolute'):
            with self.assertRaisesRegex(d.Unsafe,'UnsafeRemotePath'):self.tx.mkdirs(p)

    def test_old_success_log_cannot_validate_new_start(self):
        old='[00:01:00] Running Java 25';text=old+'\nFKAmis prêt\nDone (2s)\n'
        self.assertEqual(d.fresh_boot_section(text,old),'')

    def test_only_new_boot_section_counts_as_startup_evidence(self):
        old='[00:01:00] Running Java 25';new='[17:00:00] Running Java 25'
        text=old+'\nFKAmis prêt\nDone (2s)\n'+new+'\nPreparing world\n'
        self.assertNotIn('Done (',d.fresh_boot_section(text,old))
        self.assertIn('Done (',d.fresh_boot_section(text+'FKAmis prêt\nDone (3s)\n',old))

    def test_runtime_world_checks_against_full_current_candidate(self):
        work=Path.home()/'FKBackups/MS-DEPLOY-V22-20261123-01';candidate=work/'candidate'
        if not candidate.exists():self.skipTest('copie actuelle complète absente')
        class LocalSftp:
            def lstat(self,name):return (candidate/name).stat()
            def open(self,name,mode):
                if mode!='rb':raise AssertionError('lecture seule')
                return (candidate/name).open('rb')
        with patch.object(d,'WORK',work):
            tx=d.Transaction(LocalSftp(),Monitor(),{})
            result=d.runtime_world(tx)
        self.assertEqual(result['uniqueNaturalTerrainBlocksChecked'],37159)
        self.assertEqual(result['spawnsVerified'],4);self.assertEqual(result['shaftHeightmapFieldsVerified'],4)
        self.assertFalse(result['gameStarted'])

if __name__=='__main__':unittest.main()
