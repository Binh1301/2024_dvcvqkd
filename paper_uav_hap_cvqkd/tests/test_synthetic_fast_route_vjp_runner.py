import importlib.util
from pathlib import Path
import tempfile
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_synthetic_fast_route_vjp_validation.py"


class SyntheticFastRouteVjpRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("synthetic_fast_vjp_runner", SCRIPT)
        cls.runner = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.runner)

    def test_frozen_fixture_is_exact_4_by_64_identity_sectors(self):
        fixture = self.runner._fixture()
        self.assertEqual(len(fixture["sectors"]), 4)
        self.assertEqual(fixture["probabilities"].shape, (64,))
        self.assertTrue(all(matrix.shape == (64, 64) for matrix in fixture["sectors"]))
        torch.testing.assert_close(fixture["sectors"][0], torch.eye(64, dtype=torch.complex128) / 256)

    def test_frozen_fixture_uses_existing_fast_kernel_without_fallback(self):
        result, gate = self.runner._fast_fixture_result()
        self.assertIsNotNone(result)
        self.assertTrue(gate["all_sectors_positive"])
        self.assertEqual(gate["sector_condition_number"], 1.0)

    def test_hash_mismatch_and_nonfast_route_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bound.txt").write_text("actual", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                self.runner._verify_bindings(root, {"bound.txt": "0" * 64})
        with self.assertRaisesRegex(self.runner.SyntheticValidationFailClosed, "COMPLEX128_FAST"):
            self.runner._require_fast({"all_sectors_positive": False})

    def test_parser_rejects_numerical_overrides_and_result_is_all_rows(self):
        with self.assertRaises(SystemExit):
            self.runner._parser().parse_args(["--seed", "1"])
        self.assertEqual(self.runner._status([{"passes": True}]), "SYNTHETIC_FAST_ROUTE_VJP_VALIDATION_PASS")
        self.assertEqual(self.runner._status([{"passes": False}]), "SYNTHETIC_FAST_ROUTE_VJP_VALIDATION_FAIL_CLOSED")

    def test_row_uses_frozen_absolute_and_relative_tolerance_fields(self):
        config = self.runner._config()
        row = self.runner._row(
            "synthetic",
            {"analytic": 2.0, "numerical": 1.5, "absolute_error": 0.5, "hermitian_gradient": True, "finite": True},
            config,
        )
        expected = (
            config["finite_difference"]["absolute_tolerance"]
            + config["finite_difference"]["relative_tolerance"] * 2.0
        )
        self.assertEqual(row["allowance"], expected)


if __name__ == "__main__":
    unittest.main()
