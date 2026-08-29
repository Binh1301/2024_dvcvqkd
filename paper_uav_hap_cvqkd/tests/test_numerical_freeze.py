import unittest
import json
from pathlib import Path

import numpy as np
import torch

import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from _common import load_yaml
from _numerical_validation import (
    ensemble_sha256, representative_ensembles, unique_ensemble_roster,
    validation_representative_states,
)

from src.modulation.joint_ps_gs import JointTransmitter, reference_ensemble
from src.modulation.qam256 import c4_orbit_masses
from src.cvqkd.covariance import PhysicalityError
from src.cvqkd.holevo import holevo_information
from src.optimization.baseline_search import (
    feasible_fixed_va_grid,
    validation_only_baseline_search,
)
from src.optimization.learned_outer_selection import (
    FIXED_VA_LEARNED_MODES,
    validation_only_learned_fixed_va_selection,
)
from src.validation.publication_manifest import validate_publication_manifest
from src.validation.convergence import (
    ConvergenceTolerance,
    fock_convergence_trace,
    holevo_threshold_sensitivity_trace,
    mi_convergence_trace,
    summarize_mi_replications,
    select_representative_state_indices,
)


class NumericalConvergenceTests(unittest.TestCase):
    def setUp(self):
        self.t = torch.tensor([0.02], dtype=torch.float64)
        self.epsilon = torch.tensor([0.002], dtype=torch.float64)
        self.ensemble = reference_ensemble(
            "uniform", batch_size=1, modulation_variance=0.5
        )

    def test_mi_uses_nested_common_random_numbers_and_deterministic_selection(self):
        arguments = dict(
            ensemble=self.ensemble,
            transmittance=self.t,
            epsilon=self.epsilon,
            sample_counts=(2, 4, 8),
            seed=8181,
            tolerance=ConvergenceTolerance(absolute=10.0, relative=0.0),
        )
        first = mi_convergence_trace(**arguments)
        second = mi_convergence_trace(**arguments)
        self.assertEqual(first, second)
        self.assertEqual(first["selected_sample_count"], 2)
        self.assertEqual(first["reference_sample_count"], 8)
        self.assertIn("absolute_error_bits_by_state", first["rows"][0])

    def test_mi_success_reporting_includes_variance_and_worst_fixture(self):
        replications = [
            mi_convergence_trace(
                self.ensemble, self.t, self.epsilon,
                sample_counts=(2, 4), seed=seed,
                tolerance=ConvergenceTolerance(absolute=10.0, relative=0.0),
            )
            for seed in (101, 202)
        ]
        reporting = summarize_mi_replications(
            {"fixture": {"replications": replications}},
            state_labels=["medium"], transmittance=self.t, epsilon=self.epsilon,
            replication_base_seeds=(101, 202),
            derived_replication_seeds=(1001, 1002),
            selected_common_sample_count=2,
        )
        self.assertGreaterEqual(
            reporting["repeated_run_variance_bits_squared"]["fixture"][0], 0.0
        )
        worst = reporting["worst_certified_state_fixture"]
        self.assertEqual(worst["fixture"], "fixture")
        self.assertEqual(worst["state_label"], "medium")
        self.assertLessEqual(worst["error_to_tolerance_ratio"], 1.0)
        blocked = summarize_mi_replications(
            {}, state_labels=["medium"], transmittance=self.t,
            epsilon=self.epsilon, replication_base_seeds=(101, 202),
            derived_replication_seeds=(1001, 1002),
            selected_common_sample_count=None,
        )
        self.assertIsNone(blocked["repeated_run_variance_bits_squared"])
        self.assertIsNone(blocked["worst_certified_state_fixture"])

    def test_fock_trace_contains_all_required_quantities(self):
        trace = fock_convergence_trace(
            self.ensemble,
            self.t,
            self.epsilon,
            cutoffs=(30, 40),
            tolerance=ConvergenceTolerance(absolute=10.0, relative=0.0),
            symplectic_tolerance=ConvergenceTolerance(absolute=10.0, relative=0.0),
            information_tolerance=ConvergenceTolerance(absolute=10.0, relative=0.0),
            mutual_information_bits=torch.tensor([0.25], dtype=torch.float64),
            beta_reconciliation=0.95,
            density_trace_tolerance=1e-8,
        )
        self.assertTrue(trace["converged"])
        self.assertEqual(trace["selected_fock_cutoff"], 30)
        self.assertEqual(
            set(trace["rows"][0]["maximum_absolute_errors"]),
            {"C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K"},
        )

    def test_holevo_pseudoinverse_threshold_sensitivity_is_explicit(self):
        trace = holevo_threshold_sensitivity_trace(
            self.ensemble, self.t, self.epsilon, fock_cutoff=40,
            density_eigenvalue_tolerances=(1e-14, 1e-12),
            selected_tolerance=1e-12,
            tolerance=ConvergenceTolerance(absolute=1.0, relative=1.0),
            symmetry_tolerance=1e-8, density_trace_tolerance=1e-8,
            physicality_tolerance=1e-10,
        )
        self.assertEqual(
            trace["selected_density_eigenvalue_pseudoinverse_tolerance"], 1e-12
        )
        self.assertIn("suppressed_density_eigenvalues", trace["rows"][-1])

    def test_representative_states_are_deterministic_and_outcome_independent(self):
        t = np.linspace(0.01, 0.2, 101)
        epsilon = np.linspace(0.005, 0.0005, 101)
        first = select_representative_state_indices(t, epsilon)
        second = select_representative_state_indices(t, epsilon)
        self.assertEqual(first, second)
        self.assertEqual(set(first), {"bad", "medium", "good"})
        self.assertEqual(len(set(first.values())), 3)

    def test_certification_fixture_and_exact_duplicate_reduction_are_deterministic(self):
        root = Path(__file__).parents[1]
        config = load_yaml(root / "configs" / "default.yaml")
        _, _, t, epsilon = validation_representative_states(config)
        first = representative_ensembles(config, t, epsilon)
        torch.manual_seed(999999)
        second = representative_ensembles(config, t, epsilon)
        self.assertEqual(
            ensemble_sha256(first["untrained_full_initialization"]),
            ensemble_sha256(second["untrained_full_initialization"]),
        )
        unique, aliases = unique_ensemble_roster(first)
        self.assertEqual(len(first), 18)
        self.assertEqual(len(unique), 16)
        self.assertEqual(aliases, {
            "optimized_mb_nu_0_low_va_0.1": "uniform_low_va_0.1",
            "optimized_mb_nu_0_high_va_1.5": "uniform_high_va_1.5",
        })
        vmax = first["hard_peak_boundary_at_vmax"]
        masses = c4_orbit_masses(vmax.probabilities[0])
        self.assertEqual(float(masses[0]), 1.0 / 29.0)
        self.assertEqual(float(vmax.declared_va[0]), 4.0)
        self.assertEqual(float(vmax.amplitudes.abs().square().max()), 30.0)
        torch.testing.assert_close(
            torch.sum(vmax.probabilities * vmax.amplitudes.abs().square(), dim=-1),
            torch.full((3,), 2.0, dtype=torch.float64), rtol=1e-14, atol=1e-14,
        )
        with self.assertRaisesRegex(PhysicalityError, "Fock truncation"):
            holevo_information(
                vmax, t, epsilon, backend="fock_diagnostic", fock_cutoff=64,
                density_trace_tolerance=1e-10, density_eigenvalue_tolerance=1e-12,
            )
        passed = holevo_information(
            vmax, t, epsilon, backend="fock_diagnostic", fock_cutoff=72,
            density_trace_tolerance=1e-10, density_eigenvalue_tolerance=1e-12,
        )
        self.assertLess(float((passed.tau_trace - 1.0).abs().max()), 1e-10)
        for name in (
            "deterministic_ps_only", "deterministic_gs_only",
            "deterministic_va_only", "deterministic_deformed_full",
            "near_coincident_pseudoinverse_stress",
        ):
            first[name].validate()
        self.assertGreater(float(
            (first["deterministic_ps_only"].probabilities[0]
             - first["deterministic_ps_only"].probabilities[-1]).abs().max()
        ), 0.0)
        self.assertGreater(float(
            (first["deterministic_va_only"].declared_va[0]
             - first["deterministic_va_only"].declared_va[-1]).abs()
        ), 0.0)

    def test_sequential_script_draws_one_fixed_maximum_length_crn_tensor(self):
        source = (Path(__file__).parents[1] / "scripts" / "validate_mi_convergence.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("(transmittance.shape[0], 256, counts[-1])", source)
        self.assertNotIn("(ensemble.probabilities.shape[0], 256, count),", source)


class BaselineSelectionTests(unittest.TestCase):
    def test_all_four_baselines_are_validation_selected_and_energy_fair(self):
        score_calls = []
        def score(kind, va, nu):
            score_calls.append((kind, va, nu))
            if kind == "uniform":
                return -1.0 - (va - 1.0) ** 2
            nu_target = 0.2 if kind == "mb" else 0.0
            return -((va - 1.0) ** 2) - ((0.0 if nu is None else nu) - nu_target) ** 2

        selections = validation_only_baseline_search(
            split_name="validation",
            va_grid=(0.5, 1.0, 1.5),
            v_min=0.5,
            v_max=3.0,
            va_budget=1.5,
            reference_mb_nu=0.1,
            optimized_mb_nu_grid=(0.0, 0.1, 0.2, 0.3),
            score_validation_candidate=score,
        )
        self.assertEqual(
            set(selections), {"uniform", "binomial", "fixed_mb", "optimized_mb"}
        )
        for selection in selections.values():
            self.assertEqual(selection.split_used_for_selection, "validation")
            self.assertFalse(selection.test_set_used)
            self.assertLessEqual(selection.selected.modulation_variance_snu, 1.5)
        self.assertEqual(selections["optimized_mb"].selected.mb_nu, 0.2)
        self.assertEqual(len(score_calls), 15)
        reused = [candidate for candidate in selections["optimized_mb"].candidates
                  if candidate.exact_score_reused_from is not None]
        self.assertEqual(len(reused), 6)
        self.assertEqual(
            {candidate.mb_nu for candidate in reused}, {0.0, 0.1}
        )

    def test_test_selection_and_over_budget_candidates_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "validation-only"):
            validation_only_baseline_search(
                split_name="test",
                va_grid=(0.5,),
                v_min=0.5,
                v_max=3.0,
                va_budget=1.0,
                reference_mb_nu=0.1,
                optimized_mb_nu_grid=(0.0, 0.1),
                score_validation_candidate=lambda *_: 0.0,
            )
        with self.assertRaisesRegex(ValueError, "average V_A budget"):
            feasible_fixed_va_grid((0.5, 1.5), v_min=0.5, v_max=3.0, va_budget=1.0)


class GaugeTests(unittest.TestCase):
    def test_positive_raw_scale_leaves_relative_and_physical_ensemble_invariant(self):
        model = JointTransmitter("gs", fixed_va=2.0)
        t = torch.tensor([0.02, 0.1], dtype=torch.float64)
        epsilon = torch.tensor([0.002, 0.001], dtype=torch.float64)
        before = model(t, epsilon)
        with torch.no_grad():
            model.gs_model.raw_coordinates.mul_(7.25)
        after = model(t, epsilon)
        self.assertTrue(torch.allclose(before.raw_constellation, after.raw_constellation,
                                       atol=1e-13, rtol=1e-13))
        self.assertTrue(torch.allclose(before.amplitudes, after.amplitudes,
                                       atol=1e-13, rtol=1e-13))
        prototype_energy = model.gs_model.relative_prototypes().abs().square().mean()
        self.assertAlmostEqual(float(prototype_energy.detach()), 1.0, places=13)

    def test_gauge_gradient_is_tangent_to_raw_scale_direction(self):
        model = JointTransmitter("gs", fixed_va=2.0)
        t = torch.tensor([0.02], dtype=torch.float64)
        epsilon = torch.tensor([0.002], dtype=torch.float64)
        weights = torch.linspace(0.1, 1.0, 256, dtype=torch.float64)
        objective = torch.sum(model(t, epsilon).amplitudes[0].abs().square() * weights)
        objective.backward()
        raw = model.gs_model.raw_coordinates.detach()
        gradient = model.gs_model.raw_coordinates.grad
        self.assertGreater(float(torch.linalg.vector_norm(gradient)), 0.0)
        radial = torch.sum(raw * gradient)
        scale = torch.linalg.vector_norm(raw) * torch.linalg.vector_norm(gradient)
        self.assertLess(float(torch.abs(radial) / scale), 1e-11)


class PublicationLifecycleTests(unittest.TestCase):
    def test_learned_fixed_va_outer_selection_is_matched_and_test_blind(self):
        records = []
        for mode in FIXED_VA_LEARNED_MODES:
            for va in (0.5, 1.0):
                for seed in (11, 22):
                    records.append({
                        "mode": mode,
                        "fixed_modulation_variance_snu": va,
                        "initialization_seed": seed,
                        "selected_validation_raw_skr": va,
                        "validation_budget_feasible": True,
                        "validation_expected_budget": {
                            "expected_budget_feasible": True,
                            "expected_budget_upper_snu": va,
                        },
                        "selected_validation_peak_feasible": True,
                        "training_protocol_sha256": "same-protocol",
                        "checkpoint_id": f"{mode}-{va}-{seed}",
                        "test_set_accessed": False,
                        "development_seeds": {
                            "train_channel": 1, "train_awgn": 2,
                            "validation_channel": 3, "validation_awgn": 4,
                        },
                        "validation_state_realization_sha256": "a" * 64,
                    })
        selected = validation_only_learned_fixed_va_selection(
            records,
            va_grid=(0.5, 1.0),
            v_min=0.5,
            v_max=2.0,
            va_budget=1.0,
            initialization_seeds=(11, 22),
        )
        self.assertEqual(set(selected), set(FIXED_VA_LEARNED_MODES))
        self.assertTrue(all(value.modulation_variance_snu == 1.0 for value in selected.values()))
        contaminated = list(records)
        contaminated[0] = {**contaminated[0], "test_raw_skr": 999.0}
        with self.assertRaisesRegex(ValueError, "test results"):
            validation_only_learned_fixed_va_selection(
                contaminated, va_grid=(0.5, 1.0), v_min=0.5, v_max=2.0,
                va_budget=1.0, initialization_seeds=(11, 22)
            )
        mismatched = [dict(record) for record in records]
        mismatched[0] = {
            **mismatched[0],
            "development_seeds": {**mismatched[0]["development_seeds"], "validation_channel": 99},
        }
        with self.assertRaisesRegex(ValueError, "identical development data"):
            validation_only_learned_fixed_va_selection(
                mismatched, va_grid=(0.5, 1.0), v_min=0.5, v_max=2.0,
                va_budget=1.0, initialization_seeds=(11, 22)
            )

    def test_training_source_has_no_held_out_channel_or_metric_path(self):
        source = (Path(__file__).parents[1] / "scripts" / "_train.py").read_text(
            encoding="utf-8"
        )
        for forbidden in ("test_channel =", "test_eval =", '"test_raw_skr"',
                          '"test_per_state"', "seeds.test_channel", "seeds.test_awgn"):
            self.assertNotIn(forbidden, source)
        self.assertIn('"test_set_accessed": False', source)

    def test_manifest_gates_all_test_and_analysis_choices(self):
        manifest = {
            "schema_version": "publication-selection-manifest-v1",
            "status": "selections-and-analysis-frozen-before-test",
            "test_set_accessed_during_selection": False,
            "resolved_config_sha256": "a" * 64,
            "validation_state_sha256": "b" * 64,
            "baseline_selection_sha256": "c" * 64,
            "learned_selection_sha256": "d" * 64,
            "convergence_evidence_sha256": "e" * 64,
            "environment_lock_sha256": "f" * 64,
            "attempted_seed_accounting_sha256": "0" * 64,
            "git_revision": "1234567",
            "artifact_paths": {
                "resolved_config": "resolved.yaml",
                "baseline_selection": "baselines.json",
                "learned_selection": "learned.json",
                "convergence_evidence": "convergence.json",
                "environment_lock": "requirements.lock",
                "attempted_seed_accounting": "attempted.json",
            },
            "test_evaluation": {"fading_samples": 100, "awgn_samples_per_symbol": 50,
                                "channel_seed": 1, "awgn_seed": 2},
            "analysis_plan": {
                "t_bin_edges": [0.0, 0.5, 1.0], "epsilon_bin_edges": [0.0, 0.01],
                "va_heatmap_t_grid": [0.1, 0.9], "va_heatmap_epsilon_grid": [0.0, 0.01],
                "outage_threshold_bits": 0.0,
                "confidence_interval": "paired two-sided Student-t 95%",
            },
            "checkpoints": [{"id": "full-1", "mode": "full", "path": "full.pt",
                             "sha256": "f" * 64, "initialization_seed": 1,
                             "selected_fixed_va_snu": None,
                             "validation_peak_feasible": True,
                             "validation_max_symbol_energy": 1.0,
                             "validation_budget_feasible": True,
                             "validation_mean_va_snu": 1.0,
                             "validation_expected_budget_upper_snu": 1.0}],
        }
        validate_publication_manifest(manifest)
        invalid = {**manifest, "status": "draft"}
        with self.assertRaisesRegex(ValueError, "does not authorize"):
            validate_publication_manifest(invalid)

    def test_publication_schemas_parse_and_v2_requires_analysis_fields(self):
        schema_root = Path(__file__).parents[1] / "schemas"
        result_schema = json.loads(
            (schema_root / "publication_results.schema.json").read_text(encoding="utf-8")
        )
        manifest_schema = json.loads(
            (schema_root / "publication_selection_manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )
        convergence_schema = json.loads(
            (schema_root / "combined_convergence_evidence.schema.json").read_text(
                encoding="utf-8"
            )
        )
        mi_schema = json.loads(
            (schema_root / "mi_convergence.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result_schema["properties"]["schema_version"]["const"],
                         "publication-results-v2")
        self.assertIn("analysis_plan", result_schema["required"])
        self.assertIn("paired_contrasts", result_schema["required"])
        self.assertFalse(result_schema["additionalProperties"])
        self.assertEqual(manifest_schema["properties"]["test_set_accessed_during_selection"]["const"], False)
        self.assertEqual(
            convergence_schema["properties"]["coverage_scope"]["const"],
            "exact_selected_roster_on_preregistered_validation_realization",
        )
        self.assertEqual(
            convergence_schema["properties"]["schema_version"]["const"],
            "combined-convergence-evidence-v2",
        )
        self.assertIn("certified_roster", convergence_schema["required"])
        self.assertNotIn(
            "coverage_complete_over_admissible_transmitter_domain",
            convergence_schema["properties"],
        )
        self.assertIn("repeated_run_variance_bits_squared", mi_schema["required"])
        self.assertIn("worst_certified_state_fixture", mi_schema["required"])

    def test_finite_fixture_scripts_cannot_self_certify_selected_roster(self):
        scripts = Path(__file__).parents[1] / "scripts"
        for name in (
            "validate_mi_convergence.py",
            "validate_fock_convergence.py",
            "validate_holevo_threshold_sensitivity.py",
        ):
            source = (scripts / name).read_text(encoding="utf-8")
            self.assertIn('"selected_ensemble_certification": None', source)
        combined = (scripts / "combine_convergence_evidence.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("reconstruct_selected_roster", combined)
        self.assertEqual(combined.count("validate_exact_evidence("), 3)
        producer = (scripts / "validate_selected_roster_convergence.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("full_validation_states", producer)
        self.assertIn("reconstruct_selected_roster", producer)


if __name__ == "__main__":
    unittest.main()
