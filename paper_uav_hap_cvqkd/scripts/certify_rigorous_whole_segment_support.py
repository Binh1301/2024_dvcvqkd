"""Run the standalone Arb/FLINT certifier on the twelve frozen segments."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import flint

from _common import ROOT, load_yaml
from src.validation.rigorous_flint_support import (
    BallTransmitterPath,
    certify_affine_scalar_segment,
    certify_parameter_segment,
    exact_arb_from_float_hex,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(config_path: Path, bundle_path: Path, environment_path: Path,
        schema_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if settings["threshold_approval_permitted"] or settings["final_test_access_permitted"]:
        raise ValueError("Rigorous certification task may not approve thresholds or access final test.")
    if bundle["status"] != "FROZEN_FLOAT64_PARAMETER_PATH_INPUTS":
        raise ValueError("Rigorous segment fixture bundle is not frozen.")
    if environment["validated_arithmetic"]["python_flint_version"] != flint.__version__:
        raise ValueError("Certification environment version differs from its manifest.")
    if bundle["candidate_threshold_float64_hex"] != settings["candidate_threshold_float64_hex"]:
        raise ValueError("Fixture and certification threshold encodings differ.")

    threshold = exact_arb_from_float_hex(settings["candidate_threshold_float64_hex"])
    precision_bits = [int(value) for value in settings["precision_bits"]]
    algorithms = [str(value) for value in settings["eigensolver_algorithms"]]
    subdivision = settings["subdivision"]
    minimum_width = Fraction(1, 2 ** abs(int(subdivision["minimum_interval_width_power_of_two"])))
    total_started = time.perf_counter()
    rows = []
    total_limit = float(subdivision["maximum_total_seconds"])
    segments_by_family = {row["family"]: row for row in bundle["segments"]}
    for state in bundle["states"]:
        for family in ("ps", "gs", "va", "mixed"):
            if time.perf_counter() - total_started >= total_limit:
                result = {
                    "status": "UNCERTIFIED_TOTAL_WORK_LIMIT",
                    "runtime_seconds": 0.0,
                    "nodes": [],
                }
            else:
                segment = segments_by_family[family]
                path = BallTransmitterPath(
                    bundle["start_parameters"], segment["end_parameters"], state,
                    bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
                )
                print(f"certifying state={state['label']} family={family}", flush=True)
                result = certify_parameter_segment(
                    path,
                    threshold=threshold,
                    precision_bits=precision_bits,
                    algorithms=algorithms,
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
            diagnostic = segments_by_family[family]["endpoint_diagnostics"][state["label"]]
            rows.append({
                "state_label": state["label"],
                "family": family,
                "candidate_threshold_float64_hex": settings["candidate_threshold_float64_hex"],
                "observed_endpoint_change_float64_diagnostic": diagnostic[
                    "observed_endpoint_frobenius_change_float64"
                ],
                **result,
            })

    certified = sum(row["status"] == "WHOLE_SEGMENT_SUPPORT_CERTIFIED" for row in rows)
    crossings = sum("CROSSING" in row["status"] for row in rows)
    unresolved = len(rows) - certified - crossings
    synthetic = {
        "obvious_no_crossing": certify_affine_scalar_segment(
            float(0.8).hex(), float(0.9).hex(), float(0.5).hex()
        )["status"],
        "known_crossing": certify_affine_scalar_segment(
            float(0.6).hex(), float(0.4).hex(), float(0.5).hex()
        )["status"],
        "near_boundary_non_crossing": certify_affine_scalar_segment(
            float(0.500001).hex(), float(0.500002).hex(), float(0.5).hex()
        )["status"],
    }
    artifact: dict[str, Any] = {
        "schema_version": "rigorous-whole-segment-support-certification-v1",
        "status": (
            "EXPERIMENTAL_ALL_REALIZED_SEGMENTS_CERTIFIED"
            if certified == len(rows) else
            "EXPERIMENTAL_REALIZED_SEGMENTS_FAIL_CLOSED"
        ),
        "method": {
            "arithmetic": "python-flint Arb real balls and acb complex balls",
            "path": "exact IEEE-754 endpoint dyadics propagated through actual PS/VA/GS parameter interpolation",
            "gram": "direct interval C4 weighted coherent-state Gram, four Hermitian 64x64 sectors",
            "perturbation": "rho_I = Frobenius upper bound of interval sector minus exact-midpoint sector",
            "eigenvalues": "validated acb_mat.eig(multiple=True), never algorithm=approx",
            "support": "strict Weyl retained/suppressed classification with adaptive dyadic subdivision",
            "finite_node_sampling_is_proof": False,
            "threshold_approved": False,
        },
        "synthetic_regressions": synthetic,
        "segment_rows": rows,
        "aggregate": {
            "segment_count": len(rows),
            "whole_segment_support_certified_count": certified,
            "rigorous_crossing_count": crossings,
            "unresolved_fail_closed_count": unresolved,
            "maximum_depth_reached": max((row.get("maximum_depth_reached", 0) for row in rows), default=0),
            "runtime_seconds": time.perf_counter() - total_started,
        },
        "transactional_state_inventory_for_future_integration": [
            "model_parameters", "adam_first_moments", "adam_second_moments",
            "amsgrad_max_second_moments_if_enabled", "optimizer_step_counters",
            "learning_rate_schedulers", "energy_dual_lambda_E", "CPU_RNG_state",
            "CUDA_RNG_states", "explicit_data_and_sampler_generators",
            "training_epoch_and_batch_counters", "gradient_scaler_if_enabled",
        ],
        "future_transaction_rule_status": "DEFINED_NOT_ACTIVATED",
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
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "module_sha256": sha256(ROOT / "src" / "validation" / "rigorous_flint_support.py"),
            "config_sha256": sha256(config_path),
            "fixture_bundle_sha256": sha256(bundle_path),
            "environment_manifest_sha256": sha256(environment_path),
            "schema_sha256": sha256(schema_path),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
            "python_flint_version": flint.__version__,
            "flint_version": flint.__FLINT_VERSION__,
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "rigorous_whole_segment_support.yaml")
    parser.add_argument("--bundle", type=Path, default=ROOT / "results" / "rigorous_segment_fixture_bundle.json")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "certification_flint_environment.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "rigorous_whole_segment_support.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "rigorous_whole_segment_certification.json")
    args = parser.parse_args()
    artifact = run(args.config, args.bundle, args.environment, args.schema, args.output)
    print(json.dumps({"status": artifact["status"], **artifact["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
