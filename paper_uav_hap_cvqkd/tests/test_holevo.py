import unittest

import torch

from src.cvqkd.covariance import PhysicalityError, standard_form_covariance
from src.cvqkd.holevo import (
    density_operator, holevo_information, shared_fixed_ensemble_holevo_chi,
    support_restricted_source_moments,
)
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import square_qam256, uniform_pmf


class HolevoTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
