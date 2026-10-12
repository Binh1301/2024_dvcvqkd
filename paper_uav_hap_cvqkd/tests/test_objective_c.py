"""Budget, identity, request routing and conservative convergence; no AP."""
import unittest
from unittest.mock import patch
from scripts import run_theta10_D55_objective_c as c


class ObjectiveCTests(unittest.TestCase):
    def test_limits_and_original_algorithms(self):
        self.assertEqual((c.TOTAL,c.RESERVE,c.MAX_AP,c.STAGE1_AP),(129600.,1800.,36,12))
        self.assertEqual(c.STARTS,[(.165,5.5),(.16,6.),(.17,5.),(.15,6.5),(.175,4.5)])
        self.assertEqual((c.b.saved.ao.MAX_AO_ITERATIONS,c.b.saved.ao.K_TOLERANCE,c.b.saved.ao.PARAMETER_TOLERANCE),(6,1e-8,1e-6))
        self.assertEqual(c.b.INTERNAL,3600.)

    def test_no_automatic_execution(self):
        with patch.object(c,'preflight') as prep:
            with self.assertRaises(SystemExit):c.run()
            prep.assert_not_called()

    def test_convergence_requires_two_closed_iterations(self):
        iteration=dict(delta_K=0.,K_before=.08,V_A_search_status='NUMERICALLY_CLOSED_LOCAL_BRACKET',
            nu_search_status='NUMERICALLY_CLOSED_LOCAL_BRACKET')
        run=dict(status='CONVERGED_NUMERICALLY',iterations=[iteration],warnings=[])
        self.assertEqual(c.convergence(run),'APPARENTLY_STABLE_BUT_UNRESOLVED')
        run['iterations']=[iteration,iteration.copy()]
        self.assertEqual(c.convergence(run),'NUMERICALLY_CONVERGED_ON_TESTED_MESH')
        run['iterations'][1]['nu_search_status']='BRACKETED_EXACT_CATALOG_SOURCE_MISSING'
        self.assertEqual(c.convergence(run),'APPARENTLY_STABLE_BUT_UNRESOLVED')

    def test_requests_skip_cached_failed_and_attempted_binary64(self):
        def request(n,v):return dict(nu_raw=n,V_A=v,L_km=21.9393102292,coordinate='V_A',
            coordinate_best_K=.08,current_catalog_K=.08)
        analysis=dict(requests=[request(.165,5.4984375),request(.165,5.503125),request(.16375,5.5),request(.17,5.25)])
        state=dict(sources=[request(.165,5.503125)],historical_failed_pairs=[c.b.saved.pair(.16375,5.5)])
        bank={c.b.saved.pair(.165,5.4984375):{}}
        chosen=c.choose_request(analysis,state,bank)
        self.assertEqual((chosen['nu_raw'],chosen['V_A']),(.17,5.25))
        bank[c.b.saved.pair(.17,5.25)]={}
        self.assertIsNone(c.choose_request(analysis,state,bank))

    def test_baseline_all_182_objectives_saved(self):
        entries=c.READ(c.BASE/'objective_checkpoint.json')
        self.assertEqual(sum(len(e['rows']) for e in entries),4732)
        self.assertTrue(all(len({c.b.saved.pair(r['nu_raw'],r['V_A']) for r in e['rows']})==182 for e in entries))


if __name__=='__main__':unittest.main()
