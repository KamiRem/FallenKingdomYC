"""Comparer la sémantique des palettes Anvil, indépendamment de leur rangement."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from world_integrity import states_equal, terrain_equal


class WorldIntegrityTests(unittest.TestCase):
    def test_26_2_and_26_3_palette_encodings_are_equivalent(self):
        self.assertTrue(states_equal({'palette': [{'Name': 'minecraft:stone'}]},
                                     {'palette': [{'': 'minecraft:stone'}]}))
        self.assertTrue(states_equal({'palette': [{'Name': 'minecraft:oak_log', 'Properties': {'axis': 'y'}}]},
                                     {'palette': [{'id': 'minecraft:oak_log', 'properties': {'axis': 'y'}}]}))

    def test_omitted_defaults_require_registry_and_keep_explicit_differences(self):
        old = {'palette': [{'Name': 'minecraft:oak_log', 'Properties': {'axis': 'y'}}]}
        new = {'palette': ['minecraft:oak_log']}
        defaults = {'minecraft:oak_log': {'axis': 'y'}}
        self.assertFalse(states_equal(old, new))
        self.assertTrue(states_equal(old, new, defaults=defaults))
        changed = {'palette': [{'id': 'minecraft:oak_log', 'properties': {'axis': 'x'}}]}
        self.assertFalse(states_equal(old, changed, defaults=defaults))

    def test_reordered_palette_preserves_blocks(self):
        # Un conteneur non uniforme peut réordonner sa palette sans modifier le monde.
        left = {'palette': [{'Name': 'minecraft:stone'}, {'Name': 'minecraft:dirt'}], 'data': [0x10]}
        right = {'palette': [{'Name': 'minecraft:dirt'}, {'Name': 'minecraft:stone'}], 'data': [0x01]}
        self.assertTrue(states_equal(left, right, size=2))

    def test_changed_block_is_detected(self):
        self.assertFalse(states_equal({'palette': [{'Name': 'minecraft:chest'}]},
                                      {'palette': [{'Name': 'minecraft:air'}]}))

    def test_light_and_data_version_can_change_but_inventory_cannot(self):
        chest = {'id': 'minecraft:chest', 'x': 1, 'y': 70, 'z': 2,
                 'Items': [{'id': 'minecraft:diamond', 'count': 2}]}
        left = {'DataVersion': 1, 'sections': [{'Y': 0, 'SkyLight': b'old'}], 'block_entities': [chest]}
        right = {'DataVersion': 2, 'sections': [{'Y': 0, 'SkyLight': b'new'}], 'block_entities': [dict(chest)]}
        self.assertTrue(terrain_equal(left, right))
        right['block_entities'][0]['Items'] = []
        self.assertFalse(terrain_equal(left, right))


if __name__ == '__main__': unittest.main()
