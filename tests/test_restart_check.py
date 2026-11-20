"""Contrôles ciblés de la lecture crash/watchdog, sans réseau ni identités réelles."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import minestrator_restart_check as restart

class RestartCheckTests(unittest.TestCase):
    def test_scope_is_five_small_named_files_without_world_walk(self):
        self.assertEqual(5,len(restart.TARGETS));self.assertEqual(5,len(set(restart.TARGETS)))
        self.assertFalse(any(n.startswith(('world/','plugins/')) for n in restart.TARGETS))
    def test_notification_and_daemon_identifier_are_not_crash_policy_proof(self):
        data={'settings':{'poweraction_message':{'restart':'message seulement'}},'server':{'id_daemon':12},'history':[{'restart':True}]}
        self.assertEqual(['/server/id_daemon'],restart.matching_host_keys(data))
        data['settings']['restart_on_crash']=False
        self.assertIn('/settings/restart_on_crash',restart.matching_host_keys(data))
    def test_configuration_is_read_without_executing_restart_script(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'config').mkdir()
            (root/'spigot.yml').write_text('settings:\n  restart-on-crash: true\n  restart-script: ./start.sh\n  timeout-time: 60\n')
            (root/'config/paper-global.yml').write_text('watchdog:\n  early-warning-delay: 10000\n  early-warning-every: 5000\n')
            (root/'server.properties').write_text('max-tick-time=60000\n')
            script=root/'start.sh';script.write_text('#!/bin/sh\n: "${SERVER_PORT:?obligatoire}"\nexec python3 maintenance/host_ops.py start\n')
            before=script.read_bytes();result=restart.describe(root)
            self.assertEqual('true',result['restartOnCrash']);self.assertEqual('60',result['timeoutSeconds'])
            self.assertEqual('10000',result['paperWatchdogWarningDelayMs']);self.assertFalse(result['scriptsExecuted'])
            self.assertTrue(result['startShRequiresServerPort']);self.assertFalse(result['startShHasLoopKeyword'])
            self.assertEqual(before,script.read_bytes())

if __name__=='__main__':unittest.main()
