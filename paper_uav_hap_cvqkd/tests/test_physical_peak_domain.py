import unittest
from unittest.mock import patch

import torch

from src.modulation.joint_ps_gs import (
    JointTransmitter,
    PeakPhotonConstraintViolation,
)
from src.validation.physical_domain import (
    ALL_COMPARISON_SCHEMES,
    approved_peak_photon_limit,
    peak_feasible_reference_va_grid,
    preconvergence_domain_report,
)
from src.optimization.baseline_search import validation_only_baseline_search
from src.optimization.trainer import train_step
from src.utils.random import torch_generator


class TestCommonPeakPhotonDomain(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7401)
        self.t = torch.tensor([0.08, 0.3, 0.7], dtype=torch.float64)
        self.epsilon = torch.tensor([0.02, 0.01, 0.002], dtype=torch.float64)

    @staticmethod
    def _model(mode: str, limit: float) -> JointTransmitter:
        kwargs = {"n_peak_photons": limit}
        if mode in {"va", "ps_va", "gs_va", "full"}:
            kwargs.update(v_min=0.5, v_max=2.0)
        else:
            kwargs.update(fixed_va=1.0, v_min=0.5, v_max=2.0)
        if mode in {"mb", "optimized_mb"}:
            kwargs["nu_mb"] = 0.2
        return JointTransmitter(mode, **kwargs)

    def test_same_hard_rule_all_eleven_and_frozen_invariants(self):
        self.assertEqual(len(ALL_COMPARISON_SCHEMES), 11)
        for mode in ALL_COMPARISON_SCHEMES:
            with self.subTest(mode=mode):
                model_mode = "mb" if mode in {"fixed_mb", "optimized_mb"} else mode
                ensemble = self._model(model_mode, 100.0)(self.t, self.epsilon)
                ensemble.validate()
                self.assertLessEqual(float(ensemble.amplitudes.abs().square().max().detach()), 100.0)
                self.assertLess(float(ensemble.weighted_mean().abs().max().detach()), 1e-12)
                self.assertLess(
                    float(ensemble.weighted_pseudomoment().abs().max().detach()), 1e-12
                )
                self.assertTrue(torch.allclose(
                    ensemble.computed_va(), ensemble.declared_va, atol=1e-12, rtol=1e-12
                ))

    def test_violation_fails_without_clipping(self):
        unconstrained = JointTransmitter("uniform", fixed_va=2.0)
        expected = unconstrained(self.t[:1], self.epsilon[:1]).amplitudes.clone()
        with self.assertRaises(PeakPhotonConstraintViolation):
            JointTransmitter(
                "uniform", fixed_va=2.0, n_peak_photons=2.6
            )(self.t[:1], self.epsilon[:1])
        # The unconstrained reference still gives the exact frozen mapping;
        # failure did not mutate global/static constellation state.
        self.assertTrue(torch.equal(
            expected, unconstrained(self.t[:1], self.epsilon[:1]).amplitudes
        ))

    def test_ps_gs_va_gradients_are_finite_inside_domain(self):
        model = self._model("full", 100.0)
        ensemble = model(self.t, self.epsilon)
        weights = torch.linspace(0.3, 1.7, 256, dtype=torch.float64)
        objective = (
            (ensemble.probabilities * weights).sum()
            + (ensemble.amplitudes.abs().square() * weights).sum()
        )
        objective.backward()
        for family, module in (
            ("ps", model.ps_network), ("gs", model.gs_model), ("va", model.va_network)
        ):
            gradients = [p.grad for p in module.parameters() if p.grad is not None]
            self.assertTrue(gradients, family)
            self.assertTrue(all(torch.isfinite(value).all() for value in gradients), family)
            self.assertGreater(sum(float(value.abs().sum()) for value in gradients), 0.0, family)

    def test_gauge_invariance_and_one_hundred_update_stability(self):
        model = self._model("gs", 100.0)
        optimizer = torch.optim.SGD(model.parameters(), lr=1e-4)
        weights = torch.linspace(-1.0, 1.0, 256, dtype=torch.float64)
        for update in range(100):
            optimizer.zero_grad(set_to_none=True)
            ensemble = model(self.t[:1], self.epsilon[:1])
            raw_snapshot = model.gs_model.raw_coordinates.detach().clone()
            physical_snapshot = ensemble.amplitudes.detach().clone()
            for scale in (0.2, 3.0):
                with torch.no_grad():
                    model.gs_model.raw_coordinates.copy_(raw_snapshot * scale)
                    scaled = model(self.t[:1], self.epsilon[:1]).amplitudes
                    self.assertTrue(torch.allclose(
                        physical_snapshot, scaled, atol=1e-11, rtol=1e-11
                    ))
                with torch.no_grad():
                    model.gs_model.raw_coordinates.copy_(raw_snapshot)
            ensemble = model(self.t[:1], self.epsilon[:1])
            loss = torch.sum(weights * ensemble.amplitudes[0].abs().square())
            loss.backward()
            gradient = model.gs_model.raw_coordinates.grad
            raw = model.gs_model.raw_coordinates.detach()
            self.assertTrue(torch.isfinite(gradient).all(), update)
            self.assertGreater(float(gradient.norm()), 0.0, update)
            radial = torch.sum(raw * gradient)
            relative_radial = radial.abs() / (raw.norm() * gradient.norm())
            self.assertLessEqual(float(relative_radial), 1e-10, update)
            optimizer.step()
            with torch.no_grad():
                prototypes = model.gs_model.relative_prototypes()
                self.assertAlmostEqual(float(prototypes.abs().square().mean()), 1.0, places=12)
                self.assertTrue(torch.isfinite(model.gs_model.raw_coordinates).all())
                checked = model(self.t[:1], self.epsilon[:1])
                checked.validate()
                self.assertLessEqual(float(checked.amplitudes.abs().square().max()), 100.0)

    def test_preconvergence_report_refuses_unapproved_defaults(self):
        unresolved = {
            "cvqkd": {
                "n_peak_photons": None, "n_peak_author_approved": False,
                "peak_domain_scope": None, "v_min_snu": None, "v_max_snu": None,
                "mb_nu": None,
            },
            "baseline_search": {"optimized_mb_nu_grid": None},
        }
        report = preconvergence_domain_report(unresolved)
        self.assertEqual(report["status"], "BLOCKED_UNRESOLVED")
        self.assertFalse(report["is_fock_cutoff_certification"])
        self.assertFalse(report["physical_domain_configuration_complete"])
        with self.assertRaises(ValueError):
            approved_peak_photon_limit(unresolved)

    def test_approved_domain_reports_bounds_and_baseline_feasibility(self):
        config = {
            "cvqkd": {
                "n_peak_photons": 20.0, "n_peak_author_approved": True,
                "peak_domain_scope": "complete_preregistered_realizations",
                "v_min_snu": 0.5, "v_max_snu": 4.0, "v_a_budget_snu": 2.0,
                "mb_nu": 0.2,
            },
            "baseline_search": {
                "va_grid_snu": [0.5, 1.0, 2.0],
                "optimized_mb_nu_grid": [0.0, 0.2, 0.4],
            },
        }
        report = preconvergence_domain_report(config)
        self.assertEqual(report["status"], "READY_FOR_CONVERGENCE_EXECUTION")
        self.assertEqual(report["maximum_permitted_photon_number"], 20.0)
        self.assertAlmostEqual(report["maximum_permitted_amplitude_abs"], 20.0 ** 0.5)
        self.assertTrue(report["mandatory_fixed_benchmarks_feasible"])
        self.assertTrue(report["common_rule_applies_to_all_eleven"])
        continuous = {**config, "cvqkd": {**config["cvqkd"],
            "peak_domain_scope": "continuous_support"}}
        blocked = preconvergence_domain_report(continuous)
        self.assertEqual(blocked["status"], "BLOCKED_UNRESOLVED")
        with self.assertRaises(ValueError):
            approved_peak_photon_limit(continuous)

    def test_peak_infeasible_baseline_candidate_is_recorded_not_scored(self):
        selection = validation_only_baseline_search(
            split_name="validation", va_grid=[0.5, 1.0], v_min=0.5, v_max=2.0,
            va_budget=2.0, reference_mb_nu=0.2,
            optimized_mb_nu_grid=[0.0, 0.2],
            score_validation_candidate=lambda scheme, va, nu: (
                None if scheme == "binomial" and va == 1.0 else va
            ),
        )
        binomial = selection["binomial"]
        self.assertEqual(binomial.selected.modulation_variance_snu, 0.5)
        rejected = [row for row in binomial.candidates if not row.physical_domain_admissible]
        self.assertEqual(len(rejected), 1)
        self.assertIsNone(rejected[0].validation_raw_skr)

    def test_binomial_fixture_uses_lower_peak_feasible_preregistered_va(self):
        # Counterexample requested by the adversarial audit: the common energy
        # box permits VA=2, but Binomial PAPR=15 makes it peak-infeasible at
        # n_peak=4; VA=0.5 remains a valid preregistered candidate.
        v_max = 4.0
        va_budget = 2.0
        preregistered_va_grid = [0.5, 1.0, va_budget]
        self.assertLessEqual(max(preregistered_va_grid), min(v_max, va_budget))
        feasible = peak_feasible_reference_va_grid(
            "binomial", preregistered_va_grid, n_peak_photons=4.0
        )
        self.assertEqual(feasible, (0.5,))
        allowed = JointTransmitter(
            "binomial", fixed_va=feasible[-1], v_min=0.5, v_max=v_max,
            n_peak_photons=4.0,
        )(self.t[:1], self.epsilon[:1])
        self.assertLessEqual(float(allowed.amplitudes.abs().square().max().detach()), 4.0)
        with self.assertRaises(PeakPhotonConstraintViolation):
            JointTransmitter(
                "binomial", fixed_va=va_budget, v_min=0.5, v_max=v_max,
                n_peak_photons=4.0,
            )(self.t[:1], self.epsilon[:1])

    def test_peak_invalid_optimizer_proposal_rolls_back_model(self):
        model = JointTransmitter(
            "gs", fixed_va=1.0, v_min=0.5, v_max=2.0, n_peak_photons=1.4
        )
        optimizer = torch.optim.SGD(model.parameters(), lr=1e-5)
        before = {name: value.detach().clone() for name, value in model.state_dict().items()}

        def force_invalid_step(*args, **kwargs):
            with torch.no_grad():
                model.gs_model.raw_coordinates.fill_(1e-8)
                model.gs_model.raw_coordinates[0] = torch.tensor([8.0, 0.0])

        with patch.object(optimizer, "step", side_effect=force_invalid_step):
            result = train_step(
                model, optimizer, self.t[:1], self.epsilon[:1],
                beta_reconciliation=0.95, noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13, generator=torch_generator(8801),
                gradient_clip_norm=1.0,
            )
        self.assertFalse(result.peak_feasible_step_accepted)
        for name, value in model.state_dict().items():
            self.assertTrue(torch.equal(value, before[name]), name)


if __name__ == "__main__":
    unittest.main()
