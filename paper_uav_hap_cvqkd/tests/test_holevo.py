import unittest

import torch

from src.cvqkd.covariance import PhysicalityError, standard_form_covariance
from src.cvqkd.holevo import (
    density_operator, holevo_information, shared_fixed_ensemble_holevo_chi,
)
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import square_qam256, uniform_pmf


class HolevoTests(unittest.TestCase):
    def test_shared_fixed_source_cache_matches_generic_holevo(self):
        t = torch.tensor([0.019, 0.024, 0.029], dtype=torch.float64)
        epsilon = torch.tensor([0.04, 0.02, 0.001], dtype=torch.float64)
        for kind, nu, va in (("uniform", None, 0.4), ("binomial", None, 1.5),
                             ("mb", 0.17, 1.2)):
            ensemble = reference_ensemble(
                kind, batch_size=3, modulation_variance=va, nu_mb=nu
            )
            generic = holevo_information(
                ensemble, t, epsilon, fock_cutoff=72,
                density_trace_tolerance=1e-10,
            ).chi_be
            cached = shared_fixed_ensemble_holevo_chi(
                ensemble, t, epsilon, fock_cutoff=72,
                density_trace_tolerance=1e-10,
            )
            torch.testing.assert_close(cached, generic, rtol=1e-12, atol=1e-12)

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
            fock_cutoff=40,
        )
        self.assertTrue(bool(torch.all(torch.isfinite(result.chi_be))))
        self.assertTrue(result.covariance.symmetry.standard_form_supported)
        self.assertLess(result.diagnostics["maximum_density_trace_error"], 1e-8)
        self.assertEqual(result.diagnostics["symmetry_tolerance"], 1e-8)
        self.assertEqual(result.diagnostics["density_trace_tolerance"], 1e-8)
        self.assertEqual(
            result.diagnostics["density_eigenvalue_pseudoinverse_tolerance"], 1e-12
        )
        self.assertEqual(result.diagnostics["physicality_tolerance"], 1e-10)

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
