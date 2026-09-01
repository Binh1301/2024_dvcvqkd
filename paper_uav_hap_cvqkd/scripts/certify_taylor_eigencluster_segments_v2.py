"""Hash-gated, externally watched V2 feasibility/full-cycle orchestrator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any

try:  # direct script execution
    from _common import ROOT, load_yaml
except ModuleNotFoundError:  # package import in regression tests
    from scripts._common import ROOT, load_yaml
from src.validation.certification_provenance_v2 import (
    ProvenanceFailure,
    sha256,
    verify_freeze_manifest,
)
from src.validation.hard_watchdog_v2 import run_with_hard_timeout


def _selected_subset(roster_hash: str) -> list[dict[str, str]]:
    rows = []
    for family in ("ps", "gs", "va", "mixed"):
        candidates = []
        for state in ("bad", "medium", "good"):
            ranking_hash = hashlib.sha256(
                f"{roster_hash}|{family}|{state}".encode("ascii")
            ).hexdigest()
            candidates.append((ranking_hash, state))
        ranking_hash, state = min(candidates)
        rows.append({"state_label": state, "family": family, "ranking_sha256": ranking_hash})
    return rows


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    import os
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _lifecycle_guards() -> dict[str, bool]:
    return {
        "threshold_approved": False,
        "publication_training_performed": False,
        "final_test_accessed": False,
        "optimized_mb_grid_performed": False,
        "baseline_selection_performed": False,
        "security_functional_changed": False,
    }


def _verify_exact_tau_gate(path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = sha256(path)
    if actual != expected_sha256.lower():
        raise ProvenanceFailure((
            f"exact_tau_artifact_sha256 expected={expected_sha256.lower()} actual={actual}",
        ))
    artifact = json.loads(path.read_text(encoding="utf-8"))
    aggregate = artifact.get("aggregate", {})
    if not (
        artifact.get("status") == "EXACT_TAU_ORACLE_CERTIFIED"
        and int(aggregate.get("fixture_count", -1)) == 4
        and int(aggregate.get("certified_fixture_count", -1)) == 4
        and int(aggregate.get("unresolved_fixture_count", -1)) == 0
        and aggregate.get("complex128_reference_used") is False
    ):
        raise ProvenanceFailure(("exact_tau_oracle_gate_not_certified",))
    return {
        "status": artifact["status"],
        "sha256": actual,
        "certified_fixture_count": 4,
        "unresolved_fixture_count": 0,
    }


def _provenance_failure(output_path: Path, error: Exception) -> dict[str, Any]:
    artifact = {
        "schema_version": "taylor-eigencluster-whole-segment-v2",
        "status": "PROVENANCE_FAILURE",
        "execution_scope": "FEASIBILITY_SUBSET",
        "segment_rows": [],
        "aggregate": {"scientific_evaluation_started": False},
        "lifecycle_guards": _lifecycle_guards(),
        "provenance": {"failure": str(error)},
    }
    _atomic_json(output_path, artifact)
    return artifact


def _segment_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    radii = []
    clusters = []
    for row in rows:
        for node in row.get("nodes", []):
            for sector in node.get("sector_rows", []):
                radii.append(float(sector["taylor_frobenius_radius_upper"]))
                partition = sector.get("last_partition")
                if partition is not None:
                    clusters.append(int(partition["cluster_size"]))
    return {
        "maximum_taylor_frobenius_radius": max(radii) if radii else None,
        "median_cluster_dimension": statistics.median(clusters) if clusters else None,
        "maximum_cluster_dimension": max(clusters) if clusters else None,
    }


def _gate(settings: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    gate = settings["feasibility_gate"]
    metrics = _segment_metrics(rows)
    v1 = settings["v1_comparison"]["feasibility_root_sector0_rho"]
    ratios = []
    for row in rows:
        node_radii = [
            float(sector["taylor_frobenius_radius_upper"])
            for node in row.get("nodes", []) if int(node.get("depth", -1)) == 0
            for sector in node.get("sector_rows", [])
        ]
        key = f"{row['state_label']}/{row['family']}"
        if node_radii and key in v1:
            ratios.append(max(node_radii) / float(v1[key]))
    checks = {
        "all_path_domains_certified": len(rows) == 4 and all(
            row.get("path_domain", {}).get("status") == "PATH_DOMAIN_CERTIFIED" for row in rows
        ),
        "no_provenance_or_resource_failure": all(
            row.get("status") not in {"PROVENANCE_FAILURE", "RESOURCE_LIMIT"} for row in rows
        ),
        "minimum_complete_segments": sum(
            row.get("status") == "CERTIFIED_FIXED_INERTIA" for row in rows
        ) >= int(gate["minimum_certified_segments"]),
        "median_cluster_dimension": (
            metrics["median_cluster_dimension"] is not None
            and metrics["median_cluster_dimension"] <= int(gate["maximum_median_cluster_dimension"])
        ),
        "strictly_below_v1_ambiguity": (
            metrics["maximum_cluster_dimension"] is not None
            and metrics["maximum_cluster_dimension"] < int(gate["v1_minimum_ambiguous_modes"])
        ),
        "taylor_radius_ratio": (
            len(ratios) == 4
            and max(ratios) <= float(gate["maximum_root_radius_ratio_to_v1"])
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "root_radius_ratios_to_v1": ratios,
        **metrics,
    }


def run(
    config_path: Path,
    manifest_path: Path,
    expected_manifest_sha256: str,
    output_path: Path,
    *,
    mode: str,
    exact_tau_artifact: Path,
    expected_exact_tau_sha256: str,
    feasibility_artifact: Path | None,
    expected_feasibility_sha256: str | None,
) -> dict[str, Any]:
    try:
        provenance = verify_freeze_manifest(
            ROOT, manifest_path, expected_manifest_sha256, require_clean_worktree=True
        )
        settings = load_yaml(config_path)
        exact_tau_gate = _verify_exact_tau_gate(
            exact_tau_artifact, expected_exact_tau_sha256
        )
        roster_hash = sha256(ROOT / settings["confirmation_roster"])
        subset = _selected_subset(roster_hash)
        if subset != settings["feasibility_subset"]:
            raise ProvenanceFailure(("mechanical_feasibility_subset_mismatch",))
        if mode == "full":
            if feasibility_artifact is None or expected_feasibility_sha256 is None:
                raise ProvenanceFailure(("full_cycle_requires_bound_feasibility_artifact",))
            if sha256(feasibility_artifact) != expected_feasibility_sha256:
                raise ProvenanceFailure(("feasibility_artifact_sha256_mismatch",))
            feasibility = json.loads(feasibility_artifact.read_text(encoding="utf-8"))
            if feasibility.get("status") != "FEASIBILITY_GATE_PASS":
                raise ProvenanceFailure(("feasibility_gate_did_not_pass",))
    except (ProvenanceFailure, ValueError, OSError, json.JSONDecodeError) as error:
        return _provenance_failure(output_path, error)

    bundle = ROOT / settings["fixture_bundle"]
    if mode == "feasibility":
        requested = [(row["state_label"], row["family"]) for row in subset]
        scope = "FEASIBILITY_SUBSET"
        total_limit = float(settings["resources"]["maximum_feasibility_seconds"])
    else:
        requested = [(state, family) for state in ("bad", "medium", "good")
                     for family in ("ps", "gs", "va", "mixed")]
        scope = "FULL_12_SEGMENTS"
        total_limit = float(settings["resources"]["maximum_full_cycle_seconds"])

    started = time.perf_counter()
    rows = []
    run_dir = output_path.parent / (output_path.stem + "_work")
    for state, family in requested:
        elapsed = time.perf_counter() - started
        if elapsed >= total_limit:
            rows.append({
                "state_label": state, "family": family, "status": "RESOURCE_LIMIT",
                "reason": "TOTAL_HARD_BUDGET_EXHAUSTED_BEFORE_START",
                "elapsed_seconds": elapsed,
            })
            continue
        checkpoint = run_dir / f"{state}_{family}_checkpoint.json"
        worker_output = run_dir / f"{state}_{family}_result.json"
        watchdog_status = run_dir / f"{state}_{family}_watchdog.json"
        per_limit = min(
            float(settings["resources"]["maximum_seconds_per_segment"]),
            total_limit - elapsed,
        )
        command = [
            sys.executable, str(ROOT / "scripts" / "_taylor_eigencluster_worker_v2.py"),
            "--config", str(config_path), "--bundle", str(bundle),
            "--state", state, "--family", family,
            "--checkpoint", str(checkpoint), "--output", str(worker_output),
        ]
        watchdog = run_with_hard_timeout(
            command, cwd=ROOT, time_limit_seconds=per_limit,
            kill_grace_seconds=float(settings["resources"]["kill_grace_seconds"]),
            fixture=f"{state}/{family}", interval="0/1..1/1",
            checkpoint_path=checkpoint, status_path=watchdog_status,
        )
        if watchdog["status"] == "WORKER_COMPLETED" and worker_output.is_file():
            row = json.loads(worker_output.read_text(encoding="utf-8"))
            row["watchdog"] = watchdog
        else:
            row = {
                "state_label": state, "family": family,
                "status": "RESOURCE_LIMIT" if watchdog["status"] == "RESOURCE_LIMIT"
                else "UNCERTIFIED",
                "watchdog": watchdog,
            }
        rows.append(row)

    feasibility_gate = _gate(settings, rows) if mode == "feasibility" else None
    if mode == "feasibility":
        status = "FEASIBILITY_GATE_PASS" if feasibility_gate["passed"] else "FEASIBILITY_GATE_FAIL_CLOSED"
    else:
        status = "FULL_CYCLE_COMPLETE"
    artifact = {
        "schema_version": "taylor-eigencluster-whole-segment-v2",
        "status": status,
        "execution_scope": scope,
        "candidate_threshold_status": "PROPOSED_UNAPPROVED",
        "segment_rows": rows,
        "feasibility_gate": feasibility_gate,
        "aggregate": {
            "segment_count": len(rows),
            "certified_fixed_inertia_count": sum(row.get("status") == "CERTIFIED_FIXED_INERTIA" for row in rows),
            "proven_crossing_count": sum(row.get("status") == "PROVEN_CROSSING_BY_INERTIA_CHANGE_AND_CONTINUITY" for row in rows),
            "unresolved_count": sum(row.get("status") in {"UNCERTIFIED", "UNCERTIFIED_PATH_DOMAIN"} for row in rows),
            "resource_limit_count": sum(row.get("status") == "RESOURCE_LIMIT" for row in rows),
            "provenance_failure_count": 0,
            "path_domain_certified_count": sum(row.get("path_domain", {}).get("status") == "PATH_DOMAIN_CERTIFIED" for row in rows),
            "attempted_node_count": sum(len(row.get("nodes", [])) for row in rows),
            "runtime_seconds": time.perf_counter() - started,
        },
        "lifecycle_guards": _lifecycle_guards(),
        "provenance": {
            **provenance,
            "exact_tau_oracle_gate": exact_tau_gate,
            "config_sha256": sha256(config_path),
            "fixture_bundle_sha256": sha256(bundle),
            "freeze_manifest_sha256": sha256(manifest_path),
        },
    }
    _atomic_json(output_path, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--expected-freeze-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("feasibility", "full"), default="feasibility")
    parser.add_argument("--exact-tau-artifact", type=Path, required=True)
    parser.add_argument("--expected-exact-tau-sha256", required=True)
    parser.add_argument("--feasibility-artifact", type=Path)
    parser.add_argument("--expected-feasibility-sha256")
    args = parser.parse_args()
    artifact = run(
        args.config.resolve(), args.freeze_manifest.resolve(),
        args.expected_freeze_manifest_sha256, args.output.resolve(), mode=args.mode,
        exact_tau_artifact=args.exact_tau_artifact.resolve(),
        expected_exact_tau_sha256=args.expected_exact_tau_sha256,
        feasibility_artifact=args.feasibility_artifact.resolve()
        if args.feasibility_artifact else None,
        expected_feasibility_sha256=args.expected_feasibility_sha256,
    )
    print(json.dumps({"status": artifact["status"], "aggregate": artifact["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()
