import unittest

import numpy as np
import torch

from src.channel.atmospheric_loss import kruse_q
from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.modulation.normalization import validate_probabilities
from src.utils.random import SplitSeeds, derive_seed


class InvalidInputTests(unittest.TestCase):
    def test_invalid_visibility(self):
        with self.assertRaises(ValueError):
            kruse_q(0.0)

    def test_invalid_probability_sum(self):
        with self.assertRaises(ValueError):
            validate_probabilities(torch.full((256,), 1.0 / 255.0))

    def test_duplicate_split_seeds(self):
        with self.assertRaises(ValueError):
            SplitSeeds(1, 2, 3, 4, 5, 5).validate()

    def test_namespaced_epoch_seeds_do_not_overlap_splits(self):
        seeds = SplitSeeds(202601, 202602, 202603, 202604, 202605, 202606)
        seeds.validate()
        derived = {
            derive_seed(seeds.validation_channel, "validation_channel"),
            derive_seed(seeds.validation_awgn, "validation_awgn"),
            derive_seed(seeds.test_channel, "test_channel"),
            derive_seed(seeds.test_awgn, "test_awgn"),
        }
        for epoch in range(1000):
            derived.add(derive_seed(seeds.train_channel, "train_channel", epoch))
            derived.add(derive_seed(seeds.train_awgn, "train_awgn", epoch))
        self.assertEqual(len(derived), 2004)

    def test_invalid_sample_count(self):
        with self.assertRaises(ValueError):
            sample_fso_channel(
                geometry=LinkGeometry(),
                wavelength_m=1550e-9,
                visibility_km=10.0,
                beam_waist_m=0.0626,
                aperture_radius_m=0.2,
                cn2_m_minus_two_thirds=1e-15,
                sample_count=0,
                rng=np.random.default_rng(1),
            )


if __name__ == "__main__":
    unittest.main()
