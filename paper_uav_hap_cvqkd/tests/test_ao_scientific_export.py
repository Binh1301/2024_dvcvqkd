import unittest
from unittest.mock import patch
from scripts import export_theta10_D55_ao_scientific_results as export


class ScientificExport(unittest.TestCase):
    def test_saved_data_counts_maxima_and_genuine_history(self):
        with patch.object(export.ao, 'evaluate_candidate', export.audit.forbidden), \
             patch.object(export.ao.ExactMBEvaluator, 'source_moments', export.audit.forbidden), \
             patch.object(export.sweep, 'make_channel', export.audit.forbidden):
            data = export.analyze()
        self.assertEqual(len(data['history']), 283)
        self.assertEqual(sum(r['AO_matches_catalog'] for r in data['best']), 26)
        ref = data['rankings'][export.REF][0]
        self.assertEqual((ref['nu_raw'], ref['V_A'], ref['SKR']), (.165, 5.5, .07798099387393764))
        low = next(r for r in data['terminals'] if r['L_km'] == export.REF and r['start_id'] == 'nu_0.8')
        self.assertEqual(low['status'], 'UNRESOLVED_BOUNDARY')
        self.assertEqual((low['terminal_nu'], low['terminal_V_A']), (.4, 3.))

    def test_positive_plot_filter_keeps_exact_values_and_breaks(self):
        points = [{'distance_km': 25., 'K': .0004680449196579062},
                  {'distance_km': 25.5, 'K': -1.}, {'distance_km': 26., 'K': 0.},
                  {'distance_km': 27., 'K': .1}]
        self.assertEqual(list(export.positive_runs(points)), [[(25., .0004680449196579062)], [(27., .1)]])


if __name__ == '__main__':unittest.main()
