import copy
import hashlib
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import torch
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.run_binary_cloud_skr_experiment import DEFAULT,CONFIG,bind_inputs
from src.binary_cloud_skr import (load_clear_bank,validate_settings,slot_table,mission_results,
    select_winner,cloud_scenarios,verify_alias,validate_result,covariance_check)
from src.uav_mobility import optimize_trajectory,best_stationary


def synthetic_winners(values):
    return [dict(K_star_raw=v,K_star=max(0.,v),nu_raw=.1,V_A=2.,ensemble_hash=str(j),objective_key=str(j)) for j,v in enumerate(values)]


def small_settings():
    return dict(geometry=dict(reference_position_index=0),mission=dict(slot_duration_s=10.,max_speed_m_per_s=10.),
        optimization=dict(positive_lambda_bits_per_use=.01,reference_distance_m=100.,K_min_bits_per_use=.1))


class BinaryOptimizationTests(unittest.TestCase):
    def test_blocked_short_circuit_and_signed_rates(self):
        blocked=np.array([[True,False],[False,True]])
        with patch('src.binary_cloud_skr.saved.evaluate_authenticated',side_effect=AssertionError('No QKD call allowed')):
            table=slot_table([.4,-.2],blocked)
            np.testing.assert_array_equal(table,[[0.,.4],[0.,0.]])
            summary,series=mission_results(small_settings(),np.array([[0.,0.],[100.,0.]]),synthetic_winners([.4,-.2]),blocked)
        for r in series:
            if r['blocked']:self.assertEqual(r['usable_skr'],0.);self.assertFalse(r['source_active'])

    def test_threshold_equality_and_objective_independence(self):
        settings=small_settings();points=np.array([[0.,0.],[100.,0.]])
        cloud=np.array([[False,True,False],[True,False,True]])
        first,series=mission_results(settings,points,synthetic_winners([.1,.3]),cloud)
        self.assertTrue(next(r for r in series if r['scheme']=='S1' and r['slot']==1)['available'])
        settings['optimization']['K_min_bits_per_use']=.4
        second,other=mission_results(settings,points,synthetic_winners([.1,.3]),cloud)
        self.assertTrue(all(r['availability']==0 for r in second))
        self.assertEqual([r['position_index'] for r in series],[r['position_index'] for r in other])
        self.assertEqual([r['average_skr_bits_per_use'] for r in first],[r['average_skr_bits_per_use'] for r in second])

    def test_no_cloud_and_all_cloud(self):
        points=np.array([[0.,0.],[100.,0.]])
        for blocked in (False,True):
            c=np.full((2,4),blocked,dtype=bool)
            summary,series=mission_results(small_settings(),points,synthetic_winners([.2,.3]),c)
            if blocked:
                self.assertTrue(all(r['average_skr_bits_per_use']==0 for r in summary))
                self.assertTrue(all(r['improvement_vs_reference_percent'] is None for r in summary))
            else:
                self.assertAlmostEqual(summary[1]['average_skr_bits_per_use'],.3)
                self.assertTrue(all(r['available']==(not r['blocked']) for r in series))
                self.assertEqual(summary[3]['total_flight_distance_m'],0.)

    def test_p1_max_and_deterministic_ties(self):
        rows=[dict(SKR=k,nu_raw=nu,V_A=v,ensemble_hash=str(n)) for n,(k,nu,v) in enumerate([(-.2,.2,2),(-.1,.2,2),(-.1,.1,3)])]
        self.assertEqual(select_winner(rows),rows[2])
        with self.assertRaises(ValueError):select_winner([])

    def test_p2_and_dp_exhaustive(self):
        points=np.array([[0.,0.],[100.,0.],[200.,0.]])
        rates=np.array([[.8,.1,.2,.4],[.2,.7,.3,.1],[.1,.1,.9,.8]])
        stationary,means=best_stationary(rates)
        self.assertEqual(stationary,int(np.argmax(rates.mean(axis=1))))
        flights=[]
        for penalty in (0.,.01,.2,1.):
            result=optimize_trajectory(rates,points,slot_duration_s=10.,max_speed_m_per_s=10.,penalty_bits_per_use=penalty,reference_distance_m=100.)
            exhaustive=[]
            for path in itertools.product(range(3),repeat=4):
                legs=np.linalg.norm(np.diff(points[list(path)],axis=0),axis=1)
                if (legs<=100.).all():exhaustive.append(rates[list(path),np.arange(4)].mean()-penalty*legs.sum()/100.)
            self.assertAlmostEqual(result['penalized_objective'],max(exhaustive),places=12)
            self.assertTrue(np.isin(result['path'],np.arange(3)).all());self.assertLessEqual(result['max_transition_m'],100.)
            flights.append(result['total_flight_distance_m'])
        self.assertEqual(flights,sorted(flights,reverse=True))
        zero=optimize_trajectory(rates,points,slot_duration_s=10.,max_speed_m_per_s=0.,penalty_bits_per_use=.01,reference_distance_m=100.)
        self.assertEqual(len(set(zero['path'])),1);self.assertAlmostEqual(zero['average_skr'],means.max())

    def test_byte_alias_accepts_only_line_endings(self):
        with tempfile.TemporaryDirectory(dir=DEFAULT) as folder:
            path=Path(folder)/'source.txt';original=b'first\nsecond\n'
            path.write_bytes(original.replace(b'\n',b'\r\n'))
            expected=hashlib.sha256(original).hexdigest()
            self.assertEqual(verify_alias(path,expected)['verification'],'VERIFIED_NEWLINE_EQUIVALENT')
            path.write_bytes(b'first\n second\n')
            with self.assertRaises(ValueError):verify_alias(path,expected)

    def test_resume_rejects_identity_change(self):
        settings=saved.read_json(CONFIG)
        with tempfile.TemporaryDirectory(dir=DEFAULT) as folder:
            bind_inputs(Path(folder),settings)
            settings['cloud']['seed']+=1
            with self.assertRaises(ValueError):bind_inputs(Path(folder),settings)

    def test_settings_and_scenario_count(self):
        settings=saved.read_json(CONFIG);positions=validate_settings(settings)
        np.testing.assert_array_equal(positions[44],[450,450]);self.assertEqual(len(cloud_scenarios(settings)),16)
        settings['cloud']['radius_m']=5
        with self.assertRaises(ValueError):validate_settings(settings)
        with self.assertRaises(ValueError):slot_table([1.],np.array([[1,0]]))


class ExactClearIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.settings=saved.read_json(CONFIG);cls.manifest=saved.read_json(DEFAULT/'startup_manifest.json')
        cls.bank=load_clear_bank(cls.settings,cls.manifest['protected_hashes'])

    def test_catalog_and_clear_coverage(self):
        self.assertEqual(len(self.bank['sources']['MB']),197);self.assertEqual(len(self.bank['sources']['Uniform']),30)
        self.assertEqual(len(self.bank['rows']),22700)
        self.assertTrue(all(r['blocked'] is False and r['cloud_transmittance']==1 for r in self.bank['reuse']))
        self.assertEqual(self.bank['audit']['blocked_rows_imported'],0)

    def test_reference_same_scientific_evaluator(self):
        b=self.bank;candidate=next(c for c in b['sources']['MB'] if (c['nu_raw'],c['V_A'])==(.17,5.046875))
        result=saved.evaluate_authenticated(candidate,b['states'][44]['moments'],b['config'],self.manifest['protected_hashes'])
        self.assertAlmostEqual(result['SKR'],.0587348598790054,places=12)
        self.assertAlmostEqual(result['T_eff'],.16092029098192165,places=12)
        self.assertFalse(result['certified_fading_security_lower_bound'])
        self.assertAlmostEqual(b['states'][44]['distance_m']/1000,21.9393102292,places=10)

    def test_every_p1_is_catalog_maximum(self):
        for family,group in self.bank['winners'].items():
            for j,winner in enumerate(group):
                rows=[r for r in self.bank['rows'] if r['family']==family and r['position_index']==j]
                self.assertEqual(winner['SKR'],max(r['SKR'] for r in rows))
                self.assertEqual(winner['K_star'],max(0.,winner['SKR']))

    def test_spatial_variation_diagnostic(self):
        values=np.array([r['K_star'] for r in self.bank['winners']['MB']])
        self.assertGreater(np.ptp(values),0.)
        self.assertAlmostEqual(values.min(),.05513095017792946,places=12)
        self.assertAlmostEqual(values.max(),.06331017962568347,places=12)

    def test_tampered_objective_or_moments_rejected(self):
        candidate=self.bank['sources']['MB'][0]
        row=next(r for r in self.bank['rows'] if r['family']=='MB' and r['position_index']==0 and r['ensemble_hash']==candidate['ensemble_hash'])
        changed=dict(row,I_AB=row['I_AB']+.001)
        with self.assertRaises(ValueError):validate_result(changed,candidate,self.bank['states'][0])
        with self.assertRaises(ValueError):covariance_check(dict(row,chi_BE=row['chi_BE']+.001))
        with self.assertRaises(ValueError):validate_result(dict(row,C=row['C']+.001),candidate,self.bank['states'][0])

    def test_protected_scientific_files_and_old_cloud_outputs_unchanged(self):
        names=('src/uav_mobility.py','src/mobility_skr.py','src/effective_channel_no_fading_noise.py',
            'docs/FINAL_MODEL_SPEC.md','results/mobility_aware_skr_20261014/full/summary.csv',
            'results/mobility_numerical_results_package_20261014/overleaf_numerical_results.zip')
        for name in names:self.assertEqual(saved.digest(saved.ROOT/name),self.manifest['protected_hashes'][name])


if __name__=='__main__':unittest.main()
