"""Small checks for fixed one-attempt budget/identity; no AP."""
import unittest
from scripts import run_theta10_D55_objective_B_pilot as pilot
from scripts import recover_theta10_D55_objective_B_postprocess as recovery


class PilotBudgetTests(unittest.TestCase):
    def test_reserve_and_probe_cap(self):
        self.assertEqual(pilot.remaining_probe_seconds(100., 4600.), 3600.)
        self.assertEqual(pilot.remaining_probe_seconds(130., 4600.), 3570.)
        self.assertEqual(pilot.remaining_probe_seconds(4000., 4600.), 0.)

    def test_only_authorized_binary64_pair(self):
        self.assertEqual(pilot.NU.hex(), '0x1.51eb851eb851fp-3')
        self.assertEqual(pilot.VA.hex(), '0x1.5f9999999999ap+2')
        self.assertEqual((pilot.saved.ao.MAX_AO_ITERATIONS, pilot.saved.ao.K_TOLERANCE,
            pilot.saved.ao.PARAMETER_TOLERANCE, pilot.saved.ao.MAX_REFINEMENT_STAGES), (6, 1e-8, 1e-6, 4))

    def test_checkpoint_metadata_infinity_only(self):
        import json
        import math
        identity = {'identity': {'config': {'radius_of_curvature_m': math.inf}}, 'rows': [{'SKR': .1}]}
        self.assertEqual(json.loads(recovery.checked_json(identity)), identity)
        for key, value in (('SKR', math.inf), ('C', math.nan), ('radius_of_curvature_m', -math.inf)):
            with self.assertRaises(ValueError):
                recovery.checked_json({key: value})

    def test_completed_catalog_and_genuine_AO_records(self):
        import math
        if not (recovery.OUT / 'postprocess_report.json').exists():
            self.skipTest('Completed pilot artifacts not present')
        saved = pilot.saved
        config = saved.source.unconstrained_config()
        bank = {saved.pair(float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])): p
            for p in saved.source.load_source_payloads(config, pilot.DIRS).values()
            if float.fromhex(p['nu_mb_raw_hex']) > 0}
        self.assertEqual(len(bank), 149)
        source = bank[saved.pair(pilot.NU, pilot.VA)]
        self.assertEqual(source['cache_key'], pilot.KEY)
        self.assertEqual(source['support_size'], 256)
        self.assertTrue(math.isfinite(source['C']) and math.isfinite(source['w']))
        old = saved.read(saved.BASE / 'objective_checkpoint.json')
        checkpoints = saved.read(recovery.OUT / 'objective_checkpoint.json')
        selected = saved.rows(recovery.OUT / 'optimized_skr_26_distances.csv')
        comparison = saved.rows(recovery.OUT / 'old_vs_new_skr.csv')
        runs = saved.read(recovery.OUT / 'cache_only_runs.json')
        searches = saved.read(recovery.OUT / 'cache_only_searches.json')
        self.assertEqual([e['L_km'] for e in checkpoints], list(saved.sweep.DISTANCES_KM))
        self.assertEqual(len(selected), 26)
        self.assertEqual(len(comparison), 26)
        self.assertEqual(len(runs), 129)
        self.assertEqual(sum(len(r['iterations']) for r in runs), 283)
        aligned, _ = saved.audit.align_searches(runs, searches)
        self.assertEqual(len(aligned), 618)
        self.assertEqual(sum(saved.ao.coordinate_search_complete(s) for s in aligned), 0)
        for entry, picked, compared in zip(checkpoints, selected, comparison):
            distance = entry['L_km']
            self.assertTrue(saved.ao.objective_compatible(entry['identity'], old[str(distance)]['identity']))
            index = {saved.pair(r['nu_raw'], r['V_A']): r for r in entry['rows']}
            self.assertEqual(set(index), set(bank))
            for key, row in index.items():
                saved.ao.finite_metrics(row)
                self.assertEqual(row['source_cache_key'], bank[key]['cache_key'])
                self.assertEqual(row['ensemble_hash'], bank[key]['ensemble_hash'])
                self.assertEqual(row['channel_hash'], old[str(distance)]['identity']['identity']['channel']['channel_hash'])
                self.assertEqual(row['SKR'], row['beta_I_AB'] - row['chi_BE'])
                self.assertAlmostEqual(row['beta_I_AB'], .95 * row['I_AB'], places=15)
            winner = max(index.values(), key=lambda r: r['SKR'])
            genuine = max((r for r in runs if r['L_km'] == distance), key=lambda r: r['final']['SKR'])
            self.assertEqual(genuine['final']['SKR'], winner['SKR'])
            self.assertEqual(saved.pair(picked['nu_raw'], picked['V_A']), saved.pair(winner['nu_raw'], winner['V_A']))
            self.assertEqual(float(picked['best_SKR']), winner['SKR'])
            self.assertEqual(float(compared['delta_K']), 0.)
            for run in (r for r in runs if r['L_km'] == distance):
                for event in run['trajectory']:
                    self.assertIn(saved.pair(event['nu'], event['V_A']), index)
                for it in run['iterations']:
                    for nu, va, key in ((it['nu_before'], it['V_A_before'], 'K_before'),
                        (it['nu_before'], it['optimized_V_A'], 'K_after_VA'),
                        (it['optimized_nu'], it['optimized_V_A'], 'K_after_nu')):
                        self.assertEqual(it[key], index[saved.pair(nu, va)]['SKR'])


if __name__ == '__main__':
    unittest.main()
