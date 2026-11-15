"""Garde-fous SFTP sans réseau et sans identifiants réels."""
import io
import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import minestrator_sftp_inventory as inventory

class Key:
    def asbytes(self):return b'FAKE-KEY'
class Handle(io.BytesIO):
    def stat(self):return types.SimpleNamespace(st_size=3,st_mtime=1)
class ReadOnlyClient:
    def listdir_attr(self,path):return [types.SimpleNamespace(filename='server.properties',st_mode=stat.S_IFREG|0o600,st_size=3,st_mtime=1)]
    def open(self,path,mode):
        if mode!='rb':raise AssertionError('Écriture interdite')
        return Handle(b'abc')
    def lstat(self,path):return types.SimpleNamespace(st_size=3,st_mtime=1)

class InventoryTests(unittest.TestCase):
    def test_pin(self):
        self.assertTrue(inventory.pin_matches(Key(),inventory.fingerprint(Key())))
        self.assertFalse(inventory.pin_matches(Key(),'SHA256:'+'A'*43))
    def test_hash_from_reads(self):
        self.assertEqual(inventory.inventory(ReadOnlyClient())['files'][0]['sha256'],hashlib.sha256(b'abc').hexdigest())
    def test_invalid_name(self):
        client=ReadOnlyClient();client.listdir_attr=lambda _: [types.SimpleNamespace(filename='../secret')]
        with self.assertRaisesRegex(RuntimeError,'UnsafeRemoteName'):inventory.inventory(client)
    def test_links(self):
        client=ReadOnlyClient();client.listdir_attr=lambda _: [types.SimpleNamespace(filename='link',st_mode=stat.S_IFLNK)]
        self.assertFalse(inventory.inventory(client)['complete'])
    def test_changed_file(self):
        client=ReadOnlyClient();client.lstat=lambda _:types.SimpleNamespace(st_size=4,st_mtime=1)
        with self.assertRaisesRegex(RuntimeError,'RemoteFileChanged'):inventory.inventory(client)
    def test_no_password_before_pin(self):
        calls=[]
        class Transport:
            def __init__(self,_):pass
            def start_client(self,**kwargs):pass
            def get_remote_server_key(self):return Key()
            def auth_password(self,*args,**kwargs):calls.append('password')
            def close(self):pass
        with tempfile.TemporaryDirectory() as folder:
            config={'output':str(Path(folder)/'not-created.json'),'host':'example.invalid','port':2022,'user':'dummy','password':'FAKE-PASSWORD','fingerprint':'SHA256:'+'A'*43}
            with patch.dict(sys.modules,{'paramiko':types.SimpleNamespace(Transport=Transport)}),patch.object(sys,'stdin',io.StringIO(json.dumps(config))),patch.object(inventory.socket,'create_connection',return_value=object()):
                with self.assertRaisesRegex(RuntimeError,'HostKeyMismatch'):inventory.main()
            self.assertFalse(Path(config['output']).exists())
        self.assertEqual(calls,[])
