"""Geometry, cached-source regression, brute-force DP and cache isolation."""
import copy
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
from scripts import run_ao_effective_channel_no_fading_noise_reference as existing
from scripts.run_mobility_skr_experiment import CONFIG, DEFAULT, validate_settings, scenario
from src.mobility_skr import (load_candidates, channel_state, scientific_identity,
    objective_key, ExactStateCache)
from src.uav_mobility import (candidate_grid, path_intersections, moving_cloud,
    link_geometry, cloud_transmittance, best_stationary, optimize_trajectory, usable_skr)


class MobilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.settings=existing.read_json(CONFIG)
        cls.manifest=existing.read_json(DEFAULT/"startup_manifest.json")
        cls.candidates,cls.config,_=load_candidates(cls.settings,cls.manifest["protected_hashes"])
        cls.positions=validate_settings(cls.settings)
        cls.reference=cls.positions[cls.settings["geometry"]["reference_position_index"]]
        cls.state=channel_state(cls.settings,cls.reference,False)
        cls.candidate=next(c for c in cls.candidates if c["nu_raw"]==.17 and c["V_A"]==5.046875)
        cls.score=existing.evaluate_authenticated(cls.candidate,cls.state["moments"],cls.config,cls.manifest["protected_hashes"])

    def test_100_cell_centers_and_reference(self):
        self.assertEqual(self.positions.shape,(100,2))
        np.testing.assert_array_equal(self.positions[0],[50,50])
        np.testing.assert_array_equal(self.positions[-1],[950,950])
        np.testing.assert_array_equal(self.reference,[450,450])
        self.assertAlmostEqual(self.state["distance_m"]/1000,21.9393102292,places=10)
        other=channel_state(self.settings,self.positions[-1],False)
        self.assertNotEqual(self.state["distance_m"],other["distance_m"])
        self.assertNotEqual(self.state["moments"]["mean_sqrt_eta"],other["moments"]["mean_sqrt_eta"])

    def test_cloud_intersections_and_altitudes(self):
        points=np.array([[0.,0.],[10.,0.]])
        np.testing.assert_array_equal(path_intersections(points,[10.,10.],20.,0.,10.),[[5.,5.],[10.,5.]])
        np.testing.assert_array_equal(path_intersections(points,[10.,10.],20.,0.,5.),[[2.5,2.5],[10.,2.5]])
        for height in (0.,20.,21.):
            with self.assertRaises(ValueError):path_intersections(points,[10.,10.],20.,0.,height)

    def test_cloud_cover_outside_boundary_and_motion(self):
        blocked,centers=moving_cloud([[0.,0.],[1.,0.],[1.01,0.]], [0.,3.], [0.,0.], [1.,0.],1.)
        np.testing.assert_array_equal(blocked[:,0],[True,True,False])
        np.testing.assert_array_equal(blocked[:,1],[False,False,False])
        np.testing.assert_array_equal(centers,[[0.,0.],[3.,0.]])

    def test_no_cloud_preserves_moments_and_skr(self):
        settings=copy.deepcopy(self.settings);settings["cloud"]["attenuation_db"]=0.
        clear=channel_state(settings,self.reference,False)
        blocked=channel_state(settings,self.reference,True)
        self.assertEqual(clear["moments"],blocked["moments"])
        self.assertEqual(clear["cloud_raw_channel"],blocked["cloud_raw_channel"])
        result=existing.evaluate_authenticated(self.candidate,blocked["moments"],self.config,self.manifest["protected_hashes"])
        self.assertEqual(result["I_AB"],self.score["I_AB"])
        self.assertEqual(result["chi_BE"],self.score["chi_BE"])
        self.assertEqual(result["SKR"],self.score["SKR"])

    def test_cloud_applied_once_before_conditioning(self):
        blocked=channel_state(self.settings,self.reference,True)
        self.assertAlmostEqual(blocked["cloud_raw_channel"]["eta_atm"],self.state["clear_raw_channel"]["eta_atm"]*.1,places=15)
        self.assertEqual(blocked["cloud_raw_channel"]["P0"],self.state["clear_raw_channel"]["P0"])
        m=blocked["moments"]
        self.assertAlmostEqual(m["physical_probability_mass"],1.,places=10)
        self.assertEqual(m["mean_eta_xi_total"],2+(.0186-1)*m["mean_eta"])
        self.assertNotEqual(m["mean_eta_xi_total"],.1*self.state["moments"]["mean_eta_xi_total"])
        self.assertLess(m["mean_sqrt_eta"],self.state["moments"]["mean_sqrt_eta"])

    def test_exact_reference_skr_and_source_catalog(self):
        self.assertEqual(len(self.candidates),197)
        self.assertAlmostEqual(self.score["SKR"],.0587348598790054,places=12)
        self.assertAlmostEqual(self.score["T_eff"],.16092029098192165,places=12)
        self.assertAlmostEqual(self.score["I_AB"],.4910480331304301,places=12)
        self.assertAlmostEqual(self.score["chi_BE"],.4077607715949032,places=12)
        self.assertEqual(self.score["C"],2.9818069279923307)
        self.assertEqual(self.score["w"],6.190945650452507e-7)
        self.assertEqual(self.score["numerical_repairs"],[])

    def test_stationary_maximum_on_small_grid(self):
        raw=np.array([[1.,0.,0.],[.6,.6,.6],[-1.,.4,.5]])
        chosen,means=best_stationary(raw)
        self.assertEqual(chosen,1);self.assertAlmostEqual(means[chosen],.6)

    def test_dp_matches_exhaustive_three_positions_four_slots(self):
        points=np.array([[0.,0.],[100.,0.],[200.,0.]])
        rates=np.array([[.8,.1,.2,.4],[.2,.7,.3,.1],[.1,.1,.9,.8]])
        for penalty in (0.,.2):
            result=optimize_trajectory(rates,points,slot_duration_s=10.,max_speed_m_per_s=10.,
                penalty_bits_per_use=penalty,reference_distance_m=100.)
            values=[]
            for path in itertools.product(range(3),repeat=4):
                legs=np.linalg.norm(np.diff(points[list(path)],axis=0),axis=1)
                if (legs<=100).all():values.append(float(rates[list(path),np.arange(4)].mean())-penalty*float(legs.sum())/100)
            self.assertAlmostEqual(result["penalized_objective"],max(values),places=12)
            self.assertLessEqual(result["max_transition_m"],100.)

    def test_speed_zero_reduces_to_stationary_solution(self):
        rates=np.array([[.4,.1,.5],[.2,.8,.2],[0.,.1,.1]])
        result=optimize_trajectory(rates,[[0,0],[100,0],[200,0]],slot_duration_s=20.,max_speed_m_per_s=0.,
            penalty_bits_per_use=.01,reference_distance_m=1000.)
        self.assertEqual(len(set(result["path"])),1)
        self.assertAlmostEqual(result["average_skr"],rates.mean(axis=1).max(),places=12)
        self.assertEqual(result["total_flight_distance_m"],0.)

    def test_optimization_dominance_and_penalty_flight_monotonicity(self):
        rates=np.array([[.8,.1,.2,.4],[.2,.7,.3,.1],[.1,.1,.9,.8]])
        points=[[0,0],[100,0],[200,0]];stationary=float(rates.mean(axis=1).max());flights=[]
        for penalty in (0.,.01,.1,1.):
            result=optimize_trajectory(rates,points,slot_duration_s=20.,max_speed_m_per_s=15.,
                penalty_bits_per_use=penalty,reference_distance_m=100.)
            self.assertGreaterEqual(result["penalized_objective"]+1e-12,stationary)
            if penalty==0:self.assertGreaterEqual(result["average_skr"]+1e-12,stationary)
            flights.append(result["total_flight_distance_m"])
        self.assertEqual(flights,sorted(flights,reverse=True))

    def test_signed_negative_skr_preserved_and_invalid_input_rejected(self):
        raw=np.array([[-.1,.2],[.3,-.4]])
        np.testing.assert_array_equal(usable_skr(raw),[[0.,.2],[.3,0.]])
        self.assertEqual(raw[0,0],-.1)
        for bad in ([[float('nan')]],[[float('inf')]],[]):
            with self.assertRaises(ValueError):usable_skr(bad)
        with self.assertRaises(ValueError):cloud_transmittance(-1.,True)

    def test_cache_keys_bind_channel_ensemble_and_scientific_code(self):
        identity=scientific_identity(self.settings,self.config)
        digest=existing.digest(existing.ROOT/self.candidate["source_path"])
        key=objective_key(identity,self.state,self.candidate,digest)
        blocked=channel_state(self.settings,self.reference,True)
        self.assertNotEqual(key,objective_key(identity,blocked,self.candidate,digest))
        changed=dict(identity,security="different-target")
        self.assertNotEqual(key,objective_key(changed,self.state,self.candidate,digest))
        changed_source=dict(self.candidate,V_A=self.candidate["V_A"]+1e-14)
        self.assertNotEqual(key,objective_key(identity,self.state,changed_source,digest))
        self.assertNotEqual(key,objective_key(identity,self.state,self.candidate,"different-hash"))

    def test_journal_reuses_identical_state_and_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"cache.jsonl"
            with patch('src.mobility_skr.existing.evaluate_authenticated',return_value=self.score) as evaluator:
                first=ExactStateCache(path,dict(test="same-state"),self.manifest["protected_hashes"],self.config)
                key,row=first.evaluate(self.candidate,self.state)
                second=ExactStateCache(path,dict(test="same-state"),self.manifest["protected_hashes"],self.config)
                other_key,other_row=second.evaluate(self.candidate,self.state)
                self.assertEqual(evaluator.call_count,1);self.assertEqual(row,other_row);self.assertEqual(key,other_key)
                self.assertEqual(second.hits,1)
            record=json.loads(path.read_text());record["row"]["I_AB"]+=.1
            path.write_text(json.dumps(record)+'\n')
            with self.assertRaises(ValueError):ExactStateCache(path,dict(test="same-state"),self.manifest["protected_hashes"],self.config)

    def test_cloud_velocity_affects_blockage_not_channel_statistics(self):
        intersections=path_intersections(self.positions,self.settings["geometry"]["hap_horizontal_m"],20000,1000,5000)
        times=np.arange(30)*20
        first,_=moving_cloud(intersections,times,self.settings["cloud"]["initial_center_m"],[3,0],420)
        second,_=moving_cloud(intersections,times,self.settings["cloud"]["initial_center_m"],[6,0],420)
        self.assertTrue(first.any() and (~first).any())
        self.assertFalse(np.array_equal(first,second))
        self.assertFalse(first[44,0]);self.assertFalse(first[44,-1])
        self.assertTrue(first[44].any())
        self.assertFalse(first[:,-1].any())

    def test_noise_and_double_cloud_conventions_fail_closed(self):
        settings=copy.deepcopy(self.settings);settings["channel"]["R"]=.7
        with self.assertRaises(ValueError):channel_state(settings,self.reference,False)
        settings=copy.deepcopy(self.settings);settings["channel"]["clear_atmosphere_excludes_added_cloud_loss"]=False
        with self.assertRaises(ValueError):channel_state(settings,self.reference,False)


if __name__=="__main__":unittest.main()
