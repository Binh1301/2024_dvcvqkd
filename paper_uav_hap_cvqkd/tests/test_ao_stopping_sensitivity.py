"""Small checks for isolated overrides and the bound Python default."""
import unittest
import json
from unittest.mock import patch
from scripts import run_theta10_D55_ao_stopping_sensitivity as experiment


class StoppingSensitivityTests(unittest.TestCase):
    def test_tolerance_forwarding_and_restoration_on_failure(self):
        ao, sweep = experiment.ao, experiment.sweep
        original = sweep.adaptive_maximize_1d
        records = []
        with patch.object(ao, 'adaptive_maximize_1d', return_value={'status': 'test'}) as inner:
            with self.assertRaisesRegex(RuntimeError, 'stop'):
                with experiment.stopping_override(1e-9, records.append):
                    self.assertEqual(ao.K_TOLERANCE, 1e-9)
                    self.assertEqual(sweep.K_TOLERANCE, 1e-9)
                    sweep.adaptive_maximize_1d(variable='V_A', fixed=.165, values=[5.5], objective=None)
                    self.assertEqual(inner.call_args.kwargs['k_tolerance'], 1e-9)
                    self.assertNotIn('parameter_tolerance', inner.call_args.kwargs)
                    raise RuntimeError('stop')
        self.assertEqual(records, [{'status': 'test'}])
        self.assertIs(sweep.adaptive_maximize_1d, original)
        self.assertEqual(ao.K_TOLERANCE, 1e-8)
        self.assertEqual(sweep.K_TOLERANCE, 1e-8)
        self.assertEqual(ao.PARAMETER_TOLERANCE, 1e-6)
        self.assertEqual(ao.MAX_REFINEMENT_STAGES, 4)
        self.assertEqual(ao.MAX_BOUNDARY_EXPANSIONS, 3)

    def test_missing_binary64_pairs_not_decimal_rounded(self):
        searches = [{'variable': 'V_A', 'fixed': .165,
                     'source_missing': [{'value': 5.425}, {'value': 5.425000000000001}]}]
        self.assertEqual(len(experiment.missing_pairs(searches)), 2)

    @unittest.skipUnless((experiment.OUT / 'sensitivity_validation.json').exists(), 'Results not produced yet')
    def test_genuine_results_warm_chains_metrics_and_protection(self):
        saved = experiment.saved
        checkpoint = saved.read(saved.BASE / 'objective_checkpoint.json')
        summaries = saved.rows(experiment.OUT / 'sensitivity_grid_16_configs.csv')
        self.assertEqual(len(summaries), 16)
        for summary in summaries:
            result = saved.read(experiment.OUT / (summary['configuration'] + '.json'))
            self.assertEqual(result['Rmax'], int(summary['Rmax']))
            self.assertEqual(result['epsilon'], float(summary['epsilon']))
            self.assertEqual(len(result['runs']), 129)
            self.assertEqual(sum(len(r['iterations']) for r in result['runs']), int(summary['total_outer_iterations']))
            aligned = []
            for distance in experiment.sweep.DISTANCES_KM:
                index = {saved.pair(x['nu_raw'], x['V_A']): x for x in checkpoint[str(distance)]['rows']}
                local = [r for r in result['runs'] if r['L_km'] == distance]
                self.assertEqual([r['start_id'] for r in local[:4]], ['nu_0.1', 'nu_0.15', 'nu_0.3', 'nu_0.8'])
                selected = max(local, key=lambda r: r['final']['SKR'])['final']
                self.assertEqual(selected['SKR'], max(x['SKR'] for x in index.values()))
                if distance != 20.:
                    warm = local[-1]
                    self.assertEqual(warm['start_id'], 'warm_previous_distance')
                    self.assertEqual(saved.pair(warm['start_nu'], warm['start_V_A']), previous)
                previous = saved.pair(selected['nu_raw'], selected['V_A'])
                for run in local:
                    self.assertLessEqual(len(run['iterations']), result['Rmax'])
                    for it in run['iterations']:
                        for n, v, k in ((it['nu_before'], it['V_A_before'], it['K_before']),
                                        (it['nu_before'], it['optimized_V_A'], it['K_after_VA']),
                                        (it['optimized_nu'], it['optimized_V_A'], it['K_after_nu'])):
                            self.assertEqual(index[saved.pair(n, v)]['SKR'], k)
                        self.assertEqual(it['delta_K'], it['K_after_nu'] - it['K_before'])
                        if it['convergence_status'] != 'RUNNING':
                            self.assertLessEqual(abs(it['delta_K']), result['epsilon'])
                    self.assertEqual(run['exact_evaluations'], 0)
                # Use existing original alignment auditor, with explicit result-only fields.
            aligned, finals = saved.audit.align_searches(result['runs'], result['searches'])
            self.assertEqual(len(aligned), len(result['searches']))
            self.assertFalse(any(experiment.ao.coordinate_search_complete(s) for s in aligned))
            for s in aligned:
                valid = {saved.pair(x['nu_raw'], x['V_A']) for x in checkpoint[str(s['L_km'])]['rows']}
                self.assertTrue(all(p not in valid for p in experiment.missing_pairs([s])))
            self.assertEqual(sum(r['requested_evaluations'] - r['cache_hits'] for r in result['runs']),
                             int(summary['body_missing_events']))
        protected = saved.read(experiment.OUT / 'protected_input_manifest.json')
        self.assertTrue(all(experiment.sweep.sha256(experiment.ROOT / name) == digest for name, digest in protected.items()))
        validation = saved.read(experiment.OUT / 'sensitivity_validation.json')
        self.assertTrue(all(experiment.sweep.sha256(experiment.OUT / name) == digest
                            for name, digest in validation['output_hashes'].items()))
        table = (experiment.OUT / 'sensitivity_summary_table.tex').read_text()
        self.assertEqual(table.count(' & '), 17 * 6)
        self.assertEqual(table.count('\\begin{table}'), table.count('\\end{table}'))
        text = (experiment.OUT / 'stopping_parameter_justification.tex').read_text()
        a, b = text.split('% Version B (alternative, do not include both):')
        a = a.split('\\subsection{Sensitivity Analysis of AO Stopping Parameters}')[1]
        b = b.split('\\subsection{Sensitivity Analysis of AO Stopping Parameters}')[1]
        self.assertTrue(120 <= len(a.split()) <= 170)
        self.assertTrue(250 <= len(b.split()) <= 350)


if __name__ == '__main__':
    unittest.main()
