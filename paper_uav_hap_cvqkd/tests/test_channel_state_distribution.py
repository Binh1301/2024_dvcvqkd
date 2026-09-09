import unittest

import numpy as np

from src.channel.geometry import LinkGeometry
from src.channel.phase_noise import phase_noise_scenario
from src.channel.state_distribution import (
    IndependentUniformBaselineNoise,
    assert_disjoint_state_realizations,
    sample_channel_state_distribution,
)
from src.utils.random import derive_seed


class ChannelStateDistributionTests(unittest.TestCase):
    def _sample(self, seed: int, count: int = 512):
        return sample_channel_state_distribution(
            geometry=LinkGeometry(20_000.0, 0.0, 0.0),
            wavelength_m=1550e-9,
            visibility_km=10.0,
            beam_waist_m=0.0626,
            aperture_radius_m=0.2,
            cn2_m_minus_two_thirds=1e-15,
            epsilon_base=IndependentUniformBaselineNoise(5e-4, 5e-3),
            sample_count=count,
            seed=seed,
        )

    def test_physical_support_and_both_coordinates_vary(self):
        states = self._sample(4101)
        upper = states.fso.atmospheric_transmittance * states.fso.pointing.t0_power
        self.assertTrue(np.all(states.transmittance > 0.0))
        self.assertTrue(np.all(states.transmittance <= upper * (1.0 + 1e-12)))
        self.assertTrue(np.all(states.epsilon_base_snu >= 0.0))
        self.assertTrue(np.all(states.epsilon_base_snu >= 5e-4))
        self.assertTrue(np.all(states.epsilon_base_snu <= 5e-3))
        self.assertGreater(float(np.var(states.transmittance)), 0.0)
        self.assertGreater(float(np.var(states.epsilon_base_snu)), 0.0)
        self.assertEqual(states.metadata["transmittance_physical_upper_bound"], upper)
        self.assertEqual(
            states.metadata["statistical_dependence"],
            "T and epsilon_base independent by construction",
        )

    def test_fixed_seed_reproduces_exact_realization(self):
        first = self._sample(4102)
        second = self._sample(4102)
        np.testing.assert_array_equal(first.transmittance, second.transmittance)
        np.testing.assert_array_equal(first.epsilon_base_snu, second.epsilon_base_snu)
        self.assertEqual(first.realization_sha256, second.realization_sha256)
        self.assertNotEqual(first.transmittance_seed, first.epsilon_base_seed)

    def test_train_validation_test_realizations_do_not_leak(self):
        splits = [
            (name, self._sample(derive_seed(seed, f"{name}_channel")))
            for name, seed in (
                ("train", 202601),
                ("validation", 202603),
                ("test", 202605),
            )
        ]
        assert_disjoint_state_realizations(splits)
        self.assertEqual(len({states.realization_sha256 for _, states in splits}), 3)
        pair_sets = [
            set(zip(states.transmittance.tolist(), states.epsilon_base_snu.tolist()))
            for _, states in splits
        ]
        self.assertFalse(pair_sets[0] & pair_sets[1])
        self.assertFalse(pair_sets[0] & pair_sets[2])
        self.assertFalse(pair_sets[1] & pair_sets[2])

    def test_invalid_or_constant_epsilon_distribution_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "genuinely varies"):
            IndependentUniformBaselineNoise(1e-3, 1e-3).validate()
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            IndependentUniformBaselineNoise(-1e-3, 1e-3).validate()

    def test_joint_realization_requires_at_least_two_states(self):
        with self.assertRaisesRegex(ValueError, "sample_count >= 2"):
            self._sample(4103, count=1)

    def test_attached_phase_scenario_is_bound_to_sampled_geometry(self):
        geometry = LinkGeometry(20_000.0, 0.0, 0.0)
        scenario = phase_noise_scenario(1e-20, 1550e-9, geometry.link_length_m)
        sample_channel_state_distribution(
            geometry=geometry,
            wavelength_m=1550e-9,
            visibility_km=10.0,
            beam_waist_m=0.0626,
            aperture_radius_m=0.2,
            cn2_m_minus_two_thirds=1e-15,
            epsilon_base=IndependentUniformBaselineNoise(5e-4, 5e-3),
            sample_count=32,
            seed=4104,
            phase_noise_scenario=scenario,
        )
        mismatched = phase_noise_scenario(1e-20, 1540e-9, geometry.link_length_m)
        with self.assertRaisesRegex(ValueError, "wavelength_m"):
            sample_channel_state_distribution(
                geometry=geometry,
                wavelength_m=1550e-9,
                visibility_km=10.0,
                beam_waist_m=0.0626,
                aperture_radius_m=0.2,
                cn2_m_minus_two_thirds=1e-15,
                epsilon_base=IndependentUniformBaselineNoise(5e-4, 5e-3),
                sample_count=32,
                seed=4105,
                phase_noise_scenario=mismatched,
            )


if __name__ == "__main__":
    unittest.main()
