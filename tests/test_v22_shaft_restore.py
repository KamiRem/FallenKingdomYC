import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from v22_shaft_restore import packed_height,replace_height
from terrain_reference import SOURCE,verify_archive_restorations


class StoneReader:
    def chunk(self,x,z):
        return {'sections':[{'Y':y,'block_states':{'palette':['minecraft:stone']}} for y in range(3)]}


class ShaftRestoreTests(unittest.TestCase):
    def setUp(self):
        self.cells=[{'at':[0,y,0],'state':{'Name':'minecraft:stone','Properties':{}}} for y in range(33)]
        self.spec={'schema':1,'kind':'shaft-column-33','sourceArchiveSha256':SOURCE,'cells':self.cells}
        self.refresh()
        self.old=[[0,0,0],[0,1,0]]

    def refresh(self):
        self.spec['blockStatesSha256']=hashlib.sha256(json.dumps([[*c['at'],c['state']] for c in self.cells],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

    def test_supplement_checks_all_33_cells_and_no_exceptions(self):
        result=verify_archive_restorations(self.spec,StoneReader(),{},self.old)
        self.assertEqual(result['additionalArchiveRestorationsChecked'],33)
        self.assertEqual(result['preservedTerrainExceptions'],0)

    def test_incomplete_supplement_is_refused(self):
        self.spec['cells']=self.cells[:-1]
        with self.assertRaisesRegex(RuntimeError,'33 cellules'):verify_archive_restorations(self.spec,StoneReader(),{},self.old)

    def test_duplicate_or_non_column_points_are_refused(self):
        for position in ([0,0,0],[1,32,0],[0,34,0]):
            spec=copy.deepcopy(self.spec);spec['cells'][-1]['at']=position
            with self.assertRaisesRegex(RuntimeError,'dupliquée ou discontinue'):verify_archive_restorations(spec,StoneReader(),{},self.old)

    def test_source_archive_cannot_be_substituted(self):
        self.spec['sourceArchiveSha256']='0'*64
        with self.assertRaisesRegex(RuntimeError,'non approuvé'):verify_archive_restorations(self.spec,StoneReader(),{},self.old)

    def test_overlap_with_historical_footprint_is_exact(self):
        with self.assertRaisesRegex(RuntimeError,'31 nouvelles'):verify_archive_restorations(self.spec,StoneReader(),{},[])

    def test_changed_block_or_property_cannot_pass(self):
        self.cells[-1]['state']={'Name':'minecraft:grass_block','Properties':{'snowy':'true'}};self.refresh()
        with self.assertRaisesRegex(RuntimeError,'terrain archivé'):verify_archive_restorations(self.spec,StoneReader(),{},self.old)

    def test_expected_states_must_include_default_properties(self):
        self.cells[-1]['state']={'Name':'minecraft:grass_block','Properties':{}};self.refresh()
        with self.assertRaisesRegex(RuntimeError,'incomplet'):verify_archive_restorations(self.spec,StoneReader(),{'minecraft:grass_block':'minecraft:grass_block[snowy=false]'},self.old)

    def test_null_supplement_cannot_be_treated_as_legacy(self):
        with self.assertRaisesRegex(RuntimeError,'schéma'):verify_archive_restorations(None,StoneReader(),{},self.old)

    def test_heightmap_replacement_preserves_other_values_and_padding_bits(self):
        values=[-1]*37
        for index in (0,6,7,128,255):
            result=replace_height(values,index,129)
            self.assertEqual(packed_height(result,index),129)
            for other in range(256):
                if other!=index:self.assertEqual(packed_height(result,other),511)
            shift=(index%7)*9;changed=(values[index//7]^result[index//7])&((1<<64)-1)
            self.assertEqual(changed&~(511<<shift),0)

    def test_invalid_heightmap_or_height_is_refused(self):
        with self.assertRaisesRegex(ValueError,'InvalidHeightmap'):replace_height([0],0,129)
        with self.assertRaisesRegex(ValueError,'InvalidHeightValue'):replace_height([0]*37,0,385)

    def test_required_supplement_cannot_be_removed_from_reference(self):
        import terrain_reference as terrain
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'maintenance').mkdir();path=root/'maintenance/block-defaults-26.3.json';path.write_text('{}')
            points=[[i+1,0,0] for i in range(37128)]
            data={'caverns':[],'underground':{'mode':'vanilla-restored','sourceArchiveSha256':SOURCE,'checkPoints':points,
                'blockDefaultsSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blockStatesSha256':terrain.fingerprint(StoneReader(),points,{})}}
            (root/'map-underground-restoration.json').write_text('{"additionalArchiveRestorationsRequired":true}')
            with self.assertRaisesRegex(RuntimeError,'obligatoire absent'):terrain.verify(root,data,StoneReader())


if __name__=='__main__':unittest.main()
