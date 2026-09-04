import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class GradientVjpProtocolTests(unittest.TestCase):
    def test_protocol_preserves_evaluation_only_fallback(self):
        config = yaml.safe_load((ROOT / "configs/gradient_vjp_validation_protocol_v1.yaml").read_text())
        json.loads((ROOT / "schemas/gradient_vjp_validation_protocol_v1.schema.json").read_text())
        self.assertEqual(config["scope"], "fast_path_analytic_vjp_only")
        self.assertEqual(config["mi_sample_count"], 2048)
        self.assertEqual(config["crn_seed"], 202615)
        self.assertEqual(len(config["parameter_coordinates"]["ps"]), 3)
        self.assertIn("fallback_autograd", config["forbidden"])
        self.assertFalse(any(config["lifecycle_guards"].values()))
