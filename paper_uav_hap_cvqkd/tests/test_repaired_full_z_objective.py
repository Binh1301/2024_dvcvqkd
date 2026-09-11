import json
import unittest
from pathlib import Path

import torch

from scripts import run_repaired_full_z_objective as repaired
from src.cvqkd.holevo import _maximize_bounded_scalar


ROOT = Path(__file__).resolve().parents[1]
DTYPE = torch.float64


class RepairedFullZObjectiveTests(unittest.TestCase):
    def test_bounded_maximizer_evaluates_only_interval(self):
        lower = torch.tensor([0.2], dtype=DTYPE)
        upper = torch.tensor([0.3], dtype=DTYPE)
        seen = []

        def objective(points):
            seen.append(points.detach().clone())
            return -(points - 0.27).square()

        _maximize_bounded_scalar(
            lower,
            upper,
            objective,
            grid_size=17,
            refinement_steps=8,
        )
        self.assertTrue(seen)
        evaluated = torch.cat(seen, dim=-1)
        self.assertTrue(bool(torch.all(evaluated >= lower.unsqueeze(-1))))
        self.assertTrue(bool(torch.all(evaluated <= upper.unsqueeze(-1))))

    def test_old_proxy_violation_reproduces_for_all_active_modes(self):
        figure_data = json.loads(
            (ROOT / "results" / "analysis_figure_data_20260911.json").read_text()
        )
        points = repaired._active_points(figure_data)
        for mode, _, _ in repaired.runner.METHODS:
            old_rows = figure_data["grid_security_surrogate"][mode]["rows"]
            candidate_rows = figure_data["candidates"][mode]["rows"]
            for point, old_row, candidate in zip(points, old_rows, candidate_rows):
                with self.subTest(mode=mode, state=point["T"]):
                    proxy = repaired._old_proxy_from_values(
                        point,
                        float(old_row["C"]),
                        float(old_row["w"]),
                        float(candidate["V_A"]),
                    )
                    self.assertTrue(proxy["below_lower"])

    def test_case_a_repaired_objective_matches_reference(self):
        result = repaired._case_a_reproduction()
        self.assertLessEqual(result["errors"]["exact_chi_absolute"], 1.0e-12)
        self.assertLessEqual(result["errors"]["exact_raw_K_absolute"], 1.0e-12)
        self.assertLessEqual(
            result["errors"]["repaired_vs_exact_raw_K_absolute"],
            2.0e-6,
        )
        for name in ("exact", "repaired"):
            row = result[name]
            self.assertLessEqual(row["Z_L"], row["Z_star"] + 1.0e-12)
            self.assertGreaterEqual(row["Z_U"], row["Z_star"] - 1.0e-12)

    def test_repaired_search_matches_production_full_z_and_preserves_interval(self):
        artifact = json.loads(
            (
                ROOT
                / "results"
                / "repaired_full_z_objective_analysis_20260911.json"
            ).read_text()
        )
        rows = [
            row
            for mode in artifact["semantic_interval_audit"]["modes"].values()
            for row in mode["rows"]
        ]
        self.assertEqual(artifact["objective_equivalence"]["all_pass"], True)
        self.assertEqual(
            artifact["semantic_interval_audit"]["all_repaired_interval_violation_count"],
            0,
        )
        self.assertLessEqual(
            max(
                abs(row["chi_production_or_exact"] - row["chi_repaired"])
                for row in rows
            ),
            1.0e-6,
        )
        self.assertTrue(all(row["repaired_selected_valid"] for row in rows))

    def test_gradient_smoke_ps_gs_va_is_finite(self):
        figure_data = json.loads(
            (ROOT / "results" / "analysis_figure_data_20260911.json").read_text()
        )
        result = repaired._gradient_smoke(figure_data)
        self.assertTrue(result["all_pass"])
        self.assertEqual(
            {row["mode"] for row in result["rows"]},
            {"ps", "gs", "va"},
        )
        self.assertTrue(all(row["finite"] for row in result["rows"]))
        self.assertTrue(all(row["gradient_norm"] > 0.0 for row in result["rows"]))


if __name__ == "__main__":
    unittest.main()
