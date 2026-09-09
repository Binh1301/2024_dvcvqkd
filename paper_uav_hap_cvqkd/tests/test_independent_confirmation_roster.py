import hashlib
import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_roster_config_is_outcome_uninspected_and_seed_disjoint():
    default = yaml.safe_load((ROOT / "configs" / "default.yaml").read_text(encoding="utf-8"))
    roster = yaml.safe_load(
        (ROOT / "configs" / "independent_confirmation_roster.yaml").read_text(encoding="utf-8")
    )
    assert roster["outcome_inspection_status"] == "NOT_INSPECTED"
    forbidden = set(default["training"]["seeds"].values())
    forbidden.update(default["numerical_validation"]["mi"]["seeds"])
    forbidden.add(default["numerical_validation"]["fixture_initialization_seed"])
    forbidden.add(default["numerical_validation"]["production_gram_candidate_diagnostic"]["gradient_crn_seed"])
    assert roster["channel_base_seed"] not in forbidden
    assert roster["fixture_initialization_seed"] not in forbidden
    assert roster["channel_base_seed"] != roster["fixture_initialization_seed"]


def test_frozen_roster_payload_and_provenance_if_present():
    path = ROOT / "results" / "independent_confirmation_roster.json"
    if not path.exists():
        return
    artifact = json.loads(path.read_text(encoding="utf-8"))
    assert artifact["status"] == "FROZEN_OUTCOME_UNINSPECTED"
    assert artifact["OUTCOME_INSPECTION_STATUS"] == "NOT_INSPECTED"
    guards = artifact["lifecycle_guards"]
    assert not any(guards.values())
    payload = {
        key: artifact[key]
        for key in (
            "selection_design", "channel_realization", "representative_states",
            "fixtures", "aliases", "oracle_subset"
        )
    }
    assert artifact["roster_payload_sha256"] == _canonical_sha256(payload)
    assert len(artifact["representative_states"]) == 3
    assert len(artifact["fixtures"]) >= 16
    assert len(artifact["oracle_subset"]) >= 3
    fixture_names = {row["name"] for row in artifact["fixtures"]}
    assert set(artifact["oracle_subset"]) <= fixture_names
    provenance_mismatches = {}
    for key, relative in (
        ("producer_sha256", "scripts/freeze_independent_confirmation_roster.py"),
        ("config_sha256", "configs/independent_confirmation_roster.yaml"),
        ("default_config_sha256", "configs/default.yaml"),
        ("environment_manifest_sha256", "results/current_environment_manifest.json"),
        ("final_model_spec_sha256", "docs/FINAL_MODEL_SPEC.md"),
        ("schema_sha256", "schemas/independent_confirmation_roster.schema.json"),
    ):
        current = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if artifact["provenance"][key] != current:
            provenance_mismatches[key] = relative
    if provenance_mismatches:
        # A frozen, outcome-uninspected roster must not be overwritten merely
        # because the active security functional was later amended.  It is
        # retained as historical evidence and cannot certify the new model.
        amendment = ROOT / "docs" / "MODEL_AMENDMENT_CURRENT_MANUSCRIPT.md"
        assert amendment.exists()
        text = amendment.read_text(encoding="utf-8")
        assert "historical evidence" in text.lower()
        assert "full-interval" in text


class IndependentConfirmationRosterTests(unittest.TestCase):
    def test_roster_config_is_outcome_uninspected_and_seed_disjoint(self):
        test_roster_config_is_outcome_uninspected_and_seed_disjoint()

    def test_frozen_roster_payload_and_provenance_if_present(self):
        test_frozen_roster_payload_and_provenance_if_present()


if __name__ == "__main__":
    unittest.main()
