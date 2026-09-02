import unittest

from scripts._common import ROOT, load_yaml
from src.validation.physical_domain import (
    ALL_COMPARISON_SCHEMES,
    amplitude_domain_certification,
)


class TestApprovedAmplitudeDomainCertification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = amplitude_domain_certification(
            load_yaml(ROOT / "configs" / "default.yaml")
        )

    def test_author_domain_and_software_grids_are_exact(self):
        domain = self.report["approved_domain"]
        self.assertEqual(domain["beta_reconciliation"], 0.95)
        self.assertEqual(domain["v_min_snu"], 0.1)
        self.assertEqual(domain["v_max_snu"], 4.0)
        self.assertEqual(domain["v_a_budget_snu"], 1.5)
        self.assertEqual(domain["mean_photon_budget"], 0.75)
        self.assertEqual(domain["n_peak_photons"], 30.0)
        self.assertEqual(domain["fixed_mb_nu"], 0.1)
        grid = self.report["software_preregistered_discretization"]
        self.assertEqual(grid["fixed_va_grid_snu"], [index / 10 for index in range(1, 16)])
        self.assertEqual(grid["optimized_mb_nu_grid"], [index / 100 for index in range(31)])
        self.assertTrue(grid["chosen_before_validation_or_test_outcomes"])
        self.assertTrue(grid["test_selection_forbidden"])
        self.assertEqual(
            self.report["classifications"]["mi_samples_and_fock_cutoff"],
            "PENDING_CONVERGENCE_SELECTION",
        )
        self.assertEqual(
            self.report["classification_status"]["mi_samples_and_fock_cutoff"],
            "PENDING_NOT_YET_SELECTED",
        )

    def test_uniform_and_binomial_exact_papr_and_vmax_peaks(self):
        fixed = self.report["fixed_baseline_certification"]
        uniform = fixed["uniform"]
        binomial = fixed["binomial"]
        self.assertEqual(uniform["papr_exact"], "45/17")
        self.assertAlmostEqual(uniform["papr"], 45.0 / 17.0, places=14)
        self.assertAlmostEqual(
            uniform["analytic_peak_energy_at_v_max_photons"], 90.0 / 17.0,
            places=14,
        )
        self.assertEqual(binomial["papr_exact"], "15")
        self.assertAlmostEqual(binomial["papr"], 15.0, places=13)
        self.assertAlmostEqual(
            binomial["analytic_peak_energy_at_v_max_photons"], 30.0, places=12
        )
        self.assertTrue(fixed["binomial_v_max_boundary"]["equals_n_peak"])
        self.assertLessEqual(uniform["analytic_numerical_absolute_error"], 1e-12)
        self.assertLessEqual(binomial["analytic_numerical_absolute_error"], 1e-12)

    def test_mb_reference_and_every_optimized_candidate_are_certified(self):
        fixed = self.report["fixed_baseline_certification"]
        reference = fixed["fixed_mb"]
        self.assertEqual(reference["nu_mb"], 0.1)
        self.assertAlmostEqual(reference["papr"], 2.754443493980498, places=14)
        self.assertTrue(reference["full_common_va_box_certified"])
        candidates = fixed["optimized_mb_candidates"]
        self.assertEqual(len(candidates), 31)
        self.assertEqual([row["nu_mb"] for row in candidates], [i / 100 for i in range(31)])
        for row in candidates:
            with self.subTest(nu=row["nu_mb"]):
                self.assertTrue(row["full_common_va_box_certified"])
                self.assertTrue(row["all_preregistered_va_candidates_feasible"])
                self.assertFalse(row["fixed_search_peak_excluded_va_candidates_snu"])
                self.assertLessEqual(row["analytic_numerical_absolute_error"], 1e-12)
                self.assertLessEqual(row["analytic_peak_energy_at_v_max_photons"], 30.0)

    def test_common_fail_closed_rule_covers_all_eleven_without_false_learned_claim(self):
        audit = self.report["all_eleven_rule_audit"]
        self.assertEqual(set(audit), set(ALL_COMPARISON_SCHEMES))
        self.assertTrue(self.report["all_eleven_modes_covered"])
        for scheme, row in audit.items():
            with self.subTest(scheme=scheme):
                self.assertEqual(row["same_hard_peak_rule_photons"], 30.0)
                self.assertTrue(row["rule_applied_to_final_physical_amplitudes"])
                self.assertFalse(row["clipping_or_posthoc_renormalization"])
        learned = self.report["learned_roster"]
        self.assertEqual(learned["status"], "UNRESOLVED_PRETRAINING")
        self.assertFalse(learned["global_peak_certification_claimed"])
        self.assertTrue(learned["runtime_guard_required"])
        self.assertFalse(self.report["publication_training_performed"])
        self.assertFalse(self.report["test_set_used"])


if __name__ == "__main__":
    unittest.main()
