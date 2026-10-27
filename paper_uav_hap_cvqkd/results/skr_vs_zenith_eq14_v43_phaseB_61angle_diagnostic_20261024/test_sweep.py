"""Focused boundary checks; never calculate source moments or replay saved rates."""
import importlib.util
from pathlib import Path
import unittest

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_sweep_under_test',OUT/'sweep.py')
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


class SweepChecks(unittest.TestCase):
    def test_saved_raw_rates_rank_numerically(self):
        r = sweep.numeric([dict(K_raw='-0.009',I_AB='0.2'),dict(K_raw='-0.01',I_AB='0.1')])
        self.assertEqual(max(r,key=lambda x:x['K_raw'])['K_raw'],-.009)
        self.assertIsNone(sweep.numeric([dict(K_raw='')])[0]['K_raw'])

    def test_nested_selection_preserves_negatives_and_failed_candidates(self):
        records = [dict(zenith_deg=0,family=f,ensemble_hash=h,K_raw=k,
            numerical_status=status,source_evidence_class='INSUFFICIENT_EVIDENCE')
            for f,h,k,status in [('Uniform','u',-.02,sweep.PASS),('MB','fixed',-.01,sweep.PASS),
                ('MB','bad',None,'FAILED_NUMERICAL_VALIDATION')]]
        selected = sweep.nine.select(records,dict(fixed_MB=dict(ensemble_hash='fixed')))
        self.assertEqual([r['K_raw'] for r in selected],[-.02,-.01,-.01])
        self.assertEqual(selected[2]['available_scheme_sources'],3)
        self.assertEqual(selected[2]['valid_scheme_sources'],2)
        self.assertEqual(len(records),3)

    def test_grid_pool_and_canonical_function_identity(self):
        task = sweep.read(OUT/'protocol.json')
        physical = sweep.read(sweep.ROOT/task['physical_protocol_path'])
        original = sweep.read(sweep.ROOT/task['grid_origin'])
        self.assertEqual(task['angles_deg'],original['angles_deg'])
        self.assertTrue(set(task['previous_angles_deg']) <= set(task['angles_deg']))
        sources = list(sweep.source_pool(physical))
        self.assertEqual(len(sources),212)
        self.assertEqual(sum(s['family']=='Uniform' for s in sources),33)
        self.assertFalse(any(s['nu_raw']==0 and s['VA_hex']==task['missing_Uniform_VA_hex'] for s in sources))
        self.assertIs(sweep.evaluator.components,sweep.canonical.components)
        self.assertIs(sweep.evaluator.correlation_eq14,sweep.canonical.correlation_eq14)


if __name__=='__main__': unittest.main(verbosity=2)
