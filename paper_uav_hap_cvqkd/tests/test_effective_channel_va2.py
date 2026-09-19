import importlib.util
import inspect
import sys
import unittest
from pathlib import Path

import torch

from src.cvqkd.covariance import standard_form_covariance


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "run_effective_channel_va2.py"
spec = importlib.util.spec_from_file_location("effective_channel_va2", SCRIPT)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EffectiveChannelVa2Tests(unittest.TestCase):
    def test_active_physical_channel_pair_ignores_mean_eta(self):
        parameters = runner.physical_channel_parameters(
            0.13900597216092667,
            0.0186,
            0.003985872669589007,
            2.0,
        )
        self.assertNotIn("mean_eta", inspect.signature(
            runner.physical_channel_parameters
        ).parameters)
        self.assertAlmostEqual(parameters["T"], 0.01932266029640432, places=15)
        self.assertAlmostEqual(parameters["epsilon"], 0.026571745339178013, places=15)
        self.assertAlmostEqual(parameters["xi_phase"], 0.007971745339178014, places=15)

    def test_effective_channel_formula(self):
        result = runner.effective_channel_parameters(
            0.0003371622599136337,
            0.017292426936841014,
            6.39781242362223e-05,
            2.0,
        )
        self.assertAlmostEqual(result["T_eff"], 0.0002990280293659847, places=18)
        self.assertAlmostEqual(result["epsilon_eff"], 0.46900815829498876, places=14)
        self.assertAlmostEqual(result["sigma_c2"], 1.0000701232926659, places=14)

    def test_physical_pair_drives_z_and_covariance(self):
        config = runner.load_yaml(ROOT / "configs" / "default.yaml")
        ensemble = runner._ensemble(config, "uniform")
        t = torch.tensor([0.01932266029640432], dtype=torch.float64)
        epsilon = torch.tensor([0.026571745339178013], dtype=torch.float64)
        c = torch.tensor([1.4019995788968012], dtype=torch.float64)
        w = torch.tensor([0.026543338228713933], dtype=torch.float64)
        z_signal = 2.0 * torch.sqrt(t) * c
        z_penalty = torch.sqrt(2.0 * t * epsilon * w)
        z_star = z_signal - z_penalty
        covariance = standard_form_covariance(
            ensemble,
            t,
            epsilon,
            z_star,
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            numerical_tolerance=1e-10,
        )
        expected_b = 1.0 + t * 2.0 + t * epsilon
        self.assertAlmostEqual(float(covariance.matrix[0, 2, 2]), float(expected_b), places=15)
        expected_lambda3 = 3.0 - z_star.square() / (expected_b + 1.0)
        self.assertAlmostEqual(float(covariance.lambda3[0]), float(expected_lambda3), places=15)

    def test_phase_augmented_cross_moment(self):
        value = runner.phase_augmented_eta_xi(
            0.0003371622599136337,
            0.0205,
            0.08462735111962222,
            2.0,
        )
        self.assertAlmostEqual(value, 6.39781242362223e-05, places=18)

    def test_all_reference_ensembles_have_va_two(self):
        config = runner.load_yaml(ROOT / "configs" / "default.yaml")
        for scheme in runner.SCHEMES:
            ensemble = runner._ensemble(config, scheme)
            ensemble.validate()
            torch.testing.assert_close(
                ensemble.computed_va(),
                torch.full((1,), 2.0, dtype=torch.float64),
                atol=1e-12,
                rtol=0.0,
            )
            self.assertEqual(ensemble.probabilities.shape[-1], 256)

    def test_fixed_mb_energy_regression(self):
        from src.modulation.qam256 import maxwell_boltzmann_pmf, square_qam256

        pmf = maxwell_boltzmann_pmf(0.1)
        coefficient = 2.0 * torch.sum(pmf * square_qam256().abs().square())
        self.assertAlmostEqual(
            float(coefficient),
            0.6637540564063298,
            places=14,
        )


if __name__ == "__main__":
    unittest.main()
