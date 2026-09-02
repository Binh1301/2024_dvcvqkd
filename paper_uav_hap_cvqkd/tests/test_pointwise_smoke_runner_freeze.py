"""Read-only checks for the frozen pointwise smoke runner and manifest."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class PointwiseSmokeRunnerFreezeTests(unittest.TestCase):
    def test_manifest_and_protocol_parameters_match(self) -> None:
        protocol = yaml.safe_load((ROOT / "configs/pointwise_guard_protocol_v1.yaml").read_text())
        manifest = json.loads((ROOT / "configs/pointwise_guard_execution_manifest_v1.json").read_text())
        smoke = protocol["smoke_test"]
        frozen = manifest["smoke_parameters"]
        self.assertEqual(frozen["initialization_seed"], smoke["initialization_seed"])
        self.assertEqual(frozen["common_random_seed"], smoke["common_random_seed"])
        self.assertEqual(frozen["state_labels"], smoke["state_labels"])
        self.assertEqual(frozen["steps"], smoke["steps"])
        self.assertEqual(frozen["repetitions"], smoke["repetitions_for_determinism"])
        self.assertFalse(manifest["lifecycle_guards"]["smoke_executed"])

    def test_runner_exposes_no_scientific_override_cli(self) -> None:
        source = (ROOT / "scripts/run_pointwise_guard_smoke.py").read_text()
        self.assertNotIn("argparse", source)
        for forbidden in ("--tau", "--steps", "--seed", "--precision", "--learning-rate"):
            self.assertNotIn(forbidden, source)
        self.assertIn("verify_manifest()", source)
        self.assertIn("pointwise_guard_smoke_v2.json", source)


if __name__ == "__main__":
    unittest.main()
