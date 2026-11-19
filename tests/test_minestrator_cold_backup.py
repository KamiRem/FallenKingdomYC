"""Tests de compensation sans réseau ni secret réel."""
from pathlib import Path
import hashlib
import io
import json
import stat
import sys
import tempfile
import time
import types
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import minestrator_cold_backup as backup

class GoodGuard:
    def check(self):pass
class Handle(io.BytesIO):
    def stat(self):return types.SimpleNamespace(st_size=3,st_mtime=1,st_mode=stat.S_IFREG|0o600,st_uid=1,st_gid=1)
class Client:
    def lstat(self,name):return Handle().stat()
    def open(self,name,mode):
        assert mode=='rb';return Handle(b'abc')

class BackupTests(unittest.TestCase):
    def test_path_rejection(self):
        for name in ('../x','a\\b','CON','LPT1.txt','x:ads','x.','x ',''):
            with self.subTest(name=name),self.assertRaises(backup.Unsafe):backup.safe_name(name)
    def test_regular_and_hidden_names(self):
        self.assertEqual(backup.safe_name('.ai-backups'),'.ai-backups')
        self.assertEqual(backup.safe_name('session.lock'),'session.lock')
    def test_download_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'file';sha=backup.read_remote(Client(),'file',backup.metadata(Handle().stat()),GoodGuard(),path)
            self.assertEqual(path.read_bytes(),b'abc');self.assertEqual(sha,hashlib.sha256(b'abc').hexdigest())
    def test_changed_metadata(self):
        expected=backup.metadata(Handle().stat());expected['mtime']=2
        with self.assertRaisesRegex(backup.Unsafe,'ConcurrentFileChange'):backup.read_remote(Client(),'file',expected,GoodGuard())
    def test_incorrect_size(self):
        c=Client();c.open=lambda *args:Handle(b'abcd')
        with self.assertRaisesRegex(backup.Unsafe,'ConcurrentFileChange'):backup.read_remote(c,'file',backup.metadata(Handle().stat()),GoodGuard())
    def test_existing_target_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'file';path.write_bytes(b'original')
            with self.assertRaises(FileExistsError):backup.read_remote(Client(),'file',backup.metadata(Handle().stat()),GoodGuard(),path)
            self.assertEqual(path.read_bytes(),b'original')
    def test_monitor_rejects_restart(self):
        class Api:
            def offline(self):raise backup.Unsafe('ServerNotOffline')
        guard=backup.Guard(Api());closed=[];guard.abort=lambda:closed.append(True)
        with self.assertRaisesRegex(backup.Unsafe,'ServerNotOffline'):guard.start()
        self.assertTrue(guard.failed.is_set());self.assertEqual(closed,[True])
    def test_monitor_rejects_api_failure(self):
        class Api:
            def offline(self):raise TimeoutError()
        guard=backup.Guard(Api())
        with self.assertRaisesRegex(backup.Unsafe,'ApiObservationFailed'):guard.poll()
    def test_monitor_gap(self):
        guard=backup.Guard(None);guard.last=time.monotonic()-20
        with self.assertRaisesRegex(backup.Unsafe,'ObservationGapExceeded'):guard.check()
    def test_hidden_and_existing_manifest_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'download.partial/empty').mkdir(parents=True)
            files={}
            for name,value in [('BACKUP_MANIFEST.json',b'{"legacy":true}'),('.hidden',b'original'),('session.lock',b'lock')]:
                (root/'download.partial'/name).write_bytes(value);files[name]={'mode':0o600,'sha256':hashlib.sha256(value).hexdigest()}
            archive,restore=backup.archive_and_restore(root,{'files':files,'directories':{'empty':{'mode':0o700}}},GoodGuard())
            self.assertEqual((restore/'BACKUP_MANIFEST.json').read_bytes(),b'{"legacy":true}');self.assertTrue((restore/'empty').is_dir());self.assertTrue((restore/'session.lock').exists())
    def test_symlink_refusal(self):
        c=types.SimpleNamespace(listdir_attr=lambda p:[types.SimpleNamespace(filename='link',st_mode=stat.S_IFLNK)])
        with self.assertRaisesRegex(backup.Unsafe,'LinkOrSpecialFile'):backup.snapshot(c,GoodGuard())
    def test_windows_collision(self):
        def item(name):return types.SimpleNamespace(filename=name,st_mode=stat.S_IFREG|0o600,st_size=0,st_mtime=1)
        c=types.SimpleNamespace(listdir_attr=lambda p:[item('a'),item('A')])
        with self.assertRaisesRegex(backup.Unsafe,'WindowsPathCollision'):backup.snapshot(c,GoodGuard())
    def test_guard_thread_observes_later_restart(self):
        class Api:
            n=0
            def offline(self):
                self.n+=1
                if self.n>1:raise backup.Unsafe('ServerNotOffline')
                return {'state':'offline'}
        guard=backup.Guard(Api(),interval=.01);guard.start()
        try:self.assertTrue(guard.failed.wait(1))
        finally:guard.close()

if __name__=='__main__':unittest.main()
