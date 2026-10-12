"""Checks for reconciled identities and original paired P1 requests; no AP."""
import unittest
from scripts import prepare_theta10_D55_P1_upper_refinement as prep


class UpperPreparationTests(unittest.TestCase):
    def test_proposal_identity_and_no_execution(self):
        p = prep.saved.read(prep.OUT / 'confirmed_candidate.json')
        self.assertEqual(p['compatible_cache_key'], prep.KEY)
        self.assertEqual(prep.saved.ao.json_hash(p['original_source_identity']), prep.KEY)
        self.assertEqual((p['nu_raw_hex'], p['V_A_hex']), (prep.NU.hex(), prep.VA.hex()))
        self.assertEqual(p['P1_request_ordinal'], 2)
        self.assertFalse(p['fresh_AP_authorized'])
        self.assertEqual(p['original_internal_fallback_timeout_seconds'], 3600)
        self.assertFalse(p['timeout_change_authorized'])

    def test_catalog_and_exact_request_sequence(self):
        r = prep.saved.read(prep.OUT / 'catalog_reconciliation.json')
        self.assertEqual(len(r['roster']), 149)
        self.assertEqual(len({(x['nu_raw_hex'], x['V_A_hex']) for x in r['roster']}), 149)
        self.assertEqual(len({x['canonical_cache_key'] for x in r['roster']}), 149)
        self.assertEqual(sum(x['origin'] == 'BASELINE147' for x in r['roster']), 147)
        searches = prep.saved.read(prep.OUT / 'live_reference_searches.json')
        self.assertEqual(searches[0]['bracket'], [5.49375, 5.5125])
        self.assertEqual([x['value'] for x in searches[0]['source_missing']], [5.496875, 5.50625])
        self.assertFalse(prep.saved.ao.coordinate_search_complete(searches[0]))
        v = prep.saved.read(prep.OUT / 'preflight_verification.json')
        self.assertEqual(v['new_AP_attempts'], 0)
        self.assertEqual(v['new_SKR_evaluations'], 0)
        self.assertEqual(v['saved_catalog_maximum_matches'], 26)
        self.assertTrue(v['temporary_Sleep_lease']['released_verified'])
        protected = prep.saved.read(prep.OUT / 'protected_input_manifest.json')
        self.assertTrue(all(prep.saved.sweep.sha256(prep.ROOT / n) == h for n, h in protected.items()))


if __name__ == '__main__':
    unittest.main()
