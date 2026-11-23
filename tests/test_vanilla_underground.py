import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import server
sys.modules['serverlib']=server
sys.path.insert(0,str(server.ROOT/'deployment'))
import terrain_reference as terrain
import new_match

class UniformReader:
    def __init__(self,name='minecraft:stone',properties=None):self.name=name;self.properties=properties
    def chunk(self,x,z):return {'sections':[{'Y':0,'block_states':{'palette':[{'id':self.name,'properties':self.properties}] if self.properties else [self.name]}}]}

class VanillaReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'maintenance').mkdir()
        self.defaults={'minecraft:stone':'minecraft:stone','minecraft:water':'minecraft:water[level=0]'}
        path=self.root/'maintenance/block-defaults-26.3.json';path.write_text(json.dumps(self.defaults))
        self.points=[[i,0,0] for i in range(37128)]
        self.spec={'mode':'vanilla-restored','sourceArchiveSha256':terrain.SOURCE,'checkPoints':self.points,'blockDefaultsSha256':server.digest(path),'blockStatesSha256':terrain.fingerprint(UniformReader(),self.points,self.defaults)}
        self.data={'underground':self.spec,'caverns':[]}
    def test_complete_initial_fingerprint(self):
        self.assertEqual(37128,terrain.verify(self.root,self.data,UniformReader())['naturalTerrainBlocksChecked'])
    def test_change_in_natural_material_is_detected(self):
        with self.assertRaisesRegex(RuntimeError,'différent ou miné'):terrain.verify(self.root,self.data,UniformReader('minecraft:dirt'))
    def test_incomplete_or_duplicate_footprint_is_refused(self):
        for points in (self.points[:-1],[[0,0,0]]*37128):
            self.spec['checkPoints']=points
            with self.assertRaisesRegex(RuntimeError,'incomplète'):terrain.verify(self.root,self.data,UniformReader())
    def test_unapproved_archive_is_refused(self):
        self.spec['sourceArchiveSha256']='0'*64
        with self.assertRaisesRegex(RuntimeError,'non approuvée'):terrain.verify(self.root,self.data,UniformReader())
    def test_registry_tampering_is_refused(self):
        (self.root/'maintenance/block-defaults-26.3.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'Registre'):terrain.verify(self.root,self.data,UniformReader())
    def test_artificial_caverns_cannot_replace_terrain_check(self):
        self.data['caverns']=[{}]*4
        with self.assertRaisesRegex(RuntimeError,'ne doit pas'):terrain.verify(self.root,self.data,UniformReader())
    def test_default_properties_do_not_create_false_differences(self):
        points=[[0,0,0]]
        a=terrain.fingerprint(UniformReader('minecraft:water'),points,self.defaults)
        b=terrain.fingerprint(UniformReader('minecraft:water',{'level':'0'}),points,self.defaults)
        c=terrain.fingerprint(UniformReader('minecraft:water',{'level':'8'}),points,self.defaults)
        self.assertEqual(a,b);self.assertNotEqual(a,c)
    def test_v21_still_requires_four_caverns(self):
        with self.assertRaisesRegex(RuntimeError,'Carte V2.1'):new_match.reference_mode({'mapVersion':'2.1'},{'caverns':[]},True)
        self.assertEqual('historical',new_match.reference_mode({'mapVersion':'2.1'},{'caverns':[{}]*4},True))
    def test_v22_cannot_use_an_old_cavern_reference(self):
        with self.assertRaisesRegex(RuntimeError,'Carte V2.2'):new_match.reference_mode({'mapVersion':'2.2'},{'caverns':[{}]*4},False)
        self.assertEqual('vanilla-restored',new_match.reference_mode({'mapVersion':'2.2'},self.data,False))
    def test_historical_profile_does_not_require_natural_restoration(self):
        self.assertEqual('historical',new_match.reference_mode({'mapVersion':'2.0'},{},False))
        with self.assertRaisesRegex(RuntimeError,'incompatible'):new_match.reference_mode({'mapVersion':'2.0'},self.data,False)

if __name__=='__main__':unittest.main()
