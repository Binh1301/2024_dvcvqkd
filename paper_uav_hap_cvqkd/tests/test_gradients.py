import math
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
        objective = output.amplitudes[0, 0].abs().square()
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

    def _transmitter_objective(
        self, model: JointTransmitter, family: str
    ) -> torch.Tensor:
        ensemble = model(self.t, self.epsilon)
        if family == "ps":
            return ensemble.probabilities[0, 0] + 0.2 * ensemble.amplitudes[1, 20].abs().square()
        if family == "gs":
            return ensemble.amplitudes[0, 0].abs().square() + 0.1 * ensemble.amplitudes[1, 17].real
        if family == "va":
            return torch.dot(
                ensemble.declared_va, torch.tensor([0.7, 1.3], dtype=torch.float64)
            )
        raise ValueError(f"Unknown family {family!r}.")

    def test_finite_difference_matches_autograd_for_each_parameter_family(self):
        cases = (
            ("ps", JointTransmitter("ps", fixed_va=2.0), "ps_network"),
            ("gs", JointTransmitter("gs", fixed_va=2.0), "gs_model"),
            ("va", JointTransmitter("va", v_min=0.5, v_max=3.0), "va_network"),
        )
        step = 1e-6
        for family, model, module_name in cases:
            with self.subTest(family=family):
                module = getattr(model, module_name)
                if family in {"ps", "va"}:
                    parameter = module.network[-1].bias
                else:
                    parameter = module.raw_coordinates
                model.zero_grad(set_to_none=True)
                objective = self._transmitter_objective(model, family)
                objective.backward()
                flat_index = int(torch.argmax(parameter.grad.detach().abs()).item())
                index = tuple(
                    int(value)
                    for value in torch.unravel_index(
                        torch.tensor(flat_index, device=parameter.device), parameter.shape
                    )
                )
                automatic = float(parameter.grad[index].detach())
                with torch.no_grad():
                    original = float(parameter[index])
                    parameter[index] = original + step
                    plus = float(self._transmitter_objective(model, family))
                    parameter[index] = original - step
                    minus = float(self._transmitter_objective(model, family))
                    parameter[index] = original
                finite_difference = (plus - minus) / (2.0 * step)
                self.assertTrue(math.isfinite(automatic))
                self.assertTrue(math.isfinite(finite_difference))
                self.assertGreater(abs(automatic), 1e-10)
                self.assertAlmostEqual(automatic, finite_difference, delta=2e-5)

    def test_end_to_end_skr_gradients_reach_each_parameter_family(self):
        cases = (
            ("ps", {"fixed_va": 2.0}, "ps_network"),
            ("gs", {"fixed_va": 2.0}, "gs_model"),
            ("va", {"v_min": 0.5, "v_max": 3.0}, "va_network"),
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

    def test_full_skr_reaches_all_three_enabled_families(self):
        model = JointTransmitter("full", v_min=0.5, v_max=3.0)
        evaluation = evaluate_transmitter(
            model,
            self.t[:1],
            self.epsilon[:1],
            beta_reconciliation=0.95,
            noise_samples_per_symbol=2,
            fock_cutoff=40,
            generator=torch.Generator().manual_seed(1900),
        )
        (-evaluation.key_rate.fading_average_raw).backward()
        for target_name in ("ps_network", "gs_model", "va_network"):
            target = getattr(model, target_name)
            gradients = [parameter.grad for parameter in target.parameters() if parameter.grad is not None]
            self.assertTrue(gradients, target_name)
            self.assertTrue(all(bool(torch.all(torch.isfinite(value))) for value in gradients))
            self.assertGreater(
                sum(float(torch.linalg.vector_norm(value).detach()) for value in gradients),
                0.0,
                target_name,
            )


if __name__ == "__main__":
    unittest.main()
