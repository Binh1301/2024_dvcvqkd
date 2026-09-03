import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class FullSupportProtocolTests(unittest.TestCase):
    def test_frozen_backend_contract(self):
        config = yaml.safe_load((ROOT / "configs/full_support_c4_gram_backend_protocol_v1.yaml").read_text())
        json.loads((ROOT / "schemas/full_support_c4_gram_backend_protocol_v1.schema.json").read_text())
        self.assertEqual(config["source_support"], "mathematical_full_support_256")
        self.assertEqual(config["full_support_oracle"]["precision_ladder_decimal_digits"], [1050, 1250, 1450])
        self.assertIn("lambda_threshold_support", config["forbidden"])
        self.assertEqual(config["gradient_mode"], "evaluation_only_fallback_until_analytic_vjp_is_certified")
        frozen = yaml.safe_load((ROOT / "configs/threshold_validation_v1.yaml").read_text())
        self.assertEqual(len(frozen["fixture_roster"]), 12)
        validation = yaml.safe_load((ROOT / "configs/full_support_c4_gram_evaluation_validation_v1.yaml").read_text())
        self.assertEqual(validation["repeat_count"], 2)
