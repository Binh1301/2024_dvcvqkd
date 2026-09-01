"""Design-only regression checks for the frozen pointwise guard protocol."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "pointwise_guard_protocol_v1.yaml"
SCHEMA = ROOT / "schemas" / "pointwise_guard_protocol_v1.schema.json"
DOC = ROOT / "docs" / "POINTWISE_GUARD_PROTOCOL.md"


class PointwiseGuardProtocolDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_protocol_is_proposed_and_lifecycle_closed(self) -> None:
        self.assertEqual(self.config["status"], "PROPOSED")
        self.assertTrue(self.config["implementation_authorized"])
        self.assertFalse(self.config["publication_training_authorized"])
        self.assertEqual(
            self.config["lifecycle_status"], "NOT_READY_FOR_PUBLICATION_SCALE_RUNS"
        )
        self.assertTrue(all(value is False for value in self.config["lifecycle_guards"].values()))

    def test_certification_unit_excludes_noise_samples(self) -> None:
        unit = self.config["pointwise_certification_unit"]
        self.assertEqual(unit["name"], "UNIQUE_REALIZED_STATEWISE_PHYSICAL_ENSEMBLE")
        self.assertIn("individual Monte Carlo noise samples", unit["excludes"])
        self.assertIn("intermediate optimizer interpolation points", unit["excludes"])

    def test_threshold_is_parametric_and_unapproved(self) -> None:
        threshold = self.config["threshold"]
        self.assertEqual(threshold["lifecycle_status"], "PROPOSED_UNAPPROVED")
        self.assertEqual(threshold["historical_1e_minus_12_status"], "INVALID_UNAPPROVED")
        self.assertEqual(self.config["provenance"]["threshold_binding_rule"].count("exact"), 1)

    def test_guard_formula_and_statuses_are_exact(self) -> None:
        guard = self.config["uncertainty_and_guard"]
        self.assertEqual(guard["safety_factor"], 2)
        self.assertEqual(
            guard["guard_inequality"],
            "certified_margin > safety_factor * uncertainty_upper",
        )
        self.assertEqual(
            self.config["statuses"],
            [
                "POINTWISE_ADMISSIBLE",
                "POINTWISE_GUARD_BAND_REJECT",
                "POINTWISE_CERTIFICATION_FAILED",
                "PROVENANCE_FAILURE",
            ],
        )
        self.assertFalse(guard["raw_complex128_distance_is_sufficient"])
        self.assertFalse(guard["whole_segment_proof_required"])

    def test_update_and_rollback_contract_is_complete(self) -> None:
        update = self.config["update_semantics"]
        self.assertTrue(update["pre_update_check"])
        self.assertFalse(update["interpolation_certification"])
        self.assertTrue(update["rejected_proposal_is_noop"])
        rollback = self.config["rollback_state"]
        self.assertEqual(rollback["equivalence_name"], "ROLLBACK_EQUIVALENCE")
        required = rollback["required_fields"]
        for field in (
            "model_parameters", "optimizer", "energy_dual_controller",
            "python_rng", "numpy_rng", "torch_cpu_rng", "explicit_torch_generators",
        ):
            self.assertIn(field, required)
        self.assertFalse(required["schedulers"]["present"])
        self.assertFalse(required["grad_scaler"]["present"])

    def test_test_matrix_and_smoke_are_frozen_before_implementation(self) -> None:
        matrix = self.config["test_matrix"]
        self.assertTrue(matrix["freeze_before_implementation"])
        self.assertEqual(len(matrix["required_cases"]), 20)
        self.assertEqual(len(set(matrix["required_cases"])), 20)
        smoke = self.config["smoke_test"]
        self.assertFalse(smoke["authorized_in_this_task"])
        self.assertEqual(smoke["status"], "PROPOSED_NOT_RUN")
        self.assertEqual(smoke["steps"], 6)
        self.assertEqual(smoke["repetitions_for_determinism"], 2)
        self.assertTrue(smoke["no_retuning_after_outcome"])

    def test_schema_and_claim_boundary_match_design(self) -> None:
        self.assertEqual(self.schema["properties"]["status"]["const"], "PROPOSED")
        self.assertEqual(self.schema["properties"]["statuses"]["const"], self.config["statuses"])
        self.assertIn("global differentiability", self.doc)
        self.assertIn("whole-trajectory certification", self.doc)
        self.assertIn("unchanged validated security functional", self.doc)


if __name__ == "__main__":
    unittest.main()
