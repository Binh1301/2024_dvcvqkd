import unittest

import torch

from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import expand_c4_orbit_masses, expand_c4_orbit_values


class GradientVjpPreflightTests(unittest.TestCase):
    def test_crn_mutual_information_vjp_matches_central_difference(self):
        base = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
        transmittance = torch.tensor([0.02], dtype=torch.float64)
        epsilon = torch.tensor([0.01], dtype=torch.float64)
        noise = standard_complex_noise((1, 256, 4), generator=torch.Generator().manual_seed(202615), device="cpu")

        def objective(scale):
            amplitudes = base.amplitudes * scale
            ensemble = Ensemble(
                base.probabilities, amplitudes, base.declared_va * scale.square(),
                base.raw_constellation, c4_symmetric=True,
            )
            return discrete_mutual_information(
                ensemble, transmittance, epsilon, noise_samples_per_symbol=4,
                standard_noise_samples=noise, noise_sample_chunk_size=4,
            ).mean()

        scale = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
        analytic, = torch.autograd.grad(objective(scale), scale)
        h = 1e-6
        numerical = float((objective(scale.detach() + h) - objective(scale.detach() - h)) / (2 * h))
        self.assertAlmostEqual(float(analytic), numerical, delta=1e-9)

    def test_physical_normalization_identity_and_derivative(self):
        logits = torch.linspace(-0.2, 0.2, 64, dtype=torch.float64, requires_grad=True)
        raw = torch.stack((torch.linspace(1.0, 2.0, 64, dtype=torch.float64), torch.linspace(-0.3, 0.3, 64, dtype=torch.float64)), dim=-1).requires_grad_()
        va = torch.tensor([1.3], dtype=torch.float64, requires_grad=True)
        q = torch.softmax(logits, dim=0)
        p = expand_c4_orbit_masses(q).unsqueeze(0)
        relative = expand_c4_orbit_values(torch.view_as_complex(raw.contiguous()))
        alpha = physical_amplitudes(p, relative, va)
        energy = 2 * torch.sum(p * alpha.abs().square())
        gradients = torch.autograd.grad(energy, (logits, raw, va))
        self.assertAlmostEqual(float(energy.detach()), float(va.detach()), places=12)
        torch.testing.assert_close(gradients[0], torch.zeros_like(logits), atol=1e-12, rtol=1e-11)
        torch.testing.assert_close(gradients[1], torch.zeros_like(raw), atol=1e-12, rtol=1e-11)
        torch.testing.assert_close(gradients[2], torch.ones_like(va), atol=1e-12, rtol=1e-11)

    def test_z_covariance_holevo_and_raw_key_vjp_match_central_difference(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
        transmittance = torch.tensor([0.02], dtype=torch.float64)
        epsilon = torch.tensor([0.01], dtype=torch.float64)

        def objective(inputs):
            result = _holevo_from_source_moments(
                ensemble, transmittance, epsilon,
                coherent_correlation=inputs[:1], w_raw=inputs[1:2],
                tau=None, tau_trace=torch.ones(1, dtype=torch.float64),
                require_supported_symmetry=True, symmetry_tolerance=1e-8,
                physicality_tolerance=1e-10, diagnostics={},
            )
            return 0.95 * inputs[2] - result.chi_be.mean()

        inputs = torch.tensor([0.2, 0.01, 0.03], dtype=torch.float64, requires_grad=True)
        direction = torch.tensor([0.2, -0.1, 0.3], dtype=torch.float64)
        analytic, = torch.autograd.grad(objective(inputs), inputs)
        h = 1e-6
        numerical = float((objective(inputs.detach() + h * direction) - objective(inputs.detach() - h * direction)) / (2 * h))
        self.assertAlmostEqual(float(torch.sum(analytic * direction)), numerical, delta=1e-9)


if __name__ == "__main__":
    unittest.main()
