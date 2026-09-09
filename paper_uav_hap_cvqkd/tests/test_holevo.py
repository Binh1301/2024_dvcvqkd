import unittest

import torch

from src.cvqkd.covariance import (
    PhysicalityError,
    physical_correlation_bound,
    standard_form_covariance,
)
from src.cvqkd.holevo import (
    SecurityDomainError,
    _holevo_from_source_moments,
    density_operator,
    holevo_information,
    shared_fixed_ensemble_holevo_chi,
    support_restricted_source_moments,
)
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import square_qam256, uniform_pmf


class HolevoTests(unittest.TestCase):
    @staticmethod
    def _synthetic_interval_result(
        *,
        center_fraction_of_z_phys: float,
        radius_fraction_of_z_phys: float,
    ):
        """Exercise interval geometry independently of a particular C4 source.

        The source moments below are synthetic, but nonnegative ``w`` makes
        them legitimate inputs to the paper's interval construction.  This
        isolates the implementation's physical-domain and max-over-interval
        behavior from the separate Gram-moment calculation.
        """

        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        transmittance = torch.tensor([0.1], dtype=torch.float64)
        epsilon = torch.tensor([0.001], dtype=torch.float64)
        va = ensemble.computed_va()
        a = 1.0 + va
        b = 1.0 + transmittance * va + transmittance * epsilon
        z_phys = physical_correlation_bound(
            a, b, numerical_tolerance=1e-10
        ).z_phys
        center = center_fraction_of_z_phys * z_phys
        radius = radius_fraction_of_z_phys * z_phys
        coherent_correlation = center / (2.0 * torch.sqrt(transmittance))
        w = radius.square() / (2.0 * transmittance * epsilon)
        result = _holevo_from_source_moments(
            ensemble,
            transmittance,
            epsilon,
            coherent_correlation=coherent_correlation,
            w_raw=w,
            tau=None,
            tau_trace=torch.ones_like(transmittance),
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            physicality_tolerance=1e-10,
            interval_grid_size=65,
            interval_refinement_iterations=16,
            diagnostics={"backend": "synthetic_interval_test"},
        )
        return result, z_phys

    def test_support_restricted_source_moments_match_full_matrix_reference(self):
        t = torch.tensor([0.024], dtype=torch.float64)
        epsilon = torch.tensor([0.02], dtype=torch.float64)
        for kind, nu, va in (
            ("uniform", None, 0.1), ("binomial", None, 1.5),
            ("mb", 0.3, 0.7),
        ):
            ensemble = reference_ensemble(
                kind, batch_size=1, modulation_variance=va, nu_mb=nu
            )
            result = holevo_information(
                ensemble, t, epsilon, backend="fock_diagnostic", fock_cutoff=48,
                density_trace_tolerance=1e-10,
                density_eigenvalue_tolerance=1e-12,
            )
            tau, fock = density_operator(ensemble, 48)
            correlation, penalty, diagnostics = support_restricted_source_moments(
                tau, fock, ensemble.probabilities,
                density_eigenvalue_tolerance=1e-12,
            )
            torch.testing.assert_close(
                correlation, result.coherent_correlation, rtol=1e-12, atol=1e-12
            )
            torch.testing.assert_close(penalty, result.w, rtol=1e-11, atol=1e-12)
            self.assertEqual(len(diagnostics), 1)
            self.assertTrue(all(row["support_size"] > 0 for row in diagnostics))

    def test_shared_fixed_source_cache_matches_generic_holevo(self):
        t = torch.tensor([0.019, 0.024, 0.029], dtype=torch.float64)
        epsilon = torch.tensor([0.04, 0.02, 0.001], dtype=torch.float64)
        for kind, nu, va in (("uniform", None, 0.4), ("binomial", None, 1.5),
                             ("mb", 0.17, 1.2)):
            ensemble = reference_ensemble(
                kind, batch_size=3, modulation_variance=va, nu_mb=nu
            )
            generic = holevo_information(
                ensemble, t, epsilon, backend="c4_gram", fock_cutoff=None,
                density_eigenvalue_tolerance=1e-13,
                density_trace_tolerance=1e-10,
            ).chi_be
            cached = shared_fixed_ensemble_holevo_chi(
                ensemble, t, epsilon, backend="c4_gram", fock_cutoff=None,
                density_eigenvalue_tolerance=1e-13,
                density_trace_tolerance=1e-10,
            )
            torch.testing.assert_close(cached, generic, rtol=0.0, atol=0.0)

    def test_density_operator_has_ket_bra_orientation(self):
        amplitude = torch.tensor([[0.3 + 0.4j]], dtype=torch.complex128)
        probability = torch.ones((1, 1), dtype=torch.float64)
        va = 2.0 * amplitude.abs().square().sum(dim=-1)
        ensemble = Ensemble(probability, amplitude, va, amplitude[0])
        tau, fock = density_operator(ensemble, 8)
        expected = fock[0, 0].unsqueeze(1) @ fock[0, 0].conj().unsqueeze(0)
        legacy_wrong_orientation = expected.conj()
        self.assertTrue(torch.allclose(tau[0], expected, atol=1e-14, rtol=0.0))
        self.assertFalse(torch.allclose(tau[0], legacy_wrong_orientation, atol=1e-14, rtol=0.0))

    def test_symmetric_baseline_holevo_is_finite(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        result = holevo_information(
            ensemble,
            torch.tensor([0.08], dtype=torch.float64),
            torch.tensor([0.001], dtype=torch.float64),
            backend="c4_gram",
            fock_cutoff=None,
            density_eigenvalue_tolerance=1e-13,
        )
        self.assertTrue(bool(torch.all(torch.isfinite(result.chi_be))))
        self.assertTrue(result.covariance.symmetry.standard_form_supported)
        self.assertLess(result.diagnostics["maximum_density_trace_error"], 1e-8)
        self.assertEqual(result.diagnostics["symmetry_tolerance"], 1e-8)
        self.assertIsNone(result.tau)
        torch.testing.assert_close(result.tau_trace, torch.ones_like(result.tau_trace))
        self.assertEqual(result.diagnostics["backend"], "c4_gram")
        self.assertEqual(result.diagnostics["density_trace_tolerance"], 1e-8)
        self.assertEqual(
            result.diagnostics["density_eigenvalue_pseudoinverse_tolerance"], 1e-13
        )
        self.assertEqual(result.diagnostics["physicality_tolerance"], 1e-10)

    def test_public_backend_is_explicit_and_gram_rejects_fock_cutoff(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=0.4)
        t = torch.tensor([0.02], dtype=torch.float64)
        epsilon = torch.tensor([0.01], dtype=torch.float64)
        with self.assertRaises(TypeError):
            holevo_information(  # type: ignore[call-arg]
                ensemble, t, epsilon, density_eigenvalue_tolerance=1e-13
            )
        with self.assertRaisesRegex(ValueError, "rejects fock_cutoff"):
            holevo_information(
                ensemble, t, epsilon, backend="c4_gram", fock_cutoff=72
                , density_eigenvalue_tolerance=1e-13
            )
        with self.assertRaisesRegex(ValueError, "requires an explicit fock_cutoff"):
            holevo_information(
                ensemble, t, epsilon, backend="fock_diagnostic",
                density_eigenvalue_tolerance=1e-13,
            )

    def test_asymmetric_ensemble_is_rejected_by_standard_form_guard(self):
        probabilities = uniform_pmf().clone()
        probabilities[0] += 0.01
        probabilities[1:] -= 0.01 / 255.0
        probabilities = probabilities.unsqueeze(0)
        raw = square_qam256()
        amplitudes = physical_amplitudes(probabilities, raw, torch.tensor([2.0]))
        ensemble = Ensemble(probabilities, amplitudes, torch.tensor([2.0]), raw)
        with self.assertRaises(PhysicalityError):
            standard_form_covariance(
                ensemble,
                torch.tensor([0.1]),
                torch.tensor([0.001]),
                torch.tensor([0.0]),
            )

    def test_unphysical_correlation_is_rejected_without_cap(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        with self.assertRaises(PhysicalityError):
            standard_form_covariance(
                ensemble,
                torch.tensor([0.1]),
                torch.tensor([0.001]),
                torch.tensor([100.0]),
            )

    def test_physical_boundary_symplectic_roots_use_stable_forms(self):
        # These two binary64 cases exercise cancellation in the smaller
        # symplectic root and in the heterodyne conditional eigenvalue.  The
        # supplied correlation is the implementation's physical boundary,
        # so a stable evaluation must accept it without clipping any root.
        cases = (
            (46.461146333425674, 0.0034909983989396447, 1.84946998518394e-11),
            (0.9189930250498547, 0.7516824389811251, 5403.630819492455),
        )
        for va_value, t_value, epsilon_value in cases:
            with self.subTest(va=va_value, t=t_value, epsilon=epsilon_value):
                ensemble = reference_ensemble(
                    "uniform", batch_size=1, modulation_variance=va_value
                )
                transmittance = torch.tensor([t_value], dtype=torch.float64)
                epsilon = torch.tensor([epsilon_value], dtype=torch.float64)
                va = ensemble.computed_va()
                bound = physical_correlation_bound(
                    1.0 + va,
                    1.0 + transmittance * va + transmittance * epsilon,
                    numerical_tolerance=1e-10,
                )
                covariance = standard_form_covariance(
                    ensemble,
                    transmittance,
                    epsilon,
                    bound.z_phys,
                )
                self.assertGreaterEqual(float(covariance.lambda2[0]), 1.0)
                self.assertGreaterEqual(float(covariance.lambda3[0]), 1.0)

    def test_full_interval_intersects_both_sides_of_the_physical_domain(self):
        upper_clipped, z_phys = self._synthetic_interval_result(
            center_fraction_of_z_phys=1.1,
            radius_fraction_of_z_phys=0.4,
        )
        torch.testing.assert_close(upper_clipped.z_minus, 0.7 * z_phys)
        torch.testing.assert_close(upper_clipped.z_plus, 1.5 * z_phys)
        torch.testing.assert_close(upper_clipped.z_lower, 0.7 * z_phys)
        torch.testing.assert_close(upper_clipped.z_upper, z_phys)

        lower_clipped, _ = self._synthetic_interval_result(
            center_fraction_of_z_phys=-1.1,
            radius_fraction_of_z_phys=0.4,
        )
        torch.testing.assert_close(lower_clipped.z_lower, -z_phys)
        torch.testing.assert_close(lower_clipped.z_upper, -0.7 * z_phys)

    def test_degenerate_and_narrow_physical_intervals_are_evaluated(self):
        degenerate, _ = self._synthetic_interval_result(
            center_fraction_of_z_phys=0.0,
            radius_fraction_of_z_phys=0.0,
        )
        torch.testing.assert_close(degenerate.z_lower, torch.zeros_like(degenerate.z_lower))
        torch.testing.assert_close(degenerate.z_upper, torch.zeros_like(degenerate.z_upper))
        self.assertEqual(degenerate.maximizer_location, ("degenerate_interval",))

        narrow, _ = self._synthetic_interval_result(
            center_fraction_of_z_phys=0.2,
            radius_fraction_of_z_phys=1e-10,
        )
        self.assertLessEqual(float(narrow.z_lower[0]), float(narrow.z_star[0]))
        self.assertLessEqual(float(narrow.z_star[0]), float(narrow.z_upper[0]))
        self.assertTrue(bool(torch.all(torch.isfinite(narrow.chi_be))))

    def test_empty_interval_raises_structured_security_domain_failure(self):
        with self.assertRaises(SecurityDomainError) as captured:
            self._synthetic_interval_result(
                center_fraction_of_z_phys=2.0,
                radius_fraction_of_z_phys=0.0,
            )
        error = captured.exception
        self.assertEqual(error.batch_indices, (0,))
        self.assertGreater(
            float(error.interval_diagnostics["z_lower"][0]),
            float(error.interval_diagnostics["z_upper"][0]),
        )

    def test_interval_maximizer_is_not_fixed_to_the_lower_endpoint(self):
        # The Holevo function for this symmetric interval is maximal at Z=0,
        # while the lower endpoint is strictly negative.  It catches a return
        # to the former fixed-Z_minus implementation.
        result, z_phys = self._synthetic_interval_result(
            center_fraction_of_z_phys=0.0,
            radius_fraction_of_z_phys=0.8,
        )
        torch.testing.assert_close(result.z_lower, -0.8 * z_phys)
        self.assertGreater(float(result.z_star[0]), float(result.z_lower[0]))
        self.assertLess(abs(float(result.z_star[0])), 1e-12)
        self.assertGreaterEqual(
            float(result.chi_be[0]), float(result.chi_at_z_lower[0])
        )
        self.assertGreaterEqual(
            float(result.chi_be[0]), float(result.chi_at_z_upper[0])
        )
        diagnostics = result.diagnostics["security_interval"]
        self.assertEqual(diagnostics["maximizer_location"], ("interior",))


if __name__ == "__main__":
    unittest.main()
