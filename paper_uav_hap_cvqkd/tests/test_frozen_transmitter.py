import math
import unittest

import torch

from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.qam256 import c4_orbit_indices, c4_orbit_masses
from src.optimization.constraints import ensemble_state_diagnostics


class FrozenTransmitterTests(unittest.TestCase):
    def setUp(self):
        self.t = torch.tensor([0.01, 0.05, 0.2], dtype=torch.float64)
        self.epsilon = torch.tensor([0.004, 0.002, 0.0005], dtype=torch.float64)

    def test_full_statewise_invariants_and_diagnostics(self):
        model = JointTransmitter("full", v_min=0.2, v_max=5.0)
        ensemble = model(self.t, self.epsilon)
        ensemble.validate(tolerance=1e-11)
        p = ensemble.probabilities
        alpha = ensemble.amplitudes
        va = ensemble.declared_va
        self.assertTrue(
            torch.allclose(p.sum(dim=-1), torch.ones(3, dtype=p.dtype), atol=1e-14, rtol=0.0)
        )
        self.assertTrue(bool(torch.all(p > 0.0)))
        self.assertLess(float(ensemble.weighted_mean().abs().max().detach()), 1e-13)
        self.assertLess(float(ensemble.weighted_pseudomoment().abs().max().detach()), 1e-13)
        self.assertTrue(torch.allclose(ensemble.computed_va(), va, atol=1e-12, rtol=0.0))

        mean_x = torch.sum(p * (2.0 * alpha.real), dim=-1, keepdim=True)
        mean_p = torch.sum(p * (2.0 * alpha.imag), dim=-1, keepdim=True)
        var_x = torch.sum(p * (2.0 * alpha.real - mean_x).square(), dim=-1)
        var_p = torch.sum(p * (2.0 * alpha.imag - mean_p).square(), dim=-1)
        self.assertTrue(torch.allclose(var_x, va, atol=1e-12, rtol=0.0))
        self.assertTrue(torch.allclose(var_p, va, atol=1e-12, rtol=0.0))

        grouped_alpha = alpha[..., c4_orbit_indices()]
        for rotation in range(1, 4):
            self.assertTrue(
                torch.allclose(
                    grouped_alpha[..., rotation],
                    (1j**rotation) * grouped_alpha[..., 0],
                    atol=1e-13,
                    rtol=1e-13,
                )
            )
        q = c4_orbit_masses(p)
        grouped_p = p[..., c4_orbit_indices()]
        self.assertTrue(torch.allclose(grouped_p, q.unsqueeze(-1) / 4.0, atol=1e-15, rtol=0.0))

        diagnostics = ensemble_state_diagnostics(ensemble)
        self.assertEqual(set(diagnostics), {
            "modulation_variance", "mean_photon_number", "maximum_symbol_energy",
            "symbol_energy_quantile_99", "papr", "entropy_bits",
            "minimum_physical_pair_distance", "minimum_relative_pair_distance",
        })
        self.assertTrue(torch.allclose(diagnostics["mean_photon_number"], va / 2.0))
        self.assertTrue(bool(torch.all(diagnostics["papr"] >= 1.0)))
        self.assertTrue(bool(torch.all(torch.isfinite(diagnostics["entropy_bits"]))))
        self.assertTrue(bool(torch.all(diagnostics["minimum_physical_pair_distance"] > 0.0)))
        self.assertTrue(bool(torch.all(diagnostics["minimum_relative_pair_distance"] > 0.0)))

    def test_geometry_is_global_and_only_one_physical_scale_is_statewise(self):
        model = JointTransmitter("full", v_min=0.2, v_max=5.0)
        with torch.no_grad():
            first = model.gs_model()
            ensemble = model(self.t, self.epsilon)
            second = model.gs_model()
        self.assertTrue(torch.equal(first, second))
        self.assertEqual(tuple(model.gs_model.raw_coordinates.shape), (64, 2))
        scale = ensemble.amplitudes / first.unsqueeze(0)
        self.assertLess(float(scale.imag.abs().max()), 1e-13)
        self.assertLess(float((scale.real - scale.real[:, :1]).abs().max()), 1e-13)

    def test_heads_are_capable_of_state_adaptation_without_claiming_training(self):
        model = JointTransmitter("full", v_min=0.2, v_max=5.0)
        with torch.no_grad():
            ps_first, ps_final = model.ps_network.network[0], model.ps_network.network[2]
            ps_first.weight.zero_()
            ps_first.bias.zero_()
            ps_first.weight[0, 0] = 1.0
            ps_first.bias[0] = 5.0
            ps_final.weight.zero_()
            ps_final.weight[0, 0] = 1.0

            va_first, va_final = model.va_network.network[0], model.va_network.network[2]
            va_first.weight.zero_()
            va_first.bias.zero_()
            va_first.weight[0, 0] = 1.0
            va_first.bias[0] = 5.0
            va_final.weight.zero_()
            va_final.bias.zero_()
            va_final.weight[0, 0] = 1.0

        q = model.ps_network.orbit_masses(self.t, self.epsilon)
        va = model.va_network(self.t, self.epsilon)
        self.assertGreater(float(torch.linalg.vector_norm(q[0] - q[-1]).detach()), 1e-6)
        self.assertGreater(float(torch.abs(va[0] - va[-1]).detach()), 1e-6)
        self.assertTrue(bool(torch.all((va >= 0.2) & (va <= 5.0))))

    def test_all_ablation_gradient_owners(self):
        cases = {
            "uniform": (dict(fixed_va=2.0), ()),
            "binomial": (dict(fixed_va=2.0), ()),
            "mb": (dict(fixed_va=2.0, nu_mb=0.1), ()),
            "optimized_mb": (dict(fixed_va=2.0, nu_mb=0.1), ()),
            "ps": (dict(fixed_va=2.0), ("ps",)),
            "gs": (dict(fixed_va=2.0), ("gs",)),
            "va": (dict(v_min=0.2, v_max=5.0), ("va",)),
            "ps_gs": (dict(fixed_va=2.0), ("ps", "gs")),
            "ps_va": (dict(v_min=0.2, v_max=5.0), ("ps", "va")),
            "gs_va": (dict(v_min=0.2, v_max=5.0), ("gs", "va")),
            "full": (dict(v_min=0.2, v_max=5.0), ("ps", "gs", "va")),
        }
        for mode, (arguments, expected) in cases.items():
            with self.subTest(mode=mode):
                model = JointTransmitter(mode, **arguments)
                self.assertEqual(model.trainable_parameter_families(), expected)
                trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
                self.assertEqual(bool(trainable), bool(expected))
                if not expected:
                    continue
                ensemble = model(self.t, self.epsilon)
                symbol_weights = torch.linspace(0.1, 1.0, 256, dtype=torch.float64)
                state_weights = torch.tensor([0.3, 0.7, 1.1], dtype=torch.float64)
                objective = (
                    (ensemble.probabilities * symbol_weights).sum()
                    + (ensemble.amplitudes.abs().square() * symbol_weights).sum()
                    + (ensemble.declared_va * state_weights).sum()
                )
                objective.backward()
                modules = {
                    "ps": model.ps_network,
                    "gs": model.gs_model,
                    "va": model.va_network,
                }
                for family in expected:
                    gradients = [
                        parameter.grad for parameter in modules[family].parameters()
                        if parameter.grad is not None
                    ]
                    self.assertTrue(gradients, family)
                    self.assertTrue(all(bool(torch.all(torch.isfinite(g))) for g in gradients))
                    self.assertGreater(
                        sum(float(torch.linalg.vector_norm(g)) for g in gradients), 0.0, family
                    )
                    self.assertLess(
                        max(float(torch.linalg.vector_norm(g)) for g in gradients), 1e6, family
                    )
                for family in set(modules) - set(expected):
                    self.assertIsNone(modules[family])

    def test_optimized_mb_is_a_frozen_alias_after_validation_selection(self):
        fixed = JointTransmitter("mb", fixed_va=2.0, nu_mb=0.17)(self.t, self.epsilon)
        optimized = JointTransmitter("optimized_mb", fixed_va=2.0, nu_mb=0.17)(
            self.t, self.epsilon
        )
        self.assertTrue(torch.equal(fixed.probabilities, optimized.probabilities))
        self.assertTrue(torch.equal(fixed.amplitudes, optimized.amplitudes))
        self.assertEqual(JointTransmitter("ps", fixed_va=2.0).ps_network.network[-1].out_features, 64)

    def test_fixed_va_respects_common_box_when_bounds_are_supplied(self):
        JointTransmitter("uniform", fixed_va=2.0, v_min=0.5, v_max=3.0)
        with self.assertRaises(ValueError):
            JointTransmitter("uniform", fixed_va=4.0, v_min=0.5, v_max=3.0)


if __name__ == "__main__":
    unittest.main()
