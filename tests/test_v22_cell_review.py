from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from v22_cell_review import inspect_column, compare_reference_points


class Grid:
    def __init__(self, bottom=0, surface=32, ceiling_open=True):
        self.bottom, self.surface, self.ceiling_open = bottom, surface, ceiling_open

    def block(self, x, y, z):
        if y > self.surface:
            return 'minecraft:air'
        if x == z == 0 and self.bottom <= y and (self.ceiling_open or y <= self.bottom + 1):
            return 'minecraft:air'
        return 'minecraft:stone'


class CellReviewTests(unittest.TestCase):
    def test_exposed_shaft_detected_with_full_fall_distance(self):
        result = inspect_column(Grid(), (0, 0, 0))
        self.assertEqual(result['hazards'], ['UNGUARDED_VERTICAL_DROP_ON_STONE'])
        self.assertEqual({r['fallBlocks'] for r in result['rims']}, {33})
        self.assertTrue(result['openToSky'])

    def test_closed_two_cell_cavity_not_reported_as_open_shaft(self):
        result = inspect_column(Grid(ceiling_open=False), (0, 0, 0))
        self.assertEqual(result['hazards'], [])
        self.assertFalse(result['openToSky'])
        self.assertTrue(result['requiresInGameInspectionForGeneralSafety'])

    def test_non_air_exception_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ExpectedAirCell'):
            inspect_column(Grid(), (1, 0, 0))

    def test_reference_cannot_hide_failure_on_restoration_target(self):
        with patch('v22_cell_review.state', side_effect=[{'Name': 'minecraft:stone'}, {'Name': 'minecraft:air'}]):
            with self.assertRaisesRegex(ValueError, 'RestorationTargetMismatch'):
                compare_reference_points(None, None, [[0, 0, 0]], {}, {(0, 0, 0)})

    def test_duplicate_reference_points_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'DuplicateReferencePoint'):
            compare_reference_points(None, None, [[0, 0, 0], [0, 0, 0]], {}, set())


if __name__ == '__main__':
    unittest.main()
