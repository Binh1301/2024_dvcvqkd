"""Run the preregistered 24-endpoint shifted-inertia feasibility gate."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
from typing import Any

from flint import ctx
import numpy as np

from _common import ROOT, load_yaml
from src.validation.rigorous_flint_support import (
    BallTransmitterPath,
    exact_arb_from_float_hex,
    exact_arb_from_fraction,
)
from src.validation.rigorous_shifted_inertia import (
    aggregate_sector_inertias,
    shift_hermitian,
    verified_block_ldl_inertia,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diagnostic_complex128(sectors, threshold: float) -> dict[str, Any]:
    sector_rows = []
    all_values = []
    for index, sector in enumerate(sectors):
        matrix = np.asarray([
            [complex(float(value.real.mid()), float(value.imag.mid())) for value in row]
            for row in sector
        ], dtype=np.complex128)
        matrix = 0.5 * (matrix + matrix.conj().T)
        eigenvalues = np.linalg.eigvalsh(matrix)
        all_values.extend(eigenvalues.tolist())
        sector_rows.append({
            "sector": index,
            "support_count_above_tau": int(np.count_nonzero(eigenvalues > threshold)),
            "nearest_below_or_equal_tau": float(np.max(eigenvalues[eigenvalues <= threshold]))
            if np.any(eigenvalues <= threshold) else None,
            "nearest_above_tau": float(np.min(eigenvalues[eigenvalues > threshold]))
            if np.any(eigenvalues > threshold) else None,
        })
    values = np.asarray(all_values)
    return {
        "role": "DIAGNOSTIC_ONLY_NOT_PROOF",
        "support_count_above_tau": int(np.count_nonzero(values > threshold)),
        "nearest_below_or_equal_tau": float(np.max(values[values <= threshold]))
        if np.any(values <= threshold) else None,
        "nearest_above_tau": float(np.min(values[values > threshold]))
        if np.any(values > threshold) else None,
        "sector_rows": sector_rows,
    }


def certify_unique_point(path: BallTransmitterPath, point: Fraction, settings: dict[str, Any]) -> dict[str, Any]:
    threshold = exact_arb_from_float_hex(settings["candidate_threshold_float64_hex"])
    schedule = [int(value) for value in settings["point_inertia"]["precision_bits"]]
    maximum_seconds = float(settings["point_inertia"]["maximum_seconds_per_unique_endpoint"])
    started = time.perf_counter()
    attempts = []
    diagnostic = None
    for bits in schedule:
        if time.perf_counter() - started >= maximum_seconds:
            break
        ctx.prec = bits
        sectors = path.sectors(exact_arb_from_fraction(point))
        if diagnostic is None:
            diagnostic = diagnostic_complex128(
                sectors, float.fromhex(settings["candidate_threshold_float64_hex"])
            )
        sector_results = []
        for sector_index, sector in enumerate(sectors):
            remaining = max(0.0, maximum_seconds - (time.perf_counter() - started))
            result = verified_block_ldl_inertia(
                shift_hermitian(sector, threshold),
                precision_bits=bits,
                maximum_seconds=remaining,
            )
            sector_results.append({"sector": sector_index, **result})
            if result["status"] != "CERTIFIED_INERTIA":
                break
        for sector_index in range(len(sector_results), 4):
            sector_results.append({
                "sector": sector_index,
                "status": "NOT_ATTEMPTED_AFTER_EARLIER_SECTOR_FAILURE",
                "n_positive": 0,
                "n_negative": 0,
                "n_zero_or_unresolved": 64,
                "precision_bits": bits,
                "minimum_certified_signed_margin": None,
                "unresolved_block_size": 64,
                "pivot_rows": [],
                "runtime_seconds": 0.0,
                "failure_reason": "EARLIER_SECTOR_FAILURE",
            })
        aggregate = aggregate_sector_inertias(sector_results)
        attempts.append({
            "precision_bits": bits,
            "status": aggregate["status"],
            "n_positive": aggregate["n_positive"],
            "n_negative": aggregate["n_negative"],
            "n_zero_or_unresolved": aggregate["n_zero_or_unresolved"],
            "minimum_certified_signed_margin": aggregate["minimum_certified_signed_margin"],
            "sector_rows": sector_results,
        })
        if aggregate["status"] == "CERTIFIED_INERTIA" and len(sector_results) == 4:
            return {
                "status": "CERTIFIED_POINT_INERTIA",
                "candidate_threshold_float64_hex": settings["candidate_threshold_float64_hex"],
                "n_positive": aggregate["n_positive"],
                "n_negative": aggregate["n_negative"],
                "n_zero_or_unresolved": 0,
                "precision_bits": bits,
                "minimum_certified_signed_margin": aggregate["minimum_certified_signed_margin"],
                "diagnostic_complex128": diagnostic,
                "diagnostic_count_matches": aggregate["n_positive"] == diagnostic["support_count_above_tau"],
                "attempts": attempts,
                "runtime_seconds": time.perf_counter() - started,
            }
    last = attempts[-1] if attempts else None
    return {
        "status": "UNCERTIFIED_ENDPOINT_INERTIA",
        "candidate_threshold_float64_hex": settings["candidate_threshold_float64_hex"],
        "n_positive": last["n_positive"] if last else 0,
        "n_negative": last["n_negative"] if last else 0,
        "n_zero_or_unresolved": last["n_zero_or_unresolved"] if last else 256,
        "precision_bits": last["precision_bits"] if last else None,
        "minimum_certified_signed_margin": last["minimum_certified_signed_margin"] if last else None,
        "diagnostic_complex128": diagnostic,
        "diagnostic_count_matches": None,
        "attempts": attempts,
        "runtime_seconds": time.perf_counter() - started,
    }


def run(config_path: Path, bundle_path: Path, environment_path: Path,
        schema_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if settings["status"] != "PROSPECTIVE_FROZEN_BEFORE_ENDPOINT_OUTCOMES":
        raise ValueError("Endpoint cycle configuration is not prospectively frozen.")
    if settings["threshold_approval_permitted"] or settings["final_test_access_permitted"]:
        raise ValueError("Endpoint feasibility cannot approve thresholds or access final test.")
    for key, path_key, expected in (
        ("confirmation_roster", "confirmation_roster_sha256", settings["confirmation_roster_sha256"]),
        ("parameter_fixture_bundle", "parameter_fixture_bundle_sha256", settings["parameter_fixture_bundle_sha256"]),
        ("certification_environment_artifact", "certification_environment_sha256", settings["certification_environment_sha256"]),
        ("historical_cycle_artifact", "historical_cycle_artifact_sha256", settings["historical_cycle_artifact_sha256"]),
    ):
        del path_key
        if sha256(ROOT / settings[key]) != expected:
            raise ValueError(f"Frozen hash mismatch for {key}.")
    bindings = settings["producer_bindings"]
    if sha256(ROOT / bindings["point_module"]) != bindings["point_module_sha256"]:
        raise ValueError("Point-inertia module hash differs from frozen configuration.")
    if sha256(Path(__file__).resolve()) != bindings["endpoint_runner_sha256"]:
        raise ValueError("Endpoint runner hash differs from frozen configuration.")

    total_started = time.perf_counter()
    total_limit = float(settings["point_inertia"]["maximum_total_endpoint_seconds"])
    segments = {row["family"]: row for row in bundle["segments"]}
    cache: dict[str, dict[str, Any]] = {}
    rows = []
    for state in bundle["states"]:
        for family in ("ps", "gs", "va", "mixed"):
            segment = segments[family]
            path = BallTransmitterPath(
                bundle["start_parameters"], segment["end_parameters"], state,
                bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
            )
            for endpoint_label, point in (("start", Fraction(0)), ("end", Fraction(1))):
                key = f"{state['label']}:start" if endpoint_label == "start" else f"{state['label']}:{family}:end"
                if key not in cache:
                    if time.perf_counter() - total_started >= total_limit:
                        cache[key] = {
                            "status": "UNCERTIFIED_TOTAL_WORK_LIMIT",
                            "n_positive": 0, "n_negative": 0, "n_zero_or_unresolved": 256,
                            "precision_bits": None, "minimum_certified_signed_margin": None,
                            "diagnostic_complex128": None, "diagnostic_count_matches": None,
                            "attempts": [], "runtime_seconds": 0.0,
                        }
                    else:
                        print(f"certifying endpoint key={key}", flush=True)
                        cache[key] = certify_unique_point(path, point, settings)
                rows.append({
                    "state_label": state["label"],
                    "family": family,
                    "endpoint": endpoint_label,
                    "unique_point_key": key,
                    "cache_reused": key in {row["unique_point_key"] for row in rows},
                    **cache[key],
                })

    certified_count = sum(row["status"] == "CERTIFIED_POINT_INERTIA" for row in rows)
    segment_equal_count = 0
    for state in bundle["states"]:
        for family in ("ps", "gs", "va", "mixed"):
            pair = [row for row in rows if row["state_label"] == state["label"] and row["family"] == family]
            if len(pair) == 2 and all(row["status"] == "CERTIFIED_POINT_INERTIA" for row in pair):
                segment_equal_count += int(pair[0]["n_positive"] == pair[1]["n_positive"])
    precisions = [row["precision_bits"] for row in rows if row["status"] == "CERTIFIED_POINT_INERTIA"]
    endpoint_gate_pass = (
        certified_count == int(settings["endpoint_feasibility_gate"]["required_certified_endpoints"])
        and segment_equal_count == 12
    )
    artifact = {
        "schema_version": "shifted-inertia-endpoint-certification-v1",
        "cycle_id": settings["cycle_id"],
        "status": "ENDPOINT_FEASIBILITY_GATE_PASS" if endpoint_gate_pass else "ENDPOINT_FEASIBILITY_GATE_FAIL_CLOSED",
        "mathematical_equivalence": {
            "shift": "H_tau = G - tau I",
            "numerical_support": "r_tau(G)=number(lambda(G)>tau)=n_positive(H_tau)",
            "support_is_mathematical_rank": False,
        },
        "method": {
            "algorithm": "validated Hermitian 1x1/2x2 block LDL* recursion",
            "proof": "certified pivot signs plus validated Schur complements and Sylvester inertia additivity",
            "individual_eigenvalue_isolation_used": False,
            "complex128_role": "diagnostic comparison only",
        },
        "endpoint_rows": rows,
        "aggregate": {
            "endpoint_count": len(rows),
            "unique_point_count": len(cache),
            "certified_endpoint_count": certified_count,
            "unresolved_endpoint_count": len(rows) - certified_count,
            "segments_with_equal_certified_endpoint_inertia": segment_equal_count,
            "median_certification_precision_bits": statistics.median(precisions) if precisions else None,
            "maximum_certification_precision_bits": max(precisions) if precisions else None,
            "runtime_seconds": time.perf_counter() - total_started,
            "proceed_to_whole_segment": endpoint_gate_pass,
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
            "fixture_bundle_sha256": sha256(bundle_path),
            "environment_manifest_sha256": sha256(environment_path),
            "schema_sha256": sha256(schema_path),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "point_module_sha256": sha256(ROOT / bindings["point_module"]),
            "confirmation_roster_sha256": sha256(ROOT / settings["confirmation_roster"]),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "shifted_inertia_certification_v1.yaml")
    parser.add_argument("--bundle", type=Path, default=ROOT / "results" / "rigorous_segment_fixture_bundle.json")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "shifted_inertia_environment_v1.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "shifted_inertia_endpoint_certification_v1.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "shifted_inertia_endpoint_certification_v1.json")
    args = parser.parse_args()
    artifact = run(args.config, args.bundle, args.environment, args.schema, args.output)
    print(json.dumps({"status": artifact["status"], **artifact["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
