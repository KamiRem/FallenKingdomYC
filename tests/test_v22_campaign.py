from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import v22_final_campaign as campaign


class CampaignIsolationTests(unittest.TestCase):
    def test_refuses_output_in_repository_before_any_write(self):
        with self.assertRaisesRegex(RuntimeError,'Dossier neuf hors dépôt'):
            campaign.prepare(campaign.server.ROOT/'runtime/forbidden-final',campaign.server.ROOT/'not-a-source')

    def test_refuses_source_nested_in_destination(self):
        private=Path.home()/'FKBackups/campaign-test-do-not-create'
        with self.assertRaisesRegex(RuntimeError,'distinct de la source'):
            campaign.prepare(private,private/'candidate')

    def test_existing_probe_safety_flags_and_restart_are_required(self):
        for suite in ('final','next1','supplies','statistics'):
            _,_,flags,phases,success,_=campaign.spec(suite)
            self.assertTrue(any(flag.endswith('=true') for flag in flags))
            self.assertGreater(len(phases),1)
            self.assertIn('SUCCESS',success)


if __name__=='__main__':unittest.main()
