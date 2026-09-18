import unittest
from unittest.mock import patch

import torch

from src.cvqkd.gram_moments import GramMomentResult
from src.cvqkd.covariance import PhysicalityError, standard_form_covariance
from src.cvqkd.holevo import (
    SecurityDomainError,
    _evaluate_holevo_for_correlations,
    _holevo_from_source_moments,
    _maximize_bounded_scalar,
    holevo_information,
)
from src.modulation.joint_ps_gs import Ensemble, JointTransmitter
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import square_qam256, uniform_pmf
from src.cvqkd.secret_key_rate import fading_secret_key_rate


DTYPE = torch.float64


class BoundedZMaximizationTests(unittest.TestCase):
    def _maximize(self, objective):
        lower = torch.tensor([-1.0], dtype=DTYPE)
        upper = torch.tensor([1.0], dtype=DTYPE)
        return _maximize_bounded_scalar(
            lower,
            upper,
            objective,
            grid_size=33,
            refinement_steps=12,
        )

    def test_interior_maximum_is_refined(self):
        value, point = self._maximize(lambda z: 1.0 - (z - 0.37).square())
        self.assertGreater(float(point.item()), -1.0)
        self.assertLess(float(point.item()), 1.0)
        torch.testing.assert_close(value, 1.0 - (point - 0.37).square(), atol=1e-10, rtol=0.0)
        self.assertAlmostEqual(float(point.item()), 0.37, delta=1e-4)

    def test_lower_boundary_is_retained(self):
        value, point = self._maximize(lambda z: -z)
        torch.testing.assert_close(point, torch.tensor([-1.0], dtype=DTYPE))
        torch.testing.assert_close(value, torch.tensor([1.0], dtype=DTYPE))

    def test_upper_boundary_is_retained(self):
        value, point = self._maximize(lambda z: z)
        torch.testing.assert_close(point, torch.tensor([1.0], dtype=DTYPE))
        torch.testing.assert_close(value, torch.tensor([1.0], dtype=DTYPE))


class HolevoIntervalTests(unittest.TestCase):
    def _synthetic_source_result(
        self, *, coherent_correlation, w, transmittance=0.1, epsilon=0.1,
        maximize_full_interval=True,
    ):
        ensemble = JointTransmitter("uniform", fixed_va=2.0)(
            torch.tensor([1.0], dtype=DTYPE), torch.tensor([0.0], dtype=DTYPE)
        )
        return _holevo_from_source_moments(
            ensemble,
            torch.tensor([transmittance], dtype=DTYPE),
            torch.tensor([epsilon], dtype=DTYPE),
            coherent_correlation=torch.tensor([coherent_correlation], dtype=DTYPE),
            w_raw=torch.tensor([w], dtype=DTYPE),
            tau=None,
            tau_trace=torch.ones(1, dtype=DTYPE),
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            physicality_tolerance=1e-10,
            diagnostics={},
            maximize_full_interval=maximize_full_interval,
        )

    def test_holevo_interior_maximum_is_not_replaced_by_lower_endpoint(self):
        result = self._synthetic_source_result(coherent_correlation=0.0, w=0.2)
        self.assertEqual(result.diagnostics["maximizing_location"], ("interior",))
        self.assertGreater(float(result.z.item()), float(result.diagnostics["Z_L"].item()))
        self.assertLess(float(result.z.item()), float(result.diagnostics["Z_U"].item()))
        self.assertAlmostEqual(float(result.z.item()), 0.0, delta=1e-10)

    def test_holevo_lower_endpoint_maximum_is_preserved(self):
        result = self._synthetic_source_result(coherent_correlation=0.4, w=0.2)
        self.assertEqual(result.diagnostics["maximizing_location"], ("lower_boundary",))
        torch.testing.assert_close(result.z, result.diagnostics["Z_L"])

    def test_holevo_upper_endpoint_maximum_is_preserved(self):
        result = self._synthetic_source_result(coherent_correlation=-0.4, w=0.2)
        self.assertEqual(result.diagnostics["maximizing_location"], ("upper_boundary",))
        torch.testing.assert_close(result.z, result.diagnostics["Z_U"])

    def test_physicality_truncates_interval_and_covariance_uses_z_directly(self):
        result = self._synthetic_source_result(coherent_correlation=1.4, w=0.2)
        diagnostics = result.diagnostics
        self.assertTrue(
            {
                "Z_minus",
                "Z_plus",
                "Z_phys",
                "Z_L",
                "Z_U",
                "Z_star",
                "chi_BE_ub",
                "interval_width",
                "maximizing_location",
                "security_domain_valid",
            }.issubset(diagnostics)
        )
        self.assertGreater(float(diagnostics["Z_plus"].item()), float(diagnostics["Z_phys"].item()))
        torch.testing.assert_close(diagnostics["Z_U"], diagnostics["Z_phys"])
        self.assertLessEqual(float(result.z.item()), float(diagnostics["Z_U"].item()) + 1e-12)
        self.assertTrue(bool(torch.all(diagnostics["security_domain_valid"])))
        self.assertIn(
            diagnostics["maximizing_location"][0],
            {"lower_boundary", "interior", "upper_boundary"},
        )
        torch.testing.assert_close(
            result.covariance.matrix[0, 0, 2], result.z[0], atol=1e-12, rtol=0.0
        )

    def test_empty_interval_fails_with_structured_security_diagnostics(self):
        with self.assertRaises(SecurityDomainError) as raised:
            self._synthetic_source_result(coherent_correlation=2.0, w=0.2)
        diagnostics = raised.exception.diagnostics
        self.assertFalse(bool(torch.all(diagnostics["security_domain_valid"])))
        self.assertEqual(diagnostics["failure_reason"], "EMPTY_Z_INTERVAL")
        self.assertGreater(float(diagnostics["Z_L"].item()), float(diagnostics["Z_U"].item()))

    def test_candidate_physicality_failure_is_structured(self):
        with patch(
            "src.cvqkd.holevo.standard_form_covariance",
            side_effect=PhysicalityError("synthetic candidate failure"),
        ):
            with self.assertRaises(SecurityDomainError) as raised:
                self._synthetic_source_result(coherent_correlation=0.0, w=0.2)
        diagnostics = raised.exception.diagnostics
        self.assertEqual(diagnostics["failure_reason"], "CANDIDATE_PHYSICALITY_FAILURE")
        self.assertIn("candidate_Z", diagnostics)

    def test_primary_uses_exact_zstar_before_interval_logic(self):
        coherent_correlation = 0.4
        w = 0.2
        transmittance = 0.1
        epsilon = 0.1
        expected = (
            2.0 * torch.sqrt(torch.tensor([transmittance], dtype=DTYPE))
            * coherent_correlation
            - torch.sqrt(torch.tensor([2.0 * transmittance * epsilon * w], dtype=DTYPE))
        )
        with patch(
            "src.cvqkd.holevo._maximize_bounded_scalar",
            side_effect=AssertionError("primary mode must not maximize an interval"),
        ), patch(
            "src.cvqkd.holevo.standard_form_covariance",
            wraps=standard_form_covariance,
        ) as covariance_call:
            result = self._synthetic_source_result(
                coherent_correlation=coherent_correlation,
                w=w,
                transmittance=transmittance,
                epsilon=epsilon,
                maximize_full_interval=False,
            )
        torch.testing.assert_close(result.z, expected, atol=0.0, rtol=0.0)
        self.assertEqual(result.diagnostics["mode"], "zstar")
        torch.testing.assert_close(result.diagnostics["z_used"], expected)
        torch.testing.assert_close(result.diagnostics["chi_BE_bound"], result.chi_be)
        self.assertNotIn("Z_L", result.diagnostics)
        self.assertNotIn("Z_U", result.diagnostics)
        self.assertNotIn("Z_phys", result.diagnostics)
        torch.testing.assert_close(covariance_call.call_args.args[3], expected)

    def test_primary_physicality_failure_is_not_repaired_or_wrapped(self):
        with self.assertRaises(PhysicalityError):
            self._synthetic_source_result(
                coherent_correlation=2.0,
                w=0.2,
                maximize_full_interval=False,
            )

    def test_primary_chi_and_raw_key_use_zstar_value_without_positive_clipping(self):
        ensemble = JointTransmitter("uniform", fixed_va=2.0)(
            torch.tensor([1.0], dtype=DTYPE), torch.tensor([0.0], dtype=DTYPE)
        )
        transmittance = torch.tensor([0.1], dtype=DTYPE)
        epsilon = torch.tensor([0.1], dtype=DTYPE)
        result = _holevo_from_source_moments(
            ensemble,
            transmittance,
            epsilon,
            coherent_correlation=torch.tensor([0.4], dtype=DTYPE),
            w_raw=torch.tensor([0.2], dtype=DTYPE),
            tau=None,
            tau_trace=torch.ones(1, dtype=DTYPE),
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            physicality_tolerance=1e-10,
            diagnostics={},
            maximize_full_interval=False,
        )
        direct_chi, _, _ = _evaluate_holevo_for_correlations(
            ensemble,
            transmittance,
            epsilon,
            result.z,
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            physicality_tolerance=1e-10,
            return_covariance=False,
        )
        torch.testing.assert_close(result.diagnostics["chi_BE_bound"], direct_chi)
        raw = fading_secret_key_rate(
            torch.zeros_like(result.chi_be), result.chi_be, 0.95
        ).instantaneous_raw
        torch.testing.assert_close(raw, -result.chi_be)
        self.assertTrue(bool(torch.all(raw < 0.0)))

    def test_full_z_diagnostic_is_opt_in_and_does_not_replace_primary_values(self):
        primary = self._synthetic_source_result(
            coherent_correlation=0.0,
            w=0.2,
            maximize_full_interval=False,
        )
        diagnostic = self._synthetic_source_result(
            coherent_correlation=0.0,
            w=0.2,
            maximize_full_interval=True,
        )
        self.assertEqual(primary.diagnostics["mode"], "zstar")
        self.assertEqual(diagnostic.diagnostics["mode"], "full_z_diagnostic")
        self.assertNotIn("chi_BE_bound", diagnostic.diagnostics)
        torch.testing.assert_close(primary.chi_be, primary.diagnostics["chi_BE_bound"])
        torch.testing.assert_close(
            diagnostic.chi_be, diagnostic.diagnostics["chi_BE_full_z_max"]
        )
        self.assertNotAlmostEqual(float(primary.z.item()), float(diagnostic.z.item()))

    def test_phase_noise_va_gradient_reaches_conservative_holevo_value(self):
        probabilities = uniform_pmf().unsqueeze(0)
        relative = square_qam256().unsqueeze(0)
        modulation_variance = torch.tensor([1.0], dtype=DTYPE, requires_grad=True)
        amplitudes = physical_amplitudes(probabilities, relative, modulation_variance)
        ensemble = Ensemble(
            probabilities,
            amplitudes,
            modulation_variance,
            relative,
            c4_symmetric=True,
        )
        epsilon_total = torch.tensor([0.01], dtype=DTYPE) + 0.2 * modulation_variance
        result = _holevo_from_source_moments(
            ensemble,
            torch.tensor([0.1], dtype=DTYPE),
            epsilon_total,
            coherent_correlation=torch.tensor([0.5], dtype=DTYPE),
            w_raw=torch.tensor([0.1], dtype=DTYPE),
            tau=None,
            tau_trace=torch.ones(1, dtype=DTYPE),
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            physicality_tolerance=1e-10,
            diagnostics={},
            maximize_full_interval=True,
        )
        result.chi_be.sum().backward()
        self.assertIsNotNone(modulation_variance.grad)
        self.assertTrue(bool(torch.all(torch.isfinite(modulation_variance.grad))))
        self.assertNotEqual(float(modulation_variance.grad.item()), 0.0)

    def test_ps_and_gs_gradients_reach_worst_case_holevo_branch(self):
        for mode, parameter_name in (("ps", "ps_network"), ("gs", "gs_model")):
            with self.subTest(mode=mode):
                model = JointTransmitter(mode, fixed_va=1.0)
                def fake_source_moments(ensemble, **_kwargs):
                    if mode == "ps":
                        coordinate = ensemble.probabilities[:, 0]
                    else:
                        coordinate = ensemble.amplitudes[:, 0].real
                    correlation = 0.4 + 0.1 * coordinate
                    penalty = 0.1 + 0.01 * coordinate
                    rows = tuple(
                        {
                            "minimum_eigenvalue": 1.0,
                            "support_size": 256,
                        }
                        for _ in range(ensemble.probabilities.shape[0])
                    )
                    return GramMomentResult(correlation, penalty, rows)

                with patch(
                    "src.cvqkd.holevo.c4_gram_source_moments",
                    side_effect=fake_source_moments,
                ):
                    result = holevo_information(
                        model(
                            torch.tensor([0.08], dtype=DTYPE),
                            torch.tensor([0.001], dtype=DTYPE),
                        ),
                        torch.tensor([0.08], dtype=DTYPE),
                        torch.tensor([0.001], dtype=DTYPE),
                        backend="c4_gram",
                        density_eigenvalue_tolerance=1e-13,
                        maximize_full_interval=True,
                    )
                result.chi_be.sum().backward()
                gradients = [
                    parameter.grad
                    for parameter in getattr(model, parameter_name).parameters()
                    if parameter.grad is not None
                ]
                self.assertTrue(gradients)
                self.assertTrue(all(bool(torch.all(torch.isfinite(value))) for value in gradients))
                self.assertGreater(
                    sum(float(torch.linalg.vector_norm(value).detach()) for value in gradients),
                    0.0,
                )


if __name__ == "__main__":
    unittest.main()
