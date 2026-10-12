"""Cache-safe alternating optimization diagnostic for the theta10/D55 baseline.

The physical channel, direct-Z-minus evaluator, and exact source-moment code are
imported unchanged.  This file owns only the optimization driver and its
diagnostic artifacts.  By default it uses the existing exact source cache and
fails closed when an adaptive probe has no exact source row; ``--allow-new-
source`` is an explicit opt-in because a missing arbitrary-precision source can
take up to the repository's 3600-second watchdog.
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
import types

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_exact_mb_test2 import ExactMBEvaluator
from scripts.run_skr_vs_link_distance_theta10urad import evaluate_candidate
from scripts.run_theta10_D55_unconstrained_three_scheme import (
    BETA,
    EPSILON,
    RECEIVER_DIAMETER_M,
    SOURCE_CACHE,
    TAU_ZEN,
    THETA_DIV_FULL_RAD,
    W0_M,
    candidate_from_payload,
    channel_row,
    load_source_payloads,
    make_ensemble,
    source_points_from_bank,
    unconstrained_config,
)


OUTPUT = ROOT / "results" / "theta10_D55_alt_opt"
BASELINE_DISTANCE_KM = 21.9393102292
AO_START_NUS = (0.10, 0.15, 0.30, 0.80)
K_TOLERANCE = 1.0e-8
PARAMETER_TOLERANCE = 1.0e-6
MAX_AO_ITERATIONS = 6
MAX_BOUNDARY_EXPANSIONS = 3
MAX_REFINEMENT_STAGES = 4


class ExactSourceUnavailable(RuntimeError):
    """An adaptive point has no hash-matched exact source row."""


class ExactCandidateFailure(RuntimeError):
    """The unchanged exact evaluator rejected a finite candidate."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def json_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def finite_metrics(row: dict) -> None:
    for field in ("I_AB", "beta_I_AB", "chi_BE", "SKR"):
        value = float(row[field])
        if not math.isfinite(value):
            raise FloatingPointError(f"Non-finite exact metric {field}: {value!r}")


class ExactObjective:
    """One exact direct-Z-minus objective with deterministic pair caching."""

    def __init__(self, config: dict, channel: dict, output: Path, *, allow_new_source: bool):
        self.config = config
        self.channel = channel
        self.output = output
        self.allow_new_source = bool(allow_new_source)
        self.payloads = load_source_payloads()
        self.evaluator = ExactMBEvaluator(
            config,
            {"T_eff": 0.0, "epsilon_base": EPSILON, "c_phi": 0.0},
            output,
            source_cache_dir=SOURCE_CACHE,
            allow_legacy_exact_import=False,
        )
        self.context_hash = json_hash({"config": config, "channel": channel})
        self.rows: dict[tuple[str, str, str], dict] = {}
        self.catalog: set[tuple[float, float]] = set()
        self.requested_calls = 0
        self.unique_exact_evaluations = 0
        self.cache_hits = 0
        self.source_missing: list[dict] = []
        self.numerical_failures: list[dict] = []
        self.source_cache_before = {
            path.name: sha256(path) for path in SOURCE_CACHE.glob("*.json")
        }

    def key(self, nu: float, va: float) -> tuple[str, str, str]:
        return self.context_hash, float(nu).hex(), float(va).hex()

    def register_catalog(self, nu: float, va: float) -> None:
        if float(nu) > 0.0 and float(va) > 0.0:
            self.catalog.add((float(nu), float(va)))

    def catalog_values(self, variable: str, fixed: float) -> list[float]:
        fixed_hex = float(fixed).hex()
        if variable == "V_A":
            values = [va for nu, va in self.catalog if nu.hex() == fixed_hex]
        elif variable == "nu_raw":
            values = [nu for nu, va in self.catalog if va.hex() == fixed_hex]
        else:
            raise ValueError(variable)
        return sorted(set(values))

    def _candidate(self, nu: float, va: float) -> dict:
        candidate = candidate_from_payload(self.config, self.payloads, "MB", nu, va)
        if candidate is None and self.allow_new_source:
            ensemble = make_ensemble(self.config, "MB", nu, va)
            self.evaluator.source_moments(ensemble, nu, va)
            self.payloads = load_source_payloads()
            candidate = candidate_from_payload(self.config, self.payloads, "MB", nu, va)
        if candidate is None:
            failure = {
                "nu_raw": float(nu),
                "V_A": float(va),
                "status": "EXACT_SOURCE_MISSING",
                "allow_new_source": self.allow_new_source,
            }
            self.source_missing.append(failure)
            raise ExactSourceUnavailable(
                f"No hash-matched exact source row for nu_raw={nu:.17g}, V_A={va:.17g}"
            )
        return candidate

    def __call__(self, nu: float, va: float) -> dict:
        nu = float(nu)
        va = float(va)
        if not math.isfinite(nu) or not math.isfinite(va) or nu <= 0.0 or va <= 0.0:
            raise ValueError("AO variables must be finite and strictly positive")
        self.requested_calls += 1
        key = self.key(nu, va)
        if key in self.rows:
            self.cache_hits += 1
            return self.rows[key]
        candidate = self._candidate(nu, va)
        try:
            row = evaluate_candidate(candidate, self.channel, self.config)
            finite_metrics(row)
        except Exception as error:
            failure = {
                "nu_raw": nu,
                "V_A": va,
                "status": "NUMERICAL_FAILURE",
                "error": f"{type(error).__name__}: {error}",
            }
            self.numerical_failures.append(failure)
            raise ExactCandidateFailure(failure["error"]) from error
        row = {
            **row,
            "nu_raw": nu,
            "V_A": va,
            "security_evaluator": "current_exact_direct_Z_minus",
            "source_moment_route": candidate["source_moment_route"],
            "source_cache_key": candidate["source_cache_key"],
            "source_path": candidate["source_path"],
            "source_support_size": candidate["source_support_size"],
            "ensemble_hash": candidate["ensemble_hash"],
            "status": "PASS",
        }
        self.rows[key] = row
        self.register_catalog(nu, va)
        self.unique_exact_evaluations += 1
        return row

    def source_cache_after(self) -> dict[str, str]:
        return {path.name: sha256(path) for path in SOURCE_CACHE.glob("*.json")}


def adaptive_maximize_1d(
    *,
    variable: str,
    fixed: float,
    values: list[float],
    objective: ExactObjective,
    k_tolerance: float = K_TOLERANCE,
    parameter_tolerance: float = PARAMETER_TOLERANCE,
) -> dict:
    """Maximize an exact one-dimensional slice without interpolation.

    The initial catalogue is only a set of reusable exact evaluations.  The
    routine probes outside an improving endpoint and bisects an interior
    bracket.  A missing source moment or numerical failure is recorded and
    leaves the slice unresolved; no value is inferred between exact points.
    """

    values = sorted({float(value) for value in values if math.isfinite(float(value)) and float(value) > 0.0})
    if not values:
        return {
            "variable": variable,
            "fixed": fixed,
            "status": "INNER_SEARCH_FAILURE",
            "reason": "no exact source values on slice",
            "best": None,
            "evaluated": 0,
            "boundary_expansions": 0,
            "refinement_stages": 0,
            "source_missing": [],
            "numerical_failures": [],
            "history": [],
            "range": None,
        }

    evaluated: dict[str, dict] = {}
    failures: list[dict] = []
    numerical_failures: list[dict] = []
    history: list[dict] = []

    def evaluate_value(value: float) -> dict | None:
        key = float(value).hex()
        if key in evaluated:
            return evaluated[key]
        try:
            row = objective(fixed, value) if variable == "V_A" else objective(value, fixed)
        except ExactSourceUnavailable as error:
            failure = {"value": value, "status": "EXACT_SOURCE_MISSING", "error": str(error)}
            failures.append(failure)
            history.append(failure)
            return None
        except ExactCandidateFailure as error:
            failure = {"value": value, "status": "NUMERICAL_FAILURE", "error": str(error)}
            numerical_failures.append(failure)
            history.append(failure)
            return None
        evaluated[key] = row
        history.append({
            "value": value,
            "status": "EXACT_EVALUATED",
            "K": float(row["SKR"]),
            "nu_raw": float(row["nu_raw"]),
            "V_A": float(row["V_A"]),
        })
        return row

    # Explore every already-available exact point.  This is deliberately
    # catalogue-based, not an interpolated landscape or a monotonicity claim.
    for value in values:
        evaluate_value(value)
    valid = [(index, row) for index, value in enumerate(values) if (row := evaluated.get(float(value).hex())) is not None]
    if not valid:
        return {
            "variable": variable,
            "fixed": fixed,
            "status": "INNER_SEARCH_FAILURE",
            "reason": "all exact slice evaluations failed",
            "best": None,
            "evaluated": 0,
            "boundary_expansions": 0,
            "refinement_stages": 0,
            "source_missing": failures,
            "numerical_failures": numerical_failures,
            "history": history,
            "range": [values[0], values[-1]],
        }

    best = max((row for _, row in valid), key=lambda row: float(row["SKR"]))
    boundary_expansions = 0
    boundary_status = "INTERIOR"

    # Expand an exact-tested endpoint until an outside exact point turns down.
    # The emergency expansion cap is algorithmic only; it is never a physical
    # constraint and an increasing endpoint remains explicitly unresolved.
    for _ in range(MAX_BOUNDARY_EXPANSIONS):
        all_valid = list(evaluated.values())
        best = max(all_valid, key=lambda row: float(row["SKR"]))
        exact_values = sorted(
            float(row["V_A"] if variable == "V_A" else row["nu_raw"])
            for row in all_valid
        )
        best_value = float(best["V_A"] if variable == "V_A" else best["nu_raw"])
        if best_value != exact_values[0] and best_value != exact_values[-1]:
            boundary_status = "INTERIOR"
            break
        direction = -1 if best_value == exact_values[0] else 1
        probe = best_value / 2.0 if direction < 0 else best_value * 2.0
        boundary_expansions += 1
        outside = evaluate_value(probe)
        if outside is None:
            boundary_status = "BOUNDARY_NOT_CLOSED"
            break
        if float(outside["SKR"]) <= float(best["SKR"]) + k_tolerance:
            boundary_status = "CLOSED_BY_EXACT_OUTER_PROBE"
            break
    else:
        boundary_status = "BOUNDARY_NOT_CLOSED"

    refinement_stages = 0
    refinement_status = "NOT_NEEDED"
    while boundary_status != "BOUNDARY_NOT_CLOSED" and refinement_stages < MAX_REFINEMENT_STAGES:
        all_valid = list(evaluated.values())
        best = max(all_valid, key=lambda row: float(row["SKR"]))
        exact_values = sorted(
            float(row["V_A"] if variable == "V_A" else row["nu_raw"])
            for row in all_valid
        )
        best_value = float(best["V_A"] if variable == "V_A" else best["nu_raw"])
        lower = max((value for value in exact_values if value < best_value), default=None)
        upper = min((value for value in exact_values if value > best_value), default=None)
        if lower is None or upper is None:
            refinement_status = "BOUNDARY_POINT"
            break
        if max(best_value - lower, upper - best_value) <= parameter_tolerance:
            refinement_status = "TARGET_PARAMETER_TOLERANCE"
            break
        midpoint_rows = [
            evaluate_value((lower + best_value) / 2.0),
            evaluate_value((best_value + upper) / 2.0),
        ]
        refinement_stages += 1
        if not all(row is not None for row in midpoint_rows):
            refinement_status = "SOURCE_MISSING_REFINEMENT"
            break
        refinement_status = "EXACT_REFINEMENT"

    if refinement_stages >= MAX_REFINEMENT_STAGES and refinement_status == "EXACT_REFINEMENT":
        refinement_status = "REFINEMENT_LIMIT_REACHED"

    all_valid = list(evaluated.values())
    best = max(all_valid, key=lambda row: float(row["SKR"]))
    exact_values = sorted(
        float(row["V_A"] if variable == "V_A" else row["nu_raw"])
        for row in all_valid
    )
    best_value = float(best["V_A"] if variable == "V_A" else best["nu_raw"])
    lower = max((value for value in exact_values if value < best_value), default=None)
    upper = min((value for value in exact_values if value > best_value), default=None)
    if numerical_failures and not all_valid:
        status = "NUMERICAL_FAILURE"
    elif boundary_status == "BOUNDARY_NOT_CLOSED":
        status = "BOUNDARY_NOT_CLOSED"
    elif numerical_failures:
        status = "NUMERICAL_FAILURE"
    elif refinement_status == "SOURCE_MISSING_REFINEMENT":
        status = "BRACKETED_EXACT_CATALOG_SOURCE_MISSING"
    elif refinement_status == "REFINEMENT_LIMIT_REACHED":
        status = "INNER_SEARCH_FAILURE"
    elif boundary_status == "CLOSED_BY_EXACT_OUTER_PROBE" or lower is not None and upper is not None:
        status = "BRACKETED_EXACT_CATALOG"
    else:
        status = "INNER_SEARCH_FAILURE"
    return {
        "variable": variable,
        "fixed": fixed,
        "status": status,
        "best": best,
        "best_value": best_value,
        "best_K": float(best["SKR"]),
        "evaluated": len(evaluated),
        "boundary_expansions": boundary_expansions,
        "refinement_stages": refinement_stages,
        "boundary_status": boundary_status,
        "refinement_status": refinement_status,
        "source_missing": failures,
        "numerical_failures": numerical_failures,
        "history": history,
        "range": [min(exact_values), max(exact_values)],
        "bracket": [lower, upper],
    }


def run_single_ao(
    start_nu: float,
    objective: ExactObjective,
    *,
    max_iterations: int = MAX_AO_ITERATIONS,
) -> dict:
    current_nu = float(start_nu)
    unique_at_start = objective.unique_exact_evaluations
    requested_at_start = objective.requested_calls
    cache_hits_at_start = objective.cache_hits
    initial_values = objective.catalog_values("V_A", current_nu)
    if not initial_values:
        return {"start_nu": start_nu, "status": "INNER_SEARCH_FAILURE", "iterations": [], "final": None}
    current_va = initial_values[0]
    try:
        current = objective(current_nu, current_va)
    except ExactSourceUnavailable:
        return {"start_nu": start_nu, "status": "INNER_SEARCH_FAILURE", "iterations": [], "final": None}
    except ExactCandidateFailure:
        return {"start_nu": start_nu, "status": "NUMERICAL_FAILURE", "iterations": [], "final": None}
    iterations: list[dict] = []
    trajectory = [{"nu": current_nu, "V_A": current_va, "phase": "initial"}]
    warnings: list[dict] = []
    terminal_status = "MAX_ITER_REACHED"
    unresolved_inner = False

    for iteration in range(max_iterations):
        before = current
        unique_before_va = objective.unique_exact_evaluations
        cache_before_va = objective.cache_hits
        va_search = adaptive_maximize_1d(
            variable="V_A", fixed=current_nu,
            values=objective.catalog_values("V_A", current_nu), objective=objective,
        )
        if va_search.get("best") is None:
            terminal_status = "INNER_SEARCH_FAILURE"
            break
        after_va = va_search["best"]
        unique_after_va = objective.unique_exact_evaluations
        cache_after_va = objective.cache_hits
        trajectory.append({"nu": current_nu, "V_A": float(after_va["V_A"]), "phase": "after_V_A"})
        nu_search = adaptive_maximize_1d(
            variable="nu_raw", fixed=float(after_va["V_A"]),
            values=objective.catalog_values("nu_raw", float(after_va["V_A"])), objective=objective,
        )
        if nu_search.get("best") is None:
            terminal_status = "INNER_SEARCH_FAILURE"
            break
        after_nu = nu_search["best"]
        unique_after_nu = objective.unique_exact_evaluations
        cache_after_nu = objective.cache_hits
        current_nu = float(after_nu["nu_raw"])
        current_va = float(after_nu["V_A"])
        trajectory.append({"nu": current_nu, "V_A": current_va, "phase": "after_nu"})
        delta_k = float(after_nu["SKR"]) - float(before["SKR"])
        delta_nu = abs(float(after_nu["nu_raw"]) - float(before["nu_raw"]))
        delta_va = abs(float(after_nu["V_A"]) - float(before["V_A"]))
        monotonic_warning = []
        if float(after_va["SKR"]) + K_TOLERANCE < float(before["SKR"]):
            monotonic_warning.append("V_A")
        if float(after_nu["SKR"]) + K_TOLERANCE < float(after_va["SKR"]):
            monotonic_warning.append("nu_raw")
        if monotonic_warning:
            warning = {
                "code": "AO_MONOTONICITY_WARNING",
                "iteration": iteration,
                "variables": monotonic_warning,
                "K_before": float(before["SKR"]),
                "K_after_VA": float(after_va["SKR"]),
                "K_after_nu": float(after_nu["SKR"]),
                "absolute_difference": abs(delta_k),
                "tolerance": K_TOLERANCE,
                "previous_nu": float(before["nu_raw"]),
                "previous_V_A": float(before["V_A"]),
            }
            warnings.append(warning)
        search_failure = any(
            search["status"] not in {"BRACKETED_EXACT_CATALOG", "CLOSED_BY_EXACT_OUTER_PROBE"}
            for search in (va_search, nu_search)
        )
        unresolved_inner = unresolved_inner or search_failure
        iterations.append({
            "run_id": f"start_nu_{start_nu:g}",
            "initialization_id": f"nu_{start_nu:g}",
            "iteration": iteration,
            "nu_before": float(before["nu_raw"]),
            "V_A_before": float(before["V_A"]),
            "K_before": float(before["SKR"]),
            "optimized_V_A": float(after_va["V_A"]),
            "K_after_VA": float(after_va["SKR"]),
            "optimized_nu": float(after_nu["nu_raw"]),
            "K_after_nu": float(after_nu["SKR"]),
            "I_AB": float(after_nu["I_AB"]),
            "beta_I_AB": float(after_nu["beta_I_AB"]),
            "chi_BE": float(after_nu["chi_BE"]),
            "K": float(after_nu["SKR"]),
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
            "convergence_status": "AO_MONOTONICITY_WARNING" if monotonic_warning else "RUNNING",
            "numerical_warning": json.dumps({
                "monotonicity": warnings[-1] if monotonic_warning else None,
                "V_A_failures": va_search.get("source_missing", []) + va_search.get("numerical_failures", []),
                "nu_failures": nu_search.get("source_missing", []) + nu_search.get("numerical_failures", []),
            }),
        })
        current = after_nu
        if abs(delta_k) <= K_TOLERANCE:
            searches_closed = all(
                search["status"] in {"BRACKETED_EXACT_CATALOG", "CLOSED_BY_EXACT_OUTER_PROBE"}
                for search in (va_search, nu_search)
            )
            if warnings:
                terminal_status = "NON_MONOTONIC_WARNING"
            elif searches_closed:
                terminal_status = "CONVERGED_OBJECTIVE"
            else:
                terminal_status = "INNER_SEARCH_FAILURE"
            iterations[-1]["convergence_status"] = terminal_status
            break
        if delta_nu <= PARAMETER_TOLERANCE and delta_va <= PARAMETER_TOLERANCE:
            if warnings:
                terminal_status = "NON_MONOTONIC_WARNING"
            elif not search_failure:
                terminal_status = "CONVERGED_PARAMETERS"
            else:
                terminal_status = "INNER_SEARCH_FAILURE"
            iterations[-1]["convergence_status"] = terminal_status
            break
    else:
        terminal_status = "INNER_SEARCH_FAILURE" if unresolved_inner else "MAX_ITER_REACHED"

    final = current
    if unresolved_inner and terminal_status == "MAX_ITER_REACHED":
        terminal_status = "INNER_SEARCH_FAILURE"
    return {
        "start_nu": start_nu,
        "final": final,
        "iterations": iterations,
        "trajectory": trajectory,
        "status": terminal_status,
        "warnings": warnings,
        "ao_iterations": len(iterations),
        "exact_evaluations": objective.unique_exact_evaluations - unique_at_start,
        "requested_evaluations": objective.requested_calls - requested_at_start,
        "cache_hits": objective.cache_hits - cache_hits_at_start,
    }


def save_figure(path: Path, figure: plt.Figure) -> None:
    figure.tight_layout()
    figure.savefig(path.with_suffix(".png"), dpi=300, facecolor="white")
    sys.modules.setdefault(
        "fontTools.varLib.iup", types.ModuleType("fontTools.varLib.iup")
    ).iup_delta_optimize = lambda *args, **kwargs: None
    matplotlib.rcParams["pdf.use14corefonts"] = True
    figure.savefig(path.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)


def make_figures(output: Path, runs: list[dict]) -> None:
    figure, axis = plt.subplots(figsize=(8.8, 5.4))
    for run in runs:
        values = [float(row["K_after_nu"]) for row in run["iterations"]]
        axis.plot(range(1, len(values) + 1), values, marker="o", linewidth=1.7, label=f"nu0={run['start_nu']:g}")
    axis.set_title("ALT_OPT convergence: theta10/D55 direct Z-")
    axis.set_xlabel("ALT_OPT iteration")
    axis.set_ylabel("SKR (bits/use)")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    save_figure(output / "ao_convergence", figure)

    figure, axis = plt.subplots(figsize=(8.8, 5.4))
    for run in runs:
        trajectory = run["trajectory"]
        axis.plot(
            [float(point["nu"]) for point in trajectory],
            [float(point["V_A"]) for point in trajectory],
            marker="o", linewidth=1.5, label=f"nu0={run['start_nu']:g}",
        )
    axis.set_title("ALT_OPT trajectory: theta10/D55 direct Z-")
    axis.set_xlabel(r"$\nu_{\rm raw}$")
    axis.set_ylabel(r"$V_A$ (SNU)")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    save_figure(output / "ao_parameter_trajectory", figure)


def self_check() -> None:
    """Small optimizer check that never imports the physical evaluator."""

    class Synthetic:
        rows = {}
        catalog = {(0.2, value) for value in (0.1, 0.2, 0.3, 0.4)}
        requested_calls = 0
        cache_hits = 0
        unique_exact_evaluations = 0
        source_missing = []

        def __call__(self, nu: float, va: float) -> dict:
            self.requested_calls += 1
            key = (float(nu).hex(), float(va).hex())
            if key in self.rows:
                self.cache_hits += 1
                return self.rows[key]
            row = {"nu_raw": nu, "V_A": va, "SKR": -(va - 0.3) ** 2}
            self.rows[key] = row
            self.unique_exact_evaluations += 1
            return row

    objective = Synthetic()
    result = adaptive_maximize_1d(
        variable="V_A", fixed=0.2, values=[0.1, 0.2, 0.3, 0.4], objective=objective,
        parameter_tolerance=0.05,  # type: ignore[arg-type]
    )
    assert result["best_value"] == 0.3
    assert result["status"] == "BRACKETED_EXACT_CATALOG"

    # Repeat one hash-matched physical point through the unchanged evaluator;
    # this is a determinism check, not a new optimization run.
    config = unconstrained_config()
    channel = {
        **channel_row(config, BASELINE_DISTANCE_KM),
        "distance_km": BASELINE_DISTANCE_KM,
        "theta_div_full_rad": THETA_DIV_FULL_RAD,
        "w0_m": W0_M,
        "receiver_diameter_m": RECEIVER_DIAMETER_M,
    }
    channel["channel_hash"] = json_hash(channel)
    objective = ExactObjective(config, channel, OUTPUT, allow_new_source=False)
    first = objective(0.165, 5.5)
    second = objective(0.165, 5.5)
    for field in ("I_AB", "beta_I_AB", "chi_BE", "SKR"):
        assert float(first[field]) == float(second[field]), field


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--allow-new-source", action="store_true")
    parser.add_argument("--max-ao-iterations", type=int, default=MAX_AO_ITERATIONS)
    parser.add_argument("--distance-km", type=float, default=BASELINE_DISTANCE_KM)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        print("ALT_OPT_SELF_CHECK_PASS")
        return 0
    if args.max_ao_iterations <= 0:
        parser.error("--max-ao-iterations must be positive")
    if not math.isfinite(args.distance_km) or args.distance_km <= 0.0:
        parser.error("--distance-km must be finite and positive")

    torch.set_num_threads(1)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = unconstrained_config()
    # The reusable optical helper intentionally returns only the channel
    # quantities.  The unchanged evaluator also consumes these provenance
    # fields, so attach the same metadata as the existing D55 runner without
    # altering any physical quantity.
    channel = {
        **channel_row(config, args.distance_km),
        "distance_km": args.distance_km,
        "theta_div_full_rad": THETA_DIV_FULL_RAD,
        "w0_m": W0_M,
        "receiver_diameter_m": RECEIVER_DIAMETER_M,
    }
    channel["channel_hash"] = json_hash(channel)
    objective = ExactObjective(config, channel, output, allow_new_source=args.allow_new_source)

    # The existing exact bank is a source catalogue, not an optimization bound.
    # Only hash-matched MB source rows enter the exact candidate catalogue.
    catalogue_failures = []
    for family, nu, va in sorted(source_points_from_bank()):
        if family != "MB" or nu <= 0.0:
            continue
        try:
            candidate = candidate_from_payload(config, objective.payloads, "MB", nu, va)
            if candidate is None:
                raise ExactSourceUnavailable("source payload unavailable")
            objective.register_catalog(nu, va)
        except Exception as error:
            catalogue_failures.append({"nu_raw": nu, "V_A": va, "error": f"{type(error).__name__}: {error}"})

    runs = [run_single_ao(start, objective, max_iterations=args.max_ao_iterations) for start in AO_START_NUS]
    runs_with_final = [run for run in runs if run.get("final") is not None]
    if not runs_with_final:
        raise RuntimeError("No AO start produced an exact final candidate")
    best_run = max(runs_with_final, key=lambda run: float(run["final"]["SKR"]))

    objective_rows = list(objective.rows.values())
    write_csv(output / "ao_objective_evaluations.csv", objective_rows)
    iteration_rows = [row for run in runs for row in run["iterations"]]
    write_csv(output / "ao_iterations.csv", iteration_rows)
    summary_rows = []
    for run in runs:
        final = run.get("final")
        summary_rows.append({
            "start_id": f"nu_{run['start_nu']:g}",
            "initial_nu": run["start_nu"],
            "final_nu": None if final is None else final["nu_raw"],
            "final_V_A": None if final is None else final["V_A"],
            "I_AB": None if final is None else final["I_AB"],
            "beta_I_AB": None if final is None else final["beta_I_AB"],
            "chi_BE": None if final is None else final["chi_BE"],
            "K": None if final is None else final["SKR"],
            "AO_iterations": run.get("ao_iterations", 0),
            "exact_evaluations": run.get("exact_evaluations", 0),
            "requested_evaluations": run.get("requested_evaluations", 0),
            "cache_hits": run.get("cache_hits", 0),
            "status": run["status"],
            "warning_count": len(run.get("warnings", [])),
        })
    write_csv(output / "ao_summary.csv", summary_rows)
    make_figures(output, runs_with_final)

    same_theta_reference = objective(0.165, 5.5)
    prompt_reference = {
        "nu_raw": 0.165,
        "V_A": 5.5,
        "I_AB": 0.639529,
        "beta_I_AB": 0.607553,
        "chi_BE": 0.528511,
        "K": 0.0790419,
        "source": "user-provided validation reference",
    }
    previous_rows = list(csv.DictReader((ROOT / "results" / "skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme" / "candidate_evaluations.csv").open(encoding="utf-8", newline="")))
    previous_at_baseline = [
        row for row in previous_rows
        if abs(float(row["distance_km"]) - args.distance_km) < 1e-12
    ]
    source_cache_after = objective.source_cache_after()
    converged_statuses = {"CONVERGED_OBJECTIVE", "CONVERGED_PARAMETERS"}
    all_starts_converged = all(run["status"] in converged_statuses for run in runs)
    final_pairs = {
        (round(float(run["final"]["nu_raw"]), 12), round(float(run["final"]["V_A"]), 12))
        for run in runs_with_final
    }
    if all_starts_converged and len(final_pairs) == 1:
        initialization_result = "ALL_STARTS_CONVERGED_TO_SAME_SOLUTION"
    elif len(final_pairs) > 1:
        initialization_result = "INITIALIZATION_DEPENDENCE_OBSERVED"
    else:
        initialization_result = "INITIALIZATION_DEPENDENCE_UNRESOLVED"
    report_status = (
        "ALT_OPT_DIAGNOSTIC_COMPLETE"
        if all_starts_converged
        else "ALT_OPT_DIAGNOSTIC_COMPLETE_WITH_UNRESOLVED_INNER_SEARCH"
    )
    closed_search_statuses = {"BRACKETED_EXACT_CATALOG", "CLOSED_BY_EXACT_OUTER_PROBE"}
    search_statuses = [
        status
        for row in iteration_rows
        for status in (row.get("V_A_search_status"), row.get("nu_search_status"))
    ]
    boundary_statuses = [
        status
        for row in iteration_rows
        for status in (row.get("V_A_boundary_status"), row.get("nu_boundary_status"))
    ]
    report = {
        "status": report_status,
        "scope": "DIAGNOSTIC_ONLY",
        "baseline_distance_assumption_km": args.distance_km,
        "baseline_distance_assumption_reason": "30-degree 20-km HAP to 1-km UAV geometry and the supplied reference point",
        "configuration": {
            "theta_div_full_rad": THETA_DIV_FULL_RAD,
            "w0_m": W0_M,
            "D_r_m": RECEIVER_DIAMETER_M,
            "tau_zen": TAU_ZEN,
            "epsilon_ch": EPSILON,
            "beta": BETA,
            "AO_physical": "OFF",
            "phase_noise": "OFF",
            "peak_constraint": "OFF",
            "budget_constraint": "OFF",
            "holevo": "direct_Z_minus",
            "mi": "deterministic heterodyne product GH8",
        },
        "optimization": {
            "problem": "max_{nu_raw>0,V_A>0} K(nu_raw,V_A)",
            "algorithm": "ALT_OPT",
            "starts": list(AO_START_NUS),
            "K_tolerance": K_TOLERANCE,
            "max_iterations": args.max_ao_iterations,
            "source_policy": "hash-matched exact source cache; missing probes fail closed by default",
            "allow_new_source": args.allow_new_source,
            "context_hash": objective.context_hash,
        },
        "solution_claim": "BEST_AO_EXACT_TESTED_CANDIDATE_ONLY_NOT_GLOBAL",
        "best_ao_run": {
            "start_nu": best_run["start_nu"],
            "status": best_run["status"],
            "nu_raw": best_run["final"]["nu_raw"],
            "V_A": best_run["final"]["V_A"],
            "I_AB": best_run["final"]["I_AB"],
            "beta_I_AB": best_run["final"]["beta_I_AB"],
            "chi_BE": best_run["final"]["chi_BE"],
            "K": best_run["final"]["SKR"],
            "iterations": best_run["iterations"],
        },
        "multi_start_summary": summary_rows,
        "reference_comparison": {
            "prompt_reference": prompt_reference,
            "same_theta10_D55_exact_reference": same_theta_reference,
            "delta_K_vs_prompt_reference": float(best_run["final"]["SKR"]) - prompt_reference["K"],
            "delta_nu_vs_prompt_reference": float(best_run["final"]["nu_raw"]) - prompt_reference["nu_raw"],
            "delta_V_A_vs_prompt_reference": float(best_run["final"]["V_A"]) - prompt_reference["V_A"],
            "absolute_delta_K_vs_prompt_reference": abs(float(best_run["final"]["SKR"]) - prompt_reference["K"]),
            "relative_delta_K_vs_prompt_reference": (float(best_run["final"]["SKR"]) - prompt_reference["K"]) / prompt_reference["K"],
            "delta_K_vs_same_theta_reference": float(best_run["final"]["SKR"]) - float(same_theta_reference["SKR"]),
        },
        "initialization_analysis": {
            "status": initialization_result,
            "distinct_final_pairs": [list(pair) for pair in sorted(final_pairs)],
            "all_starts_converged": all_starts_converged,
        },
        "closure_analysis": {
            "all_outer_directions_checked": bool(search_statuses),
            "all_outer_directions_closed": bool(search_statuses) and all(
                status in closed_search_statuses for status in search_statuses
            ),
            "unclosed_inner_search_count": sum(
                status not in closed_search_statuses for status in search_statuses
            ),
            "boundary_not_closed_count": sum(
                status == "BOUNDARY_NOT_CLOSED" for status in boundary_statuses
            ),
        },
        "warnings_analysis": {
            "monotonicity_warning_count": sum(bool(run.get("warnings")) for run in runs),
            "numerical_failure_count": len(objective.numerical_failures),
        },
        "previous_exact_bank_reference": {
            "rerun": False,
            "artifact": "results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme/candidate_evaluations.csv",
            "exact_rows_at_baseline_distance": len(previous_at_baseline),
            "best_K_at_baseline_distance": max((float(row["SKR"]) for row in previous_at_baseline), default=None),
        },
        "evaluation_accounting": {
            "requested_objective_calls": objective.requested_calls,
            "unique_exact_SKR_evaluations": objective.unique_exact_evaluations,
            "cache_hits": objective.cache_hits,
            "source_missing_requests": len(objective.source_missing),
            "numerical_failure_requests": len(objective.numerical_failures),
            "catalogue_failures": catalogue_failures,
            "cache_context_hash": objective.context_hash,
        },
        "provenance": {
            "source_cache_before_count": len(objective.source_cache_before),
            "source_cache_after_count": len(source_cache_after),
            "source_cache_changed": objective.source_cache_before != source_cache_after,
            "source_cache_sha256_before": json_hash(objective.source_cache_before),
            "source_cache_sha256_after": json_hash(source_cache_after),
            "source_csv_modified": False,
            "physical_security_evaluator_modified": False,
        },
        "artifacts": {
            "summary_csv": "ao_summary.csv",
            "iteration_csv": "ao_iterations.csv",
            "objective_csv": "ao_objective_evaluations.csv",
            "report_json": "ao_report.json",
            "report_markdown": "ao_report.md",
            "convergence_png": "ao_convergence.png",
            "convergence_pdf": "ao_convergence.pdf",
            "trajectory_png": "ao_parameter_trajectory.png",
            "trajectory_pdf": "ao_parameter_trajectory.pdf",
        },
        "limitations": [
            "AO is a coordinate-wise diagnostic and is not a proof of global optimality.",
            "The supplied theta10/D55 reference differs slightly from the w0=0.10 reference artifact; both are reported separately.",
            "Continuous midpoint/boundary closure is reported as unresolved when the exact source cache lacks the required candidate; no interpolation is used.",
            "The repository lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.",
        ],
    }
    report["runner_sha256"] = sha256(Path(__file__).resolve())
    report_markdown = "\n".join([
        "# ALT_OPT exact diagnostic report",
        "",
        f"- Status: `{report['status']}`",
        f"- Scope: `{report['scope']}`",
        f"- Distance: `{args.distance_km:.12g} km`",
        f"- Claim: `{report['solution_claim']}`",
        "",
        "## Best exact-tested AO candidate",
        "",
        f"- Start: `{best_run['start_nu']:.12g}`",
        f"- nu_raw: `{best_run['final']['nu_raw']:.17g}`",
        f"- V_A: `{best_run['final']['V_A']:.17g}`",
        f"- I_AB: `{best_run['final']['I_AB']:.17g}`",
        f"- beta I_AB: `{best_run['final']['beta_I_AB']:.17g}`",
        f"- chi_BE: `{best_run['final']['chi_BE']:.17g}`",
        f"- K: `{best_run['final']['SKR']:.17g}`",
        f"- Run status: `{best_run['status']}`",
        "",
        "## Multi-start final rows",
        "",
        "| Initial nu | Final nu | Final V_A | K | Iterations | Exact evaluations | Status |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ] + [
        f"| {row['initial_nu']:.17g} | {row['final_nu']:.17g} | {row['final_V_A']:.17g} | {row['K']:.17g} | {row['AO_iterations']} | {row['exact_evaluations']} | `{row['status']}` |"
        for row in summary_rows
    ] + [
        "",
        "## Accounting and limitations",
        "",
        f"- Requested objective calls: `{objective.requested_calls}`",
        f"- Unique exact SKR evaluations: `{objective.unique_exact_evaluations}`",
        f"- Cache hits: `{objective.cache_hits}`",
        f"- Missing exact source probes: `{len(objective.source_missing)}`",
        f"- Numerical failures: `{len(objective.numerical_failures)}`",
        f"- Source cache changed: `{objective.source_cache_before != source_cache_after}`",
        "- No interpolation of source moments or SKR was used.",
        "- Physical AO and phase noise remained OFF; optimization AO is named ALT_OPT.",
        "- The result is not a global-optimality proof.",
        "",
    ])
    (output / "ao_report.md").write_text(report_markdown, encoding="utf-8")
    (output / "ao_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(Path(__file__).resolve(), output / Path(__file__).name)
    print(json.dumps({
        "status": report["status"],
        "best": report["best_ao_run"],
        "evaluation_accounting": report["evaluation_accounting"],
        "provenance": report["provenance"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
