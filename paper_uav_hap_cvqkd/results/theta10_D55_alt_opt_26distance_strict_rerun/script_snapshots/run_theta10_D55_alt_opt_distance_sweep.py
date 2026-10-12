"""Continue the validated ALT_OPT diagnostic over the exact distance grid.

This driver reuses the existing direct-Z-minus evaluator, source cache, exact
one-dimensional search, and positive-log renderer.  It replaces only the
optimized-MB rows in a new output CSV; the stored Uniform and fixed-MB rows
are copied without reevaluation.  Missing source moments fail closed unless
``--allow-new-source`` is explicitly supplied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.render_theta10_D55_three_scheme_log10 import render as render_log10
from scripts.run_theta10_D55_alt_opt import (
    ExactCandidateFailure,
    ExactObjective,
    ExactSourceUnavailable,
    K_TOLERANCE,
    PARAMETER_TOLERANCE,
    RECEIVER_DIAMETER_M,
    SOURCE_CACHE,
    TAU_ZEN,
    THETA_DIV_FULL_RAD,
    W0_M,
    adaptive_maximize_1d,
    coordinate_search_complete,
    stopping_status,
    candidate_from_payload,
    channel_row,
    json_hash,
    load_source_payloads,
    source_points_from_bank,
    unconstrained_config,
)


OUTPUT = ROOT / "results" / "theta10_D55_alt_opt_distance_sweep"
PREVIOUS_CSV = (
    ROOT
    / "results"
    / "skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme"
    / "skr_vs_distance_three_scheme.csv"
)
DISTANCES_KM = (
    20.0, 21.0, 21.9393102292, 22.0, 23.0, 24.0, 25.0, 25.5,
    26.0, 26.5, 27.0, 27.5, 28.0, 29.0, 30.0, 30.5, 31.0,
    31.5, 32.0, 32.5, 33.0, 34.0, 35.0, 36.0, 38.0, 40.0,
)
BASE_STARTS = (0.10, 0.15, 0.30, 0.80)
BASELINE_DISTANCE_KM = 21.9393102292
MAX_AO_ITERATIONS = 6
OPTIMIZED_MB_SCHEME = "Optimized MB-shaped 256-QAM"
UNIFORM_SCHEME = "Optimized Uniform 256-QAM"
FIXED_MB_SCHEME = "Fixed MB-shaped 256-QAM"
SCHEME_ORDER = (UNIFORM_SCHEME, FIXED_MB_SCHEME, OPTIMIZED_MB_SCHEME)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def make_channel(config: dict, distance_km: float) -> dict:
    base = channel_row(config, distance_km)
    channel = {
        **base,
        "distance_km": float(distance_km),
        "theta_div_full_rad": THETA_DIV_FULL_RAD,
        "w0_m": W0_M,
        "receiver_diameter_m": RECEIVER_DIAMETER_M,
    }
    # Match the established D55 runner's provenance hash: its hash covers the
    # optical row before the descriptive metadata is attached.
    channel["channel_hash"] = json_hash(base)
    return channel


def register_exact_catalog(objective: ExactObjective) -> None:
    payloads = objective.payloads
    for family, nu, va in sorted(source_points_from_bank()):
        if family != "MB" or nu <= 0.0:
            continue
        if candidate_from_payload(objective.config, payloads, "MB", nu, va) is not None:
            objective.register_catalog(nu, va)


def starting_va(objective: ExactObjective, nu: float, warm_va: float | None) -> float | None:
    values = objective.catalog_values("V_A", nu)
    if not values:
        return None
    if warm_va is not None:
        warm_hex = float(warm_va).hex()
        for value in values:
            if float(value).hex() == warm_hex:
                return float(value)
    return float(values[0])


def closed(status: str) -> bool:
    return status == "NUMERICALLY_CLOSED_LOCAL_BRACKET"


def run_single_distance_ao(
    *,
    distance_km: float,
    start_id: str,
    start_nu: float,
    start_va: float | None,
    objective: ExactObjective,
    max_iterations: int,
) -> dict:
    unique_at_start = objective.unique_exact_evaluations
    requested_at_start = objective.requested_calls
    cache_hits_at_start = objective.cache_hits
    initial_va = starting_va(objective, start_nu, start_va)
    if initial_va is None:
        return {
            "start_id": start_id,
            "start_nu": start_nu,
            "start_V_A": start_va,
            "status": "INNER_SEARCH_FAILURE",
            "final": None,
            "iterations": [],
            "trajectory": [],
            "warnings": [],
            "exact_evaluations": 0,
            "requested_evaluations": 0,
            "cache_hits": 0,
        }
    try:
        current = objective(start_nu, initial_va)
    except ExactSourceUnavailable:
        return {
            "start_id": start_id,
            "start_nu": start_nu,
            "start_V_A": initial_va,
            "status": "INNER_SEARCH_FAILURE",
            "final": None,
            "iterations": [],
            "trajectory": [],
            "warnings": [],
            "exact_evaluations": objective.unique_exact_evaluations - unique_at_start,
            "requested_evaluations": objective.requested_calls - requested_at_start,
            "cache_hits": objective.cache_hits - cache_hits_at_start,
        }
    except ExactCandidateFailure:
        return {
            "start_id": start_id,
            "start_nu": start_nu,
            "start_V_A": initial_va,
            "status": "NUMERICAL_FAILURE",
            "final": None,
            "iterations": [],
            "trajectory": [],
            "warnings": [],
            "exact_evaluations": objective.unique_exact_evaluations - unique_at_start,
            "requested_evaluations": objective.requested_calls - requested_at_start,
            "cache_hits": objective.cache_hits - cache_hits_at_start,
        }

    current_nu = float(start_nu)
    current_va = float(initial_va)
    iterations: list[dict] = []
    trajectory = [{"nu": current_nu, "V_A": current_va, "phase": "initial"}]
    warnings: list[dict] = []
    unresolved_inner = False
    terminal_status = "MAX_ITERATIONS_REACHED"

    for iteration in range(max_iterations):
        before = current
        unique_before_va = objective.unique_exact_evaluations
        cache_before_va = objective.cache_hits
        va_search = adaptive_maximize_1d(
            variable="V_A",
            fixed=current_nu,
            values=objective.catalog_values("V_A", current_nu),
            objective=objective,
        )
        if va_search.get("best") is None:
            terminal_status = "NUMERICAL_FAILURE" if va_search.get("numerical_failures") else "INNER_SEARCH_FAILURE"
            unresolved_inner = True
            break
        after_va = va_search["best"]
        unique_after_va = objective.unique_exact_evaluations
        cache_after_va = objective.cache_hits
        trajectory.append({
            "nu": current_nu,
            "V_A": float(after_va["V_A"]),
            "phase": "after_V_A",
        })

        nu_search = adaptive_maximize_1d(
            variable="nu_raw",
            fixed=float(after_va["V_A"]),
            values=objective.catalog_values("nu_raw", float(after_va["V_A"])),
            objective=objective,
        )
        if nu_search.get("best") is None:
            terminal_status = "NUMERICAL_FAILURE" if nu_search.get("numerical_failures") else "INNER_SEARCH_FAILURE"
            unresolved_inner = True
            break
        after_nu = nu_search["best"]
        unique_after_nu = objective.unique_exact_evaluations
        cache_after_nu = objective.cache_hits
        current_nu = float(after_nu["nu_raw"])
        current_va = float(after_nu["V_A"])
        trajectory.append({
            "nu": current_nu,
            "V_A": current_va,
            "phase": "after_nu",
        })

        k_before = float(before["SKR"])
        k_after_va = float(after_va["SKR"])
        k_after_nu = float(after_nu["SKR"])
        delta_k = k_after_nu - k_before
        delta_nu = abs(current_nu - float(before["nu_raw"]))
        delta_va = abs(current_va - float(before["V_A"]))
        monotonic_variables = []
        if k_after_va + K_TOLERANCE < k_before:
            monotonic_variables.append("V_A")
        if k_after_nu + K_TOLERANCE < k_after_va:
            monotonic_variables.append("nu_raw")
        if monotonic_variables:
            warnings.append({
                "code": "AO_MONOTONICITY_WARNING",
                "distance_km": distance_km,
                "start_id": start_id,
                "iteration": iteration,
                "variables": monotonic_variables,
                "K_before": k_before,
                "K_after_VA": k_after_va,
                "K_after_nu": k_after_nu,
                "absolute_difference": abs(delta_k),
                "tolerance": K_TOLERANCE,
            })

        searches_closed = all(coordinate_search_complete(s) for s in (va_search, nu_search))
        search_failure = not searches_closed
        unresolved_inner = unresolved_inner or search_failure
        iterations.append({
            "distance_km": distance_km,
            "start_id": start_id,
            "initial_nu": start_nu,
            "initial_V_A": initial_va,
            "iteration": iteration,
            "nu_before": float(before["nu_raw"]),
            "V_A_before": float(before["V_A"]),
            "K_before": k_before,
            "optimized_V_A": float(after_va["V_A"]),
            "K_after_VA": k_after_va,
            "optimized_nu": float(after_nu["nu_raw"]),
            "K_after_nu": k_after_nu,
            "I_AB": float(after_nu["I_AB"]),
            "beta_I_AB": float(after_nu["beta_I_AB"]),
            "chi_BE": float(after_nu["chi_BE"]),
            "K": k_after_nu,
            "delta_K": delta_k,
            "delta_nu": delta_nu,
            "delta_V_A": delta_va,
            "V_A_exact_evaluations": unique_after_va - unique_before_va,
            "nu_exact_evaluations": unique_after_nu - unique_after_va,
            "V_A_search_evaluated_points": va_search.get("evaluated", 0),
            "nu_search_evaluated_points": nu_search.get("evaluated", 0),
            "V_A_search_status": va_search["status"],
            "nu_search_status": nu_search["status"],
            "V_A_boundary_status": va_search.get("boundary_status", ""),
            "nu_boundary_status": nu_search.get("boundary_status", ""),
            "V_A_refinement_status": va_search.get("refinement_status", ""),
            "nu_refinement_status": nu_search.get("refinement_status", ""),
            "V_A_refinement_stages": va_search.get("refinement_stages", 0),
            "nu_refinement_stages": nu_search.get("refinement_stages", 0),
            "boundary_expansions": va_search.get("boundary_expansions", 0) + nu_search.get("boundary_expansions", 0),
            "V_A_search_range": json.dumps(va_search.get("range")),
            "nu_search_range": json.dumps(nu_search.get("range")),
            "V_A_bracket": json.dumps(va_search.get("bracket")),
            "nu_bracket": json.dumps(nu_search.get("bracket")),
            "V_A_candidate_history": json.dumps(va_search.get("history", [])),
            "nu_candidate_history": json.dumps(nu_search.get("history", [])),
            "V_A_cache_hits": cache_after_va - cache_before_va,
            "nu_cache_hits": cache_after_nu - cache_after_va,
            "cache_hits": cache_after_nu - cache_before_va,
            "convergence_status": "AO_MONOTONICITY_WARNING" if monotonic_variables else "RUNNING",
            "numerical_warning": json.dumps({
                "monotonicity": warnings[-1] if monotonic_variables else None,
                "V_A_failures": va_search.get("source_missing", []) + va_search.get("numerical_failures", []),
                "nu_failures": nu_search.get("source_missing", []) + nu_search.get("numerical_failures", []),
            }),
        })
        current = after_nu

        decision = stopping_status(delta_k, (va_search, nu_search), previous_unresolved=unresolved_inner, monotonic_warning=bool(monotonic_variables))
        if decision is not None:
            terminal_status = decision
            iterations[-1]["convergence_status"] = decision
            break
    else:
        terminal_status = "MAX_ITERATIONS_REACHED"
    return {
        "start_id": start_id,
        "start_nu": start_nu,
        "start_V_A": initial_va,
        "status": terminal_status,
        "final": current,
        "iterations": iterations,
        "trajectory": trajectory,
        "warnings": warnings,
        "exact_evaluations": objective.unique_exact_evaluations - unique_at_start,
        "requested_evaluations": objective.requested_calls - requested_at_start,
        "cache_hits": objective.cache_hits - cache_hits_at_start,
    }


def load_previous_rows() -> list[dict]:
    with PREVIOUS_CSV.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    expected = set(DISTANCES_KM)
    for scheme in (UNIFORM_SCHEME, FIXED_MB_SCHEME, OPTIMIZED_MB_SCHEME):
        actual = {float(row["distance_km"]) for row in rows if row["scheme"] == scheme}
        if actual != expected:
            raise RuntimeError(f"Previous CSV has incomplete {scheme} distance set")
    return rows


def final_mb_row(config: dict, objective: ExactObjective, result: dict, experiment_hash: str) -> dict:
    final = result["final"]
    nu = float(final["nu_raw"])
    va = float(final["V_A"])
    candidate = candidate_from_payload(config, objective.payloads, "MB", nu, va)
    if candidate is None:
        raise RuntimeError(f"Best exact candidate lost source payload: nu={nu!r}, VA={va!r}")
    row = dict(final)
    row.update({
        "distance_km": float(final["L_km"]),
        "L_km": float(final["L_km"]),
        "K": float(final["SKR"]),
        "SKR": float(final["SKR"]),
        "C": float(candidate["C"]),
        "w": float(candidate["w"]),
        "family": "MB",
        "scheme": OPTIMIZED_MB_SCHEME,
        "selection": "best_AO_exact_tested_candidate",
        "selection_origin": "ALT_OPT_MULTI_START_EXACT_TESTED",
        "experiment_hash": experiment_hash,
        "source_cache_origin": candidate.get("source_cache_origin"),
        "source_support_size": candidate["source_support_size"],
        "peak_photon_observed": candidate["peak_photon_observed"],
        "status": "PASS",
    })
    return row


def direction(values: list[float], tolerance: float = 1.0e-12) -> str:
    differences = [b - a for a, b in zip(values, values[1:])]
    if all(value >= -tolerance for value in differences):
        return "non-decreasing"
    if all(value <= tolerance for value in differences):
        return "non-increasing"
    return "non-monotone"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--allow-new-source", action="store_true")
    parser.add_argument("--max-ao-iterations", type=int, default=MAX_AO_ITERATIONS)
    args = parser.parse_args()
    if args.max_ao_iterations <= 0:
        parser.error("--max-ao-iterations must be positive")

    torch.set_num_threads(1)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    previous_rows = load_previous_rows()
    previous_hash = sha256(PREVIOUS_CSV)
    config = unconstrained_config()
    source_before = {path.name: sha256(path) for path in SOURCE_CACHE.glob("*.json")}
    experiment_hash = json_hash({
        "driver": "ALT_OPT_DISTANCE_SWEEP",
        "distances_km": DISTANCES_KM,
        "previous_csv_sha256": previous_hash,
        "theta_div_full_rad": THETA_DIV_FULL_RAD,
        "w0_m": W0_M,
        "D_r_m": RECEIVER_DIAMETER_M,
        "tau_zen": TAU_ZEN,
    })

    all_iteration_rows: list[dict] = []
    all_objective_rows: list[dict] = []
    all_start_rows: list[dict] = []
    best_rows: list[dict] = []
    comparison_rows: list[dict] = []
    distance_records: list[dict] = []
    warm_start: tuple[float, float] | None = None
    baseline_validation: dict | None = None

    for distance_km in DISTANCES_KM:
        channel = make_channel(config, distance_km)
        objective = ExactObjective(
            config,
            channel,
            output,
            allow_new_source=args.allow_new_source,
        )
        register_exact_catalog(objective)
        starts = [(f"nu_{nu:g}", float(nu), None) for nu in BASE_STARTS]
        if warm_start is not None:
            starts.append(("warm_previous_distance", warm_start[0], warm_start[1]))
        runs = [
            run_single_distance_ao(
                distance_km=distance_km,
                start_id=start_id,
                start_nu=start_nu,
                start_va=start_va,
                objective=objective,
                max_iterations=args.max_ao_iterations,
            )
            for start_id, start_nu, start_va in starts
        ]
        runs_with_final = [run for run in runs if run.get("final") is not None]
        if not runs_with_final:
            raise RuntimeError(f"No exact candidate at distance {distance_km}")
        best_run = max(runs_with_final, key=lambda run: float(run["final"]["SKR"]))
        best = best_run["final"]

        for row in objective.rows.values():
            objective_row = dict(row)
            objective_row["distance_km"] = objective_row.get("L_km")
            all_objective_rows.append(objective_row)
        for row in (iteration for run in runs for iteration in run["iterations"]):
            all_iteration_rows.append(row)

        final_pairs = {
            (round(float(run["final"]["nu_raw"]), 12), round(float(run["final"]["V_A"]), 12))
            for run in runs_with_final
        }
        search_statuses = [
            status
            for row in (iteration for run in runs for iteration in run["iterations"])
            for status in (row.get("V_A_search_status"), row.get("nu_search_status"))
        ]
        boundary_statuses = [
            status
            for row in (iteration for run in runs for iteration in run["iterations"])
            for status in (row.get("V_A_boundary_status"), row.get("nu_boundary_status"))
        ]
        monotonicity_violations = sum(len(run["warnings"]) for run in runs)
        unresolved_inner = sum(not closed(status) for status in search_statuses)
        unresolved_boundaries = sum(status == "BOUNDARY_NOT_CLOSED" for status in boundary_statuses)
        all_closed = bool(search_statuses) and unresolved_inner == 0
        if all_closed and best_run["status"] == "CONVERGED_NUMERICALLY":
            distance_status = "BEST_AO_EXACT_TESTED_CANDIDATE_ONLY"
        else:
            distance_status = "BEST_AO_EXACT_TESTED_CANDIDATE_ONLY;INNER_SEARCH_FAILURE"
        if unresolved_boundaries:
            distance_status += ";UNRESOLVED_BOUNDARY"

        if abs(distance_km - BASELINE_DISTANCE_KM) < 1.0e-12:
            expected = {
                "nu_raw": 0.165,
                "V_A": 5.5,
                "I_AB": 0.6341892631163653,
                "beta_I_AB": 0.6024797999605470,
                "chi_BE": 0.5244988060866094,
                "SKR": 0.07798099387393764,
            }
            mismatches = {
                key: float(best[key]) - value
                for key, value in expected.items()
                if abs(float(best[key]) - value) > 1.0e-12
            }
            baseline_validation = {
                "status": "CURRENTLY_VERIFIED_PASS" if not mismatches else "FAILED",
                "expected": expected,
                "observed": {key: float(best[key]) for key in expected},
                "mismatches": mismatches,
            }
            if mismatches:
                raise RuntimeError(f"Validated baseline mismatch at {distance_km} km: {mismatches}")

        best_row = final_mb_row(config, objective, best_run, experiment_hash)
        best_rows.append(best_row)
        old = next(
            row for row in previous_rows
            if row["scheme"] == OPTIMIZED_MB_SCHEME
            and abs(float(row["distance_km"]) - distance_km) < 1.0e-12
        )
        comparison_rows.append({
            "distance_km": distance_km,
            "previous_nu_raw": float(old["nu_raw"]),
            "new_nu_raw": float(best["nu_raw"]),
            "previous_V_A": float(old["V_A"]),
            "new_V_A": float(best["V_A"]),
            "previous_K": float(old["K"]),
            "new_K": float(best["SKR"]),
            "delta_K": float(best["SKR"]) - float(old["K"]),
            "same_pair": (
                float(old["nu_raw"]) == float(best["nu_raw"])
                and float(old["V_A"]) == float(best["V_A"])
            ),
        })

        for run in runs:
            final = run.get("final")
            all_start_rows.append({
                "distance_km": distance_km,
                "start_id": run["start_id"],
                "initial_nu": run["start_nu"],
                "initial_V_A": run["start_V_A"],
                "final_nu": None if final is None else final["nu_raw"],
                "final_V_A": None if final is None else final["V_A"],
                "I_AB": None if final is None else final["I_AB"],
                "beta_I_AB": None if final is None else final["beta_I_AB"],
                "chi_BE": None if final is None else final["chi_BE"],
                "K": None if final is None else final["SKR"],
                "AO_iterations": len(run["iterations"]),
                "requested_evaluations": run["requested_evaluations"],
                "exact_evaluations": run["exact_evaluations"],
                "cache_hits": run["cache_hits"],
                "status": run["status"],
                "warning_count": len(run["warnings"]),
            })

        distance_records.append({
            "L_km": distance_km,
            "zeta_deg": float(best["zeta_deg"]),
            "nu_raw_star": float(best["nu_raw"]),
            "V_A_star": float(best["V_A"]),
            "I_AB": float(best["I_AB"]),
            "beta_I_AB": float(best["beta_I_AB"]),
            "chi_BE": float(best["chi_BE"]),
            "K": float(best["SKR"]),
            "status": distance_status,
            "best_run_status": best_run["status"],
            "selected_initialization": best_run["start_id"],
            "AO_iterations": len(best_run["iterations"]),
            "requested_objective_calls": objective.requested_calls,
            "unique_exact_SKR_evaluations": objective.unique_exact_evaluations,
            "cache_hits": objective.cache_hits,
            "missing_exact_source_probes": len(objective.source_missing),
            "numerical_failures": len(objective.numerical_failures),
            "monotonicity_violations": monotonicity_violations,
            "unresolved_inner_search_directions": unresolved_inner,
            "unresolved_boundary_directions": unresolved_boundaries,
            "multi_start_same_candidate": len(final_pairs) == 1,
            "multi_start_final_pairs": json.dumps(sorted([list(pair) for pair in final_pairs])),
            "warm_start_used": warm_start is not None,
        })
        warm_start = (float(best["nu_raw"]), float(best["V_A"]))
        del objective

    source_after = {path.name: sha256(path) for path in SOURCE_CACHE.glob("*.json")}
    previous_hash_after = sha256(PREVIOUS_CSV)
    previous_non_mb = [row for row in previous_rows if row["scheme"] != OPTIMIZED_MB_SCHEME]
    combined_rows = previous_non_mb + best_rows
    combined_rows.sort(key=lambda row: (float(row["distance_km"]), SCHEME_ORDER.index(row["scheme"])))

    distance_summary_path = output / "mb_alt_opt_distance_summary.csv"
    start_summary_path = output / "ao_multistart_summary.csv"
    iteration_path = output / "ao_iterations.csv"
    objective_path = output / "ao_objective_evaluations.csv"
    comparison_path = output / "previous_mb_comparison.csv"
    combined_path = output / "three_scheme_alt_opt.csv"
    write_csv(distance_summary_path, distance_records)
    write_csv(start_summary_path, all_start_rows)
    write_csv(iteration_path, all_iteration_rows)
    write_csv(objective_path, all_objective_rows)
    write_csv(comparison_path, comparison_rows)
    write_csv(combined_path, combined_rows)

    png, pdf, renderer_report = render_log10(combined_path, output)
    shutil.copy2(
        ROOT / "scripts" / "render_theta10_D55_three_scheme_log10.py",
        output / "render_theta10_D55_alt_opt_distance_sweep_log10.py",
    )

    nu_values = [float(row["nu_raw_star"]) for row in distance_records]
    va_values = [float(row["V_A_star"]) for row in distance_records]
    drift_jumps = [
        {
            "from_L_km": distance_records[index - 1]["L_km"],
            "to_L_km": distance_records[index]["L_km"],
            "delta_nu_raw": nu_values[index] - nu_values[index - 1],
            "delta_V_A": va_values[index] - va_values[index - 1],
        }
        for index in range(1, len(distance_records))
        if abs(nu_values[index] - nu_values[index - 1]) >= 0.01
        or abs(va_values[index] - va_values[index - 1]) >= 1.0
    ]
    same_pair_count = sum(bool(row["same_pair"]) for row in comparison_rows)
    unresolved_distance_status = any(
        row["status"] != "BEST_AO_EXACT_TESTED_CANDIDATE_ONLY"
        for row in distance_records
    )
    report = {
        "status": (
            "FULL_DISTANCE_ALT_OPT_COMPLETE_WITH_UNRESOLVED_SEARCH"
            if unresolved_distance_status
            else "FULL_DISTANCE_ALT_OPT_COMPLETE"
        ),
        "scope": "DIAGNOSTIC_ONLY",
        "algorithm": "ALT_OPT",
        "configuration": {
            "theta_div_full_rad": THETA_DIV_FULL_RAD,
            "w0_m": W0_M,
            "D_r_m": RECEIVER_DIAMETER_M,
            "h_HAP_km": 20.0,
            "h_UAV_km": 1.0,
            "wavelength_nm": 1550.0,
            "tau_zen": TAU_ZEN,
            "epsilon_ch": 0.0186,
            "beta": 0.95,
            "AO_physical": "OFF",
            "phase_noise": "OFF",
            "holevo": "direct_Z_minus",
            "mi": "deterministic heterodyne product GH8",
            "peak_constraint": "OFF",
            "budget_constraint": "OFF",
        },
        "distance_set_km": list(DISTANCES_KM),
        "source_policy": {
            "allow_new_source": args.allow_new_source,
            "source_cache_only_default": True,
            "no_interpolation": True,
            "source_cache_before_count": len(source_before),
            "source_cache_after_count": len(source_after),
            "source_cache_changed": source_before != source_after,
            "source_cache_snapshot_sha256_before": json_hash(source_before),
            "source_cache_snapshot_sha256_after": json_hash(source_after),
        },
        "baseline_validation": baseline_validation,
        "per_distance_summary": distance_records,
        "multi_start_summary": all_start_rows,
        "parameter_drift": {
            "nu_raw_sequence": nu_values,
            "V_A_sequence": va_values,
            "nu_raw_direction": direction(nu_values),
            "V_A_direction": direction(va_values),
            "smooth_with_distance": len(drift_jumps) == 0,
            "branch_or_large_catalog_jumps": drift_jumps,
            "initialization_dependence_distances": [
                row["L_km"] for row in distance_records if not row["multi_start_same_candidate"]
            ],
        },
        "previous_curve_comparison": {
            "previous_csv": str(PREVIOUS_CSV.relative_to(ROOT)).replace("\\", "/"),
            "previous_csv_sha256": previous_hash,
            "source_csv_sha256_after": previous_hash_after,
            "source_csv_unchanged": previous_hash == previous_hash_after,
            "same_exact_pair_count": same_pair_count,
            "distance_count": len(comparison_rows),
            "max_abs_delta_K": max(abs(float(row["delta_K"])) for row in comparison_rows),
            "rows": comparison_rows,
        },
        "provenance": {
            "physical_security_evaluator_modified": False,
            "uniform_rerun": False,
            "fixed_mb_rerun": False,
            "previous_source_csv_modified": False,
            "source_csv_sha256_current": previous_hash,
            "experiment_hash": experiment_hash,
        },
        "artifacts": {
            "distance_summary_csv": distance_summary_path.name,
            "multistart_summary_csv": start_summary_path.name,
            "iterations_csv": iteration_path.name,
            "objective_evaluations_csv": objective_path.name,
            "previous_comparison_csv": comparison_path.name,
            "combined_plot_csv": combined_path.name,
            "png": png.name,
            "pdf": pdf.name,
            "renderer_report": renderer_report.name,
            "renderer": "render_theta10_D55_alt_opt_distance_sweep_log10.py",
        },
        "limitations": [
            "The result is the best exact-tested AO candidate at each distance, not a continuous global optimum proof.",
            "Missing exact source moments leave unresolved inner and boundary directions fail-closed.",
            "Uniform and fixed-MB rows were copied from the existing exact CSV without reevaluation.",
            "Publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.",
        ],
    }
    report["runner_sha256"] = sha256(Path(__file__).resolve())
    report_path = output / "run_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown = [
        "# Full-distance ALT_OPT diagnostic report",
        "",
        f"- Status: `{report['status']}`",
        f"- Distances: `{len(DISTANCES_KM)}` exact points from 20 to 40 km",
        f"- Baseline validation: `{baseline_validation['status'] if baseline_validation else 'NOT_RUN'}`",
        f"- Previous MB pairs reproduced: `{same_pair_count}/{len(comparison_rows)}`",
        "",
        "## Best exact-tested MB candidate by distance",
        "",
        "| L (km) | nu_raw* | V_A* | I_AB | beta I_AB | chi_BE | K | Status |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    markdown.extend(
        f"| {row['L_km']:.12g} | {row['nu_raw_star']:.17g} | {row['V_A_star']:.17g} | {row['I_AB']:.17g} | {row['beta_I_AB']:.17g} | {row['chi_BE']:.17g} | {row['K']:.17g} | `{row['status']}` |"
        for row in distance_records
    )
    markdown.extend([
        "",
        "## Drift",
        "",
        f"- nu direction: `{report['parameter_drift']['nu_raw_direction']}`",
        f"- V_A direction: `{report['parameter_drift']['V_A_direction']}`",
        f"- Smooth: `{report['parameter_drift']['smooth_with_distance']}`",
        f"- Initialization-dependence distances: `{report['parameter_drift']['initialization_dependence_distances']}`",
        "",
        "No source-moment or SKR interpolation was used. The standard base-10 log renderer displays only exact rows with `K > 0`.",
        "",
    ])
    (output / "run_report.md").write_text("\n".join(markdown), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "baseline_validation": baseline_validation,
        "artifacts": report["artifacts"],
        "previous_pair_match_count": same_pair_count,
        "source_cache_changed": report["source_policy"]["source_cache_changed"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
