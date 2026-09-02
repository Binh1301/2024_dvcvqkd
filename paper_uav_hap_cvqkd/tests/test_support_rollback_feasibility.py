import json
from pathlib import Path
import sys
import unittest

import torch


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_support_rollback_feasibility import (  # noqa: E402
    _unit_direction, CANDIDATE_THRESHOLD, INITIALIZATION_SEED, MULTIPLIERS,
    NOMINAL_LEARNING_RATES, TRAJECTORY_COUNT_PER_FAMILY, TRAJECTORY_HORIZON,
    TRAJECTORY_MULTIPLIER,
)


class SupportRollbackFeasibilityTests(unittest.TestCase):
    def test_direction_is_unit_norm_and_reproducible(self):
        parameters = {
            "ps_network.a": torch.zeros(3, dtype=torch.float64),
            "ps_network.b": torch.zeros((2, 4), dtype=torch.float64),
        }
        first, seed_first, hash_first = _unit_direction(
            parameters, family="ps", proposal_index=7
        )
        second, seed_second, hash_second = _unit_direction(
            parameters, family="ps", proposal_index=7
        )
        norm = torch.sqrt(sum(torch.sum(value.square()) for value in first.values()))
        self.assertAlmostEqual(float(norm), 1.0, places=14)
        self.assertEqual(seed_first, seed_second)
        self.assertEqual(hash_first, hash_second)
        self.assertTrue(all(torch.equal(first[name], second[name]) for name in first))

    def test_prospective_grid_constants_are_exact(self):
        self.assertEqual(CANDIDATE_THRESHOLD, 1e-13)
        self.assertEqual(INITIALIZATION_SEED, 202613)
        self.assertEqual(MULTIPLIERS, (1, 3, 10, 30, 100))
        self.assertEqual(
            NOMINAL_LEARNING_RATES, {"ps": 3e-4, "gs": 1e-4, "va": 1e-4}
        )
        self.assertEqual(TRAJECTORY_COUNT_PER_FAMILY, 8)
        self.assertEqual(TRAJECTORY_HORIZON, 32)
        self.assertEqual(TRAJECTORY_MULTIPLIER, 100)

    def test_schema_cannot_claim_freeze_or_lifecycle_activity(self):
        schema = json.loads(
            (ROOT / "schemas" / "support_rollback_feasibility.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            schema["properties"]["status"]["const"],
            "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        )
        guards = schema["properties"]["lifecycle_guards"]["properties"]
        self.assertTrue(all(value["const"] is False for value in guards.values()))

    def test_generated_grid_has_exact_requested_dimensions(self):
        path = ROOT / "results" / "support_rollback_feasibility.json"
        if not path.exists():
            self.skipTest("Generated rollback artifact is not present.")
        artifact = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["overall"]["proposal_count"], 960)
        self.assertEqual(len(artifact["aggregate_by_family_multiplier"]), 15)
        self.assertEqual(len(artifact["proposal_rows"]), 960)
        self.assertEqual(len(artifact["rollback_trajectory_rows"]), 24)
        self.assertEqual(
            {row["family"] for row in artifact["rollback_trajectory_rows"]},
            {"ps", "gs", "va"},
        )


if __name__ == "__main__":
    unittest.main()
