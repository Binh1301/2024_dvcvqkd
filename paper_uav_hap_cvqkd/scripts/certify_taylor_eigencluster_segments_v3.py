"""Prospectively frozen V3 feasibility orchestrator.

Only the mechanically selected four-row feasibility scope is executable here.
The parent verifies every freeze binding before loading a scientific fixture,
uses a Windows Job Object for each worker, and reconstructs all attempted work
from the durable journal after completion or forced termination.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any

try:
    from _common import ROOT, load_yaml
except ModuleNotFoundError:
    from scripts._common import ROOT, load_yaml
from src.validation.certification_provenance_v3 import (
    ProvenanceFailure,
    sha256,
    verify_freeze_manifest,
    verify_selection_artifact,
)
from src.validation.durable_journal_v3 import JournalError, replay_journal
from src.validation.hard_watchdog_v3 import run_with_job_timeout


def _remaining_total_budget(
    started: float, total_limit_seconds: float, *, now: float | None = None,
) -> float:
    observed = time.perf_counter() if now is None else float(now)
    return max(0.0, float(total_limit_seconds) - (observed - float(started)))


def _durable_atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.tmp-{os.getpid()}-{time.perf_counter_ns()}"
    )
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


def _lifecycle_guards() -> dict[str, bool]:
    return {
        "threshold_approved": False,
        "publication_training_performed": False,
        "final_test_accessed": False,
        "optimized_mb_grid_performed": False,
        "baseline_selection_performed": False,
        "full_12_execution_performed": False,
        "security_functional_changed": False,
    }


def _verify_exact_tau(path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = sha256(path)
    if actual != expected_sha256.lower():
        raise ProvenanceFailure(("exact_tau_artifact_sha256_mismatch",))
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
    return {"status": artifact["status"], "sha256": actual}


def _verify_preflight(path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = sha256(path)
    if actual != expected_sha256.lower():
        raise ProvenanceFailure(("synthetic_preflight_sha256_mismatch",))
    artifact = json.loads(path.read_text(encoding="utf-8"))
    watchdog = artifact.get("watchdog", {})
    journal = artifact.get("journal_recovery", {})
    if not (
        artifact.get("schema_version") == "taylor-eigencluster-synthetic-preflight-v3"
        and artifact.get("status") == "SYNTHETIC_PREFLIGHT_PASS"
        and int(artifact.get("required_case_count", -1)) == 20
        and int(artifact.get("passed_case_count", -1)) == 20
        and int(artifact.get("failed_case_count", -1)) == 0
        and watchdog.get("passed") is True
        and float(watchdog.get("maximum_observed_overshoot_seconds", 99)) <= 2.0
        and journal.get("passed") is True
    ):
        raise ProvenanceFailure(("synthetic_preflight_not_certified",))
    return {"status": artifact["status"], "sha256": actual}


def _journal_summary(
    journal_directory: Path,
    *,
    identity: dict[str, Any],
    attempt_id: str,
    segment_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    replay = replay_journal(
        journal_directory,
        expected_identity=identity,
        expected_attempt_id=attempt_id,
        expected_segment_id=segment_id,
    )
    if not replay.records:
        raise JournalError("Journal contains no durable records.")
    started = [row for row in replay.records if row["event_type"] == "NODE_STARTED"]
    committed = [
        row for row in replay.records if row["event_type"] == "NODE_COMMITTED"
    ]
    schur = [
        row for row in replay.records
        if row["event_type"] == "SCHUR_ELIMINATION_COMMITTED"
    ]
    summary = {
        "status": "JOURNAL_VALID",
        "head_sha256": replay.head_sha256,
        "chunk_count": len(replay.chunks),
        "record_count": len(replay.records),
        "attempted_node_count": len(started),
        "completed_node_count": len(committed),
        "successful_schur_elimination_count": len(schur),
        "outstanding_node_id": replay.outstanding_node_id,
        "path_domain_persisted": replay.path_domain is not None,
        "path_domain_status": (
            replay.path_domain.get("status") if replay.path_domain else None
        ),
        "segment_completed_event_persisted": replay.completed,
        "torn_tail_count": sum(
            chunk.torn_tail_size_bytes > 0 for chunk in replay.chunks
        ),
        "chunks": [chunk.__dict__ for chunk in replay.chunks],
    }
    return summary, [record["payload"]["node"] for record in committed]


def _terminal_metrics(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    ratios: list[float] = []
    unresolved: list[int] = []
    reduced: list[int] = []
    true_near: list[int] = []
    for node in nodes:
        attempts = node.get("precision_attempts", [])
        last = attempts[-1] if attempts else node
        for sector in last.get("sector_rows", []):
            if sector.get("paired_radius_ratio") is not None:
                ratios.append(float(sector["paired_radius_ratio"]))
            if sector.get("unresolved_far_size") is not None:
                unresolved.append(int(sector["unresolved_far_size"]))
            if sector.get("final_schur_reduced_dimension") is not None:
                reduced.append(int(sector["final_schur_reduced_dimension"]))
            if sector.get("true_near_size") is not None:
                true_near.append(int(sector["true_near_size"]))
    return {
        "paired_radius_ratios": ratios,
        "unresolved_far_distribution": unresolved,
        "final_reduced_dimension_distribution": reduced,
        "true_near_size_distribution": true_near,
    }


def _gate(
    settings: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    preflight: dict[str, Any],
    total_elapsed_seconds: float,
) -> dict[str, Any]:
    gate = settings["feasibility_gate"]
    ratios = [
        value for row in rows for value in row["metrics"]["paired_radius_ratios"]
    ]
    unresolved = [
        value for row in rows
        for value in row["metrics"]["unresolved_far_distribution"]
    ]
    reduced = [
        value for row in rows
        for value in row["metrics"]["final_reduced_dimension_distribution"]
    ]
    spectral_rows = [row for row in rows if row["attempted_node_count"] > 0]
    checks = {
        "exact_four_selected_segments": len(rows) == int(
            gate["exact_selected_segment_count"]
        ),
        "all_twenty_synthetic_cases_passed": preflight["status"] == (
            "SYNTHETIC_PREFLIGHT_PASS"
        ),
        "all_path_domains_certified_and_durable": len(rows) == 4 and all(
            row["path_domain_persisted"]
            and row["path_domain_status"] == "PATH_DOMAIN_CERTIFIED"
            for row in rows
        ),
        "zero_provenance_resource_journal_or_watchdog_defects": all(
            row["status"] not in {"PROVENANCE_FAILURE", "RESOURCE_LIMIT"}
            and row["journal_status"] == "JOURNAL_VALID"
            and row["watchdog"].get("return_bound_satisfied") is True
            for row in rows
        ),
        "minimum_certified_fixed_inertia_segments": sum(
            row["status"] == "CERTIFIED_FIXED_INERTIA" for row in rows
        ) >= int(gate["minimum_certified_fixed_inertia_segments"]),
        "successful_schur_for_every_spectral_segment": bool(spectral_rows) and all(
            row["successful_schur_elimination_count"] >= 1
            for row in spectral_rows
        ),
        "median_terminal_unresolved_far_improves_v2_3": bool(unresolved) and (
            statistics.median(unresolved)
            <= int(gate["maximum_median_terminal_unresolved_far_count"])
        ),
        "median_terminal_reduced_dimension_improves_v2_3": bool(reduced) and (
            statistics.median(reduced)
            <= int(gate["maximum_median_terminal_final_reduced_dimension"])
        ),
        "all_paired_coefficient_radii_strictly_tighter": bool(ratios) and all(
            value < float(
                gate[
                    "require_all_paired_coefficient_to_entrywise_radius_ratios_strictly_below"
                ]
            ) for value in ratios
        ),
        "hard_total_runtime_bound": total_elapsed_seconds <= float(
            settings["resources"]["maximum_feasibility_seconds"]
            + settings["resources"]["maximum_timeout_overshoot_seconds"]
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "paired_radius_ratio_distribution": ratios,
        "unresolved_far_distribution": unresolved,
        "final_reduced_dimension_distribution": reduced,
        "median_terminal_unresolved_far_count": (
            statistics.median(unresolved) if unresolved else None
        ),
        "median_terminal_final_reduced_dimension": (
            statistics.median(reduced) if reduced else None
        ),
        "historical_v2_3_comparison": {
            "certified_segments": 0,
            "crossings": 0,
            "resource_limits": 4,
            "representative_last_unresolved_far_per_sector": 38,
            "representative_effective_reduced_dimension": 62,
            "runtime_seconds": 1800.0382972999942,
        },
    }


def _provenance_failure(output_path: Path, error: Exception) -> dict[str, Any]:
    artifact = {
        "schema_version": "taylor-eigencluster-whole-segment-v3",
        "status": "PROVENANCE_FAILURE",
        "execution_scope": "FEASIBILITY_SUBSET",
        "candidate_threshold_status": "PROPOSED_UNAPPROVED",
        "selection": {}, "segment_rows": [], "feasibility_gate": None,
        "aggregate": {"scientific_evaluation_started": False},
        "lifecycle_guards": _lifecycle_guards(),
        "provenance": {"failure": str(error)},
    }
    _durable_atomic_json(output_path, artifact)
    return artifact


def run(
    config_path: Path,
    freeze_manifest_path: Path,
    expected_freeze_manifest_sha256: str,
    selection_path: Path,
    expected_selection_sha256: str,
    preflight_path: Path,
    expected_preflight_sha256: str,
    output_path: Path,
) -> dict[str, Any]:
    if output_path.exists():
        raise ProvenanceFailure(("v3_output_already_exists_rerun_forbidden",))
    try:
        provenance = verify_freeze_manifest(
            ROOT, freeze_manifest_path, expected_freeze_manifest_sha256,
            require_clean_worktree=True,
        )
        settings = load_yaml(config_path)
        manifest = provenance["manifest"]
        if manifest.get("selection_artifact_sha256") != expected_selection_sha256:
            raise ProvenanceFailure(("manifest_selection_artifact_sha256_mismatch",))
        if manifest.get("candidate_threshold_float64_hex") != settings.get(
            "candidate_threshold_float64_hex"
        ) or manifest.get("candidate_threshold_exact_dyadic") != settings.get(
            "candidate_threshold_exact_dyadic"
        ):
            raise ProvenanceFailure(("manifest_candidate_threshold_mismatch",))
        selection = verify_selection_artifact(
            selection_path, expected_selection_sha256,
            roster_path=ROOT / settings["confirmation_roster"],
            bundle_path=ROOT / settings["fixture_bundle"],
            expected_preselection_manifest_sha256=manifest[
                "preselection_manifest_sha256"
            ],
            expected_config_sha256=sha256(config_path),
        )
        preflight = _verify_preflight(preflight_path, expected_preflight_sha256)
        exact_tau = _verify_exact_tau(
            ROOT / settings["exact_tau_artifact"],
            settings["exact_tau_artifact_sha256"],
        )
        if manifest.get("execution_scope") != "FEASIBILITY_SUBSET_ONLY":
            raise ProvenanceFailure(("manifest_execution_scope",))
    except (ProvenanceFailure, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        return _provenance_failure(output_path, error)

    selected_rows = selection["selection"]["selected_rows"]
    run_id = "v3-" + hashlib.sha256((
        expected_freeze_manifest_sha256 + expected_selection_sha256
    ).encode("ascii")).hexdigest()[:16]
    run_dir = output_path.parent / f"{output_path.stem}_work"
    if run_dir.exists():
        return _provenance_failure(
            output_path, ProvenanceFailure(("v3_work_directory_exists_rerun_forbidden",))
        )
    run_dir.mkdir(parents=True)
    bundle_path = ROOT / settings["fixture_bundle"]
    total_limit = float(settings["resources"]["maximum_feasibility_seconds"])
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []

    for selected in selected_rows:
        state = selected["state_label"]
        family = selected["family"]
        segment_id = f"{state}/{family}"
        elapsed = time.perf_counter() - started
        remaining_total = _remaining_total_budget(started, total_limit)
        if remaining_total <= 0:
            rows.append({
                "state_label": state, "family": family, "status": "RESOURCE_LIMIT",
                "reason": "TOTAL_HARD_BUDGET_EXHAUSTED_BEFORE_START",
                "attempted_node_count": 0, "completed_node_count": 0,
                "successful_schur_elimination_count": 0,
                "path_domain_persisted": False, "path_domain_status": None,
                "journal_status": "JOURNAL_MISSING", "watchdog": {},
                "metrics": _terminal_metrics([]),
            })
            continue
        segment_dir = run_dir / f"{state}_{family}"
        journal_dir = segment_dir / "journal"
        identity_path = segment_dir / "journal_identity.json"
        worker_output = segment_dir / "segment_result.json"
        path_domain_output = segment_dir / "path_domain.json"
        watchdog_output = segment_dir / "watchdog.json"
        attempt_id = f"{run_id}-{state}-{family}"
        identity = {
            "run_id": run_id,
            "segment_id": segment_id,
            "config_sha256": sha256(config_path),
            "freeze_manifest_sha256": expected_freeze_manifest_sha256,
            "selection_artifact_sha256": expected_selection_sha256,
            "fixture_bundle_sha256": sha256(bundle_path),
            "worker_sha256": sha256(ROOT / "scripts/_taylor_eigencluster_worker_v3.py"),
        }
        _durable_atomic_json(identity_path, identity)
        per_limit = min(
            float(settings["resources"]["maximum_seconds_per_segment"]),
            remaining_total,
        )
        command = [
            sys.executable, str(ROOT / "scripts/_taylor_eigencluster_worker_v3.py"),
            "--config", str(config_path), "--bundle", str(bundle_path),
            "--state", state, "--family", family, "--attempt-id", attempt_id,
            "--journal-directory", str(journal_dir),
            "--journal-identity", str(identity_path),
            "--path-domain-output", str(path_domain_output),
            "--output", str(worker_output),
        ]
        watchdog = run_with_job_timeout(
            command, cwd=ROOT, time_limit_seconds=per_limit,
            kill_grace_seconds=float(settings["resources"]["kill_grace_seconds"]),
            finalization_allowance_seconds=float(
                settings["resources"]["finalization_allowance_seconds"]
            ),
            fixture=segment_id, interval="0/1..1/1",
            status_path=watchdog_output,
        )
        try:
            journal, nodes = _journal_summary(
                journal_dir, identity=identity, attempt_id=attempt_id,
                segment_id=segment_id,
            )
        except (JournalError, OSError) as error:
            journal = {
                "status": "JOURNAL_INVALID", "failure": str(error),
                "attempted_node_count": 0, "completed_node_count": 0,
                "successful_schur_elimination_count": 0,
                "path_domain_persisted": False, "path_domain_status": None,
            }
            nodes = []
        if watchdog["status"] == "WORKER_COMPLETED" and worker_output.is_file():
            worker = json.loads(worker_output.read_text(encoding="utf-8"))
            status = worker["status"]
            reason = worker.get("reason")
        elif watchdog["status"] in {"RESOURCE_LIMIT", "WATCHDOG_CONTRACT_BREACH"}:
            worker = None
            status = "RESOURCE_LIMIT"
            reason = watchdog.get("reason")
        else:
            worker = None
            status = "UNCERTIFIED"
            reason = watchdog.get("reason")
        rows.append({
            "state_label": state, "family": family, "status": status,
            "reason": reason,
            "attempted_node_count": journal["attempted_node_count"],
            "completed_node_count": journal["completed_node_count"],
            "successful_schur_elimination_count": journal[
                "successful_schur_elimination_count"
            ],
            "path_domain_persisted": journal["path_domain_persisted"],
            "path_domain_status": journal["path_domain_status"],
            "journal_status": journal["status"], "journal": journal,
            "watchdog": watchdog, "worker_result": worker,
            "metrics": _terminal_metrics(nodes),
        })

    elapsed = time.perf_counter() - started
    gate = _gate(settings, rows, preflight=preflight, total_elapsed_seconds=elapsed)
    status = "FEASIBILITY_GATE_PASS" if gate["passed"] else (
        "FEASIBILITY_GATE_FAIL_CLOSED"
    )
    artifact = {
        "schema_version": "taylor-eigencluster-whole-segment-v3",
        "status": status, "execution_scope": "FEASIBILITY_SUBSET",
        "candidate_threshold_status": "PROPOSED_UNAPPROVED",
        "selection": selection["selection"], "segment_rows": rows,
        "feasibility_gate": gate,
        "aggregate": {
            "segment_count": len(rows),
            "certified_fixed_inertia_count": sum(
                row["status"] == "CERTIFIED_FIXED_INERTIA" for row in rows
            ),
            "proven_crossing_count": sum(
                row["status"] == "PROVEN_CROSSING" for row in rows
            ),
            "unresolved_count": sum(row["status"] == "UNCERTIFIED" for row in rows),
            "resource_limit_count": sum(
                row["status"] == "RESOURCE_LIMIT" for row in rows
            ),
            "attempted_node_count": sum(row["attempted_node_count"] for row in rows),
            "completed_node_count": sum(row["completed_node_count"] for row in rows),
            "successful_schur_elimination_count": sum(
                row["successful_schur_elimination_count"] for row in rows
            ),
            "path_domain_certified_count": sum(
                row["path_domain_status"] == "PATH_DOMAIN_CERTIFIED" for row in rows
            ),
            "runtime_seconds": elapsed,
        },
        "lifecycle_guards": _lifecycle_guards(),
        "provenance": {
            **{key: value for key, value in provenance.items() if key != "manifest"},
            "config_sha256": sha256(config_path),
            "selection_artifact_sha256": expected_selection_sha256,
            "synthetic_preflight": preflight,
            "exact_tau_oracle": exact_tau,
        },
    }
    _durable_atomic_json(output_path, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--expected-freeze-manifest-sha256", required=True)
    parser.add_argument("--selection-artifact", type=Path, required=True)
    parser.add_argument("--expected-selection-sha256", required=True)
    parser.add_argument("--synthetic-preflight", type=Path, required=True)
    parser.add_argument("--expected-synthetic-preflight-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = run(
        args.config.resolve(), args.freeze_manifest.resolve(),
        args.expected_freeze_manifest_sha256,
        args.selection_artifact.resolve(), args.expected_selection_sha256,
        args.synthetic_preflight.resolve(),
        args.expected_synthetic_preflight_sha256, args.output.resolve(),
    )
    print(json.dumps({
        "status": artifact["status"], "aggregate": artifact["aggregate"],
    }, indent=2))


if __name__ == "__main__":
    main()
