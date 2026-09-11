"""Run bounded interval-preserving full-Z objective checks.

This is an analysis-only runner.  It reuses the existing full-Z Holevo
maximizer and the already calibrated TRAINING_SURROGATE_ONLY C/w path.  It
does not alter the production equations, select a baseline, access final-test
data, or run publication-scale training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_analysis_figures as runner  # noqa: E402


DATE = "20260911"
INPUT = ROOT / "results" / f"analysis_figure_data_{DATE}.json"
EXACT_INPUT = ROOT / "results" / f"analysis_exact_ap_security_anchors_{DATE}.json"
OUTPUT = ROOT / "results" / f"repaired_full_z_objective_analysis_{DATE}.json"
EXACT_JOB_CACHE = ROOT / "results" / f"repaired_full_z_exact_jobs_{DATE}.json"

SEARCH_Z_GRID_SIZE = runner.ANALYSIS_Z_GRID_SIZE
SEARCH_Z_REFINEMENT_STEPS = runner.ANALYSIS_Z_REFINEMENT_STEPS
PRODUCTION_Z_GRID_SIZE = runner.SECURITY_Z_GRID_SIZE
PRODUCTION_Z_REFINEMENT_STEPS = runner.SECURITY_Z_REFINEMENT_STEPS
PHYSICALITY_TOLERANCE = 1.0e-10
INTERVAL_ASSERTION_TOLERANCE = 1.0e-12
SMOKE_STEPS = 20
OPTIMIZATION_STEPS = 50
CASE_A_T = 0.028919672940466015
CASE_A_EPSILON = 0.001
CASE_A_EXPECTED_CHI = 0.01518919002933572
CASE_A_EXPECTED_RAW_K = 0.004757635492383283
EXACT_GAIN_THRESHOLD = 1.0e-5


class RepairBlocked(RuntimeError):
    """A semantic, gradient, or exact-evaluation gate failed."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _write_json(payload: dict[str, Any]) -> None:
    OUTPUT.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _load_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    figure_data = json.loads(INPUT.read_text(encoding="utf-8"))
    exact_data = json.loads(EXACT_INPUT.read_text(encoding="utf-8"))
    if exact_data.get("status") != "EXACT_AP_SOURCE_ROWS_COMPLETE":
        raise RepairBlocked("existing exact AP source rows are incomplete")
    return figure_data, exact_data


def _active_points(figure_data: dict[str, Any]) -> list[dict[str, Any]]:
    points = [point for point in figure_data["grid"]["points"] if point["active"]]
    if len(points) != 16:
        raise RepairBlocked(f"expected 16 active points, found {len(points)}")
    return points


def _state_tensors(points: list[dict[str, Any]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    return (
        torch.tensor([float(point["T"]) for point in points], dtype=torch.float64),
        torch.tensor([float(point["epsilon_base"]) for point in points], dtype=torch.float64),
        torch.tensor([float(point["weight"]) for point in points], dtype=torch.float64),
    )


def _noise(count: int, samples: int, seed: int) -> torch.Tensor:
    return runner.standard_complex_noise(
        (count, 256, samples),
        generator=torch.Generator(device="cpu").manual_seed(seed),
        device=torch.device("cpu"),
    )


def _old_proxy_from_values(
    point: dict[str, Any],
    c: float,
    w: float,
    va: float,
) -> dict[str, float | bool]:
    transmittance = float(point["T"])
    epsilon = float(point["epsilon_base"])
    a = va + 1.0
    b = 1.0 + transmittance * va + transmittance * epsilon
    physical_radicand = a * b - 1.0 - abs(a - b)
    z_phys = float(np.sqrt(max(physical_radicand, 0.0)))
    width = float(np.sqrt(max(2.0 * transmittance * epsilon * w, 0.0) + 1.0e-18))
    representative = 2.0 * np.sqrt(transmittance) * c + width
    z_proxy = 0.98 * z_phys * np.tanh(
        representative / (0.98 * z_phys + 1.0e-12)
    )
    z_minus = 2.0 * np.sqrt(transmittance) * c - np.sqrt(
        max(2.0 * transmittance * epsilon * w, 0.0)
    )
    z_plus = representative
    z_lower = max(z_minus, -z_phys)
    z_upper = min(z_plus, z_phys)
    return {
        "Z_proxy": z_proxy,
        "Z_L": z_lower,
        "Z_U": z_upper,
        "Z_phys": z_phys,
        "Z_proxy_minus_Z_L": z_proxy - z_lower,
        "below_lower": z_proxy < z_lower - 1.0e-12,
        "above_upper": z_proxy > z_upper + 1.0e-12,
    }


def _ensemble_from_rows(rows: list[dict[str, Any]]) -> runner.Ensemble:
    probabilities = torch.tensor(
        [row["probabilities"] for row in rows], dtype=torch.float64
    )
    amplitudes = torch.tensor(
        [
            [complex(value[0], value[1]) for value in row["amplitudes"]]
            for row in rows
        ],
        dtype=torch.complex128,
    )
    declared_va = torch.tensor(
        [float(row["V_A"]) for row in rows], dtype=torch.float64
    )
    ensemble = runner.Ensemble(
        probabilities=probabilities,
        amplitudes=amplitudes,
        declared_va=declared_va,
        raw_constellation=amplitudes[0],
        exact_csi_oracle=True,
        c4_symmetric=True,
    )
    ensemble.validate()
    return ensemble


def _full_z_holevo(
    ensemble: runner.Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    correlations: torch.Tensor,
    w_raw: torch.Tensor,
    *,
    grid_size: int,
    refinement_steps: int,
    marker: str,
) -> Any:
    """Call the existing full-Z implementation with surrogate C/w only."""

    return runner._holevo_from_source_moments(
        ensemble,
        transmittance,
        epsilon,
        coherent_correlation=correlations,
        w_raw=w_raw,
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=1.0e-8,
        physicality_tolerance=PHYSICALITY_TOLERANCE,
        diagnostics={
            "backend": marker,
            "artifact_class": "ANALYSIS_ESTIMATE",
            "source_moment_marker": "TRAINING_SURROGATE_ONLY",
            "phase_disabled": True,
            "c_phi": runner.PHASE_COEFFICIENT,
        },
        z_grid_size=grid_size,
        z_refinement_steps=refinement_steps,
    )


def _assert_selected_interval(result: Any, label: str) -> int:
    lower = result.diagnostics["Z_L"].detach()
    upper = result.diagnostics["Z_U"].detach()
    selected = result.z.detach()
    scale = torch.maximum(
        torch.ones_like(lower),
        torch.maximum(torch.abs(lower), torch.abs(upper)),
    )
    tolerance = INTERVAL_ASSERTION_TOLERANCE * scale
    invalid = (selected < lower - tolerance) | (selected > upper + tolerance)
    if bool(torch.any(invalid)):
        raise RepairBlocked(f"{label}: selected full-Z point escaped interval")
    return int(invalid.sum())


def _evaluate_with_moments(
    ensemble: runner.Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    correlations: torch.Tensor,
    w_raw: torch.Tensor,
    standard_noise: torch.Tensor,
    *,
    grid_size: int,
    refinement_steps: int,
    marker: str,
) -> dict[str, Any]:
    mi = runner.discrete_mutual_information(
        ensemble,
        transmittance,
        epsilon,
        noise_samples_per_symbol=standard_noise.shape[-1],
        standard_noise_samples=standard_noise,
        noise_sample_chunk_size=standard_noise.shape[-1],
    )
    holevo = _full_z_holevo(
        ensemble,
        transmittance,
        epsilon,
        correlations,
        w_raw,
        grid_size=grid_size,
        refinement_steps=refinement_steps,
        marker=marker,
    )
    raw = runner.BETA * mi - holevo.chi_be
    if not bool(torch.isfinite(raw).all()):
        raise RepairBlocked(f"{marker}: non-finite raw key rate")
    _assert_selected_interval(holevo, marker)
    return {
        "ensemble": ensemble,
        "I_AB": mi,
        "chi_BE": holevo.chi_be,
        "raw_K": raw,
        "holevo": holevo,
    }


def _exact_mb_source(exact_data: dict[str, Any]) -> tuple[float, float]:
    mb = exact_data["results"]["mb"]
    return float(mb["C"]), float(mb["w"])


def _source_for_mode(
    mode: str,
    rows: list[dict[str, Any]],
    exact_data: dict[str, Any],
) -> tuple[torch.Tensor, torch.Tensor, str]:
    if mode == "uniform":
        c, w = runner.CORRECTED_C, runner.CORRECTED_W
        marker = "corrected_AP_source_moments"
    elif mode == "mb":
        c, w = _exact_mb_source(exact_data)
        marker = "existing_exact_AP_source_moments"
    else:
        return (
            torch.tensor([float(row["C_surrogate"]) for row in rows], dtype=torch.float64),
            torch.tensor([float(row["w_surrogate"]) for row in rows], dtype=torch.float64),
            "saved_training_surrogate_source_moments",
        )
    count = len(rows)
    return (
        torch.full((count,), c, dtype=torch.float64),
        torch.full((count,), w, dtype=torch.float64),
        marker,
    )


def _semantic_audit(
    figure_data: dict[str, Any],
    exact_data: dict[str, Any],
) -> dict[str, Any]:
    points = _active_points(figure_data)
    transmittance, epsilon, weights = _state_tensors(points)
    standard_noise = _noise(
        len(points), runner.GRID_NOISE_SAMPLES, runner.existing_case.AWGN_SEED
    )
    modes: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for mode, _, _ in runner.METHODS:
        candidate_rows = figure_data["candidates"][mode]["rows"]
        old_rows = figure_data["grid_security_surrogate"][mode]["rows"]
        ensemble = _ensemble_from_rows(candidate_rows)
        surrogate_c, surrogate_w, surrogate_marker = _source_for_mode(
            mode, candidate_rows, exact_data
        )
        production = _evaluate_with_moments(
            ensemble,
            transmittance,
            epsilon,
            surrogate_c if mode not in {"uniform", "mb"} else surrogate_c,
            surrogate_w,
            standard_noise,
            grid_size=PRODUCTION_Z_GRID_SIZE,
            refinement_steps=PRODUCTION_Z_REFINEMENT_STEPS,
            marker="production_full_Z_recheck",
        )
        repaired = _evaluate_with_moments(
            ensemble,
            transmittance,
            epsilon,
            torch.tensor(
                [float(row["C_surrogate"]) for row in candidate_rows],
                dtype=torch.float64,
            ),
            torch.tensor(
                [float(row["w_surrogate"]) for row in candidate_rows],
                dtype=torch.float64,
            ),
            standard_noise,
            grid_size=SEARCH_Z_GRID_SIZE,
            refinement_steps=SEARCH_Z_REFINEMENT_STEPS,
            marker="repaired_interval_preserving_search",
        )
        semantic_rows: list[dict[str, Any]] = []
        for index, (point, old_row) in enumerate(zip(points, old_rows)):
            old_proxy = _old_proxy_from_values(
                point,
                float(old_row["C"]),
                float(old_row["w"]),
                float(candidate_rows[index]["V_A"]),
            )
            lower = float(repaired["holevo"].diagnostics["Z_L"][index].detach())
            upper = float(repaired["holevo"].diagnostics["Z_U"][index].detach())
            row = {
                "state": index,
                "T": float(point["T"]),
                "epsilon_base": float(point["epsilon_base"]),
                "V_A": float(candidate_rows[index]["V_A"]),
                "Z_L": lower,
                "Z_U": upper,
                "Z_star_production": float(production["holevo"].z[index].detach()),
                "Z_star_repaired": float(repaired["holevo"].z[index].detach()),
                "Z_proxy": float(old_proxy["Z_proxy"]),
                "Z_proxy_minus_Z_L": float(old_proxy["Z_proxy_minus_Z_L"]),
                "chi_production_or_exact": float(production["chi_BE"][index].detach()),
                "chi_repaired": float(repaired["chi_BE"][index].detach()),
                "K_repaired": float(repaired["raw_K"][index].detach()),
                "old_proxy_K": float(old_row["raw_K"]),
                "old_proxy_below_lower": bool(old_proxy["below_lower"]),
                "repaired_selected_valid": bool(
                    float(repaired["holevo"].z[index].detach())
                    >= lower - INTERVAL_ASSERTION_TOLERANCE
                    and float(repaired["holevo"].z[index].detach())
                    <= upper + INTERVAL_ASSERTION_TOLERANCE
                ),
                "production_source_moments": surrogate_marker,
            }
            semantic_rows.append(row)
            all_rows.append(row)
        modes[mode] = {
            "source_moment_provenance": surrogate_marker,
            "production_resolution": {
                "grid_size": PRODUCTION_Z_GRID_SIZE,
                "refinement_steps": PRODUCTION_Z_REFINEMENT_STEPS,
            },
            "repaired_search_resolution": {
                "grid_size": SEARCH_Z_GRID_SIZE,
                "refinement_steps": SEARCH_Z_REFINEMENT_STEPS,
            },
            "rows": semantic_rows,
            "old_proxy_below_lower_count": sum(
                bool(row["old_proxy_below_lower"]) for row in semantic_rows
            ),
            "repaired_interval_violation_count": sum(
                not bool(row["repaired_selected_valid"]) for row in semantic_rows
            ),
            "production_weighted_raw_K": float(
                torch.sum(weights * production["raw_K"].detach())
            ),
            "repaired_weighted_raw_K": float(
                torch.sum(weights * repaired["raw_K"].detach())
            ),
        }
    return {
        "active_state_count": len(points),
        "modes": modes,
        "all_old_proxy_below_lower_count": sum(
            bool(row["old_proxy_below_lower"]) for row in all_rows
        ),
        "all_repaired_interval_violation_count": sum(
            not bool(row["repaired_selected_valid"]) for row in all_rows
        ),
    }


def _frozen_candidate_ranking(
    figure_data: dict[str, Any],
    semantic: dict[str, Any],
) -> dict[str, Any]:
    points = _active_points(figure_data)
    old_scores = {
        mode: float(
            sum(
                float(point["weight"]) * float(row["raw_K"])
                for point, row in zip(
                    points, figure_data["grid_security_surrogate"][mode]["rows"]
                )
            )
        )
        for mode, _, _ in runner.METHODS
    }
    repaired_scores = {
        mode: float(semantic["modes"][mode]["repaired_weighted_raw_K"])
        for mode, _, _ in runner.METHODS
    }
    production_scores = {
        mode: float(semantic["modes"][mode]["production_weighted_raw_K"])
        for mode, _, _ in runner.METHODS
    }

    def ranks(scores: dict[str, float]) -> dict[str, int]:
        ordered = sorted(scores, key=lambda key: (-scores[key], key))
        return {mode: index + 1 for index, mode in enumerate(ordered)}

    old_rank = ranks(old_scores)
    repaired_rank = ranks(repaired_scores)
    production_rank = ranks(production_scores)
    rows = []
    for mode, label, _ in runner.METHODS:
        rows.append(
            {
                "method": mode,
                "label": label,
                "old_proxy_weighted_raw_K": old_scores[mode],
                "repaired_weighted_raw_K": repaired_scores[mode],
                "production_full_Z_weighted_raw_K": production_scores[mode],
                "old_rank": old_rank[mode],
                "repaired_rank": repaired_rank[mode],
                "production_rank": production_rank[mode],
                "rank_change_old_to_repaired": repaired_rank[mode] - old_rank[mode],
            }
        )
    return {
        "rows": rows,
        "old_rank_order": sorted(old_scores, key=lambda key: (-old_scores[key], key)),
        "repaired_rank_order": sorted(
            repaired_scores, key=lambda key: (-repaired_scores[key], key)
        ),
        "production_rank_order": sorted(
            production_scores, key=lambda key: (-production_scores[key], key)
        ),
    }


def _case_a_reproduction() -> dict[str, Any]:
    transmitter = runner._initialize_transmitter("uniform", 20260920)
    transmittance = torch.tensor([CASE_A_T], dtype=torch.float64)
    epsilon = torch.tensor([CASE_A_EPSILON], dtype=torch.float64)
    standard_noise = _noise(1, runner.existing_case.AWGN_SAMPLES, runner.existing_case.AWGN_SEED)
    ensemble = transmitter(transmittance, epsilon)
    exact_c = torch.tensor([runner.CORRECTED_C], dtype=torch.float64)
    exact_w = torch.tensor([runner.CORRECTED_W], dtype=torch.float64)
    surrogate_c, surrogate_w, _ = runner._surrogate_batch(ensemble)
    exact = _evaluate_with_moments(
        ensemble,
        transmittance,
        epsilon,
        exact_c,
        exact_w,
        standard_noise,
        grid_size=PRODUCTION_Z_GRID_SIZE,
        refinement_steps=PRODUCTION_Z_REFINEMENT_STEPS,
        marker="case_A_exact_reference",
    )
    repaired = _evaluate_with_moments(
        ensemble,
        transmittance,
        epsilon,
        surrogate_c,
        surrogate_w,
        standard_noise,
        grid_size=PRODUCTION_Z_GRID_SIZE,
        refinement_steps=PRODUCTION_Z_REFINEMENT_STEPS,
        marker="case_A_repaired_surrogate_full_Z",
    )
    exact_raw = float(exact["raw_K"][0].detach())
    repaired_raw = float(repaired["raw_K"][0].detach())
    exact_chi = float(exact["chi_BE"][0].detach())
    repaired_chi = float(repaired["chi_BE"][0].detach())
    return {
        "state": {
            "T": CASE_A_T,
            "epsilon_base": CASE_A_EPSILON,
            "V_A": 1.0,
        },
        "expected_reference": {
            "chi_BE": CASE_A_EXPECTED_CHI,
            "raw_K": CASE_A_EXPECTED_RAW_K,
        },
        "exact_source_moments": {"C": runner.CORRECTED_C, "w": runner.CORRECTED_W},
        "repaired_source_moments": {
            "C": float(surrogate_c[0].detach()),
            "w": float(surrogate_w[0].detach()),
        },
        "exact": {
            "I_AB": float(exact["I_AB"][0].detach()),
            "chi_BE": exact_chi,
            "raw_K": exact_raw,
            "Z_L": float(exact["holevo"].diagnostics["Z_L"][0].detach()),
            "Z_U": float(exact["holevo"].diagnostics["Z_U"][0].detach()),
            "Z_star": float(exact["holevo"].z[0].detach()),
        },
        "repaired": {
            "I_AB": float(repaired["I_AB"][0].detach()),
            "chi_BE": repaired_chi,
            "raw_K": repaired_raw,
            "Z_L": float(repaired["holevo"].diagnostics["Z_L"][0].detach()),
            "Z_U": float(repaired["holevo"].diagnostics["Z_U"][0].detach()),
            "Z_star": float(repaired["holevo"].z[0].detach()),
        },
        "errors": {
            "exact_chi_absolute": abs(exact_chi - CASE_A_EXPECTED_CHI),
            "exact_raw_K_absolute": abs(exact_raw - CASE_A_EXPECTED_RAW_K),
            "repaired_vs_exact_raw_K_absolute": abs(repaired_raw - exact_raw),
            "repaired_vs_exact_chi_absolute": abs(repaired_chi - exact_chi),
        },
        "interval_violation_count": 0,
    }


def _anchor_comparison(figure_data: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for mode in ("uniform", "mb", "full"):
        exact_rows = figure_data["anchor_security"][mode]["exact"]["rows"]
        repaired_rows = figure_data["anchor_security"][mode]["surrogate"]["rows"]
        rows = []
        for exact, repaired in zip(exact_rows, repaired_rows):
            exact_k = float(exact["raw_K"])
            repaired_k = float(repaired["raw_K"])
            row = {
                "T": float(exact["T"]),
                "epsilon_base": float(exact["epsilon_base"]),
                "exact_raw_K": exact_k,
                "repaired_surrogate_raw_K": repaired_k,
                "absolute_error": abs(repaired_k - exact_k),
                "relative_error": abs(repaired_k - exact_k) / max(abs(exact_k), 1.0e-40),
                "exact_chi_BE": float(exact["chi_BE"]),
                "repaired_surrogate_chi_BE": float(repaired["chi_BE"]),
                "exact_Z_star": float(exact["Z_star"]),
                "repaired_Z_star": float(repaired["Z_star"]),
            }
            rows.append(row)
            all_rows.append(row)
        comparisons[mode] = {
            "rows": rows,
            "max_absolute_K_error": max(row["absolute_error"] for row in rows),
            "max_relative_K_error": max(row["relative_error"] for row in rows),
        }

    exact_by_anchor = {
        mode: figure_data["anchor_security"][mode]["exact"]["rows"]
        for mode in ("uniform", "mb", "full")
    }
    repaired_by_anchor = {
        mode: figure_data["anchor_security"][mode]["surrogate"]["rows"]
        for mode in ("uniform", "mb", "full")
    }
    rank_rows = []
    for index in range(len(exact_by_anchor["uniform"])):
        exact_order = sorted(
            exact_by_anchor,
            key=lambda mode: (-float(exact_by_anchor[mode][index]["raw_K"]), mode),
        )
        repaired_order = sorted(
            repaired_by_anchor,
            key=lambda mode: (-float(repaired_by_anchor[mode][index]["raw_K"]), mode),
        )
        rank_rows.append(
            {
                "anchor": index,
                "T": float(exact_by_anchor["uniform"][index]["T"]),
                "exact_order": exact_order,
                "repaired_order": repaired_order,
                "rank_consistent": exact_order == repaired_order,
            }
        )
    return {
        "comparisons": comparisons,
        "max_absolute_K_error_all_rows": max(row["absolute_error"] for row in all_rows),
        "max_relative_K_error_all_rows": max(row["relative_error"] for row in all_rows),
        "rank_rows": rank_rows,
        "all_rank_consistent": all(row["rank_consistent"] for row in rank_rows),
        "ps_va_exact_anchor_available": False,
    }


def _gradient_smoke(figure_data: dict[str, Any]) -> dict[str, Any]:
    points = _active_points(figure_data)
    point = points[5]
    transmittance = torch.tensor([float(point["T"])], dtype=torch.float64)
    epsilon = torch.tensor([float(point["epsilon_base"])], dtype=torch.float64)
    standard_noise = _noise(1, 16, runner.existing_case.AWGN_SEED + 5)
    rows = []
    for index, mode in enumerate(("ps", "gs", "va")):
        transmitter = runner._initialize_transmitter(mode, 203000 + index)
        for parameter in transmitter.parameters():
            parameter.grad = None
        evaluation = _evaluate_transmitter(
            transmitter, transmittance, epsilon, standard_noise, search=True
        )
        loss = -evaluation["raw_K"].sum()
        if not bool(torch.isfinite(loss)):
            raise RepairBlocked(f"gradient smoke {mode}: non-finite loss")
        loss.backward()
        gradients = [
            parameter.grad
            for parameter in transmitter.parameters()
            if parameter.grad is not None
        ]
        finite = bool(gradients) and all(bool(torch.isfinite(value).all()) for value in gradients)
        norm = (
            float(torch.sqrt(sum(torch.sum(value.detach().square()) for value in gradients)))
            if finite
            else float("nan")
        )
        if not finite or not np.isfinite(norm) or norm <= 0.0:
            raise RepairBlocked(f"gradient smoke {mode}: invalid gradient")
        holevo = evaluation["holevo"]
        rows.append(
            {
                "mode": mode,
                "finite": finite,
                "gradient_norm": norm,
                "maximizing_location": list(holevo.diagnostics["maximizing_location"]),
                "Z_L": float(holevo.diagnostics["Z_L"][0].detach()),
                "Z_U": float(holevo.diagnostics["Z_U"][0].detach()),
                "Z_star": float(holevo.z[0].detach()),
                "selected_branch_valid": True,
            }
        )
    return {"state": point, "rows": rows, "all_pass": True}


def _evaluate_transmitter(
    transmitter: runner.JointTransmitter,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    standard_noise: torch.Tensor,
    *,
    search: bool,
) -> dict[str, Any]:
    ensemble = transmitter(transmittance, epsilon)
    correlations, w_raw, source_diagnostics = runner._surrogate_batch(ensemble)
    result = _evaluate_with_moments(
        ensemble,
        transmittance,
        epsilon,
        correlations,
        w_raw,
        standard_noise,
        grid_size=SEARCH_Z_GRID_SIZE if search else PRODUCTION_Z_GRID_SIZE,
        refinement_steps=SEARCH_Z_REFINEMENT_STEPS if search else PRODUCTION_Z_REFINEMENT_STEPS,
        marker=(
            "repaired_interval_preserving_search"
            if search
            else "repaired_full_Z_security_recheck"
        ),
    )
    result["C"] = correlations
    result["w"] = w_raw
    result["source_diagnostics"] = source_diagnostics
    return result


def _ps_entropy(probabilities: torch.Tensor) -> float:
    safe = torch.clamp_min(probabilities, 1.0e-300)
    return float((-torch.sum(probabilities * torch.log2(safe), dim=-1)).mean())


def _gs_displacement(transmitter: runner.JointTransmitter) -> float | None:
    if transmitter.gs_model is None:
        return None
    base = transmitter.base_relative_constellation[runner.ORBIT_INDICES]
    relative = transmitter.gs_model.relative_prototypes()
    return float(torch.sqrt(torch.mean((relative - base).abs().square())).detach())


def _trajectory_metrics(
    transmitter: runner.JointTransmitter,
    evaluation: dict[str, Any],
    weights: torch.Tensor,
    step: int,
) -> dict[str, Any]:
    ensemble = evaluation["ensemble"]
    objective = torch.sum(weights * evaluation["raw_K"])
    beta_i = torch.sum(weights * runner.BETA * evaluation["I_AB"])
    chi = torch.sum(weights * evaluation["chi_BE"])
    mean_va = ensemble.declared_va.mean()
    return {
        "step": step,
        "repaired_objective_weighted_raw_K": float(objective.detach()),
        "weighted_beta_I_AB": float(beta_i.detach()),
        "weighted_chi_BE": float(chi.detach()),
        "mean_V_A": float(mean_va.detach()),
        "ps_entropy": _ps_entropy(ensemble.probabilities.detach()),
        "energy_constraint_mean_V_A_minus_budget": float((mean_va - runner.VA_BUDGET).detach()),
        "min_probability": float(ensemble.probabilities.detach().min()),
        "maximum_probability_sum_error": float(
            (ensemble.probabilities.detach().sum(dim=-1) - 1.0).abs().max()
        ),
        "minimum_unique_state_count": min(
            runner._unique_state_count(ensemble.amplitudes, row)
            for row in range(ensemble.amplitudes.shape[0])
        ),
        "maximum_symbol_energy": float(ensemble.amplitudes.detach().abs().square().max()),
        "GS_relative_prototype_displacement": _gs_displacement(transmitter),
        "finite": bool(
            torch.isfinite(ensemble.probabilities).all()
            and torch.isfinite(ensemble.amplitudes.real).all()
            and torch.isfinite(ensemble.amplitudes.imag).all()
            and torch.isfinite(evaluation["raw_K"]).all()
        ),
    }


def _initialize_pair(seed: int) -> tuple[runner.JointTransmitter, runner.JointTransmitter]:
    ps_va = runner._initialize_transmitter("ps_va", seed)
    full = runner._initialize_transmitter("full", seed)
    if ps_va.ps_network is None or ps_va.va_network is None:
        raise RepairBlocked("PS+V_A initializer did not create both branches")
    if full.ps_network is None or full.va_network is None:
        raise RepairBlocked("Full initializer did not create both branches")
    full.ps_network.load_state_dict(ps_va.ps_network.state_dict())
    full.va_network.load_state_dict(ps_va.va_network.state_dict())
    same_ps = all(
        torch.equal(left, right)
        for left, right in zip(ps_va.ps_network.parameters(), full.ps_network.parameters())
    )
    same_va = all(
        torch.equal(left, right)
        for left, right in zip(ps_va.va_network.parameters(), full.va_network.parameters())
    )
    if not same_ps or not same_va:
        raise RepairBlocked("PS+V_A and Full initial branches are not identical")
    return ps_va, full


def _optimize_one(
    transmitter: runner.JointTransmitter,
    mode: str,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    weights: torch.Tensor,
    standard_noise: torch.Tensor,
) -> dict[str, Any]:
    learning_rate = {"ps_va": 3.0e-4, "full": 1.0e-4}[mode]
    optimizer = torch.optim.Adam(transmitter.parameters(), lr=learning_rate)
    dual = 0.0
    with torch.no_grad():
        initial = _evaluate_transmitter(
            transmitter, transmittance, epsilon, standard_noise, search=True
        )
    trajectory = [_trajectory_metrics(transmitter, initial, weights, 0)]
    objective_trace = [trajectory[0]["repaired_objective_weighted_raw_K"]]
    gradient_norms: list[float] = []
    for step in range(1, OPTIMIZATION_STEPS + 1):
        optimizer.zero_grad(set_to_none=True)
        evaluation = _evaluate_transmitter(
            transmitter, transmittance, epsilon, standard_noise, search=True
        )
        objective = torch.sum(weights * evaluation["raw_K"])
        violation_tensor = evaluation["ensemble"].declared_va.mean() - runner.VA_BUDGET
        loss = -objective + dual * violation_tensor
        if not bool(torch.isfinite(loss)):
            raise RepairBlocked(f"{mode} step {step}: non-finite loss")
        loss.backward()
        parameters = [parameter for parameter in transmitter.parameters() if parameter.grad is not None]
        if not parameters or any(not bool(torch.isfinite(parameter.grad).all()) for parameter in parameters):
            raise RepairBlocked(f"{mode} step {step}: non-finite gradient")
        gradient_norm = float(
            torch.sqrt(sum(torch.sum(parameter.grad.detach().square()) for parameter in parameters))
        )
        gradient_norms.append(gradient_norm)
        torch.nn.utils.clip_grad_norm_(parameters, 1.0)
        optimizer.step()
        dual = max(0.0, dual + 1.0e-2 * float(violation_tensor.detach()))
        with torch.no_grad():
            post = _evaluate_transmitter(
                transmitter, transmittance, epsilon, standard_noise, search=True
            )
        metrics = _trajectory_metrics(transmitter, post, weights, step)
        objective_trace.append(metrics["repaired_objective_weighted_raw_K"])
        if step % 10 == 0 or step == OPTIMIZATION_STEPS:
            metrics["gradient_norm_pre_clip"] = gradient_norm
            metrics["energy_dual"] = dual
            trajectory.append(metrics)
            print(
                f"repaired {mode} step {step}: "
                f"K={metrics['repaired_objective_weighted_raw_K']:.12g}",
                flush=True,
            )
        if step == SMOKE_STEPS:
            first_window = objective_trace[1:6]
            last_window = objective_trace[SMOKE_STEPS - 4 : SMOKE_STEPS + 1]
            smoke_pass = (
                all(bool(record["finite"]) for record in trajectory)
                and min(float(record["min_probability"]) for record in trajectory) > 0.0
                and min(int(record["minimum_unique_state_count"]) for record in trajectory) == 256
                and np.mean(last_window) >= np.mean(first_window) - 1.0e-8
            )
            if not smoke_pass:
                raise RepairBlocked(f"{mode}: 20-step repaired-objective smoke failed")
    checkpoint = ROOT / "results" / f"repaired_full_z_checkpoint_{mode}_{DATE}_step_{OPTIMIZATION_STEPS}.pt"
    torch.save(
        {
            "artifact_class": "ANALYSIS_ESTIMATE",
            "objective": "interval_preserving_full_Z_with_surrogate_Cw",
            "mode": mode,
            "step": OPTIMIZATION_STEPS,
            "state_dict": transmitter.state_dict(),
        },
        checkpoint,
    )
    return {
        "mode": mode,
        "status": "BOUNDED_ANALYSIS_OPTIMIZED",
        "steps": OPTIMIZATION_STEPS,
        "smoke": {"status": "PASS", "steps": SMOKE_STEPS},
        "initial_objective": objective_trace[0],
        "final_objective": objective_trace[-1],
        "objective_change": objective_trace[-1] - objective_trace[0],
        "trajectory": trajectory,
        "checkpoint": str(checkpoint.relative_to(ROOT)),
        "checkpoint_sha256": _sha256(checkpoint),
        "maximum_gradient_norm_pre_clip": max(gradient_norms),
    }


def _bounded_optimization(figure_data: dict[str, Any]) -> dict[str, Any]:
    points = _active_points(figure_data)
    transmittance, epsilon, weights = _state_tensors(points)
    standard_noise = _noise(
        len(points), runner.TRAINING_NOISE_SAMPLES, runner.existing_case.AWGN_SEED + 2
    )
    ps_va, full = _initialize_pair(20260924)
    print("repaired optimization ps_va: start", flush=True)
    ps_va_result = _optimize_one(
        ps_va, "ps_va", transmittance, epsilon, weights, standard_noise
    )
    print("repaired optimization full: start", flush=True)
    full_result = _optimize_one(
        full, "full", transmittance, epsilon, weights, standard_noise
    )
    return {
        "same_initial_ps_and_va": True,
        "modes": {"ps_va": ps_va_result, "full": full_result},
        "grid": {
            "active_state_count": len(points),
            "same_weights": True,
            "same_noise_seed": runner.existing_case.AWGN_SEED + 2,
            "phase_disabled": True,
        },
    }


def _load_checkpoint_pair(optimization: dict[str, Any]) -> dict[str, runner.JointTransmitter]:
    ps_va, full = _initialize_pair(20260924)
    for mode, transmitter in (("ps_va", ps_va), ("full", full)):
        path = ROOT / optimization["modes"][mode]["checkpoint"]
        state = torch.load(path, map_location="cpu", weights_only=False)
        transmitter.load_state_dict(state["state_dict"])
    return {"ps_va": ps_va, "full": full}


def _exact_three_state(
    figure_data: dict[str, Any],
    exact_data: dict[str, Any],
    optimization: dict[str, Any],
    method_names: tuple[str, ...] = ("ps_va", "full"),
) -> dict[str, Any]:
    transmitters = _load_checkpoint_pair(optimization)
    anchor_points = figure_data["grid"]["anchor_points"]
    selected_indices = (0, len(anchor_points) // 2, len(anchor_points) - 1)
    selected = [anchor_points[index] for index in selected_indices]
    labels = ("poor", "median", "good")
    transmittance = torch.tensor([float(point["T"]) for point in selected], dtype=torch.float64)
    epsilon = torch.tensor([float(point["epsilon_base"]) for point in selected], dtype=torch.float64)
    weights = torch.ones(3, dtype=torch.float64) / 3.0
    standard_noise = _noise(3, runner.ANCHOR_NOISE_SAMPLES, runner.existing_case.AWGN_SEED + 1)

    mb_transmitter = runner._initialize_transmitter("mb", 20260921)
    mb_ensemble = mb_transmitter(transmittance, epsilon)
    mb_c, mb_w = _exact_mb_source(exact_data)
    mb_c_tensor = torch.full((3,), mb_c, dtype=torch.float64)
    mb_w_tensor = torch.full((3,), mb_w, dtype=torch.float64)
    mb_eval = _evaluate_with_moments(
        mb_ensemble,
        transmittance,
        epsilon,
        mb_c_tensor,
        mb_w_tensor,
        standard_noise,
        grid_size=PRODUCTION_Z_GRID_SIZE,
        refinement_steps=PRODUCTION_Z_REFINEMENT_STEPS,
        marker="exact_three_state_MB_existing_AP_source",
    )

    jobs: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    ensembles: dict[str, runner.Ensemble] = {}
    for mode in method_names:
        transmitter = transmitters[mode]
        ensemble = transmitter(transmittance, epsilon)
        ensembles[mode] = ensemble
        for index, label in enumerate(labels):
            probabilities, prototypes = runner._orbit_inputs(ensemble, index)
            jobs[f"{mode}_{label}"] = (probabilities.detach(), prototypes.detach())
    print("exact AP three-state source moments: start", flush=True)
    exact_jobs = runner._run_exact_jobs(jobs)
    EXACT_JOB_CACHE.write_text(
        json.dumps(
            {
                "artifact_class": "EXACT_AP_SECURITY_ANCHOR",
                "status": "EXACT_AP_JOB_BATCH_COMPLETE",
                "method_names": list(method_names),
                "jobs": exact_jobs,
            },
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    incomplete_jobs = {
        key: {
            "status": value.get("status"),
            "reason": value.get("reason"),
            "runtime_seconds": value.get("runtime_seconds"),
            "rows": value.get("rows", []),
        }
        for key, value in exact_jobs.items()
        if value.get("status") != "FULL_SUPPORT_CONVERGED"
    }

    rows: list[dict[str, Any]] = []
    method_evaluations: dict[str, Any] = {
        "mb": {
            "ensemble": mb_ensemble,
            "evaluation": mb_eval,
            "source_moment_marker": "existing_exact_AP_source_moments",
        }
    }
    for mode in method_names:
        if any(
            exact_jobs[f"{mode}_{label}"].get("status") != "FULL_SUPPORT_CONVERGED"
            for label in labels
        ):
            continue
        c = torch.tensor(
            [float(exact_jobs[f"{mode}_{label}"]["C"]) for label in labels],
            dtype=torch.float64,
        )
        w = torch.tensor(
            [float(exact_jobs[f"{mode}_{label}"]["w"]) for label in labels],
            dtype=torch.float64,
        )
        evaluation = _evaluate_with_moments(
            ensembles[mode],
            transmittance,
            epsilon,
            c,
            w,
            standard_noise,
            grid_size=PRODUCTION_Z_GRID_SIZE,
            refinement_steps=PRODUCTION_Z_REFINEMENT_STEPS,
            marker=f"exact_three_state_{mode}_AP_source",
        )
        method_evaluations[mode] = {
            "ensemble": ensembles[mode],
            "evaluation": evaluation,
            "source_moment_marker": "new_exact_AP_source_moments",
            "C": c,
            "w": w,
        }

    for index, (label, point) in enumerate(zip(labels, selected)):
        state_methods: dict[str, Any] = {}
        for mode in ("mb", *method_names):
            if mode not in method_evaluations:
                continue
            item = method_evaluations[mode]
            evaluation = item["evaluation"]
            holevo = evaluation["holevo"]
            state_methods[mode] = {
                "I_AB": float(evaluation["I_AB"][index].detach()),
                "chi_BE": float(evaluation["chi_BE"][index].detach()),
                "raw_K": float(evaluation["raw_K"][index].detach()),
                "Z_L": float(holevo.diagnostics["Z_L"][index].detach()),
                "Z_U": float(holevo.diagnostics["Z_U"][index].detach()),
                "Z_star": float(holevo.z[index].detach()),
                "source_moment_marker": item["source_moment_marker"],
            }
        order = sorted(state_methods, key=lambda mode: (-state_methods[mode]["raw_K"], mode))
        ps_va_k = state_methods.get("ps_va", {}).get("raw_K")
        full_k = state_methods.get("full", {}).get("raw_K")
        mb_k = state_methods["mb"]["raw_K"]
        rows.append(
            {
                "label": label,
                "T": float(point["T"]),
                "epsilon_base": float(point["epsilon_base"]),
                "methods": state_methods,
                "rank_order": order,
                "ps_va_minus_mb": None if ps_va_k is None else ps_va_k - mb_k,
                "full_minus_mb": None if full_k is None else full_k - mb_k,
                "full_minus_ps_va": (
                    None
                    if full_k is None or ps_va_k is None
                    else full_k - ps_va_k
                ),
            }
        )
    weighted = {
        mode: float(
            torch.sum(weights * method_evaluations[mode]["evaluation"]["raw_K"].detach())
        )
        for mode in ("mb", *method_names)
        if mode in method_evaluations
    }
    return {
        "state_selection": {
            "labels": labels,
            "anchor_indices": list(selected_indices),
            "selection_rule": "existing poor/median/good full-Z anchor states",
        },
        "exact_ap_jobs": {
            key: {
                "status": value["status"],
                "C": value.get("C"),
                "w": value.get("w"),
                "minimum_eigenvalue": value.get("minimum_eigenvalue"),
                "runtime_seconds": value["runtime_seconds"],
                "reason": value.get("reason"),
            }
            for key, value in exact_jobs.items()
        },
        "rows": rows,
        "weighted_equal_three_state_raw_K": weighted,
        "incomplete_exact_ap_jobs": incomplete_jobs,
        "evaluated_methods": ["mb", *method_names],
        "exact_job_cache": str(EXACT_JOB_CACHE.relative_to(ROOT)),
        "exact_job_cache_sha256": _sha256(EXACT_JOB_CACHE),
        "same_channel_states": True,
        "same_noise": True,
        "phase_disabled": True,
    }


def _objective_equivalence(
    semantic: dict[str, Any],
    case_a: dict[str, Any],
    anchors: dict[str, Any],
    gradient: dict[str, Any],
) -> dict[str, Any]:
    interval_pass = semantic["all_repaired_interval_violation_count"] == 0
    case_a_pass = (
        case_a["errors"]["exact_chi_absolute"] <= 1.0e-12
        and case_a["errors"]["exact_raw_K_absolute"] <= 1.0e-12
        and case_a["errors"]["repaired_vs_exact_raw_K_absolute"] <= 2.0e-6
    )
    anchor_pass = (
        anchors["max_absolute_K_error_all_rows"] <= 1.0e-6
        and anchors["max_relative_K_error_all_rows"] <= 1.0e-3
        and anchors["all_rank_consistent"]
    )
    gradient_pass = bool(gradient["all_pass"])
    return {
        "interval_invariant_pass": interval_pass,
        "case_a_reproduction_pass": case_a_pass,
        "existing_anchor_equivalence_pass": anchor_pass,
        "gradient_smoke_pass": gradient_pass,
        "security_equation_changed": False,
        "only_Cw_approximate_during_search": True,
        "all_pass": interval_pass and case_a_pass and anchor_pass and gradient_pass,
        "thresholds": {
            "case_a_repaired_vs_exact_raw_K_absolute_max": 2.0e-6,
            "anchor_absolute_K_error_max": 1.0e-6,
            "anchor_relative_K_error_max": 1.0e-3,
        },
    }


def _base_artifact(figure_data: dict[str, Any], exact_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "status": "REPAIRED_OBJECTIVE_AUDIT_RUNNING",
        "not_security_certification": True,
        "scope": (
            "bounded interval-preserving full-Z objective audit, fixed-candidate "
            "ranking, gradient smoke, and PS+V_A/Full short analysis only"
        ),
        "objective": {
            "old_proxy": (
                "Z_proxy=0.98*z_phys*tanh((2*sqrt(T)*C+sqrt(2*T*epsilon*w)) "
                "/(0.98*z_phys+1e-12))"
            ),
            "repaired": (
                "existing _holevo_from_source_moments with "
                "Z_L=max(Z_minus,-Z_phys), Z_U=min(Z_plus,Z_phys), "
                "and deterministic full-Z maximization"
            ),
            "K": "beta_rec*I_AB-chi_BE",
            "search_source_moments": "TRAINING_SURROGATE_ONLY C,w",
            "security_equation_changed": False,
        },
        "inputs": {
            "figure_data": str(INPUT.relative_to(ROOT)),
            "figure_data_sha256": _sha256(INPUT),
            "exact_anchor_data": str(EXACT_INPUT.relative_to(ROOT)),
            "exact_anchor_data_sha256": _sha256(EXACT_INPUT),
            "analysis_runner": "scripts/run_analysis_figures.py",
            "analysis_runner_sha256": _sha256(ROOT / "scripts" / "run_analysis_figures.py"),
            "holevo_source": "src/cvqkd/holevo.py",
            "holevo_source_sha256": _sha256(ROOT / "src" / "cvqkd" / "holevo.py"),
            "final_model_spec_sha256": _sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
        "configuration": {
            "search_z_grid_size": SEARCH_Z_GRID_SIZE,
            "search_z_refinement_steps": SEARCH_Z_REFINEMENT_STEPS,
            "production_z_grid_size": PRODUCTION_Z_GRID_SIZE,
            "production_z_refinement_steps": PRODUCTION_Z_REFINEMENT_STEPS,
            "beta_rec": runner.BETA,
            "phase_disabled": True,
            "c_phi": runner.PHASE_COEFFICIENT,
            "epsilon_total_definition": runner.EPSILON_TOTAL_DEFINITION,
            "same_grid_as_previous_analysis": True,
            "same_channel_weights": True,
        },
        "provenance": {
            "repository_commit": _git("rev-parse", "HEAD"),
            "repository_branch": _git("branch", "--show-current"),
            "repository_dirty": bool(_git("status", "--porcelain")),
            "producer": str(Path(__file__).relative_to(ROOT)),
            "producer_sha256": _sha256(Path(__file__)),
        },
        "lifecycle": {
            "publication_scale_training": False,
            "final_test_accessed": False,
            "adaptive_training_authorized": False,
            "new_security_claim": False,
        },
    }


def _run_audit(figure_data: dict[str, Any], exact_data: dict[str, Any]) -> dict[str, Any]:
    print("old proxy reproduction: start", flush=True)
    semantic = _semantic_audit(figure_data, exact_data)
    print(
        "old proxy below lower: "
        f"{semantic['all_old_proxy_below_lower_count']}/96 mode-state rows",
        flush=True,
    )
    print("case-A reproduction: start", flush=True)
    case_a = _case_a_reproduction()
    print("existing full-Z anchor comparison: start", flush=True)
    anchors = _anchor_comparison(figure_data)
    print("gradient smoke: start", flush=True)
    gradient = _gradient_smoke(figure_data)
    equivalence = _objective_equivalence(semantic, case_a, anchors, gradient)
    result: dict[str, Any] = {
        "semantic_interval_audit": semantic,
        "case_A_reproduction": case_a,
        "existing_anchor_comparison": anchors,
        "gradient_smoke": gradient,
        "objective_equivalence": equivalence,
        "frozen_candidate_ranking": _frozen_candidate_ranking(figure_data, semantic),
    }
    if not equivalence["all_pass"]:
        result["status"] = "FULL_Z_SEARCH_OBJECTIVE_REPAIR_FAILED"
        return result
    print("repaired bounded optimization: start", flush=True)
    result["optimization"] = _bounded_optimization(figure_data)
    result["status"] = "BOUNDED_OBJECTIVE_REPAIR_READY_FOR_EXACT_CHECK"
    return result


def _final_classification(exact: dict[str, Any]) -> tuple[str, str]:
    weighted = exact["weighted_equal_three_state_raw_K"]
    if not {"mb", "ps_va", "full"}.issubset(weighted):
        return "FULL_Z_SEARCH_OBJECTIVE_REPAIRED", "CURRENT_NOVELTY_NOT_SUPPORTED"
    mb = weighted["mb"]
    ps_va = weighted["ps_va"]
    full = weighted["full"]
    best_gain = max(ps_va - mb, full - mb)
    if best_gain >= EXACT_GAIN_THRESHOLD:
        return "FULL_Z_SEARCH_OBJECTIVE_REPAIRED", "NOVELTY_REQUIRES_BROADER_VALIDATION"
    return "FULL_Z_SEARCH_OBJECTIVE_REPAIRED_BUT_NO_GAIN", "CURRENT_NOVELTY_NOT_SUPPORTED"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("audit", "exact", "exact-full", "all"),
        default="audit",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    figure_data, exact_data = _load_inputs()
    if args.phase in {"audit", "all"}:
        artifact = _base_artifact(figure_data, exact_data)
        audit = _run_audit(figure_data, exact_data)
        artifact.update(audit)
        artifact["runtime_seconds_before_exact"] = time.perf_counter() - started
        _write_json(artifact)
        print(f"repaired audit written: {OUTPUT}", flush=True)
        if artifact["status"] == "FULL_Z_SEARCH_OBJECTIVE_REPAIR_FAILED":
            return 2
    else:
        if not OUTPUT.exists():
            raise RepairBlocked("audit artifact is missing; run --phase audit first")
        artifact = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if artifact.get("status") == "FULL_Z_SEARCH_OBJECTIVE_REPAIR_FAILED":
            raise RepairBlocked("objective equivalence failed; exact phase is closed")
    if args.phase in {"exact", "exact-full", "all"}:
        print("bounded exact AP/full-Z three-state check: start", flush=True)
        method_names = ("full",) if args.phase == "exact-full" else ("ps_va", "full")
        exact = _exact_three_state(
            figure_data,
            exact_data,
            artifact["optimization"],
            method_names=method_names,
        )
        classification, novelty = _final_classification(exact)
        artifact["exact_three_state_check"] = exact
        artifact["classification"] = classification
        artifact["novelty_status"] = novelty
        artifact["status"] = classification
        artifact["runtime_seconds"] = time.perf_counter() - started
        _write_json(artifact)
        print(f"repaired objective result: {classification}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepairBlocked as error:
        print(f"REPAIRED_OBJECTIVE_BLOCKED: {error}", file=sys.stderr, flush=True)
        raise SystemExit(2)
