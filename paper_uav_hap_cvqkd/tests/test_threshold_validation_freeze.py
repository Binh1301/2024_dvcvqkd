import hashlib
from pathlib import Path
import unittest
import copy

import yaml
import torch


ROOT = Path(__file__).resolve().parents[1]


class ThresholdValidationFreezeTests(unittest.TestCase):
    def test_threshold_validation_freeze_is_exact_and_execution_only(self):
        config = yaml.safe_load((ROOT / "configs" / "threshold_validation_v1.yaml").read_text())
        self.assertEqual(config["status"], "FROZEN_BEFORE_EXECUTION")
        self.assertEqual(config["candidate_threshold_float64_hex"], "0x1.c25c268497682p-44")
        self.assertEqual(len(config["fixture_roster"]), 12)
        self.assertEqual(config["oracle"]["precision_sequences"]["regular"], [600, 800])
        self.assertEqual(config["observables"], ["support_rank", "C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K"])
        self.assertFalse(any(config["lifecycle_guards"].values()))
        source = (ROOT / "scripts" / "run_threshold_validation_v1.py").read_text()
        self.assertIn("--execute-frozen-validation", source)
        self.assertIn("threshold_validation_v1.json", source)
        self.assertEqual(hashlib.sha256((ROOT / "docs" / "FINAL_MODEL_SPEC.md").read_bytes()).hexdigest(), "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1")

    def test_production_fixture_hash_overrides_independent_roster_binding(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from _common import load_yaml
        from _numerical_validation import ensemble_sha256, representative_ensembles
        config = yaml.safe_load((ROOT / "configs" / "threshold_validation_v1.yaml").read_text())
        default = copy.deepcopy(load_yaml(ROOT / "configs" / "default.yaml"))
        default["numerical_validation"]["fixture_initialization_seed"] = config["oracle"]["fixture_initialization_seed"]
        states = config["oracle"]["representative_states"]
        t = torch.tensor([row["transmittance"] for row in states], dtype=torch.float64)
        e = torch.tensor([row["epsilon_snu"] for row in states], dtype=torch.float64)
        actual = ensemble_sha256(representative_ensembles(default, t, e)["untrained_full_initialization"])
        self.assertEqual(actual, config["fixture_roster"]["untrained_full_initialization"])
