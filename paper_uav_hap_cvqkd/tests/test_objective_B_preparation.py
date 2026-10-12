"""Focused B1 evidence checks: no source/evaluator/optimizer runs."""
import json
import unittest
from scripts import prepare_theta10_D55_objective_B as preparation


class ObjectiveBPreparationTests(unittest.TestCase):
    def test_reference_brackets_and_actual_missing_events(self):
        rows = preparation.saved.rows(preparation.OUT / 'reference_ao_coordinate_search.csv')
        self.assertEqual(len(rows), 2)
        self.assertEqual([json.loads(x['bracket']) for x in rows], [[5.4875, 5.5125], [.1625, .16562500000000002]])
        self.assertTrue(all(x['coordinate_complete'] == 'False' for x in rows))
        self.assertTrue(all(int(x['refinement_stages']) == 1 for x in rows))
        self.assertEqual([len(json.loads(x['missing_exact_points'])) for x in rows], [2, 2])
        for row in rows:
            for e in json.loads(row['candidate_history']):
                if e['status'] == 'EXACT_SOURCE_MISSING':
                    self.assertNotIn('K', e)

    def test_only_one_fresh_probe_requested(self):
        rows = preparation.saved.rows(preparation.OUT / 'targeted_exact_probe_plan.csv')
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(x['execution_scope'] == 'REQUEST_ONE_FRESH_ATTEMPT_NOW' for x in rows), 1)
        self.assertEqual(rows[0]['compatible_current_cache_key'], 'db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59')
        for x in rows:
            self.assertEqual(float.fromhex(x['nu_raw_hex']), float(x['nu_raw']))
            self.assertEqual(float.fromhex(x['V_A_hex']), float(x['V_A']))
            self.assertEqual(preparation.ao.json_hash(json.loads(x['original_source_identity'])), x['compatible_current_cache_key'])
            self.assertEqual(int(x['proposed_total_seconds']), int(x['proposed_per_probe_seconds']) + int(x['cleanup_postprocessing_reserve_seconds']))
            self.assertEqual(x['SKR_prediction'], 'NOT_AVAILABLE')
        self.assertEqual(json.loads(rows[0]['latest_additional_attempt_evidence'])['status'], 'WATCHDOG_ABORT')

    def test_saved_distances_and_optimality_scope(self):
        rows = preparation.saved.rows(preparation.OUT / 'optimized_skr_26_distances.csv')
        self.assertEqual([float(x['L_km']) for x in rows], list(preparation.sweep.DISTANCES_KM))
        self.assertTrue(all(x['supported_level'] == '1' for x in rows))
        ref = next(x for x in rows if float(x['L_km']) == preparation.saved.REF)
        self.assertEqual(float(ref['best_SKR']), .07798099387393764)
        self.assertAlmostEqual(float(ref['beta_I_AB']) - float(ref['chi_BE']), float(ref['best_SKR']), places=15)
        starts = preparation.saved.rows(preparation.OUT / 'ao_multistart_validation.csv')
        self.assertEqual(len(starts), 129)
        low = next(x for x in starts if float(x['L_km']) == preparation.saved.REF and x['start_id'] == 'nu_0.8')
        self.assertEqual((float(low['terminal_nu']), float(low['terminal_V_A'])), (.4, 3.))
        self.assertEqual(low['status'], 'UNRESOLVED_BOUNDARY')

    def test_fresh_evaluator_guard_preserves_context_constants(self):
        for key in ('BETA', 'EPSILON', 'GH_ORDER'):
            self.assertEqual(preparation.forbidden.__globals__[key], preparation.ao.evaluate_candidate.__globals__[key])
        with self.assertRaisesRegex(AssertionError, 'B1 forbids'):
            preparation.forbidden()

    def test_protected_inputs_outputs_and_no_AP(self):
        v = preparation.saved.read(preparation.OUT / 'objective_B_verification.json')
        self.assertFalse(v['B2_authorized'])
        self.assertEqual(v['new_source_moments'], 0)
        self.assertEqual(v['new_SKR_evaluations'], 1)
        self.assertEqual(v['compatible_positive_sources_in_global_inventory'], 148)
        point = v['additional_reference_existing_source_checks'][0]
        self.assertEqual((point['nu_raw'], point['V_A'], point['SKR']), (.25, 2., .06321019816401585))
        self.assertLess(point['SKR'], .07798099387393764)
        self.assertEqual(v['live_reference_coordinate_calls'], 2)
        self.assertTrue(all(preparation.sweep.sha256(preparation.ROOT / n) == h for n, h in v['protected_input_hashes'].items()))
        self.assertTrue(all(preparation.sweep.sha256(preparation.ROOT / n) == h for n, h in v['additional_provenance_input_hashes'].items()))
        self.assertTrue(all(preparation.sweep.sha256(preparation.OUT / n) == h for n, h in v['output_hashes'].items()))


if __name__ == '__main__':
    unittest.main()
