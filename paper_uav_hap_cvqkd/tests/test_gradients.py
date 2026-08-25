import unittest

import torch

from src.modulation.joint_ps_gs import AdaptiveVarianceNetwork, JointTransmitter
from src.optimization.trainer import evaluate_transmitter


class GradientTests(unittest.TestCase):
    def setUp(self):
        self.t = torch.tensor([0.02, 0.08], dtype=torch.float64)
        self.epsilon = torch.tensor([0.001, 0.002], dtype=torch.float64)

    def test_ps_gradient(self):
        model = JointTransmitter("ps", fixed_va=2.0)
        output = model(self.t, self.epsilon)
        objective = output.probabilities[:, 0].sum()
        objective.backward()
        gradients = [p.grad for p in model.ps_network.parameters() if p.grad is not None]
        self.assertTrue(gradients)
        self.assertGreater(sum(float(torch.linalg.vector_norm(g)) for g in gradients), 0.0)

    def test_gs_gradient(self):
        model = JointTransmitter("gs", fixed_va=2.0)
        output = model(self.t, self.epsilon)
        objective = output.amplitudes.real.square().mean() + 0.3 * output.amplitudes.imag.square().mean()
        objective.backward()
        gradient = model.gs_model.raw_coordinates.grad
        self.assertTrue(bool(torch.all(torch.isfinite(gradient))))
        self.assertGreater(float(torch.linalg.vector_norm(gradient)), 0.0)

    def test_adaptive_va_bounds_and_gradient(self):
        model = AdaptiveVarianceNetwork(0.2, 5.0)
        value = model(self.t, self.epsilon)
        self.assertTrue(bool(torch.all(value >= 0.2)))
        self.assertTrue(bool(torch.all(value <= 5.0)))
        value.sum().backward()
        gradients = [p.grad for p in model.parameters() if p.grad is not None]
        self.assertGreater(sum(float(torch.linalg.vector_norm(g)) for g in gradients), 0.0)

    def test_adaptive_va_requires_explicit_valid_bounds(self):
        with self.assertRaises(ValueError):
            AdaptiveVarianceNetwork(float("nan"), float("nan"))

    def test_end_to_end_skr_gradients_reach_each_parameter_family(self):
        cases = (
            ("ps", {"fixed_va": 2.0}, "ps_network"),
            ("gs", {"fixed_va": 2.0}, "gs_model"),
            ("gs_va", {"v_min": 0.5, "v_max": 3.0}, "va_network"),
        )
        for mode, arguments, target_name in cases:
            with self.subTest(mode=mode):
                model = JointTransmitter(mode, **arguments)
                evaluation = evaluate_transmitter(
                    model,
                    self.t[:1],
                    self.epsilon[:1],
                    beta_reconciliation=0.95,
                    noise_samples_per_symbol=2,
                    fock_cutoff=40,
                    generator=torch.Generator().manual_seed(900 + len(mode)),
                )
                (-evaluation.key_rate.fading_average_raw).backward()
                target = getattr(model, target_name)
                gradients = [parameter.grad for parameter in target.parameters() if parameter.grad is not None]
                self.assertTrue(gradients)
                self.assertTrue(all(bool(torch.all(torch.isfinite(value))) for value in gradients))
                self.assertGreater(
                    sum(float(torch.linalg.vector_norm(value).detach()) for value in gradients),
                    0.0,
                )


if __name__ == "__main__":
    unittest.main()
