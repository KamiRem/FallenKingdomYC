import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import server
sys.modules['serverlib']=server
spec=importlib.util.spec_from_file_location('new_match',ROOT/'deployment/new_match.py')
new_match=importlib.util.module_from_spec(spec);spec.loader.exec_module(new_match)


class NewMatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.cache/test-temp');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        folder=self.root/'plugins/FKAmis';folder.mkdir(parents=True)
        (folder/'state.yml').write_text('schema: 1\nday: 3\n')
        (folder/'reset-candidate.yml').write_text('schema: 1\nday: 0\n')
        (self.root/'plugins/FKAmis-1.0.0.jar').write_bytes(b'plugin');(self.root/'paper.jar').write_bytes(b'paper')
        self.data={'schema':1,'expiresAt':int(time.time()*1000)+300000,'tokenSha256':hashlib.sha256(b'token').hexdigest(),
            'sourceStateSha256':server.digest(folder/'state.yml'),'candidateSha256':server.digest(folder/'reset-candidate.yml'),
            'paperSha256':server.digest(self.root/'paper.jar'),'pluginSha256':server.digest(self.root/'plugins/FKAmis-1.0.0.jar'),
            'candidateFile':'plugins/FKAmis/reset-candidate.yml'}
        self.save()
    def save(self): (self.root/'plugins/FKAmis/reset-request.json').write_text(json.dumps(self.data),encoding='utf-8')
    def test_yaml_known_sections_are_read_without_parsing_unknown_data(self):
        text='schema: 1\nunknown: conserver\nnative:\n  TeamManager:\n    Rouge:\n      Members: []\n'
        self.assertEqual('1',new_match.section(text,('schema',)))
        self.assertEqual('[]',new_match.section(text,('native','TeamManager','Rouge','Members')))
        self.assertIsNone(new_match.section(text,('roster',)))
    def test_valid_request_checks_exact_state_and_candidate(self):
        data,candidate=new_match.request(self.root,'token');self.assertEqual(self.data,data);self.assertEqual('reset-candidate.yml',candidate.name)
    def test_invalid_or_expired_tokens_are_refused(self):
        with self.assertRaises(RuntimeError):new_match.request(self.root,'intrus')
        self.data['expiresAt']=0;self.save()
        with self.assertRaises(RuntimeError):new_match.request(self.root,'token')
    def test_changed_progress_is_never_reset(self):
        (self.root/'plugins/FKAmis/state.yml').write_text('schema: 1\nday: 4\n')
        with self.assertRaises(RuntimeError):new_match.request(self.root,'token')
    def test_candidate_tampering_and_path_escape_are_refused(self):
        (self.root/'plugins/FKAmis/reset-candidate.yml').write_text('altered')
        with self.assertRaises(RuntimeError):new_match.request(self.root,'token')
        self.data['candidateFile']='../outside.yml';self.save()
        with self.assertRaises((RuntimeError,ValueError)):new_match.request(self.root,'token')
    def test_future_schema_is_refused(self):
        self.data['schema']=2;self.save()
        with self.assertRaises(RuntimeError):new_match.request(self.root,'token')
    def test_policies_ignore_only_properties_comments(self):
        path=self.root/'server.properties';path.write_text('# date une\nserver-port=22880\n')
        original=new_match.policies(self.root)
        path.write_text('# date deux\nserver-port=22880\n');self.assertEqual(original,new_match.policies(self.root))
        path.write_text('# date deux\nserver-port=22881\n');self.assertNotEqual(original,new_match.policies(self.root))


if __name__=='__main__':unittest.main()
