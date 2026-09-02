"""Run whole-segment shifted-inertia certification after endpoint gate pass."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

from _common import ROOT, load_yaml
from src.validation.rigorous_flint_support import BallTransmitterPath, exact_arb_from_float_hex
from src.validation.rigorous_shifted_inertia_segment import certify_interval_tree, evaluate_path_interval


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(config_path: Path, bundle_path: Path, environment_path: Path,
        schema_path: Path, output_path: Path) -> dict:
    settings = load_yaml(config_path)
    base = load_yaml(ROOT / settings["base_cycle_config"])
    endpoints = json.loads((ROOT / settings["endpoint_gate_artifact"]).read_text(encoding="utf-8"))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    if settings["status"] != "PROSPECTIVE_FROZEN_BEFORE_SEGMENT_OUTCOMES":
        raise ValueError("Whole-segment extension is not prospectively frozen.")
    if endpoints["status"] != settings["required_endpoint_gate_status"]:
        raise ValueError("Endpoint feasibility gate did not pass.")
    if settings["threshold_approval_permitted"] or settings["final_test_access_permitted"]:
        raise ValueError("Whole-segment cycle cannot approve a threshold or access final test.")
    if sha256(ROOT / settings["base_cycle_config"]) != settings["base_cycle_config_sha256"]:
        raise ValueError("Base-cycle config hash mismatch.")
    if sha256(ROOT / settings["endpoint_gate_artifact"]) != settings["endpoint_gate_artifact_sha256"]:
        raise ValueError("Endpoint artifact hash mismatch.")
    bindings = settings["producer_bindings"]
    for path_key, hash_key in (
        ("point_module", "point_module_sha256"),
        ("segment_module", "segment_module_sha256"),
        ("segment_runner", "segment_runner_sha256"),
    ):
        target = Path(__file__).resolve() if path_key == "segment_runner" else ROOT / bindings[path_key]
        if sha256(target) != bindings[hash_key]:
            raise ValueError(f"Frozen producer hash mismatch: {path_key}.")

    endpoint_map = {
        (row["state_label"], row["family"], row["endpoint"]): row
        for row in endpoints["endpoint_rows"]
    }
    segments = {row["family"]: row for row in bundle["segments"]}
    subdivision = settings["subdivision"]
    threshold = exact_arb_from_float_hex(settings["candidate_threshold_float64_hex"])
    precision_schedule = [int(value) for value in settings["precision_bits"]]
    minimum_width = Fraction(1, 2 ** abs(int(subdivision["minimum_interval_width_power_of_two"])))
    total_started = time.perf_counter()
    rows = []
    for state in bundle["states"]:
        for family in ("ps", "gs", "va", "mixed"):
            if time.perf_counter() - total_started >= float(subdivision["maximum_total_seconds"]):
                result = {
                    "status": "UNCERTIFIED_TOTAL_WORK_LIMIT", "nodes": [],
                    "runtime_seconds": 0.0, "maximum_depth_reached": 0,
                    "accepted_leaf_count": 0, "unresolved_leaf_count": 1,
                }
            else:
                segment = segments[family]
                path = BallTransmitterPath(
                    bundle["start_parameters"], segment["end_parameters"], state,
                    bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
                )
                start_rank = int(endpoint_map[(state["label"], family, "start")]["n_positive"])
                end_rank = int(endpoint_map[(state["label"], family, "end")]["n_positive"])
                print(f"certifying segment state={state['label']} family={family}", flush=True)
                result = certify_interval_tree(
                    lambda left, right: evaluate_path_interval(
                        path, left, right, threshold=threshold,
                        precision_schedule=precision_schedule,
                        maximum_seconds=float(subdivision["maximum_seconds_per_node"]),
                    ),
                    start_rank=start_rank,
                    end_rank=end_rank,
                    maximum_depth=int(subdivision["maximum_depth"]),
                    minimum_width=minimum_width,
                    maximum_nodes=int(subdivision["maximum_nodes_per_segment"]),
                    maximum_seconds=float(subdivision["maximum_seconds_per_segment"]),
                    progress=lambda node: print(
                        f"  depth={node['depth']} interval={node['left']}..{node['right']} "
                        f"status={node['status']} precision={node.get('precision_bits')}",
                        flush=True,
                    ),
                )
            rows.append({"state_label": state["label"], "family": family, **result})

    certified = sum(row["status"] == "WHOLE_SEGMENT_FIXED_INERTIA_CERTIFIED" for row in rows)
    crossings = sum(row["status"] == "RIGOROUS_ENDPOINT_INERTIA_CROSSING" for row in rows)
    unresolved = len(rows) - certified - crossings
    node_precisions = [
        node["precision_bits"] for row in rows for node in row.get("nodes", [])
        if node.get("precision_bits") is not None
    ]
    node_depths = [node["depth"] for row in rows for node in row.get("nodes", [])]
    artifact = {
        "schema_version": "shifted-inertia-whole-segment-certification-v1",
        "cycle_id": settings["cycle_id"],
        "status": "EXPERIMENTAL_ALL_SEGMENTS_CERTIFIED" if certified == 12 else "EXPERIMENTAL_SEGMENTS_FAIL_CLOSED",
        "method": {
            "interval_gram": "validated Arb/acb actual parameter path",
            "rho": "rigorous Frobenius upper bound of interval-minus-midpoint C4 sector",
            "inertia": "validated 1x1/2x2 block LDL* at midpoint shifts tau-rho and tau+rho",
            "proof": "equal positive inertia counts plus Weyl imply fixed support throughout the interval",
            "zero_included_proves_crossing": False,
            "endpoint_equality_alone_is_proof": False,
        },
        "segment_rows": rows,
        "aggregate": {
            "segment_count": len(rows),
            "whole_segment_certified_count": certified,
            "rigorous_crossing_count": crossings,
            "unresolved_fail_closed_count": unresolved,
            "median_precision_bits": statistics.median(node_precisions) if node_precisions else None,
            "maximum_precision_bits": max(node_precisions) if node_precisions else None,
            "median_subdivision_depth": statistics.median(node_depths) if node_depths else None,
            "maximum_subdivision_depth": max(node_depths) if node_depths else None,
            "runtime_seconds": time.perf_counter() - total_started,
            "previous_eigenvalue_isolation_runtime_seconds": float(base["comparison_baseline_runtime_seconds"]),
        },
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "optimizer_integration_performed": False,
            "security_functional_changed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "worktree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "config_sha256": sha256(config_path),
            "base_cycle_config_sha256": sha256(ROOT / settings["base_cycle_config"]),
            "endpoint_gate_artifact_sha256": sha256(ROOT / settings["endpoint_gate_artifact"]),
            "fixture_bundle_sha256": sha256(bundle_path),
            "environment_manifest_sha256": sha256(environment_path),
            "schema_sha256": sha256(schema_path),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "point_module_sha256": sha256(ROOT / bindings["point_module"]),
            "segment_module_sha256": sha256(ROOT / bindings["segment_module"]),
            "confirmation_roster_sha256": sha256(ROOT / base["confirmation_roster"]),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "shifted_inertia_segment_v1.yaml")
    parser.add_argument("--bundle", type=Path, default=ROOT / "results" / "rigorous_segment_fixture_bundle.json")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "shifted_inertia_environment_v1.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "shifted_inertia_whole_segment_v1.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "shifted_inertia_whole_segment_certification_v1.json")
    args = parser.parse_args()
    artifact = run(args.config, args.bundle, args.environment, args.schema, args.output)
    print(json.dumps({"status": artifact["status"], **artifact["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
