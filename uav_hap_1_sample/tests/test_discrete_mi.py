from __future__ import annotations

import math
import unittest

import numpy as np
import torch

from uav_hap_1_sample.iab.discrete import mismatched_mi_discrete_awgn, normalize_constellation
from uav_hap_1_sample.zstar.base import build_constellation, gaussian_iab_reference


class DiscreteMutualInformationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.probs = torch.full((256,), 1.0 / 256.0, dtype=torch.float64)
        raw_alpha = torch.tensor(build_constellation(1.0), dtype=torch.complex128)
        self.alpha = normalize_constellation(self.probs, raw_alpha, modulation_variance=2.0)

    @staticmethod
    def _generator(seed: int = 2026) -> torch.Generator:
        return torch.Generator().manual_seed(seed)

    def _mi(
        self,
        transmittance: torch.Tensor | float,
        excess_noise: torch.Tensor | float,
        samples: int = 8,
        alpha: torch.Tensor | None = None,
        probs: torch.Tensor | None = None,
    ) -> torch.Tensor:
        return mismatched_mi_discrete_awgn(
            self.probs if probs is None else probs,
            self.alpha if alpha is None else alpha,
            transmittance,
            excess_noise,
            noise_samples_per_symbol=samples,
            generator=self._generator(),
            antithetic=True,
            candidate_chunk_size=64,
        )

    def test_probability_and_modulation_normalization(self) -> None:
        self.assertLess(abs(float(self.probs.sum()) - 1.0), 1e-10)
        va = 2.0 * torch.sum(self.probs * self.alpha.abs().square())
        mean = torch.sum(self.probs * self.alpha)
        self.assertLess(abs(float(va) - 2.0), 1e-8)
        self.assertLess(abs(complex(mean.item())), 1e-12)

    def test_mi_bounds_and_fading_shape(self) -> None:
        transmittance = torch.tensor([1e-8, 0.05, 0.2, 1.0], dtype=torch.float64)
        mi = self._mi(transmittance, 0.01, samples=16)
        h_x = float(-(self.probs * torch.log2(self.probs)).sum())
        self.assertEqual(tuple(mi.shape), (4,))
        self.assertEqual(mi.dtype, torch.float64)
        self.assertTrue(torch.all(mi >= -1e-10), msg=str(mi))
        self.assertTrue(torch.all(mi <= h_x + 1e-10), msg=str(mi))
        self.assertLessEqual(h_x, math.log2(256) + 1e-12)

    def test_zero_transmittance_limit(self) -> None:
        mi = self._mi(0.0, 0.1, samples=4)
        self.assertLess(abs(float(mi[0])), 1e-12)

    def test_high_snr_and_uniform_qam_limit(self) -> None:
        high_energy_alpha = normalize_constellation(self.probs, self.alpha, modulation_variance=1e6)
        mi = self._mi(1.0, 0.0, samples=4, alpha=high_energy_alpha)
        self.assertLess(abs(float(mi[0]) - 8.0), 1e-8)

    def test_probability_logit_gradient_is_finite_and_nonzero(self) -> None:
        logits = torch.linspace(-0.4, 0.4, 256, dtype=torch.float64, requires_grad=True)
        probs = torch.softmax(logits, dim=0)
        alpha = normalize_constellation(probs, self.alpha, modulation_variance=2.0)
        loss = -self._mi(0.4, 0.02, samples=8, alpha=alpha, probs=probs).mean()
        loss.backward()
        self.assertIsNotNone(logits.grad)
        self.assertTrue(torch.all(torch.isfinite(logits.grad)))
        self.assertGreater(float(torch.linalg.vector_norm(logits.grad)), 1e-10)

    def test_candidate_chunking_matches_full_logsumexp(self) -> None:
        kwargs = {
            "probs": self.probs,
            "alpha": self.alpha,
            "transmittance": torch.tensor([0.1, 0.6], dtype=torch.float64),
            "excess_noise_snu": 0.01,
            "noise_samples_per_symbol": 8,
            "antithetic": True,
        }
        full = mismatched_mi_discrete_awgn(
            **kwargs,
            generator=self._generator(91),
            candidate_chunk_size=None,
        )
        chunked = mismatched_mi_discrete_awgn(
            **kwargs,
            generator=self._generator(91),
            candidate_chunk_size=31,
        )
        self.assertTrue(torch.allclose(full, chunked, atol=1e-12, rtol=1e-12))

    def test_no_nan_or_inf_over_channel_grid(self) -> None:
        transmittance = torch.logspace(-8, 0, 5, dtype=torch.float64)
        excess_noise = torch.linspace(0.0, 0.1, 5, dtype=torch.float64)
        for va in (0.2, 2.0, 20.0):
            alpha = normalize_constellation(self.probs, self.alpha, modulation_variance=va)
            mi = self._mi(transmittance, excess_noise, samples=8, alpha=alpha)
            self.assertTrue(torch.all(torch.isfinite(mi)), msg=f"VA={va}: {mi}")

    def test_legacy_gaussian_reference_regression(self) -> None:
        for t in np.linspace(1e-8, 1.0, 11):
            va = 2.75
            epsilon = 0.031
            expected = math.log2(1.0 + t * va / (2.0 + t * epsilon))
            actual = gaussian_iab_reference(float(t), va, epsilon)
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
