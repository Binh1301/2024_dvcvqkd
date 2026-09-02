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

        def fake_mi(ensemble, *_args, **_kwargs):
            seen.append(ensemble)
            snapshots.append((ensemble.probabilities.clone(), ensemble.amplitudes.clone()))
            return torch.tensor([0.5], dtype=torch.float64)

        def fake_holevo(ensemble, *_args, **_kwargs):
            seen.append(ensemble)
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
            )
        self.assertEqual(len(seen), 2)
        self.assertIs(seen[0], seen[1])
        self.assertIs(seen[0], result.ensemble)
        self.assertEqual(seen[0].probabilities.data_ptr(), seen[1].probabilities.data_ptr())
        self.assertEqual(seen[0].amplitudes.data_ptr(), seen[1].amplitudes.data_ptr())
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
                require_supported_symmetry=False,
            )


if __name__ == "__main__":
    unittest.main()
