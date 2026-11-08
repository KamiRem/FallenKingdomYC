import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import server
sys.modules['serverlib']=server
spec=importlib.util.spec_from_file_location('gameplay_patch',ROOT/'deployment/apply_gameplay_update.py')
update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)


class GameplayUpdateTests(unittest.TestCase):
    def test_missing_defaults_are_added_without_rewriting_custom_values(self):
        original='pvp-day: 2\ncustom: valeur\ncapture-radius: 3.5\n'
        result=update.config_defaults(original)
        self.assertTrue(result.startswith(original));self.assertIn('players-per-team: 2',result)
        self.assertEqual(result,update.config_defaults(result))

    def test_existing_capacity_debug_and_tips_preferences_are_preserved(self):
        original='players-per-team: 4 # quatre\ndamage-debug: true\ndisable-native-tips: true\n'
        self.assertEqual(original,update.config_defaults(original))

    def test_invalid_capacity_and_duplicate_keys_fail_before_changes(self):
        for original in ('players-per-team: 0\n','players-per-team: 5\n','players-per-team: "2"\n',
                         'players-per-team: 2\nplayers-per-team: 3\n'):
            with self.assertRaises(RuntimeError):update.config_defaults(original)

    def test_payload_contains_no_live_data(self):
        self.assertNotIn('plugins/FKAmis/state.yml',update.ALLOWED)
        self.assertNotIn('server.properties',update.ALLOWED)
        self.assertEqual({'plugins/FKAmis-1.0.0.jar','FKAmis.sha256','maintenance/serverlib.py','maintenance/host_ops.py'},update.ALLOWED)


if __name__=='__main__':unittest.main()
