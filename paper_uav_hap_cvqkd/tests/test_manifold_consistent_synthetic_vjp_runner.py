import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_manifold_consistent_synthetic_vjp_validation.py"


class ManifoldConsistentSyntheticVjpRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("manifold_vjp_runner", SCRIPT)
        cls.runner = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.runner)

    def test_fixture_a_is_spectral_only_and_fixture_b_is_prototype_generated(self):
        fixture_a = self.runner._fixture_a()
        fixture_b = self.runner._fixture_b()
        self.assertEqual(len(fixture_a["sectors"]), 4)
        self.assertEqual(fixture_b["probabilities"].shape, (64,))
        self.assertEqual(fixture_b["prototypes"].shape, (64,))
        self.assertEqual(fixture_b["direction"].shape, (64,))

    def test_fixture_b_center_plus_minus_use_all_production_sectors_and_fast_gate(self):
        fixture = self.runner._fixture_b()
        rows = [self.runner._fixture_b_point(fixture, sign) for sign in (0.0, 1.0, -1.0)]
        for row in rows:
            self.assertEqual(len(row["sectors"]), 4)
            self.assertIsNotNone(row["result"])
            self.assertTrue(row["gate"]["all_sectors_positive"])
        self.assertTrue(all(not self.runner.torch.equal(left, right) for left, right in zip(rows[0]["sectors"], rows[1]["sectors"])))

    def test_gate_failure_reports_detailed_gate_values(self):
        with self.assertRaisesRegex(self.runner.ManifoldValidationFailClosed, "minimum_eigenvalue"):
            self.runner._require_fast(None, {"all_sectors_positive": False, "minimum_eigenvalue": -1e-16})

    def test_runner_has_no_independent_sector_direction_api(self):
        self.assertNotIn("_fast_from_sectors", self.runner.__dict__)
        self.assertNotIn("independent_sector", SCRIPT.read_text(encoding="utf-8"))

    def test_parser_rejects_numerical_overrides(self):
        with self.assertRaises(SystemExit):
            self.runner._parser().parse_args(["--step", "1e-5"])


if __name__ == "__main__":
    unittest.main()
