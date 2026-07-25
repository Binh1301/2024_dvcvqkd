from __future__ import annotations

import csv
import inspect
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

import uav_hap_joint_ps_gs as core
import visualize_skr_parameter_sweeps as sweeps
from uav_hap_1.channel.channel_model import link_distance_m


class SKRParameterSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.workspace = Path(__file__).resolve().parent
        cls.config = sweeps.load_config(
            cls.workspace / "skr_visualization_config.json",
            quick=True,
            output_override=Path(cls.temporary_directory.name) / "outputs",
        )
        cls.config["repetitions"] = 1
        cls.config["seed_list"] = cls.config["seed_list"][:1]
        cls.config["fading_sample_budget"] = 1
        cls.config["awgn_sample_budget"] = 1
        cls.config["ncut"] = 12
        cls.config["ncut_convergence"]["comparison_ncut"] = 10
        cls.config["ncut_convergence"]["fading_samples"] = 1
        cls.config["ncut_convergence"]["awgn_samples"] = 1
        for sweep in cls.config["sweeps"].values():
            sweep["points"] = 1
        cls.bundle = sweeps.load_scheme_checkpoints(cls.config)
        cls.result = sweeps.run_pipeline(cls.config, tuple(sweeps.SWEEP_SPECS))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_all_six_schemes_and_six_sweeps_are_evaluated(self) -> None:
        self.assertEqual(set(self.result.raw_rows), set(sweeps.SWEEP_SPECS))
        for rows in self.result.raw_rows.values():
            self.assertEqual({row["scheme"] for row in rows}, set(sweeps.SCHEME_ORDER))
            self.assertEqual(len(rows), len(sweeps.SCHEME_ORDER))

    def test_common_random_numbers_are_identical_across_schemes(self) -> None:
        for rows in self.result.raw_rows.values():
            self.assertEqual(len({row["channel_sample_hash"] for row in rows}), 1)
            self.assertEqual(len({row["awgn_sample_hash"] for row in rows}), 1)
            self.assertEqual(len({row["channel_seed"] for row in rows}), 1)
            self.assertEqual(len({row["awgn_seed"] for row in rows}), 1)

    def test_weighted_energy_and_frozen_parameters(self) -> None:
        transmittance = torch.tensor([0.08], dtype=core.REAL_DTYPE)
        with torch.inference_mode():
            outputs = sweeps.build_scheme_outputs(
                self.bundle,
                transmittance,
                float(self.config["baseline_excess_noise_snu"]),
            )
            sweeps.verify_energy_normalization(outputs)
        sweeps.assert_models_unchanged(self.bundle)
        for model in self.bundle.models.values():
            self.assertFalse(model.training)
            self.assertTrue(all(not parameter.requires_grad for parameter in model.parameters()))

    def test_all_metrics_are_finite_and_requested_ncut_is_used(self) -> None:
        for rows in self.result.raw_rows.values():
            for row in rows:
                for field in ("I_AB", "chi_BE", "beta_I_AB", "K_raw", "K_positive"):
                    self.assertTrue(math.isfinite(float(row[field])), msg=(field, row))
                self.assertEqual(int(row["ncut"]), int(self.config["ncut"]))

    def test_turbulence_axis_is_logarithmic(self) -> None:
        self.assertEqual(self.result.plot_xscales["turbulence"], "log")
        values = sweeps.sweep_values(self.config, "turbulence")
        self.assertTrue(np.all(np.diff(values) >= 0.0))

    def test_distance_sweep_preserves_altitudes_and_sets_link_length(self) -> None:
        distance_km = float(sweeps.sweep_values(self.config, "distance")[0])
        geometry = sweeps.geometry_for_sweep(self.config, "distance", distance_km)
        baseline = sweeps.build_geometry(self.config)
        self.assertEqual(geometry.H_UAV_m, baseline.H_UAV_m)
        self.assertEqual(geometry.H_HAP_m, baseline.H_HAP_m)
        self.assertAlmostEqual(link_distance_m(geometry) / 1000.0, distance_km, places=10)

    def test_all_six_png_and_pdf_files_exist(self) -> None:
        for spec in sweeps.SWEEP_SPECS.values():
            for extension in ("png", "pdf"):
                path = self.result.output_dir / f"{spec.figure_stem}.{extension}"
                self.assertTrue(path.exists(), msg=path)
                self.assertGreater(path.stat().st_size, 0)

    def test_expected_csv_columns_exist(self) -> None:
        for spec in sweeps.SWEEP_SPECS.values():
            path = self.result.output_dir / spec.raw_filename
            self.assertTrue(path.exists(), msg=path)
            with path.open("r", newline="", encoding="utf-8") as handle:
                fieldnames = csv.DictReader(handle).fieldnames
            self.assertTrue(set(sweeps.RAW_FIELDS).issubset(fieldnames or []))
        summary_path = self.result.output_dir / "skr_parameter_sweep_summary.csv"
        with summary_path.open("r", newline="", encoding="utf-8") as handle:
            fieldnames = csv.DictReader(handle).fieldnames
        self.assertTrue(set(sweeps.SUMMARY_FIELDS).issubset(fieldnames or []))

    def test_fixed_seed_is_exactly_reproducible(self) -> None:
        value = float(sweeps.sweep_values(self.config, "aperture")[0])
        first = sweeps.evaluate_parameter_point(
            self.bundle,
            self.config,
            "aperture",
            value,
            point_index=0,
            repetition=0,
        )
        second = sweeps.evaluate_parameter_point(
            self.bundle,
            self.config,
            "aperture",
            value,
            point_index=0,
            repetition=0,
        )
        fields = (
            "scheme",
            "I_AB",
            "chi_BE",
            "K_raw",
            "K_positive",
            "channel_sample_hash",
            "awgn_sample_hash",
        )
        self.assertEqual(
            [{field: row[field] for field in fields} for row in first],
            [{field: row[field] for field in fields} for row in second],
        )

    def test_correct_checkpoint_modes_are_loaded(self) -> None:
        expected = {"GS": "gs", "PS": "ps", "PS+GS": "joint"}
        for scheme, mode in expected.items():
            self.assertEqual(self.bundle.checkpoint_metadata[scheme]["mode"], mode)
            self.assertIn(f"best_{mode}.pt", self.bundle.checkpoint_paths[scheme].name)

    def test_binomial_symbol_pmf_is_not_rayleigh_fading(self) -> None:
        actual = core.project_probabilities("binomial", torch.device("cpu")).numpy()
        expected = core.project_zbase.build_probs_binomial()
        uniform = core.project_zbase.build_probs_uniform()
        self.assertTrue(np.array_equal(actual, expected))
        self.assertFalse(np.array_equal(actual, uniform))
        self.assertIn("Binomial QAM", sweeps.SCHEME_ORDER)
        self.assertFalse(any("Rayleigh" in scheme for scheme in sweeps.SCHEME_ORDER))
        channel_source = inspect.getsource(core.channel)
        self.assertIn("generator.rayleigh", channel_source)


if __name__ == "__main__":
    unittest.main()
