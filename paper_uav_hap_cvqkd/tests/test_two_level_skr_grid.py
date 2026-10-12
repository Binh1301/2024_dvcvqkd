"""Grid/exact-data integrity checks,never a scientific evaluator call."""
import math
import unittest
from unittest.mock import patch
from scripts import build_theta10_D55_two_level_skr_grid as grid


class TwoLevelGridTests(unittest.TestCase):
    def test_grid_identity_overlap_and_best_included(self):
        rows=grid.grid_specification()
        self.assertEqual(len(rows),51)
        self.assertEqual(len({grid.audit.pair(r) for r in rows}),51)
        self.assertEqual(sum(r['Grid_A'] for r in rows),30)
        self.assertEqual(sum(r['Grid_B'] for r in rows),25)
        self.assertEqual([(r['nu_raw'],r['V_A']) for r in rows if r['membership']=='A+B'],
                         [(.15,5.),(.15,6.5),(.175,5.),(.175,6.5)])
        self.assertTrue(any((r['nu_raw'],r['V_A'])==(.165,5.5) and r['Grid_B'] for r in rows))

    def test_current_exact_coverage_and_matrix_mask(self):
        entries=grid.audit.read(grid.audit.INPUT/'objective_checkpoint.json')
        ref=next(e for e in entries if e['L_km']==grid.audit.REF)
        bank={grid.audit.pair(r):r for r in ref['rows']}
        spec=grid.grid_specification();coverage=grid.grid_coverage(spec,bank)
        self.assertEqual(sum(r['status']=='EXACT_CACHED' for r in coverage),20)
        self.assertEqual(sum(r['status']=='MISSING_SOURCE' for r in coverage),31)
        self.assertEqual(sum(r['Grid_A'] and r['status']=='EXACT_CACHED' for r in coverage),11)
        self.assertEqual(sum(r['Grid_B'] and r['status']=='EXACT_CACHED' for r in coverage),12)
        keys={grid.audit.pair(r) for r in spec}
        self.assertEqual(sum(grid.audit.pair(r) in keys for e in entries for r in e['rows']),520)
        reference=[r for r in grid.export.classify(ref['rows'],ref['L_km']) if grid.audit.pair(r) in keys]
        self.assertEqual(sum(r['near_optimal']=='YES' for r in reference),1)
        cells=grid.matrix_cells(spec,reference)
        self.assertEqual(len(cells),72)
        self.assertEqual(sum(r['status']=='NOT_IN_PROPOSED_GRID' for r in cells),21)
        self.assertEqual(sum(r['SKR']!='' for r in cells),20)
        self.assertTrue(all(r['C']==r['w']=='' for r in coverage if r['status']=='MISSING_SOURCE'))
        self.assertTrue(all(r['SKR']=='' for r in cells if r['status']!='EXACT_CACHED'))

    def test_no_approximate_parameter_match(self):
        spec=grid.grid_specification();row=next(r for r in spec if (r['nu_raw'],r['V_A'])==(.165,5.5))
        almost=dict(row,V_A=math.nextafter(5.5,math.inf))
        coverage=grid.grid_coverage([row],{grid.audit.pair(almost):{'source_path':'MUST_NOT_READ'}})
        self.assertEqual(coverage[0]['status'],'MISSING_SOURCE')

    def test_invalid_point_and_no_overwrite(self):
        row=dict(nu_raw=-.1,V_A=5.)
        self.assertEqual(grid.grid_coverage([row],{})[0]['status'],'INVALID')
        with patch.object(grid,'OUT',grid.export.OUT),patch.object(grid.audit,'load_verified') as load:
            with self.assertRaises(SystemExit):grid.main()
            load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
