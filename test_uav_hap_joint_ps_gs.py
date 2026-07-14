from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import torch

import uav_hap_joint_ps_gs as shaping


class JointPSGSPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.args = shaping.parse_args(["--smoke-test"])
        self.device = torch.device("cpu")
        self.base_qam = shaping.build_project_qam(self.device)

    def test_weighted_unit_energy_and_gradients(self) -> None:
        logits = torch.linspace(-0.5, 0.5, shaping.SYMBOL_COUNT, dtype=torch.float64)
        logits.requires_grad_(True)
        coordinates = self.base_qam.clone().requires_grad_(True)
        probabilities = torch.softmax(logits, dim=-1).unsqueeze(0)
        unit = shaping.normalize_unit_energy_batch(
            probabilities,
            shaping.complex_from_xy(coordinates),
        )
        mean = torch.sum(probabilities * unit, dim=-1)
        energy = torch.sum(probabilities * unit.abs().square(), dim=-1)
        self.assertLess(float(mean.abs().max().detach()), 1e-10)
        self.assertTrue(torch.allclose(energy, torch.ones_like(energy), atol=1e-10, rtol=0.0))
        objective = unit.real.square().mean() + unit.imag.square().mean()
        objective.backward()
        self.assertTrue(torch.all(torch.isfinite(logits.grad)))
        self.assertTrue(torch.all(torch.isfinite(coordinates.grad)))
        self.assertGreater(float(torch.linalg.vector_norm(logits.grad)), 0.0)
        self.assertGreater(float(torch.linalg.vector_norm(coordinates.grad)), 0.0)

    def test_ps_preserving_joint_is_exact_special_case(self) -> None:
        ps_model = shaping.create_model("ps", self.base_qam, self.args)
        gs_model = shaping.create_model("gs", self.base_qam, self.args, "uniform")
        joint_model = shaping.initialize_joint_candidate(
            "ps_preserving",
            ps_model,
            gs_model,
            self.base_qam,
            self.args,
        )
        transmittance = torch.tensor([0.04, 0.1], dtype=torch.float64)
        noise = shaping.make_standard_complex_noise(
            2,
            shaping.SYMBOL_COUNT,
            self.args.validation_awgn_samples,
            shaping.tensor_generator(2026, self.device),
            self.device,
        )
        self.assertTrue(
            shaping.ps_preserving_metrics_match(
                ps_model,
                joint_model,
                transmittance,
                noise,
                self.args,
            )
        )

    def test_epoch_zero_ranking_can_reject_worse_update(self) -> None:
        epoch_zero = {
            "raw_skr": 0.02,
            "i_ab": 0.10,
            "chi_be": 0.075,
            "peak_energy": 3.0,
            "minimum_pairwise_distance": 0.1,
        }
        worse_update = {
            "raw_skr": 0.019,
            "i_ab": 0.11,
            "chi_be": 0.08,
            "peak_energy": 2.0,
            "minimum_pairwise_distance": 0.2,
        }
        tie_with_better_iab = dict(epoch_zero, i_ab=0.101)
        self.assertFalse(shaping.checkpoint_is_better(worse_update, epoch_zero))
        self.assertTrue(shaping.checkpoint_is_better(tie_with_better_iab, epoch_zero))

    def test_checkpoint_round_trip_restores_model_optimizer_and_rng(self) -> None:
        model = shaping.create_model("joint", self.base_qam, self.args)
        optimizer, _, _ = shaping.build_optimizer(model, 1e-3, 1e-4, "adam", 0.0)
        output = model(torch.tensor([0.08], dtype=torch.float64), self.args.epsilon)
        metrics = {
            "raw_skr": 0.0,
            "i_ab": 0.0,
            "chi_be": 0.0,
            "peak_energy": shaping.geometry_statistics(output)["maximum_symbol_energy"],
            "minimum_pairwise_distance": shaping.geometry_statistics(output)[
                "minimum_pairwise_distance"
            ],
        }
        expected_state = {key: value.clone() for key, value in model.state_dict().items()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.pt"
            shaping.save_training_checkpoint(
                path,
                model,
                optimizer,
                None,
                0,
                "test",
                self.args,
                metrics,
                output,
                0.0,
            )
            expected_random = torch.rand(4)
            with torch.no_grad():
                model.raw_constellation.add_(1.0)
            torch.manual_seed(999)
            shaping.load_training_checkpoint(path, model, optimizer, restore_rng=True)
            actual_random = torch.rand(4)
        for key, expected in expected_state.items():
            self.assertTrue(torch.equal(model.state_dict()[key], expected), msg=key)
        self.assertTrue(torch.equal(expected_random, actual_random))

    def test_chi_be_gradients_reach_probabilities_and_geometry(self) -> None:
        logits = torch.log(shaping.project_probabilities("mb", self.device)).requires_grad_(True)
        coordinates = self.base_qam.clone().requires_grad_(True)
        probabilities = torch.softmax(logits, dim=-1).unsqueeze(0)
        unit = shaping.normalize_unit_energy_batch(
            probabilities,
            shaping.complex_from_xy(coordinates),
        )
        security = shaping.differentiable_security_block(
            probabilities,
            unit,
            torch.tensor([0.08], dtype=torch.float64),
            self.args.epsilon,
            2.0,
            16,
        )
        logit_gradient, coordinate_gradient = torch.autograd.grad(
            security.chi_be.mean(),
            (logits, coordinates),
        )
        self.assertTrue(torch.all(torch.isfinite(logit_gradient)))
        self.assertTrue(torch.all(torch.isfinite(coordinate_gradient)))
        self.assertGreater(float(torch.linalg.vector_norm(logit_gradient)), 1e-12)
        self.assertGreater(float(torch.linalg.vector_norm(coordinate_gradient)), 1e-12)

    def test_mi_fading_streaming_preserves_common_random_numbers(self) -> None:
        transmittance = torch.tensor([0.04, 0.10], dtype=torch.float64)
        output = shaping.model_output_for_baseline(
            "mb",
            transmittance,
            self.base_qam,
            2.0,
        )
        noise_samples = 64
        standard_noise = shaping.make_standard_complex_noise(
            transmittance.numel(),
            shaping.SYMBOL_COUNT,
            noise_samples,
            shaping.tensor_generator(31415, self.device),
            self.device,
        )
        streamed = shaping.discrete_mi_mismatched_awgn_batch(
            output.probabilities,
            output.constellation,
            transmittance,
            self.args.epsilon,
            noise_samples,
            standard_noise,
            64,
        )
        per_state = torch.cat(
            [
                shaping.discrete_mi_mismatched_awgn_batch(
                    output.probabilities[index : index + 1],
                    output.constellation[index : index + 1],
                    transmittance[index : index + 1],
                    self.args.epsilon,
                    noise_samples,
                    standard_noise[index : index + 1],
                    64,
                )
                for index in range(transmittance.numel())
            ]
        )
        self.assertTrue(torch.equal(streamed, per_state))

    def test_full_ncut_security_evaluation_is_finite(self) -> None:
        output = shaping.model_output_for_baseline(
            "uniform",
            torch.tensor([0.08], dtype=torch.float64),
            self.base_qam,
            2.0,
        )
        with torch.no_grad():
            security = shaping.differentiable_security_block(
                output.probabilities,
                output.constellation,
                torch.tensor([0.08], dtype=torch.float64),
                self.args.epsilon,
                2.0,
                150,
            )
        self.assertTrue(torch.all(torch.isfinite(security.chi_be)))
        self.assertTrue(torch.all(torch.isfinite(security.w)))


if __name__ == "__main__":
    unittest.main()
