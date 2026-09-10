import types
import unittest
from unittest.mock import patch

import torch

from src.modulation.joint_ps_gs import JointTransmitter
from src.optimization.trainer import evaluate_transmitter


class PipelineConsistencyTests(unittest.TestCase):
    def test_mi_and_holevo_receive_the_identical_ensemble_object(self):
        seen: list[object] = []
        snapshots: list[tuple[torch.Tensor, torch.Tensor]] = []
        epsilons: list[torch.Tensor] = []

        def fake_mi(ensemble, *_args, **_kwargs):
            seen.append(ensemble)
            epsilons.append(_args[1])
            snapshots.append((ensemble.probabilities.clone(), ensemble.amplitudes.clone()))
            return torch.tensor([0.5], dtype=torch.float64)

        def fake_holevo(ensemble, *_args, **_kwargs):
            seen.append(ensemble)
            epsilons.append(_args[1])
            snapshots.append((ensemble.probabilities.clone(), ensemble.amplitudes.clone()))
            return types.SimpleNamespace(chi_be=torch.tensor([0.1], dtype=torch.float64))

        model = JointTransmitter("uniform", fixed_va=2.0)
        with patch("src.optimization.trainer.discrete_mutual_information", side_effect=fake_mi), patch(
            "src.optimization.trainer.holevo_information", side_effect=fake_holevo
        ):
            result = evaluate_transmitter(
                model,
                torch.tensor([0.1], dtype=torch.float64),
                torch.tensor([0.001], dtype=torch.float64),
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(1),
                phase_coefficient=0.25,
            )
        self.assertEqual(len(seen), 2)
        self.assertIs(seen[0], seen[1])
        self.assertIs(seen[0], result.ensemble)
        self.assertEqual(seen[0].probabilities.data_ptr(), seen[1].probabilities.data_ptr())
        self.assertEqual(seen[0].amplitudes.data_ptr(), seen[1].amplitudes.data_ptr())
        for probabilities, amplitudes in snapshots:
            self.assertTrue(torch.equal(probabilities, result.ensemble.probabilities))
            self.assertTrue(torch.equal(amplitudes, result.ensemble.amplitudes))
        expected_epsilon = torch.tensor([0.001], dtype=torch.float64) + (
            0.25 * result.ensemble.declared_va
        )
        self.assertEqual(len(epsilons), 2)
        self.assertIs(epsilons[0], epsilons[1])
        torch.testing.assert_close(epsilons[0], expected_epsilon)
        torch.testing.assert_close(epsilons[1], expected_epsilon)

    def test_missing_phase_coefficient_fails_closed(self):
        model = JointTransmitter("uniform", fixed_va=2.0)
        with self.assertRaisesRegex(ValueError, "phase_coefficient"):
            evaluate_transmitter(
                model,
                torch.tensor([0.1], dtype=torch.float64),
                torch.tensor([0.001], dtype=torch.float64),
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(3),
            )

    def test_policy_path_rejects_aoa_outage_without_evaluating_log10_zero(self):
        model = JointTransmitter("uniform", fixed_va=2.0)
        with self.assertRaisesRegex(ValueError, "outage"):
            evaluate_transmitter(
                model,
                torch.tensor([0.0], dtype=torch.float64),
                torch.tensor([0.001], dtype=torch.float64),
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(30),
                phase_coefficient=0.0,
            )

    def test_phase_coefficient_cannot_change_policy_action(self):
        model = JointTransmitter("full", v_min=0.5, v_max=3.0)
        transmittance = torch.tensor([0.1, 0.2], dtype=torch.float64)
        epsilon_base = torch.tensor([0.001, 0.002], dtype=torch.float64)

        def fake_mi(ensemble, *_args, **_kwargs):
            return torch.zeros(ensemble.probabilities.shape[0], dtype=torch.float64)

        def fake_holevo(ensemble, *_args, **_kwargs):
            return types.SimpleNamespace(
                chi_be=torch.zeros(ensemble.probabilities.shape[0], dtype=torch.float64)
            )

        with patch(
            "src.optimization.trainer.discrete_mutual_information", side_effect=fake_mi
        ), patch("src.optimization.trainer.holevo_information", side_effect=fake_holevo):
            first = evaluate_transmitter(
                model,
                transmittance,
                epsilon_base,
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(4),
                phase_coefficient=0.0,
            )
            second = evaluate_transmitter(
                model,
                transmittance,
                epsilon_base,
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(4),
                phase_coefficient=0.25,
            )
        torch.testing.assert_close(first.ensemble.probabilities, second.ensemble.probabilities)
        torch.testing.assert_close(first.ensemble.amplitudes, second.ensemble.amplitudes)
        torch.testing.assert_close(first.ensemble.declared_va, second.ensemble.declared_va)
        self.assertFalse(torch.equal(first.epsilon_total, second.epsilon_total))

    def test_adaptive_va_receives_gradient_through_total_noise(self):
        model = JointTransmitter("va", v_min=0.5, v_max=3.0)
        transmittance = torch.tensor([0.1, 0.2], dtype=torch.float64)
        epsilon_base = torch.tensor([0.001, 0.002], dtype=torch.float64)

        def fake_mi(_ensemble, _transmittance, epsilon_total, **_kwargs):
            return epsilon_total

        def fake_holevo(ensemble, *_args, **_kwargs):
            return types.SimpleNamespace(
                chi_be=torch.zeros(ensemble.probabilities.shape[0], dtype=torch.float64)
            )

        with patch(
            "src.optimization.trainer.discrete_mutual_information", side_effect=fake_mi
        ), patch("src.optimization.trainer.holevo_information", side_effect=fake_holevo):
            result = evaluate_transmitter(
                model,
                transmittance,
                epsilon_base,
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(5),
                phase_coefficient=0.25,
            )
        (-result.key_rate.fading_average_raw).backward()
        va_gradients = [
            parameter.grad
            for parameter in model.va_network.parameters()
            if parameter.grad is not None
        ]
        self.assertTrue(va_gradients)
        self.assertTrue(all(bool(torch.all(torch.isfinite(grad))) for grad in va_gradients))
        self.assertTrue(any(bool(torch.any(grad != 0.0)) for grad in va_gradients))

    def test_frozen_trainer_rejects_symmetry_override(self):
        model = JointTransmitter("uniform", fixed_va=2.0)
        with self.assertRaises(ValueError):
            evaluate_transmitter(
                model,
                torch.tensor([0.1], dtype=torch.float64),
                torch.tensor([0.001], dtype=torch.float64),
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(2),
                phase_coefficient=0.0,
                require_supported_symmetry=False,
            )


if __name__ == "__main__":
    unittest.main()
