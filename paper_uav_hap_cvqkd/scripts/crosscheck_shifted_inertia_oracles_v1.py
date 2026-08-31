"""Cross-check certified threshold support on the four frozen oracle fixtures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time
from typing import Any

from flint import acb, arb, ctx
import numpy as np
import torch

from _common import ROOT, load_yaml
from _numerical_validation import ensemble_sha256, representative_ensembles
from freeze_independent_confirmation_roster import stress_ensemble
from src.modulation.qam256 import c4_orbit_indices
from src.validation.rigorous_flint_support import exact_arb_from_float_hex
from src.validation.rigorous_shifted_inertia import (
    aggregate_sector_inertias,
    shift_hermitian,
    verified_block_ldl_inertia,
)


I = acb(0, 1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sectors_from_float64(probabilities: list[float], prototypes: list[complex]) -> list[list[list[acb]]]:
    """Build the exact-float64 C4 sectors using only Arb/acb arithmetic."""

    p = [exact_arb_from_float_hex(float(value).hex()) for value in probabilities]
    z = [acb(exact_arb_from_float_hex(float(value.real).hex()),
             exact_arb_from_float_hex(float(value.imag).hex())) for value in prototypes]
    rotations = [acb(1), I, acb(-1), -I]
    result = []
    for sector in range(4):
        raw = [[acb(0) for _ in range(64)] for _ in range(64)]
        for row in range(64):
            for column in range(64):
                root_probability = (p[row] * p[column]).sqrt()
                value = acb(0)
                for difference in range(4):
                    left, right = z[row], rotations[difference] * z[column]
                    left_energy = left.real * left.real + left.imag * left.imag
                    right_energy = right.real * right.real + right.imag * right.imag
                    overlap = (acb(-(left_energy + right_energy) / 2) + left.conjugate() * right).exp()
                    value += root_probability * overlap * (I ** (sector * difference))
                raw[row][column] = value
        result.append([[
            (raw[row][column] + raw[column][row].conjugate()) / 2
            for column in range(64)
        ] for row in range(64)])
    return result


def diagnostic_support(sectors: list[list[list[acb]]], threshold: float) -> int:
    count = 0
    for sector in sectors:
        matrix = np.asarray([[
            complex(float(value.real.mid()), float(value.imag.mid())) for value in row
        ] for row in sector], dtype=np.complex128)
        values = np.linalg.eigvalsh(0.5 * (matrix + matrix.conj().T))
        count += int(np.count_nonzero(values > threshold))
    return count


def compact_sector(result: dict[str, Any], sector: int) -> dict[str, Any]:
    pivots = result["pivot_rows"]
    return {
        "sector": sector,
        "status": result["status"],
        "n_positive": result["n_positive"],
        "n_negative": result["n_negative"],
        "n_zero_or_unresolved": result["n_zero_or_unresolved"],
        "minimum_certified_signed_margin": result["minimum_certified_signed_margin"],
        "one_by_one_pivot_count": sum(row["block_size"] == 1 for row in pivots),
        "two_by_two_pivot_count": sum(row["block_size"] == 2 for row in pivots),
        "runtime_seconds": result["runtime_seconds"],
        "failure_reason": result["failure_reason"],
    }


def run(config_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    if settings["status"] != "PROSPECTIVE_FROZEN_BEFORE_ORACLE_CROSSCHECK_OUTCOMES":
        raise ValueError("Oracle cross-check config is not prospectively frozen.")
    if settings["threshold_approval_permitted"] or settings["final_test_access_permitted"]:
        raise ValueError("Cross-check cannot approve thresholds or access final-test data.")
    for key, expected_key in (
        ("confirmation_roster", "confirmation_roster_sha256"),
        ("oracle_artifact", "oracle_artifact_sha256"),
        ("candidate_threshold_audit", "candidate_threshold_audit_sha256"),
    ):
        if sha256(ROOT / settings[key]) != settings[expected_key]:
            raise ValueError(f"Frozen hash mismatch: {key}")
    if sha256(Path(__file__).resolve()) != settings["producer_sha256"]:
        raise ValueError("Cross-check producer differs from frozen configuration.")
    point_path = ROOT / settings["point_module"]
    if sha256(point_path) != settings["point_module_sha256"]:
        raise ValueError("Point-inertia module differs from frozen configuration.")

    default = load_yaml(ROOT / "configs" / "default.yaml")
    roster_design = load_yaml(ROOT / "configs" / "independent_confirmation_roster.yaml")
    roster = json.loads((ROOT / settings["confirmation_roster"]).read_text(encoding="utf-8"))
    oracle = json.loads((ROOT / settings["oracle_artifact"]).read_text(encoding="utf-8"))
    prior = json.loads((ROOT / settings["candidate_threshold_audit"]).read_text(encoding="utf-8"))

    states = roster["representative_states"]
    t = torch.tensor([row["transmittance"] for row in states], dtype=torch.float64)
    epsilon = torch.tensor([row["epsilon_snu"] for row in states], dtype=torch.float64)
    fixture_config = copy.deepcopy(default)
    fixture_config["numerical_validation"]["fixture_initialization_seed"] = int(
        roster_design["fixture_initialization_seed"]
    )
    ensembles = representative_ensembles(fixture_config, t, epsilon)
    ensembles.pop("near_coincident_pseudoinverse_stress", None)
    for phase in roster_design["near_coincident_phase_steps_rad"]:
        ensembles[f"near_coincident_phase_step_{float(phase):g}"] = stress_ensemble(
            float(phase), batch_size=3, v_max=float(default["cvqkd"]["v_max_snu"]),
            n_peak=float(default["cvqkd"]["n_peak_photons"]),
        )

    oracle_by_name = {row["fixture"]: row for row in oracle["oracle_fixture_rows"]}
    prior_by_name = {row["fixture"]: row for row in prior["all_fixture_comparison_summary"]}
    roster_hashes = {row["name"]: row["ensemble_sha256"] for row in roster["fixtures"]}
    indices = c4_orbit_indices()[:, 0]
    threshold_float = float.fromhex(settings["candidate_threshold_float64_hex"])
    threshold = exact_arb_from_float_hex(settings["candidate_threshold_float64_hex"])
    started = time.perf_counter()
    rows = []
    for name in roster["oracle_subset"]:
        ensemble = ensembles[name]
        if ensemble_sha256(ensemble) != roster_hashes[name]:
            raise ValueError(f"Reconstructed oracle fixture hash mismatch: {name}")
        probabilities = [float(value) for value in ensemble.probabilities[0, indices].tolist()]
        prototypes = [complex(value) for value in ensemble.amplitudes[0, indices].tolist()]
        attempts = []
        diagnostic = None
        certified = None
        for bits in settings["precision_bits"]:
            ctx.prec = int(bits)
            gram_sectors = sectors_from_float64(probabilities, prototypes)
            if diagnostic is None:
                diagnostic = diagnostic_support(gram_sectors, threshold_float)
            sector_results = []
            for sector_index, sector in enumerate(gram_sectors):
                result = verified_block_ldl_inertia(
                    shift_hermitian(sector, threshold), precision_bits=int(bits),
                    maximum_seconds=float(settings["maximum_seconds_per_fixture"]),
                )
                sector_results.append(compact_sector(result, sector_index))
                if result["status"] != "CERTIFIED_INERTIA":
                    break
            aggregate = aggregate_sector_inertias(sector_results)
            attempt = {
                "precision_bits": int(bits), "status": aggregate["status"],
                "n_positive": aggregate["n_positive"], "n_negative": aggregate["n_negative"],
                "n_zero_or_unresolved": aggregate["n_zero_or_unresolved"],
                "minimum_certified_signed_margin": aggregate["minimum_certified_signed_margin"],
                "sector_rows": sector_results,
            }
            attempts.append(attempt)
            if aggregate["status"] == "CERTIFIED_INERTIA" and len(sector_results) == 4:
                certified = attempt
                break
        oracle_row = oracle_by_name[name]
        full_rows = [row for row in oracle_row["precision_rows"] if row["full_support_resolved"]]
        prior_candidate = prior_by_name.get(name, {}).get("candidate_retained_rank_by_state")
        rows.append({
            "fixture": name,
            "ensemble_sha256": roster_hashes[name],
            "status": "CERTIFIED_ORACLE_FIXTURE_SUPPORT" if certified else "UNCERTIFIED_ORACLE_FIXTURE_SUPPORT",
            "certified_threshold_support": None if certified is None else certified["n_positive"],
            "certification_precision_bits": None if certified is None else certified["precision_bits"],
            "diagnostic_complex128_support": diagnostic,
            "diagnostic_count_matches": certified is not None and certified["n_positive"] == diagnostic,
            "prior_candidate_support_by_state": prior_candidate,
            "prior_candidate_support_matches": prior_candidate is None or (
                certified is not None and all(int(value) == certified["n_positive"] for value in prior_candidate)
            ),
            "oracle_full_mathematical_rank": 256 if len(full_rows) >= 2 else None,
            "oracle_full_support_precision_digits": [int(row["decimal_digits"]) for row in full_rows[-2:]],
            "numerical_support_is_mathematical_rank": False,
            "attempts": attempts,
        })

    precisions = [row["certification_precision_bits"] for row in rows if row["certification_precision_bits"]]
    all_pass = all(
        row["status"] == "CERTIFIED_ORACLE_FIXTURE_SUPPORT"
        and row["diagnostic_count_matches"] and row["prior_candidate_support_matches"]
        and row["oracle_full_mathematical_rank"] == 256
        for row in rows
    )
    artifact = {
        "schema_version": "shifted-inertia-oracle-crosscheck-v1",
        "cycle_id": settings["cycle_id"],
        "status": "ORACLE_CROSSCHECK_PASS" if all_pass else "ORACLE_CROSSCHECK_FAIL_CLOSED",
        "candidate_threshold_status": "PROPOSED_UNAPPROVED",
        "fixture_rows": rows,
        "aggregate": {
            "fixture_count": len(rows),
            "certified_fixture_count": sum(row["status"] == "CERTIFIED_ORACLE_FIXTURE_SUPPORT" for row in rows),
            "full_mathematical_rank_fixture_count": sum(row["oracle_full_mathematical_rank"] == 256 for row in rows),
            "diagnostic_match_count": sum(bool(row["diagnostic_count_matches"]) for row in rows),
            "prior_candidate_match_or_not_applicable_count": sum(bool(row["prior_candidate_support_matches"]) for row in rows),
            "median_precision_bits": statistics.median(precisions) if precisions else None,
            "maximum_precision_bits": max(precisions) if precisions else None,
            "runtime_seconds": time.perf_counter() - started,
        },
        "lifecycle_guards": {
            "threshold_approved": False, "publication_training_performed": False,
            "final_test_accessed": False, "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False, "security_functional_changed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "worktree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "config_sha256": sha256(config_path), "producer_sha256": sha256(Path(__file__).resolve()),
            "point_module_sha256": sha256(point_path),
            "confirmation_roster_sha256": sha256(ROOT / settings["confirmation_roster"]),
            "oracle_artifact_sha256": sha256(ROOT / settings["oracle_artifact"]),
            "candidate_threshold_audit_sha256": sha256(ROOT / settings["candidate_threshold_audit"]),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "shifted_inertia_oracle_crosscheck_v1.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "shifted_inertia_oracle_crosscheck_v1.json")
    args = parser.parse_args()
    artifact = run(args.config.resolve(), args.output.resolve())
    print(json.dumps({"status": artifact["status"], "aggregate": artifact["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()
