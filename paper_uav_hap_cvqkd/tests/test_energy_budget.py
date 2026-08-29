import unittest

import torch

from src.modulation.joint_ps_gs import JointTransmitter
from src.optimization.trainer import EnergyBudgetController, train_step
from src.optimization.constraints import (
    heldout_budget_comparison_status, validation_expected_budget_status,
)


class EnergyBudgetTests(unittest.TestCase):
    def test_validation_margin_and_heldout_violation_are_fail_closed(self):
        validation = validation_expected_budget_status(1.8, 2.0, 0.25)
        self.assertFalse(validation["expected_budget_feasible"])
        self.assertAlmostEqual(validation["expected_budget_upper_snu"], 2.05)
        heldout = heldout_budget_comparison_status(2.01, 2.0)
        self.assertFalse(heldout["heldout_budget_feasible"])
        self.assertFalse(heldout["comparison_valid"])
        self.assertLess(heldout["heldout_budget_slack_snu"], 0.0)
        self.assertIn("do not retrain/reselect", heldout["invalid_reason"])

    def test_projected_dual_ascent_is_nonnegative(self):
        controller = EnergyBudgetController(
            va_budget=1.0, dual_learning_rate=0.2, multiplier=0.5
        )
        term, violation = controller.constraint_term(
            torch.tensor([2.0, 2.0], dtype=torch.float64)
        )
        self.assertAlmostEqual(float(term), 0.5)
        self.assertAlmostEqual(float(violation), 1.0)
        controller.projected_ascent(violation)
        self.assertAlmostEqual(controller.multiplier, 0.7)
        controller.projected_ascent(torch.tensor(-10.0, dtype=torch.float64))
        self.assertEqual(controller.multiplier, 0.0)

    def test_train_step_adds_declared_constraint_term(self):
        model = JointTransmitter("ps", fixed_va=2.0)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        controller = EnergyBudgetController(
            va_budget=1.5, dual_learning_rate=0.1, multiplier=0.4
        )
        result = train_step(
            model,
            optimizer,
            torch.tensor([0.08], dtype=torch.float64),
            torch.tensor([0.001], dtype=torch.float64),
            beta_reconciliation=0.95,
            noise_samples_per_symbol=2,
            density_eigenvalue_tolerance=1e-13,
            generator=torch.Generator().manual_seed(201),
            energy_budget_controller=controller,
        )
        self.assertAlmostEqual(float(result.energy_constraint_violation), 0.5, places=12)
        self.assertAlmostEqual(result.energy_dual_before_update, 0.4, places=12)
        self.assertAlmostEqual(result.energy_dual_after_update, 0.45, places=12)
        expected = result.negative_raw_skr + 0.4 * result.energy_constraint_violation
        self.assertTrue(torch.allclose(result.optimization_loss, expected, atol=1e-14, rtol=0.0))

    def test_controller_parameters_are_explicitly_validated(self):
        with self.assertRaises(ValueError):
            EnergyBudgetController(va_budget=0.0, dual_learning_rate=0.1)
        with self.assertRaises(ValueError):
            EnergyBudgetController(va_budget=1.0, dual_learning_rate=0.0)
        with self.assertRaises(ValueError):
            EnergyBudgetController(va_budget=1.0, dual_learning_rate=0.1, multiplier=-1.0)

    def test_binding_budget_reaches_adaptive_va_and_increases_multiplier(self):
        model = JointTransmitter("va", v_min=0.5, v_max=4.0)
        with torch.no_grad():
            model.va_network.network[-1].weight.zero_()
            model.va_network.network[-1].bias.fill_(1.0)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        controller = EnergyBudgetController(
            va_budget=1.0, dual_learning_rate=0.2, multiplier=0.5
        )
        result = train_step(
            model,
            optimizer,
            torch.tensor([0.08], dtype=torch.float64),
            torch.tensor([0.001], dtype=torch.float64),
            beta_reconciliation=0.95,
            noise_samples_per_symbol=2,
            density_eigenvalue_tolerance=1e-13,
            generator=torch.Generator().manual_seed(1201),
            energy_budget_controller=controller,
        )
        self.assertGreater(float(result.energy_constraint_violation), 0.0)
        self.assertGreater(result.energy_dual_after_update, result.energy_dual_before_update)
        gradients = [p.grad for p in model.va_network.parameters() if p.grad is not None]
        self.assertTrue(gradients)
        self.assertGreater(sum(float(torch.linalg.vector_norm(g)) for g in gradients), 0.0)


if __name__ == "__main__":
    unittest.main()
