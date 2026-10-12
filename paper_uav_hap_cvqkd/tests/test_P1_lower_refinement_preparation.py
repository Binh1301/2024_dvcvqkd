"""Original source identity, exact catalog and P1 request order; no AP."""
import unittest
from scripts import prepare_theta10_D55_P1_lower_refinement as prep


class LowerPreparationTests(unittest.TestCase):
    def test_binary64_identity_and_one_attempt_plan(self):
        p = prep.saved.read(prep.OUT/'confirmed_candidate.json')
        self.assertEqual(prep.saved.ao.json_hash(p['original_source_identity']),prep.KEY)
        self.assertEqual((p['nu_raw_hex'],p['V_A_hex']),('0x1.51eb851eb851fp-3','0x1.5fccccccccccdp+2'))
        self.assertEqual(p['P1_request_ordinal'],1)
        self.assertEqual((p['maximum_new_attempts'],p['original_internal_fallback_timeout_seconds']),(1,3600))
        self.assertFalse(p['source_exists'])
        self.assertFalse(p['fresh_AP_authorized'])
        self.assertFalse(p['other_AP_allowed'])
        self.assertFalse(p['retry_allowed'])

    def test_live_original_request_and_protected_baseline(self):
        c = prep.saved.read(prep.OUT/'live_reference_searches.json')[0]
        self.assertEqual(c['bracket'],[5.49375,5.50625])
        self.assertEqual(c['best_value'],5.5)
        self.assertEqual(c['best_K'],.07798099387393764)
        self.assertEqual([r['value'] for r in c['source_missing']],[5.496875,5.503125])
        self.assertFalse(prep.saved.ao.coordinate_search_complete(c))
        v = prep.saved.read(prep.OUT/'preflight_verification.json')
        self.assertEqual((v['unique_MB_sources'],v['saved_exact_metrics_verified'],v['saved_catalog_matches']),(150,3900,26))
        self.assertEqual(v['new_AP_attempts'],0)
        self.assertEqual(v['new_SKR_evaluations'],0)
        self.assertTrue(v['temporary_Sleep_lease']['released_verified'])
        manifest = prep.saved.read(prep.OUT/'protected_input_manifest.json')
        self.assertTrue(all(prep.saved.sweep.sha256(prep.ROOT/n)==h for n,h in manifest.items()))


if __name__ == '__main__':
    unittest.main()
