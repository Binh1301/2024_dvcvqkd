"""Design-only checks for the frozen prospective pointwise guard V2."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "pointwise_guard_protocol_v2.yaml"
SCHEMA = ROOT / "schemas" / "pointwise_guard_protocol_v2.schema.json"
DOC = ROOT / "docs" / "POINTWISE_GUARD_PROTOCOL_V2.md"
V1_CONFIG = ROOT / "configs" / "pointwise_guard_protocol_v1.yaml"
V1_MANIFEST = ROOT / "configs" / "pointwise_guard_execution_manifest_v1.json"


class PointwiseGuardProtocolV2DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.v1 = yaml.safe_load(V1_CONFIG.read_text(encoding="utf-8"))
        cls.v1_manifest = json.loads(V1_MANIFEST.read_text(encoding="utf-8"))

    def test_implemented_freeze_authorizes_smoke_only(self) -> None:
        self.assertEqual(self.config["status"], "PROPOSED")
        self.assertEqual(self.config["freeze_status"], "FROZEN_BEFORE_IMPLEMENTATION")
        self.assertTrue(self.config["implementation_authorized"])
        self.assertTrue(self.config["implementation_performed"])
        self.assertTrue(self.config["smoke_rerun_authorized"])
        self.assertFalse(self.config["publication_training_authorized"])

    def test_rule_uses_rigorous_gap_once(self) -> None:
        support = self.config["support_certification"]
        rule = self.config["admission_rule"]
        self.assertTrue(support["complete_spectrum_classification_required"])
        self.assertFalse(support["midpoint_ordering_is_proof"])
        self.assertEqual(
            rule["formula"],
            "support_is_rigorously_certified AND certified_margin > 0",
        )
        self.assertEqual(rule["uncertainty_upper_role"], "DIAGNOSTIC_ONLY")
        self.assertIsNone(rule["additional_safety_factor"])
        self.assertEqual(self.config["engineering_gradient_margin"]["value"], 0)

    def test_threshold_statuses_remain_closed(self) -> None:
        threshold = self.config["threshold"]
        self.assertEqual(threshold["lifecycle_status"], "PROPOSED_UNAPPROVED")
        self.assertEqual(threshold["historical_1e_minus_12_status"], "INVALID_UNAPPROVED")
        self.assertTrue(all(value is False for value in self.config["lifecycle_guards"].values()))

    def test_future_smoke_settings_match_v1(self) -> None:
        smoke = self.config["prospective_v2_smoke"]
        v1_smoke = self.v1["smoke_test"]
        self.assertEqual(smoke["status"], "PROSPECTIVE_FROZEN_AND_AUTHORIZED_NOT_RUN")
        for key in (
            "state_source", "state_source_sha256", "state_labels",
            "initialization_seed", "common_random_seed", "steps", "optimizer",
            "learning_rates", "energy_dual_learning_rate", "gradient_clip_norm",
            "regularizers", "repetitions_for_determinism", "no_retuning_after_outcome",
        ):
            self.assertEqual(smoke[key], v1_smoke[key], key)
        self.assertEqual(
            smoke["precision_bits"],
            self.v1_manifest["smoke_parameters"]["precision_bits"],
        )

    def test_schema_and_method_boundary(self) -> None:
        self.assertEqual(
            self.schema["properties"]["admission_rule"]["properties"]["formula"]["const"],
            self.config["admission_rule"]["formula"],
        )
        self.assertIn("midpoint", self.doc)
        self.assertIn("nearest-round", self.doc)
        self.assertIn("fixed-support derivative", self.doc)


if __name__ == "__main__":
    unittest.main()
