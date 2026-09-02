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

    def test_v2_runner_manifest_is_frozen_and_uses_v2_protocol(self) -> None:
        protocol = yaml.safe_load((ROOT / "configs/pointwise_guard_protocol_v2.yaml").read_text())
        manifest = json.loads((ROOT / "configs/pointwise_guard_execution_manifest_v2.json").read_text())
        self.assertEqual(manifest["status"], "PROSPECTIVE_FROZEN_BEFORE_V2_SMOKE_OUTCOMES")
        self.assertEqual(manifest["protocol_config_sha256"], _sha256(ROOT / "configs/pointwise_guard_protocol_v2.yaml"))
        smoke = protocol["prospective_v2_smoke"]
        frozen = manifest["smoke_parameters"]
        for key in ("initialization_seed", "common_random_seed", "state_labels", "steps", "optimizer", "learning_rates", "energy_dual_learning_rate", "gradient_clip_norm", "regularizers"):
            self.assertEqual(frozen[key], smoke[key], key)
        self.assertEqual(frozen["repetitions"], smoke["repetitions_for_determinism"])
        self.assertFalse(manifest["lifecycle_guards"]["smoke_executed"])

    def test_v2_runner_writes_a_new_result_and_has_no_override_cli(self) -> None:
        source = (ROOT / "scripts/run_pointwise_guard_smoke_v2.py").read_text()
        self.assertIn("pointwise_guard_protocol_v2.yaml", source)
        self.assertIn("pointwise_guard_smoke_v3.json", source)
        for forbidden in ("--tau", "--steps", "--seed", "--precision", "--learning-rate"):
            self.assertNotIn(forbidden, source)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
