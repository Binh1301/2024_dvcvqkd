import unittest

import torch

from src.modulation.joint_ps_gs import reference_ensemble
from src.modulation.qam256 import square_qam256
from src.optimization.losses import paper_loss


class LossTests(unittest.TestCase):
    def test_raw_skr_is_unclipped_and_frozen_regularizers_are_exact(self):
        ensemble = reference_ensemble("uniform", batch_size=2, modulation_variance=2.0)
        raw_skr = torch.tensor([-0.2, 0.5], dtype=torch.float64)
        peak_limit = 0.1
        result = paper_loss(
            raw_skr,
            ensemble,
            square_qam256(),
            lambda_separation=0.0,
            lambda_peak=0.0,
            lambda_drift=0.0,
            separation_scale=0.15,
            peak_energy_limit=peak_limit,
        )
        self.assertAlmostEqual(float(result.negative_skr), -0.15, places=14)
        self.assertAlmostEqual(float(result.total), -0.15, places=14)
        self.assertGreaterEqual(float(result.separation), 0.0)
        self.assertLess(abs(float(result.drift)), 1e-14)
        maximum_energy = ensemble.amplitudes.abs().square().amax(dim=-1)
        expected_peak = torch.relu(maximum_energy / peak_limit - 1.0).square().mean()
        self.assertTrue(torch.allclose(result.peak, expected_peak, atol=1e-14, rtol=0.0))

    def test_invalid_regularizer_settings_are_rejected(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        with self.assertRaises(ValueError):
            paper_loss(
                torch.zeros(1, dtype=torch.float64),
                ensemble,
                square_qam256(),
                lambda_peak=-1.0,
            )


if __name__ == "__main__":
    unittest.main()
