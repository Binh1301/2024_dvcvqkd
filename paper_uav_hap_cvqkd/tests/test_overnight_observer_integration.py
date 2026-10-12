import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import mpmath
from scripts.overnight_source_observer_v2 import run_observed


class PrecisionMetadataIntegration(unittest.TestCase):
    def test_real_module_context_all_wrappers_dummy_operations_only(self):
        calls=[];worker=types.SimpleNamespace(mp=mpmath)
        def sectors(p,z):calls.append(('sectors',p,z));return 'GRAM_DUMMY'
        def solve(a,b):calls.append(('solve',a,b));return 'SOLVE_DUMMY'
        def eigen(g):calls.append(('eigen',g));return 'EIGEN_DUMMY'
        def row(p,z,digits):
            with mpmath.workdps(digits):
                result=(worker._sectors(p,z),worker.mp.eighe('GRAM_DUMMY'),worker._lu_solve_matrix('A','B'))
            return result
        worker._sectors=sectors;worker._lu_solve_matrix=solve;worker._row=row
        worker.main=lambda:[worker._row('P','Z',d) for d in (1050,1250,1450)]
        original_precision=mpmath.mp.dps
        with tempfile.TemporaryDirectory() as directory,patch.object(mpmath,'eighe',eigen):
            prefix=Path(directory)/'dummy'
            result=run_observed(worker,prefix)
            data=json.loads(Path(str(prefix)+'_stage_snapshot.json').read_text())
            self.assertEqual(result,[('GRAM_DUMMY','EIGEN_DUMMY','SOLVE_DUMMY')]*3)
            self.assertEqual(len(calls),9)
            self.assertEqual([r['digits'] for r in data['completed_stages'] if r['name']=='Gram_sector_construction'],[1050,1250,1450])
            self.assertTrue(all(r['completed_normally'] for r in data['completed_stages']))
            self.assertEqual(worker._row,row);self.assertEqual(worker._sectors,sectors)
            self.assertEqual(worker._lu_solve_matrix,solve);self.assertEqual(worker.mp.eighe,eigen)
            self.assertEqual(mpmath.mp.dps,original_precision)

    def test_failure_restores_hooks_without_retry(self):
        calls=[];worker=types.SimpleNamespace(mp=mpmath)
        def row(*args):calls.append(args);raise ValueError('dummy original failure')
        worker._row=row;worker._sectors=lambda *a:None;worker._lu_solve_matrix=lambda *a:None
        worker.main=lambda:worker._row('P','Z',1050)
        eigen=mpmath.eighe
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'dummy original failure'):
                run_observed(worker,Path(directory)/'dummy')
        self.assertEqual(calls,[('P','Z',1050)])
        self.assertIs(worker._row,row);self.assertIs(mpmath.eighe,eigen)


if __name__=='__main__':unittest.main()
