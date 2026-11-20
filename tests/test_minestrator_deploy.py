"""Garanties de déploiement : faux SFTP local, aucun accès réseau ni secret."""
import hashlib
import io
from pathlib import Path
import stat
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import minestrator_deploy as d

class Monitor:
    def check(self):pass

class File(io.BytesIO):
    def __init__(self,client,path,writing):
        self.client=client;self.path=path;self.writing=writing
        super().__init__(client.files[path])
    def flush(self):
        if self.writing:self.client.files[self.path]=self.getvalue()
    def close(self):self.flush();super().close()
    def stat(self):return self.client.lstat(self.path)

class Sftp:
    def __init__(self):self.files={};self.dirs={'.'};self.modes={};self.renamed=[];self.opened=[]
    def lstat(self,path):
        if path not in self.files and path not in self.dirs:raise FileNotFoundError(path)
        return types.SimpleNamespace(st_size=len(self.files.get(path,b'')),st_mtime=1,
            st_mode=(stat.S_IFDIR if path in self.dirs else stat.S_IFREG)|self.modes.get(path,0o644),st_uid=1,st_gid=1)
    def mkdir(self,path,mode):
        if path in self.files or path in self.dirs:raise FileExistsError(path)
        self.dirs.add(path);self.modes[path]=mode
    def open(self,path,mode):
        self.opened.append((path,mode))
        if mode=='wx':
            if path in self.files or path in self.dirs:raise FileExistsError(path)
            self.files[path]=b''
        elif mode!='rb':raise AssertionError('ouverture non autorisée')
        return File(self,path,mode=='wx')
    def chmod(self,path,mode):self.modes[path]=mode
    def rename(self,source,target):
        if target in self.files or target in self.dirs:raise FileExistsError(target)
        self.files[target]=self.files.pop(source);self.modes[target]=self.modes.pop(source,0o644)
        self.renamed.append((source,target))

class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.work=Path(self.folder.name);self.client=Sftp();self.tx=d.Transaction(self.client,Monitor(),self.work,{})
        self.payload=self.work/'payload';self.payload.write_bytes(b'candidate')
        self.sha=hashlib.sha256(b'candidate').hexdigest()
    def test_root_promotion_and_verified_upload(self):
        self.tx.upload(self.payload,'staging/item',self.sha)
        self.tx.move('staging/item','item',self.sha)
        self.assertEqual(self.client.files,{'item':b'candidate'})
        self.assertIn(('staging/item','wx'),self.client.opened)
        self.assertEqual(self.tx.report['remoteWritesPerformed'],True)
    def test_existing_upload_is_never_truncated(self):
        self.client.files['item']=b'historical'
        with self.assertRaisesRegex(d.Unsafe,'DestinationAlreadyExists'):self.tx.upload(self.payload,'item',self.sha)
        self.assertEqual(self.client.files['item'],b'historical');self.assertEqual(self.client.opened,[])
    def test_rename_refuses_existing_destination(self):
        self.client.files.update({'old':b'original','target':b'preserve'})
        with self.assertRaisesRegex(d.Unsafe,'DestinationAlreadyExists'):self.tx.move('old','target')
        self.assertEqual(self.client.renamed,[]);self.assertEqual(len(self.client.files),2)
    def test_local_hash_mismatch_prevents_upload(self):
        with self.assertRaisesRegex(d.Unsafe,'LocalPayloadChanged'):self.tx.upload(self.payload,'item','0'*64)
        self.assertEqual(self.client.opened,[])
    def test_remote_content_mismatch_stops_promotion(self):
        self.client.files['old']=b'concurrent change'
        with self.assertRaisesRegex(d.Unsafe,'RemoteHashChanged'):self.tx.move('old','target',self.sha)
        self.assertEqual(self.client.renamed,[])
    def test_unsafe_path_rejected_before_write(self):
        for path in ('../outside','/absolute'):
            with self.subTest(path=path),self.assertRaises(d.Unsafe):self.tx.mkdirs(path)
        self.assertEqual(self.client.dirs,{'.'})
    def test_monitor_failure_aborts_copy_without_promotion(self):
        class FailingMonitor:
            def __init__(self):self.calls=0
            def check(self):
                self.calls+=1
                if self.calls>=3:raise d.Unsafe('ServerNotOffline')
        self.tx.guard=FailingMonitor()
        with self.assertRaisesRegex(d.Unsafe,'ServerNotOffline'):self.tx.upload(self.payload,'item',self.sha)
        self.assertEqual(self.client.renamed,[])
        self.assertNotIn('upload_verified',(self.work/'journal.jsonl').read_text())
    def test_api_rejects_game_start_and_other_mutations(self):
        api=d.DeployApi('fake',513365)
        for suffix,body in [('/command',{'command':'fka start'}),('/poweraction',{'poweraction':'restart'}),('/settings',{})]:
            with self.subTest(suffix=suffix),patch('urllib.request.build_opener') as opener,self.assertRaisesRegex(d.Unsafe,'ApiMutationNotAllowed'):
                api.put(suffix,body)
            opener.assert_not_called()
    def test_online_monitor_aborts_on_unexpected_stop(self):
        api=types.SimpleNamespace(get=lambda _: {'state':'offline','stats':{'state':'offline'}})
        guard=d.OnlineGuard(api);abort=[];guard.abort=lambda:abort.append(True)
        with self.assertRaisesRegex(d.Unsafe,'UnexpectedRuntimeState'):guard.start()
        self.assertTrue(guard.failed.is_set());self.assertEqual(abort,[True])
    def test_online_monitor_retains_observation_gap_control(self):
        guard=d.OnlineGuard(None);guard.last=time.monotonic()-20
        with self.assertRaisesRegex(d.Unsafe,'ObservationGapExceeded'):guard.check()
    def test_successful_installation_cannot_be_rolled_back_implicitly(self):
        self.tx.report.update({'activationStarted':True,'state':'RUNNING_RECIPE_ONLY'})
        with self.assertRaisesRegex(d.Unsafe,'RollbackRequiresCriticalDeploymentFailure'):d.rollback(self.tx,None,{})
    def test_candidate_world_validation_with_local_sftp(self):
        class LocalSftp:
            def lstat(self,path):return (d.CANDIDATE/'preproduction-candidate'/path).stat()
            def open(self,path,mode):
                if mode!='rb':raise AssertionError('lecture seulement')
                return (d.CANDIDATE/'preproduction-candidate'/path).open('rb')
        if not d.CANDIDATE.exists():self.skipTest('candidat privé absent')
        result=d.world_checks(LocalSftp(),Monitor())
        self.assertEqual(result['cavernsVerified'],4);self.assertEqual(result['spawnsVerified'],4)
        self.assertFalse(result['gameStarted']);self.assertEqual(result['cavernReferenceBlocksVerified'],37128)
    def test_prestart_rejects_unplanned_active_files(self):
        baseline={'files':{'keep':{'pathStatBaseline':d.metadata(self.client.lstat('.'))}}}
        operation={'quarantineWholeTrees':[],'quarantineIndividualFiles':[]}
        with patch.object(d,'remote_files',return_value={'keep':{},'spigot.yml':{},'unexpected':{}}):
            with self.assertRaisesRegex(d.Unsafe,'ActiveInstanceFileSetChanged'):
                d.verify_preserved_metadata(self.tx,baseline,{'files':[]},operation)
    def test_prestart_detects_change_to_retained_configuration(self):
        self.client.files['keep']=b'changed'
        saved=d.metadata(self.client.lstat('keep'));saved['mtime']=0;saved['_sftp']['attributes']['mtime']['value']=0
        baseline={'files':{'keep':{'pathStatBaseline':saved}}}
        operation={'quarantineWholeTrees':[],'quarantineIndividualFiles':[]}
        with patch.object(d,'remote_files',return_value={'keep':{},'spigot.yml':{}}):
            with self.assertRaisesRegex(d.Unsafe,'ConcurrentFileChange'):
                d.verify_preserved_metadata(self.tx,baseline,{'files':[]},operation)

if __name__=='__main__':unittest.main()
