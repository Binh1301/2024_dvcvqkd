import importlib.util
from pathlib import Path
import tempfile
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_gradient_vjp_validation.py"


class GradientVjpRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("gradient_vjp_runner", SCRIPT)
        cls.runner = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.runner)

    def test_frozen_config_loads_all_nine_coordinates(self):
        config = self.runner._load_protocol()
        self.assertEqual(sum(len(rows) for rows in config["parameter_coordinates"].values()), 9)
        self.assertEqual(config["crn_seed"], 202615)
        self.assertEqual(config["mi_sample_count"], 2048)

    def test_crn_is_deterministic(self):
        config = self.runner._load_protocol()
        left = self.runner._noise(config, 3)
        right = self.runner._noise(config, 3)
        torch.testing.assert_close(left, right, atol=0, rtol=0)

    def test_nonfast_route_fails_closed(self):
        with self.assertRaisesRegex(self.runner.GradientValidationFailClosed, "COMPLEX128_FAST"):
            self.runner._require_fast([{"route": "ARBITRARY_PRECISION_FALLBACK"}])

    def test_hash_mismatch_fails_before_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bound.txt").write_text("actual", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                self.runner._verify_bindings(root, {"bound.txt": "0" * 64})

    def test_parser_rejects_numerical_overrides(self):
        with self.assertRaises(SystemExit):
            self.runner._parser().parse_args(["--seed", "1"])

    def test_result_status_is_all_rows_or_fail_closed(self):
        self.assertEqual(self.runner._status([{"passes": True}]), "GRADIENT_VJP_VALIDATION_PASS")
        self.assertEqual(self.runner._status([{"passes": True}, {"passes": False}]), "GRADIENT_VJP_VALIDATION_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
