"""Stage B adapter boundaries and paired cloud design; no quantum calculations."""
import copy
from pathlib import Path
import unittest

import numpy as np
from scripts.run_mobility_cloud_sensitivity import cases_for, usable_rates, validate
from scripts.run_mobility_parameter_sensitivity import read_json, solve
from src.binary_cloud import generate_cloud

ROOT=Path(__file__).resolve().parents[1]


class CloudSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.c=read_json(ROOT/'configs/mobility_parameter_sensitivity_stage_b.json')
        self.archive=read_json(ROOT/'results/binary_cloud_skr_20261015/cloud_scenarios.json')

    def test_exact_design(self):
        validate(self.c)
        cases,members=cases_for(self.c,self.archive)
        self.assertEqual((len(cases),len(members)),(16,18))
        self.assertEqual(sum(x['archive_id'] is None for x in cases),3)
        self.assertEqual(sum(x['stage_a_case_id'] is not None for x in cases),9)

    def test_reject_scope_changes(self):
        for field,value in [('stage','A'),('new_physical_skr_allowed',True),('probabilities',[.1,.9]),('cloud_seed',1),('lambda_values',[0,1e-5])]:
            with self.subTest(field=field):
                c=copy.deepcopy(self.c);c[field]=value
                with self.assertRaises(ValueError):validate(c)

    def test_temporal_grid_from_archive(self):
        cases,_=cases_for(self.c,self.archive)
        temporal=[x for x in cases if x['case_id'].startswith('temporal')]
        self.assertEqual(len(temporal),4)
        self.assertTrue(all(x['archive_id'] is not None and x['stage_a_case_id'] is None for x in temporal))

    def test_missing_archive_fails(self):
        with self.assertRaises(KeyError):cases_for(self.c,[])

    def test_current_p1_not_old_optical_rates(self):
        C=np.array([[True,False],[False,True]])
        np.testing.assert_array_equal(usable_rates(C,np.array([1e-4,2e-4])),[[0,1e-4],[2e-4,0]])
        np.testing.assert_array_equal(usable_rates(np.ones((2,3),dtype=bool),np.array([1e-4,2e-4])),np.zeros((2,3)))

    def test_invalid_inputs(self):
        for C,K in [(np.zeros((2,3)),[1,2]),(np.zeros((2,3),dtype=bool),[1]),(np.zeros((2,3),dtype=bool),[1,-1]),(np.zeros((2,3),dtype=bool),[1,np.nan])]:
            with self.assertRaises(ValueError):usable_rates(C,K)

    def test_seed_replay_and_nested_probabilities(self):
        xy=np.array([[0,0],[100,0],[0,100]])
        previous=np.zeros((3,30),dtype=bool)
        for p in self.c['probabilities']:
            C=generate_cloud(xy,30,p,250,.9,20261015,99)
            np.testing.assert_array_equal(C,generate_cloud(xy,30,p,250,.9,20261015,99))
            self.assertTrue(np.all(previous<=C));previous=C

    def test_common_first_slot_across_temporal_rho(self):
        xy=np.array([[0,0],[100,0],[0,100]])
        first=[generate_cloud(xy,30,.4,250,rho,20261015,1)[:,0] for rho in self.c['temporal_rhos']]
        self.assertTrue(all(np.array_equal(first[0],v) for v in first))

    def test_clear_and_blocked_mobility_controls(self):
        xy=np.array([[0,0],[100,0],[200,0]])
        for blocked in (True,False):
            C=np.full((3,4),blocked);K=np.array([1e-4,2e-4,3e-4])
            for lam in self.c['lambda_values']:
                metrics,_=solve(usable_rates(C,K),C,xy,lam,15)
                self.assertTrue(all(r['D']==0 and r['K']==(0 if blocked else 3e-4) for r in metrics))


if __name__=='__main__':unittest.main()
