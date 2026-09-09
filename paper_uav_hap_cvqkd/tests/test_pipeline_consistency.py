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
        received_noise: list[torch.Tensor] = []
        holevo_kwargs: list[dict[str, object]] = []

        def fake_mi(ensemble, _transmittance, epsilon_total, **_kwargs):
            seen.append(ensemble)
            snapshots.append((ensemble.probabilities.clone(), ensemble.amplitudes.clone()))
            received_noise.append(epsilon_total)
            return torch.tensor([0.5], dtype=torch.float64)

        def fake_holevo(ensemble, _transmittance, epsilon_total, **kwargs):
            seen.append(ensemble)
            snapshots.append((ensemble.probabilities.clone(), ensemble.amplitudes.clone()))
            received_noise.append(epsilon_total)
            holevo_kwargs.append(kwargs)
            return types.SimpleNamespace(chi_be=torch.tensor([0.1], dtype=torch.float64))

        model = JointTransmitter("uniform", fixed_va=2.0)
        epsilon_base = torch.tensor([0.001], dtype=torch.float64)
        with patch("src.optimization.trainer.discrete_mutual_information", side_effect=fake_mi), patch(
            "src.optimization.trainer.holevo_information", side_effect=fake_holevo
        ), patch.object(model, "forward", wraps=model.forward) as forward:
            result = evaluate_transmitter(
                model,
                torch.tensor([0.1], dtype=torch.float64),
                epsilon_base,
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(1),
                phase_noise_coefficient=0.25,
                interval_grid_size=17,
                interval_refinement_iterations=5,
            )
        self.assertEqual(len(seen), 2)
        self.assertEqual(len(received_noise), 2)
        self.assertIs(received_noise[0], received_noise[1])
        self.assertEqual(holevo_kwargs[0]["interval_grid_size"], 17)
        self.assertEqual(holevo_kwargs[0]["interval_refinement_iterations"], 5)
        torch.testing.assert_close(
            received_noise[0], torch.tensor([0.501], dtype=torch.float64)
        )
        torch.testing.assert_close(result.epsilon_total, received_noise[0])
        self.assertIs(seen[0], seen[1])
        self.assertIs(seen[0], result.ensemble)
        self.assertEqual(seen[0].probabilities.data_ptr(), seen[1].probabilities.data_ptr())
        self.assertEqual(seen[0].amplitudes.data_ptr(), seen[1].amplitudes.data_ptr())
        self.assertEqual(forward.call_count, 1)
        torch.testing.assert_close(forward.call_args.args[1], epsilon_base)
        self.assertNotEqual(float(forward.call_args.args[1][0]), float(received_noise[0][0]))
        for probabilities, amplitudes in snapshots:
            self.assertTrue(torch.equal(probabilities, result.ensemble.probabilities))
            self.assertTrue(torch.equal(amplitudes, result.ensemble.amplitudes))

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
                phase_noise_coefficient=0.0,
                require_supported_symmetry=False,
            )

    def test_fake_downstream_paths_prove_phase_noise_va_gradient_is_not_detached(self):
        model = JointTransmitter("va", v_min=0.5, v_max=3.0)
        seen: list[torch.Tensor] = []

        def fake_mi(_ensemble, _transmittance, epsilon_total, **_kwargs):
            seen.append(epsilon_total)
            return epsilon_total

        def fake_holevo(_ensemble, _transmittance, epsilon_total, **_kwargs):
            seen.append(epsilon_total)
            return types.SimpleNamespace(chi_be=torch.zeros_like(epsilon_total))

        with patch(
            "src.optimization.trainer.discrete_mutual_information", side_effect=fake_mi
        ), patch("src.optimization.trainer.holevo_information", side_effect=fake_holevo):
            result = evaluate_transmitter(
                model,
                torch.tensor([0.02], dtype=torch.float64),
                torch.tensor([0.001], dtype=torch.float64),
                beta_reconciliation=0.95,
                noise_samples_per_symbol=1,
                density_eigenvalue_tolerance=1e-13,
                generator=torch.Generator().manual_seed(3),
                phase_noise_coefficient=0.25,
            )
        self.assertEqual(len(seen), 2)
        self.assertIs(seen[0], seen[1])
        self.assertIs(seen[0], result.epsilon_total)
        (-result.key_rate.fading_average_raw).backward()
        gradients = [
            parameter.grad
            for parameter in model.va_network.parameters()
            if parameter.grad is not None
        ]
        self.assertTrue(gradients)
        self.assertGreater(
            sum(float(torch.linalg.vector_norm(value).detach()) for value in gradients),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
