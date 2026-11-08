import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import server
sys.modules['serverlib']=server
spec=importlib.util.spec_from_file_location('vnext_patch',ROOT/'deployment/apply_vnext_update.py')
update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)


class VNextUpdateTests(unittest.TestCase):
    def test_additive_config_is_idempotent_and_preserves_unknown_values(self):
        original='custom-note: conserver\nplayers-per-team: 3\ncapture-seconds: 77\n'
        value=update.config_defaults(original)
        self.assertTrue(value.startswith(original));self.assertIn('respawn-protection-seconds: 5',value)
        self.assertEqual(value,update.config_defaults(value))
        self.assertNotIn('supply-interval-seconds',value)

    def test_existing_grace_is_preserved_and_invalid_or_duplicate_values_are_refused(self):
        original='players-per-team: 2\ndamage-debug: false\ndisable-native-tips: true\nrespawn-protection-seconds: 0\n'
        self.assertEqual(original,update.config_defaults(original))
        for value in ('-1','31','NaN','5.5','"5"'):
            with self.assertRaises(RuntimeError):update.config_defaults('respawn-protection-seconds: '+value+'\n')
        with self.assertRaises(RuntimeError):update.config_defaults('respawn-protection-seconds: 5\nrespawn-protection-seconds: 0\n')

    def test_update_payload_cannot_overwrite_live_state_or_host_settings(self):
        for name in ('server.properties','plugins/FKAmis/state.yml','plugins/FKAmis/admins.yml','plugins/FKAmis/supplies.yml','world/level.dat'):
            self.assertNotIn(name,update.ALLOWED)
        self.assertEqual('83e721d8ac12feefdb590976747f88d6825b3243976c7e9f10b1cc35fac5239d',update.PREVIOUS)
        self.assertIn('maintenance/new_match.py',update.ALLOWED)


if __name__=='__main__':unittest.main()
