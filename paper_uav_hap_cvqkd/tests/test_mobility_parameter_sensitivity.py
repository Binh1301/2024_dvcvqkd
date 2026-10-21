"""Small deterministic mobility fixtures; no new meteorological realizations."""
from copy import deepcopy
import itertools
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import run_mobility_parameter_sensitivity as m


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.config=m.read_json(ROOT/'configs/mobility_parameter_sensitivity.json')
        self.grid=np.array([(x,y) for y in range(50,1000,100) for x in range(50,1000,100)],dtype=float)
        self.p=np.array([[0.,0.],[100.,0.],[200.,0.]])
        self.S=np.array([[.3,0,.7,.1],[.5,.8,0,.4],[0,.7,.6,.9]])
        self.C=self.S==0

    def test_approved_config(self):m.validate_config(self.config)

    def test_reject_stage_b(self):
        for key,value in [('stage','B'),('stage_b_allowed',True),('new_cloud_generation_allowed',True),
                          ('new_physical_skr_allowed',True),('probabilities',[.1,.2,.3,.4,.6,.8])]:
            c=deepcopy(self.config);c[key]=value
            with self.assertRaises(ValueError):m.validate_config(c)

    def test_lambda_cannot_rescale(self):
        c=deepcopy(self.config);c['lambda_values'][1]*=2
        with self.assertRaises(ValueError):m.validate_config(c)

    def test_output_namespace_locked(self):
        c=deepcopy(self.config);c['output_directory']='results/manuscript_mobility_p1_p2_p3_20261019'
        with self.assertRaises(ValueError):m.validate_config(c)

    def test_nested_spatial_design(self):
        order=m.nested_order(self.grid)
        self.assertEqual(order[:4],[0,9,90,99]);self.assertEqual(sorted(order),list(range(100)))
        previous=set()
        for size in self.config['candidate_counts']:
            current=set(order[:size]);self.assertTrue(previous<=current);previous=current
            q=[int(self.grid[j,0]>=500)+2*int(self.grid[j,1]>=500) for j in current]
            counts=np.bincount(q,minlength=4);self.assertLessEqual(counts.max()-counts.min(),1)
        self.assertEqual(order,m.nested_order(self.grid.copy()))

    def test_subset_coordinates_cannot_change(self):
        p=self.grid.copy();p[0,0]+=1
        with self.assertRaises(ValueError):m.nested_order(p)

    def test_all_axes_share_one_base(self):
        scenarios=m.read_json(ROOT/'results/binary_cloud_skr_20261015/cloud_scenarios.json')
        cases,members,_=m.make_cases(self.config,self.grid,scenarios)
        self.assertEqual(len(cases),26);self.assertEqual(len(members),30)
        self.assertEqual(sum(r['case_id']=='base' for r in members),5)
        self.assertEqual({r['scenario_id'] for r in cases},{0,2,3,4,5,8,9,10,11})

    def test_missing_scenario_fails_closed(self):
        scenarios=m.read_json(ROOT/'results/binary_cloud_skr_20261015/cloud_scenarios.json')
        with self.assertRaises(ValueError):m.make_cases(self.config,self.grid,[s for s in scenarios if s['scenario_id']!=8])

    def test_dp_matches_exhaustive(self):
        for lam in (0.,.5,4.):
            for speed in (0.,5.,10.):
                result,paths=m.solve(self.S,self.C,self.p,lam,speed)
                scores=[]
                for trial in itertools.product(range(3),repeat=4):
                    legs=np.linalg.norm(np.diff(self.p[list(trial)],axis=0),axis=1)
                    if np.all(legs<=speed*20):scores.append(float(self.S[list(trial),np.arange(4)].mean())-lam*legs.sum()/1000)
                self.assertAlmostEqual(result[2]['U'],max(scores),places=12)
                self.assertAlmostEqual(result[2]['U'],m.literal_dp(self.S,self.p,lam,speed),places=12)

    def test_zero_speed_dp_is_stationary_but_greedy_can_differ(self):
        S=np.array([[1.,0,0,0],[0,.8,.8,.8]])
        result,paths=m.solve(S,S==0,self.p[:2],.1,0.)
        self.assertEqual(result[2]['D'],0);self.assertEqual(result[2]['U'],result[0]['U'])
        self.assertLess(result[1]['U'],result[0]['U'])

    def test_single_slot(self):
        result,paths=m.solve(self.S[:,:1],self.C[:,:1],self.p,100.,0.)
        self.assertTrue(all(r['K']==.5 and r['D']==0 and r['U']==.5 for r in result))

    def test_greedy_uses_Nt_lambda(self):
        S=np.array([[.0001,0],[0,.0001]])
        result,paths=m.solve(S,S==0,self.p[:2],.0006,5.)
        self.assertEqual(paths[1].tolist(),[0,0])

    def test_greedy_current_slot_only(self):
        S=np.c_[self.S,np.array([.6,.2,.4])]
        future=S.copy();future[:,3:]=np.array([[9,9],[0,0],[0,0]])
        a=m.solve(S,S==0,self.p,.3,5.)[1][1]
        b=m.solve(future,future==0,self.p,.3,5.)[1][1]
        np.testing.assert_array_equal(a[:3],b[:3])

    def test_prefix_is_reoptimized(self):
        S=np.array([[1.,1,0,0],[0,0,2,2]])
        short=m.solve(S[:,:2],S[:,:2]==0,self.p[:2],0.,0.)[1][2]
        long=m.solve(S,S==0,self.p[:2],0.,0.)[1][2]
        self.assertNotEqual(short[0],long[0])

    def test_speed_and_subset_objective_monotonicity(self):
        previous=-float('inf')
        for speed in (0.,2.5,5.,10.):
            score=m.solve(self.S,self.C,self.p,.5,speed)[0][2]['U']
            self.assertGreaterEqual(score+1e-12,previous);previous=score
        small=m.solve(self.S[[0,2]],self.C[[0,2]],self.p[[0,2]],.5,5.)[0][2]['U']
        large=m.solve(self.S,self.C,self.p,.5,5.)[0][2]['U']
        self.assertGreaterEqual(large+1e-12,small)

    def test_complete_blockage_and_no_engineering_threshold(self):
        zero=np.zeros((3,4));blocked=np.ones_like(zero,dtype=bool)
        result,_=m.solve(zero,blocked,self.p,.1,5)
        self.assertTrue(all(r['K']==0 and r['D']==0 and r['availability']==0 for r in result))
        tiny=np.full((3,4),1e-8)
        result,_=m.solve(tiny,np.zeros_like(blocked),self.p,0,5)
        self.assertTrue(all(r['availability']==1 for r in result))

    def test_path_metrics_reject_infeasible_and_reconstruct_objective(self):
        with self.assertRaises(ValueError):m.path_metrics(self.S,self.C,self.p,np.array([0,2,0,2]),0.,5.)
        result=m.path_metrics(self.S,self.C,self.p,np.array([0,1,1,2]),.5,5.)
        self.assertAlmostEqual(result['D'],200.);self.assertAlmostEqual(result['U'],result['K']-.1)

    def test_no_cloud_or_physical_evaluator_calls(self):
        with patch('src.binary_cloud.generate_cloud',side_effect=AssertionError('No cloud generation')) as cloud, \
             patch('src.manuscript_mobility.evaluate_source',side_effect=AssertionError('No SKR')) as skr, \
             patch('src.manuscript_mobility.channel_at_angle',side_effect=AssertionError('No channel')) as channel:
            m.solve(self.S,self.C,self.p,.1,5.)
            cloud.assert_not_called();skr.assert_not_called();channel.assert_not_called()


if __name__=='__main__':unittest.main()
