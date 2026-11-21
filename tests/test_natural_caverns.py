"""Édition hors ligne bornée : fixtures NBT, régions et terrain organique."""
import sys
from pathlib import Path
import unittest
import zlib
import struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import anvil_patch as a
from natural_caverns_plan import room_shape,distance_from_edge,reachable,walkable
from natural_caverns_rework import verify_region,run
from natural_caverns_checks import containment

def chunk():
    section=a.Tag(10,{'Y':a.Tag(1,0),'block_states':a.Tag(10,{'palette':a.Tag(9,(8,[a.text('minecraft:stone')]))}),
        'biomes':a.Tag(10,{'palette':a.Tag(9,(8,[a.text('minecraft:plains')]))}),'BlockLight':a.Tag(7,bytes(2048))})
    root=a.Tag(10,{'DataVersion':a.Tag(3,9999),'xPos':a.Tag(3,-1),'sections':a.Tag(9,(10,[section])),
        'isLightOn':a.Tag(1,1),'unknown':a.Tag(10,{'uuid':a.Tag(12,[123,-456]),'text':a.text('préserver\x00🌿')})})
    return a.dump(b'',root)
def region():
    data=bytearray(8192)
    for i in (0,1):
        raw=zlib.compress(chunk());record=(len(raw)+1).to_bytes(4,'big')+b'\2'+raw
        data[i*4:i*4+4]=(len(data)//4096).to_bytes(3,'big')+b'\1'
        data.extend(record+bytes(4096-len(record)))
    data[4096:4104]=bytes.fromhex('1234567801234567')
    return bytes(data)

class NaturalTests(unittest.TestCase):
    def test_typed_roundtrip(self):
        raw=chunk();name,node=a.load(raw);self.assertEqual(a.dump(name,node),raw)
    def test_metadata_survives_edit(self):
        before=chunk();after,_=a.edit_chunk(before,{0:{17:'minecraft:water[level=8]'}})
        _,x=a.load(before);_,y=a.load(after)
        self.assertEqual(a.dump(b'',x.value['unknown']),a.dump(b'',y.value['unknown']))
        self.assertEqual(y.value['isLightOn'].value,0)
        self.assertNotIn('BlockLight',y.value['sections'].value[1][0].value)
    def test_palette_crosses_bit_width_boundary(self):
        changes={i:'minecraft:fixture_'+str(i) for i in range(23)}
        after,_=a.edit_chunk(chunk(),{0:changes});_,root=a.load(after)
        states=root.value['sections'].value[1][0].value['block_states'].value
        values=a.indices(states);palette=[a.state_key(a.plain(t)) for t in states['palette'].value[1]]
        for i,state in changes.items():self.assertEqual(palette[values[i]],a.parse_state(state))
        self.assertEqual(palette[values[4095]],('minecraft:stone',()))
    def test_compound_palette_keeps_properties(self):
        after,_=a.edit_chunk(chunk(),{0:{7:'minecraft:water[level=8]'}});_,root=a.load(after)
        states=root.value['sections'].value[1][0].value['block_states'].value
        i=a.indices(states)[7];self.assertEqual(a.state_key(a.plain(states['palette'].value[1][i])),('minecraft:water',(('level','8'),)))
    def test_neighbor_payload_and_timestamps_identical(self):
        before=region();after,_=a.patch_region(before,{0:{0:{0:'minecraft:air'}}})
        self.assertEqual(a.region_entries(before)[1],a.region_entries(after)[1])
        self.assertEqual(before[4096:8192],after[4096:8192])
        self.assertTrue(verify_region(before,after,{0:{0:{0:'minecraft:air'}}})['nonLightingMetadataIdentical'])
    def test_unexpected_edit_is_detected(self):
        before=region();after,_=a.patch_region(before,{0:{0:{0:'minecraft:air',1:'minecraft:air'}}})
        with self.assertRaisesRegex(RuntimeError,'Bloc hors plan'):verify_region(before,after,{0:{0:{0:'minecraft:air'}}})
    def test_no_new_chunk(self):
        with self.assertRaisesRegex(ValueError,'Chunk absent'):a.patch_region(region(),{4:{0:{0:'minecraft:air'}}})
    def test_no_new_section(self):
        with self.assertRaisesRegex(ValueError,'Section absente'):a.edit_chunk(chunk(),{15:{0:'minecraft:air'}})
    def test_truncated_nbt_rejected(self):
        with self.assertRaises(ValueError):a.load(chunk()[:-2])
    def test_truncated_region_rejected(self):
        with self.assertRaises(ValueError):a.region_entries(region()[:-1])
    def test_sector_overlap_rejected(self):
        raw=bytearray(region());raw[4:8]=raw[:4]
        with self.assertRaisesRegex(ValueError,'Secteurs partagés'):a.region_entries(bytes(raw))
    def test_external_chunk_rejected(self):
        raw=bytearray(region());raw[8196]=128|2
        with self.assertRaises(ValueError):a.region_entries(bytes(raw))
    def test_distinct_bounded_shapes(self):
        shapes=[room_shape(i) for i in range(1,5)]
        self.assertEqual(len({frozenset(s) for s in shapes}),4)
        for shape in shapes:
            self.assertTrue(all(abs(x)<=24 and abs(z)<=21 for x,z in shape))
            d=distance_from_edge(shape)
            for (x,z),v in d.items():
                for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                    if (x+dx,z+dz) in d:self.assertLessEqual(abs(v-d[x+dx,z+dz]),1)
    def test_cannot_overwrite_source(self):
        with self.assertRaises(RuntimeError):run(Path(__file__).parent,Path(__file__).parent)
    def test_one_block_steps_and_disconnected_island(self):
        cells={(0,0,0),(1,-1,0),(2,-2,0),(8,0,0)}
        self.assertEqual(reachable(cells,(0,0,0)),cells-{(8,0,0)})
    def test_lichen_does_not_block_the_walking_graph(self):
        local={(0,0,0):'minecraft:stone',(0,1,0):'minecraft:glow_lichen[north=true]',(0,2,0):'minecraft:cave_air'}
        self.assertIn((0,1,0),walkable(local))
    def test_water_cannot_be_used_as_a_solid_support(self):
        local={(0,0,0):'minecraft:water[level=0]',(0,1,0):'minecraft:cave_air',(0,2,0):'minecraft:cave_air'}
        self.assertNotIn((0,1,0),walkable(local))
    def test_sealed_volume_can_connect_only_to_its_entrance(self):
        class R:
            def block(self,x,y,z):return 'minecraft:cave_air' if (x,y,z) in {(0,0,0),(1,0,0)} else 'minecraft:stone'
        result=containment(R(),(0,0,0),[(-1,-1,-1),(2,1,1)],(8,6,0))
        self.assertTrue(result['undergroundContained'])
    def test_unexpected_tunnel_outside_envelope_is_rejected(self):
        class R:
            def block(self,x,y,z):return 'minecraft:air' if x==0 and y==0 and z in (0,1,2) else 'minecraft:stone'
        with self.assertRaisesRegex(RuntimeError,'hors enveloppe'):containment(R(),(0,0,0),[(-1,-1,-1),(1,1,1)],(8,6,0))
    def test_cave_without_entrance_is_rejected(self):
        class R:
            def block(self,x,y,z):return 'minecraft:air' if (x,y,z)==(0,0,0) else 'minecraft:stone'
        with self.assertRaisesRegex(RuntimeError,'Accès de surface absent'):containment(R(),(0,0,0),[(-1,-1,-1),(1,1,1)],(8,6,0))

if __name__=='__main__':unittest.main()
