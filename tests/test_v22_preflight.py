from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from minestrator_v22_preflight import ReadOnlySftp,ObservationGuard,Unsafe,hosting_fields
from v22_rebase_plan import classify,simulate_transfer,propose_reference


class ReadOnlyPreflightTests(unittest.TestCase):
    def test_sftp_refuses_all_open_modes_except_binary_read(self):
        raw=Mock();client=ReadOnlySftp(raw)
        for mode in ('w','wb','a','r+','x','r'):
            with self.assertRaises(Unsafe):client.open('file',mode)
        raw.open.assert_not_called();client.open('file','rb');raw.open.assert_called_once_with('file','rb')

    def test_mutation_methods_are_not_exposed(self):
        client=ReadOnlySftp(Mock())
        for name in ('put','remove','rename','mkdir','chmod','chown','symlink','truncate'):
            self.assertFalse(hasattr(client,name))

    def test_only_statvfs_extension_is_permitted(self):
        client=ReadOnlySftp(Mock())
        with self.assertRaises(Unsafe):client._request(200,'posix-rename@openssh.com','old','new')

    def test_observation_does_not_assume_server_is_offline(self):
        api=Mock();api.get.return_value={'state':'online','stats':{'state':'online'}}
        guard=ObservationGuard(api);guard.poll();self.assertEqual(guard.initial,'online');guard.check()

    def test_state_change_aborts_without_power_command(self):
        api=Mock();api.get.side_effect=[{'state':'offline','stats':{'state':'offline'}},{'state':'online','stats':{'state':'online'}}]
        guard=ObservationGuard(api);guard.poll();guard.abort=Mock()
        with self.assertRaisesRegex(Unsafe,'ServerStateChanged'):guard.poll()
        guard.abort.assert_called_once();self.assertTrue(guard.failed.is_set())

    def test_notification_message_is_not_restart_policy_evidence(self):
        self.assertEqual(hosting_fields({'poweraction_message':{'restart':'text'},'websocket':{'token':'secret'}}),[])

    def test_rebase_never_overwrites_an_unexpected_block(self):
        from unittest.mock import patch
        blocks=[{'at':[1,2,3],'before':'minecraft:stone','after':'minecraft:air'}]
        with patch('v22_rebase_plan.state',return_value={'Name':'minecraft:chest'}):
            edits,already,conflicts=classify(None,blocks,{})
        self.assertEqual(edits,[]);self.assertEqual(already,[]);self.assertEqual(len(conflicts),1)

    def test_rebase_is_idempotent_and_compares_default_properties(self):
        from unittest.mock import patch
        blocks=[{'at':[1,2,3],'before':'minecraft:stone','after':'minecraft:water[level=0]'}]
        with patch('v22_rebase_plan.state',return_value={'Name':'minecraft:water'}):
            edits,already,conflicts=classify(None,blocks,{'minecraft:water':'minecraft:water[level=0]'})
        self.assertEqual(edits,[]);self.assertEqual(already,[[1,2,3]]);self.assertEqual(conflicts,[])

    def test_changed_source_or_bad_stage_aborts_before_quarantine(self):
        with self.assertRaisesRegex(RuntimeError,'source modifiée'):
            simulate_transfer({'file':'old'},{'file':'new'},[],observed={'file':'unexpected'})
        with self.assertRaisesRegex(RuntimeError,'staging incorrect'):
            simulate_transfer({'file':'old'},{'file':'new'},[],staged={'file':'corrupt'})

    def test_full_hash_model_rollback_preserves_unknown_player_files(self):
        before={'file':'old','world/players/data/real.dat':'protected','old-cavern-record.json':'history'}
        result=simulate_transfer(before,{'file':'new','reference/history.json':'history'},['old-cavern-record.json'],fail_after=1,backup_verified=True)
        self.assertTrue(result['rollbackHashModelMatchesCurrentSource']);self.assertFalse(result['realRestorePerformed'])

    def test_rollback_refused_without_verified_current_backup(self):
        with self.assertRaisesRegex(RuntimeError,'sans sauvegarde courante'):
            simulate_transfer({'file':'old'},{'file':'new'},[],fail_after=1)

    def test_player_data_and_other_dimensions_cannot_be_targets(self):
        for name in ('world/players/data/real.dat','world_nether/region.mca','world_the_end/region.mca',
                     'world/dimensions/minecraft/the_nether/region/r.0.0.mca',
                     'world/dimensions/minecraft/the_end/region/r.0.0.mca',
                     'world/dimensions/minecraft/overworld/region/r.1.0.mca','world/level.dat'):
            with self.assertRaisesRegex(RuntimeError,'protégées'):
                simulate_transfer({name:'old'},{name:'new'},[])
            with self.assertRaisesRegex(RuntimeError,'protégées'):
                simulate_transfer({name:'old'},{},[name])

    def test_reference_proposal_cannot_mask_a_failed_restoration(self):
        from unittest.mock import patch
        original={'underground':{'checkPoints':[[1,2,3]],'blockStatesSha256':'original'}}
        with patch('v22_rebase_plan.state',side_effect=[{'Name':'minecraft:stone'},{'Name':'minecraft:air'}]):
            with self.assertRaisesRegex(RuntimeError,'restauration masqué'):
                propose_reference(original,None,None,{}, {(1,2,3)})
        self.assertEqual(original['underground']['blockStatesSha256'],'original')

    def test_preserved_edit_proposal_does_not_approve_or_change_original_reference(self):
        from unittest.mock import patch
        original={'underground':{'checkPoints':[[1,2,3]],'blockStatesSha256':'original'}}
        with patch('v22_rebase_plan.state',side_effect=[{'Name':'minecraft:stone'},{'Name':'minecraft:air'}]),patch('terrain_reference.fingerprint',return_value='proposed'):
            result,differences=propose_reference(original,None,None,{},set())
        self.assertEqual(len(differences),1);self.assertEqual(result['underground']['approvalStatus'],'proposed_only_not_approved')
        self.assertEqual(original['underground']['blockStatesSha256'],'original')


if __name__=='__main__':unittest.main()
