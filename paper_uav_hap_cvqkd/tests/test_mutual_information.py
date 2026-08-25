import unittest

import torch

from src.cvqkd.mutual_information import discrete_mutual_information
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.normalization import physical_amplitudes, weighted_center_and_normalize
from src.modulation.qam256 import square_qam256


class MutualInformationTests(unittest.TestCase):
    def test_zero_transmittance_limit(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        noise = torch.zeros((1, 256, 2), dtype=torch.complex128)
        value = discrete_mutual_information(
            ensemble,
            torch.tensor([0.0]),
            torch.tensor([0.0]),
            noise_samples_per_symbol=2,
            standard_noise_samples=noise,
        )
        self.assertLess(abs(float(value)), 1e-12)

    def test_high_snr_uniform_limit(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1e6)
        generator = torch.Generator().manual_seed(77)
        value = discrete_mutual_information(
            ensemble,
            torch.tensor([1.0]),
            torch.tensor([0.0]),
            noise_samples_per_symbol=4,
            generator=generator,
        )
        self.assertLess(abs(float(value) - 8.0), 1e-8)

    def test_zero_probability_symbols_are_numerically_safe(self):
        probabilities = torch.zeros((1, 256), dtype=torch.float64)
        probabilities[:, :128] = 1.0 / 128.0
        raw = square_qam256()
        unit = weighted_center_and_normalize(probabilities, raw)
        variance = torch.tensor([2.0], dtype=torch.float64)
        ensemble = Ensemble(
            probabilities,
            physical_amplitudes(unit, variance),
            variance,
            raw,
        )
        value = discrete_mutual_information(
            ensemble,
            torch.tensor([0.0]),
            torch.tensor([0.0]),
            noise_samples_per_symbol=1,
            standard_noise_samples=torch.zeros((1, 256, 1), dtype=torch.complex128),
        )
        self.assertTrue(bool(torch.isfinite(value).all()))
        self.assertLess(abs(float(value)), 1e-12)

    def test_differentiable_exact_zero_probability_is_rejected(self):
        probabilities = torch.zeros((1, 256), dtype=torch.float64)
        probabilities[:, :128] = 1.0 / 128.0
        probabilities.requires_grad_(True)
        raw = square_qam256()
        unit = weighted_center_and_normalize(probabilities, raw)
        variance = torch.tensor([2.0], dtype=torch.float64)
        ensemble = Ensemble(
            probabilities,
            physical_amplitudes(unit, variance),
            variance,
            raw,
        )
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            discrete_mutual_information(
                ensemble,
                torch.tensor([0.1]),
                torch.tensor([0.0]),
                noise_samples_per_symbol=1,
                standard_noise_samples=torch.zeros((1, 256, 1), dtype=torch.complex128),
            )


if __name__ == "__main__":
    unittest.main()
