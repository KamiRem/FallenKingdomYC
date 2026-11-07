"""Le patch de configuration conserve les valeurs étrangères au changement demandé."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import server
sys.modules['serverlib']=server
spec=importlib.util.spec_from_file_location('apply_admin_update',ROOT/'deployment/apply_admin_update.py')
update=importlib.util.module_from_spec(spec);spec.loader.exec_module(update)


class ConfigurationPatchTests(unittest.TestCase):
    def test_security_network_and_custom_settings_are_preserved(self):
        before='# personnalisé\nserver-port=22880\nonline-mode=true\nmax-players=8\ngamemode=spectator\nlevel-name=world\n'
        after=update.patch_keys(before,{'max-players':'10','gamemode':'survival','force-gamemode':'false'})
        for line in ['server-port=22880','online-mode=true','level-name=world','# personnalisé']:
            self.assertIn(line,after)
        self.assertIn('max-players=10',after);self.assertIn('gamemode=survival',after)

    def test_yaml_only_adds_or_changes_tips_flag(self):
        before='pvp-day: 2\nassault-day: 3\nteams: [Rouge, Bleue, Verte, Jaune]\n'
        after=update.patch_keys(before,{'disable-native-tips':'true'},':')
        self.assertTrue(after.startswith(before));self.assertIn('disable-native-tips: true',after)
        self.assertEqual(after,update.patch_keys(after,{'disable-native-tips':'true'},':'))

    def test_duplicate_key_is_refused(self):
        with self.assertRaises(RuntimeError):update.patch_keys('max-players=8\nmax-players=20\n',{'max-players':'10'})


if __name__=='__main__':unittest.main()
