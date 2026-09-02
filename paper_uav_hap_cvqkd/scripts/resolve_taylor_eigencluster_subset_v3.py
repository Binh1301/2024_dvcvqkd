"""Resolve the frozen, outcome-blind V3 feasibility subset.

This selection-only executable intentionally imports no numerical validation,
transmitter, Gram, or result-analysis module.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Any

try:
    from _common import ROOT, load_yaml
except ModuleNotFoundError:
    from scripts._common import ROOT, load_yaml
from src.validation.certification_provenance_v3 import (
    SELECTION_SCHEMA,
    ProvenanceFailure,
    resolve_feasibility_selection,
    sha256,
    verify_preselection_manifest,
)


def _durable_atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.perf_counter_ns()}")
    encoded = (json.dumps(
        payload, indent=2, sort_keys=True, allow_nan=False,
    ) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def resolve(
    config_path: Path,
    preselection_manifest_path: Path,
    expected_preselection_manifest_sha256: str,
    output_path: Path,
    *,
    require_clean_worktree: bool = True,
) -> dict[str, Any]:
    provenance = verify_preselection_manifest(
        ROOT, preselection_manifest_path, expected_preselection_manifest_sha256,
        require_clean_worktree=require_clean_worktree,
    )
    settings = load_yaml(config_path)
    if settings.get("schema_version") != "taylor-eigencluster-certification-config-v3":
        raise ProvenanceFailure(("config_schema_version",))
    if settings.get("status") != (
        "PROSPECTIVE_FROZEN_BEFORE_V3_SELECTION_RESOLUTION_AND_OUTCOMES"
    ):
        raise ProvenanceFailure(("config_status",))
    config_hash = sha256(config_path)
    bindings = provenance["manifest"].get("file_bindings", {})
    config_relative = config_path.resolve().relative_to(ROOT.resolve()).as_posix()
    if bindings.get(config_relative) != config_hash:
        raise ProvenanceFailure(("preselection_manifest_does_not_bind_config",))

    roster_path = ROOT / settings["confirmation_roster"]
    bundle_path = ROOT / settings["fixture_bundle"]
    roster_hash = sha256(roster_path)
    bundle_hash = sha256(bundle_path)
    if roster_hash != settings.get("confirmation_roster_sha256"):
        raise ProvenanceFailure(("config_roster_sha256_mismatch",))
    if bundle_hash != settings.get("fixture_bundle_sha256"):
        raise ProvenanceFailure(("config_fixture_bundle_sha256_mismatch",))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    selection = resolve_feasibility_selection(
        roster_sha256=roster_hash,
        fixture_bundle_sha256=bundle_hash,
        bundle=bundle,
        namespace=settings["selection"]["namespace"],
    )
    artifact = {
        "schema_version": SELECTION_SCHEMA,
        "status": "DETERMINISTIC_SELECTION_RESOLVED_BEFORE_V3_OUTCOMES",
        "scientific_evaluation_started": False,
        "preselection_manifest_sha256": provenance["freeze_manifest_sha256"],
        "config_sha256": config_hash,
        "confirmation_roster_sha256": roster_hash,
        "fixture_bundle_sha256": bundle_hash,
        "selection": selection,
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "full_12_execution_performed": False,
            "security_functional_changed": False,
        },
    }
    _durable_atomic_json(output_path, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--preselection-manifest", type=Path, required=True)
    parser.add_argument("--expected-preselection-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = resolve(
        args.config.resolve(), args.preselection_manifest.resolve(),
        args.expected_preselection_manifest_sha256, args.output.resolve(),
    )
    print(json.dumps({
        "status": artifact["status"],
        "selected_rows": artifact["selection"]["selected_rows"],
    }, indent=2))


if __name__ == "__main__":
    main()
