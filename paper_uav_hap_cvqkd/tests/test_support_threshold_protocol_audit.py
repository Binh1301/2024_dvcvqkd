import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_support_threshold_protocol import _comparison  # noqa: E402


class SupportThresholdProtocolAuditTests(unittest.TestCase):
    def test_zero_safe_relative_error_and_frozen_pass_formula_are_separate(self):
        result = _comparison([1e-8], [0.0], "C")
        self.assertTrue(result["passes_frozen_tolerance"])
        self.assertEqual(result["absolute_errors_by_state"], [1e-8])
        self.assertGreater(result["relative_errors_by_state"][0], 1e290)
        self.assertLess(result["maximum_normalized_error_to_tolerance"], 1.0)

    def test_schema_is_proposed_and_fail_closed_on_lifecycle(self):
        schema = json.loads(
            (ROOT / "schemas" / "support_threshold_protocol_audit.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            schema["properties"]["status"]["const"],
            "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        )
        guards = schema["properties"]["lifecycle_guards"]["properties"]
        for field in (
            "publication_training_performed", "test_set_accessed",
            "final_held_out_evaluation_performed", "optimized_mb_grid_performed",
            "baseline_selection_performed", "active_config_changed",
            "physical_or_security_functional_changed",
        ):
            self.assertIs(guards[field]["const"], False)

    def test_generated_artifact_has_complete_disagreement_characterization(self):
        artifact_path = ROOT / "results" / "support_threshold_protocol_audit.json"
        if not artifact_path.exists():
            self.skipTest("Generated diagnostic artifact is not present.")
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["support_disagreement_count"], 12)
        self.assertEqual(len(artifact["support_disagreements"]), 12)
        self.assertTrue(
            artifact["candidate_threshold_assessment"]["all_declared_observables_pass"]
        )
        self.assertFalse(
            artifact["historical_active_threshold_assessment"][
                "all_declared_observables_pass"
            ]
        )
        for row in artifact["support_disagreements"]:
            self.assertEqual(len(row["between_threshold_eigenvalues_by_state"]), 3)
            self.assertEqual(
                set(row["candidate_comparison_to_reference"]),
                {"C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K"},
            )
            for state, rank_reference, rank_candidate in zip(
                row["between_threshold_eigenvalues_by_state"],
                row["reference_retained_rank_by_state"],
                row["candidate_retained_rank_by_state"],
            ):
                self.assertEqual(
                    len(state["between_threshold_eigenvalues"]),
                    rank_reference - rank_candidate,
                )


if __name__ == "__main__":
    unittest.main()
