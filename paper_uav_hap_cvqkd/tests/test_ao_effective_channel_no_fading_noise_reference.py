"""Scoped AO/source-adapter checks; tests never invoke the exact-source oracle."""
import copy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from scripts import run_ao_effective_channel_no_fading_noise_reference as driver


class AOReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objective = driver.Objective()
        cls.prepared = driver.read_json(driver.OUT/"catalog_preparation.json")

    def test_reference_adapter_equals_preserved_evaluator(self):
        from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
        from src.effective_channel_no_fading_noise import evaluate_candidate
        candidate = candidate_from_payload(self.objective.config,self.objective.payloads,"MB",.165,5.5)
        with patch("src.cvqkd.gram_moments._fallback",side_effect=AssertionError("No source computation in tests")):
            row=driver.evaluate_authenticated(candidate,self.objective.moments,self.objective.config,self.objective.hashes)
            preserved=evaluate_candidate(candidate,self.objective.moments,self.objective.config)
        for name in ("a","b","Z_star","lambda_1","lambda_2","lambda_3","I_AB","chi_BE","SKR"):
            self.assertEqual(row[name],preserved[name])

    def test_forged_cached_source_rejected(self):
        from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
        candidate=candidate_from_payload(self.objective.config,self.objective.payloads,"MB",.165,5.5)
        for wrong in (dict(candidate,C=candidate["C"]+1e-8),dict(candidate,nu_raw=.166)):
            with self.assertRaises(ValueError):
                driver.authenticate(wrong,self.objective.hashes,self.objective.config)
        with self.assertRaises(ValueError):
            driver.authenticate(candidate,{},self.objective.config)

    def test_catalog_ranking_has_182_and_valid_quantum_spectrum(self):
        self.assertEqual(self.prepared["catalog_rows"],182)
        row=self.prepared["best_catalog_MB"]
        matrix=np.array(row["Gamma_AB"])
        omega=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])
        self.assertGreater(np.linalg.eigvalsh(matrix+1j*omega).min(),0.)
        np.testing.assert_allclose(sorted(abs(np.linalg.eigvals(1j*omega@matrix))),
            [row["lambda_2"]]*2+[row["lambda_1"]]*2,rtol=0.,atol=1e-12)
        g=lambda n:0. if n==0 else (n+1)*math.log2(n+1)-n*math.log2(n)
        chi=sum(g((row[k]-1)/2)*sign for k,sign in [("lambda_1",1),("lambda_2",1),("lambda_3",-1)])
        self.assertAlmostEqual(chi,row["chi_BE"],places=12)
        self.assertFalse(row["fading_noise_included"])

    def test_P2_uses_new_P1_variance(self):
        start=dict(start_id="fixture",nu_raw=.165,V_A=5.5)
        def row(n,v,k):
            return dict(nu_raw=n,V_A=v,SKR=k,source_cache_key="fixture",MI_integration_order=32)
        first=row(.165,5.5,.05);p1=row(.165,6.,.06);p2=row(.15,6.,.07)
        class Fixture:
            settings=dict(max_ao_iterations=1,SKR_tolerance=1e-8,parameter_tolerance=1e-6)
            def __call__(self,n,v): return first
        with tempfile.TemporaryDirectory() as folder,patch.object(driver,"OUT",Path(folder)),patch.object(
            driver,"search_coordinate",side_effect=[dict(best=p1,status="BRACKETED_EXACT_CATALOG"),dict(best=p2,status="BRACKETED_EXACT_CATALOG")]) as search:
            result=driver.run_start(Fixture(),start,1)
        self.assertEqual(search.call_args_list[1].args[2],6.)
        self.assertEqual(result["final"]["nu_raw"],.15)
        self.assertGreater(result["iterations"][0]["delta_K"],0.)

    def test_decreasing_coordinate_update_is_rejected_and_logged(self):
        first=dict(nu_raw=.165,V_A=5.5,SKR=.06,source_cache_key="fixture",MI_integration_order=32)
        lower=dict(first,V_A=6.,SKR=.05)
        class Fixture:
            settings=dict(max_ao_iterations=1,SKR_tolerance=1e-8,parameter_tolerance=1e-6)
            def __call__(self,n,v):return first
        with tempfile.TemporaryDirectory() as folder,patch.object(driver,"OUT",Path(folder)),patch.object(
            driver,"search_coordinate",side_effect=[dict(best=lower,status="BRACKETED_EXACT_CATALOG"),dict(best=first,status="BRACKETED_EXACT_CATALOG")]):
            result=driver.run_start(Fixture(),dict(start_id="fixture",nu_raw=.165,V_A=5.5),1)
        self.assertEqual(result["final"],first)
        self.assertEqual(result["iterations"][0]["rejected_steps"][0]["reason"],"DECREASE_REJECTED")
        self.assertNotEqual(result["status"],"CONVERGED_COORDINATE_LOCAL")

    def test_zero_endpoint_checked_explicitly(self):
        current=dict(nu_raw=.15,V_A=6.,SKR=.06)
        class Fixture:
            settings=dict(SKR_tolerance=1e-8,parameter_tolerance=1e-6)
            def catalog_values(self,variable,fixed):return [.15,.2]
            def __call__(self,n,v):
                if n!=0:raise AssertionError("This fixture must explicitly check nu=0")
                return dict(nu_raw=0.,V_A=v,SKR=.07)
        coarse=dict(best=current,status="BRACKETED_EXACT_CATALOG",history=[],source_missing=[])
        with patch("scripts.run_theta10_D55_alt_opt.adaptive_maximize_1d",return_value=coarse):
            result=driver.search_coordinate(Fixture(),"nu_raw",6.,current)
        self.assertEqual(result["best"]["nu_raw"],0.)
        self.assertEqual(result["zero_endpoint_status"],"EXACT_CHECKED")

    def test_budget_preserves_uniform_reserve_without_oracle(self):
        objective=object.__new__(driver.Objective)
        objective.settings=dict(source_wall_budget_seconds=1800,uniform_source_reserve_seconds=600,
            max_new_source_attempts=3,per_source_deadline_seconds=720)
        objective.used_source_seconds=1200
        objective.attempts=[];objective.group="MB"
        with patch("scripts.run_theta10_D55_alt_opt_closure_continuation.supervised_probe",side_effect=AssertionError("Budget exhausted")):
            self.assertFalse(objective.generate(.16,6.25))


if __name__=="__main__":
    unittest.main()
