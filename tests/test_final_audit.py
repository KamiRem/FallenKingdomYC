"""Audit borné en lecture : divergence => aucune lecture du fichier suivant."""
from pathlib import Path
import copy
import hashlib
import io
import stat
import sys
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import minestrator_final_audit as audit
from minestrator_cold_backup import metadata,Unsafe

class Guard:
    def check(self):pass
def attrs():return types.SimpleNamespace(st_size=3,st_mtime=1,st_mode=stat.S_IFREG|0o600,st_uid=1,st_gid=1)
class Handle(io.BytesIO):
    def stat(self):return attrs()
class Client:
    def __init__(self):self.reads=[]
    def lstat(self,name):return attrs()
    def open(self,name,mode):
        assert mode=='rb';self.reads.append(name);return Handle(b'abc')

class AuditTests(unittest.TestCase):
    def baseline(self):
        a=metadata(attrs());a['sha256']=hashlib.sha256(b'abc').hexdigest();a['pathStatBaseline']=metadata(attrs())
        return {'files':{'a':copy.deepcopy(a),'b':copy.deepcopy(a)},'directories':{}}
    def test_both_reads_are_verified_against_backup(self):
        baseline=self.baseline();client=Client();report={}
        with patch.object(audit,'snapshot',return_value=baseline):audit.audit_hashes(client,baseline,Guard(),lambda v:None,report)
        self.assertEqual(['a','b','a','b'],client.reads);self.assertEqual([2,2],report['filesHashedPerPass'])
        self.assertTrue(report['allSourceHashesMatchBackupTwice'])
    def test_first_content_divergence_stops_before_next_file(self):
        baseline=self.baseline();baseline['files']['a']['sha256']='0'*64;client=Client();report={}
        with patch.object(audit,'snapshot',return_value=baseline),self.assertRaisesRegex(Unsafe,'RemoteHashChanged'):
            audit.audit_hashes(client,baseline,Guard(),lambda v:None,report)
        self.assertEqual(['a'],client.reads);self.assertEqual([0,0],report['filesHashedPerPass'])
    def test_tree_divergence_prevents_all_content_reads(self):
        baseline=self.baseline();changed=copy.deepcopy(baseline);changed['files']['new']=metadata(attrs());client=Client()
        with patch.object(audit,'snapshot',return_value=changed),self.assertRaisesRegex(Unsafe,'RemoteTreeChanged'):
            audit.audit_hashes(client,baseline,Guard(),lambda v:None,{})
        self.assertEqual([],client.reads)

if __name__=='__main__':unittest.main()
