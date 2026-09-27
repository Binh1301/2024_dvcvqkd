"""Focused V1 tests; synthetic objectives never certify physical gradients."""
import copy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from scripts import optimize_mb_va_adam_fd as opt
from src.cvqkd.gram_moments import GramMomentResult


def synthetic(nu, va):
    k = -(nu - .2) ** 2 - (va - .7) ** 2
    return dict(nu=nu, VA=va, raw_SKR=k, raw_SKR_replicates=[k] * 5,
                I_AB=0., chi_BE=-k, epsilon_total=0., status="TEST")


class MBVAAdamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_two_scalar_parameters_initialization_and_bounds(self):
        model = opt.MBVAParameters()
        parameters = list(model.parameters())
        self.assertEqual(len(parameters), 2)
        self.assertTrue(all(p.numel() == 1 and p.ndim == 0 and p.dtype == torch.float64 for p in parameters))
        nu, va = model()
        self.assertAlmostEqual(float(nu.detach()), .15)
        self.assertAlmostEqual(float(va.detach()), 1.)
        for value in (-10., 10.):
            with torch.no_grad():
                model.u_mb.fill_(value)
                model.u_va.fill_(value)
                nu, va = model()
            self.assertTrue(0 < nu < .3)
            self.assertTrue(.1 < va < 1.5)

    def test_sign_and_same_old_pair_in_one_adam_step(self):
        model = opt.MBVAParameters()
        optimizer = torch.optim.Adam(model.parameters(), lr=.01)
        calls = []
        def evaluate(nu, va):
            calls.append((nu, va))
            return synthetic(nu, va)
        result = opt.joint_adam_step(model, optimizer, evaluate, .001, .01)
        self.assertLess(result["grad_u_nu"], 0)
        self.assertGreater(result["grad_u_va"], 0)
        self.assertAlmostEqual(result["dK_dnu"], .1)
        self.assertAlmostEqual(result["dK_dVA"], -.6)
        self.assertGreater(result["nu"], .15)
        self.assertLess(result["VA"], 1.)
        self.assertGreater(result["raw_SKR"], synthetic(.15, 1.)["raw_SKR"])
        self.assertEqual(len(calls), 5)
        for observed, expected in zip(calls[:4], ((.151, 1.), (.149, 1.), (.15, 1.01), (.15, .99))):
            for left, right in zip(observed, expected):
                self.assertAlmostEqual(left, right)
        self.assertTrue(all(float(optimizer.state[p]["step"]) == 1 for p in model.parameters()))

    def test_failed_stencil_does_not_update(self):
        model = opt.MBVAParameters()
        optimizer = torch.optim.Adam(model.parameters(), lr=.01)
        before = copy.deepcopy(model.state_dict())
        def failure(*_args):
            raise FloatingPointError("stencil failure")
        with self.assertRaisesRegex(FloatingPointError, "stencil failure"):
            opt.joint_adam_step(model, optimizer, failure, .001, .01)
        self.assertFalse(optimizer.state)
        for name, value in model.state_dict().items():
            torch.testing.assert_close(value, before[name], rtol=0, atol=0)

    def test_failed_post_step_restores_logits_and_adam_state(self):
        model = opt.MBVAParameters()
        optimizer = torch.optim.Adam(model.parameters(), lr=.01)
        opt.joint_adam_step(model, optimizer, synthetic, .001, .01)
        state, adam = copy.deepcopy(model.state_dict()), copy.deepcopy(optimizer.state_dict())
        calls = 0
        def failure(nu, va):
            nonlocal calls
            calls += 1
            if calls == 5:
                raise FloatingPointError("post-step failure")
            return synthetic(nu, va)
        with self.assertRaisesRegex(FloatingPointError, "post-step failure"):
            opt.joint_adam_step(model, optimizer, failure, .001, .01)
        for name, value in model.state_dict().items():
            torch.testing.assert_close(value, state[name], rtol=0, atol=0)
        for index, values in optimizer.state_dict()["state"].items():
            for name, value in values.items():
                torch.testing.assert_close(value, adam["state"][index][name], rtol=0, atol=0)

    def test_readiness_gate_and_boundary_stencil(self):
        with tempfile.TemporaryDirectory() as directory:
            _, ready = opt.readiness(synthetic, directory)
            self.assertEqual(ready["status"], "CURRENTLY_VERIFIED_PASS")
            def flat(nu, va):
                return dict(nu=nu, VA=va, raw_SKR=0., raw_SKR_replicates=[0.] * 5)
            _, zero = opt.readiness(flat, directory)
            self.assertEqual(zero["status"], "FAILED")
            self.assertTrue(all(r["status"] == "NEAR_ZERO_OR_UNRESOLVED" for r in zero["rows"]))
        with self.assertRaisesRegex(ValueError, "boundary"):
            opt.stencil(.001, 1., "nu", .01)

    def test_ao_noise_and_landscape_share_crn(self):
        config = opt.load_yaml(opt.ROOT / "configs/default.yaml")
        channel = dict(effective_T=.0002616886826253797, epsilon_base=.0186,
                       c_phi_AO=.05809578321824574)
        def source(*_args):
            # Plumbing fixture: no claim about actual full-support moments.
            return GramMomentResult(torch.zeros(1, dtype=torch.float64), torch.zeros(1, dtype=torch.float64),
                                    ({"route": "TEST"},))
        with tempfile.TemporaryDirectory() as directory, patch.object(opt, "MI_SAMPLES_PER_SYMBOL", 2), patch.object(opt, "MI_SEEDS", (1, 2)):
            evaluate = opt.ExactEvaluator(config, channel, directory, source)
            original = opt.evaluate_fixed_ensemble
            noise_ids, coefficients = [], []
            def tracked(*args, **kwargs):
                noise_ids.append(id(kwargs["standard_noise_samples"]))
                coefficients.append(kwargs["phase_coefficient"])
                return original(*args, **kwargs)
            with patch.object(opt, "evaluate_fixed_ensemble", side_effect=tracked):
                initial = evaluate(.15, 1.)
                changed = evaluate(.15, 1.1)
                opt.local_landscape(evaluate, initial, directory, workers=1)
            self.assertAlmostEqual(initial["epsilon_total"], .0186 + channel["c_phi_AO"])
            self.assertAlmostEqual(changed["epsilon_total"] - initial["epsilon_total"], .1 * channel["c_phi_AO"])
            self.assertEqual(set(noise_ids), {id(n) for n in evaluate.noises})
            self.assertTrue(all(c == channel["c_phi_AO"] for c in coefficients))
            self.assertTrue((Path(directory) / "local_landscape.csv").is_file())
            self.assertTrue(all(row["peak_photons"] <= 30 and row["VA_error"] < 1e-12 for row in evaluate.cache.values()))
            with self.assertRaisesRegex(ValueError, "budget"):
                evaluate(.15, 2.)

    def test_effective_channel_regression_with_existing_exact_cache(self):
        checkpoint = Path(tempfile.gettempdir()) / "cvqkd_mb_nu_0p150000_va2_c4_checkpoint.json"
        if not checkpoint.is_file():
            self.skipTest("Historical exact-input AP regression checkpoint is unavailable")
        config = opt.load_yaml(opt.ROOT / "configs/default.yaml")
        channel = opt.scenario(config)
        self.assertAlmostEqual(channel["c_phi_AO"], .05809578321824574, places=14)
        with tempfile.TemporaryDirectory() as directory:
            report = opt.reproduction(opt.ExactEvaluator(config, channel, directory))
        self.assertEqual(report["status"], "CURRENTLY_VERIFIED_PASS")


if __name__ == "__main__":
    unittest.main()
