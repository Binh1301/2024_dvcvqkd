"""Exact joint MB/V_A feasible-region and bounded landscape diagnostic."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import json
import math
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.run_exact_mb_test2 import (
    ExactMBEvaluator,
    VA,
    build_mb_ensemble,
    channel_fixture,
    ensemble_hash,
    nu_mb_repo,
)
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import deterministic_mutual_information
from src.cvqkd.secret_key_rate import fading_secret_key_rate


OUTPUT = ROOT / "results" / "joint_mb_va"
SHARED_CACHE = ROOT / "results" / "exact_mb_test2" / "exact_source_cache"
V_MIN = 0.1
BOUNDARY_NUS = tuple(round(0.025 * i, 3) for i in range(13)) + (0.35, 0.4, 0.5, 1.0)
LANDSCAPE_NUS = (0.0, 0.1, 0.2, 0.25, 0.3)
LANDSCAPE_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)


def feasible_vmax(config: dict, nu_raw: float) -> dict:
    ensemble = build_mb_ensemble(config, nu_raw, V_MIN)
    relative = ensemble.raw_constellation
    m2 = float(torch.sum(ensemble.probabilities[0] * relative.abs().square()))
    x_max2 = float(relative.abs().square().max())
    configured = float(config["cvqkd"]["v_max_snu"])
    hard = 2.0 * float(config["cvqkd"]["n_peak_photons"]) * m2 / x_max2
    return {
        "nu_raw": nu_raw,
        "nu_repo": nu_mb_repo(nu_raw),
        "m2": m2,
        "x_max2": x_max2,
        "V_A_max_peak": hard,
        "V_A_max_feasible": min(configured, hard),
        "V_A_min": V_MIN,
    }


def deterministic_joint_mi(
    ensemble, channel: dict[str, float], va: float, quadrature_order: int = 8
) -> float:
    t = torch.tensor([channel["T_eff"]], dtype=torch.float64)
    epsilon = torch.tensor(
        [channel["epsilon_base"] + channel["c_phi"] * va], dtype=torch.float64
    )
    return float(deterministic_mutual_information(
        ensemble, t, epsilon, quadrature_order=quadrature_order, implementation="product"
    )[0])


def evaluate(
    config: dict,
    channel: dict[str, float],
    evaluator: ExactMBEvaluator,
    nu: float,
    va: float,
    quadrature_order: int = 8,
) -> dict:
    ensemble = build_mb_ensemble(config, nu, va)
    m2 = float(torch.sum(ensemble.probabilities[0] * ensemble.raw_constellation.abs().square()))
    x_max2 = float(ensemble.raw_constellation.abs().square().max())
    source = evaluator.source_moments(ensemble, nu, va)
    t = torch.tensor([channel["T_eff"]], dtype=torch.float64)
    epsilon_total = channel["epsilon_base"] + channel["c_phi"] * va
    epsilon = torch.tensor([epsilon_total], dtype=torch.float64)
    mi = deterministic_joint_mi(ensemble, channel, va, quadrature_order)
    n = evaluator.numerical
    holevo = _holevo_from_source_moments(
        ensemble, t, epsilon,
        coherent_correlation=torch.tensor([source["C"]], dtype=torch.float64),
        w_raw=torch.tensor([source["w"]], dtype=torch.float64),
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=n["symmetry_tolerance"],
        physicality_tolerance=n["physicality_tolerance"],
        diagnostics={"backend": "joint_mb_va_exact", "ensemble_hash": ensemble_hash(ensemble)},
    )
    beta = float(config["cvqkd"]["beta_reconciliation"])
    beta_i = beta * mi
    chi = float(holevo.chi_be[0])
    return {
        "nu_raw": nu,
        "nu_repo": nu_mb_repo(nu),
        "VA": va,
        "epsilon_total": epsilon_total,
        "peak_photon": float(ensemble.amplitudes.abs().square().max()),
        "P_peak": float(ensemble.amplitudes.abs().square().max()),
        "m2": m2,
        "x_max2": x_max2,
        "physical_scale": math.sqrt(float(va) / (2.0 * m2)),
        "feasible": True,
        "H_X": float(-(ensemble.probabilities[0] * torch.log2(ensemble.probabilities[0])).sum()),
        "N_eff": float(torch.exp(-(ensemble.probabilities[0] * torch.log(ensemble.probabilities[0])).sum())),
        "max_p": float(ensemble.probabilities.max()),
        "I_AB_GH": mi,
        "I_AB": mi,
        "C": float(source["C"]),
        "w": float(source["w"]),
        "Z_star": float(holevo.z[0]),
        "chi_BE": chi,
        "beta_IAB": beta_i,
        "SKR": beta_i - chi,
        "ensemble_hash": ensemble_hash(ensemble),
        "source_cache_key": source["cache_key"],
        "fresh_or_cache": source["cache_origin"],
        "cache_hit": bool(source["cache_hit"]),
        "VA_actual": float(ensemble.computed_va()[0]),
        "fourth_moment": float(torch.sum(ensemble.probabilities[0] * ensemble.amplitudes[0].abs().square().square())),
        "GH_order": quadrature_order,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted({key for row in rows for key in row}), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-workers", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    boundary = []
    for nu in BOUNDARY_NUS:
        try:
            boundary.append(feasible_vmax(config, nu))
        except Exception as error:
            boundary.append({"nu_raw": nu, "status": "INVALID", "error": f"{type(error).__name__}: {error}"})
    write_csv(args.output_dir / "feasible_boundary.csv", boundary)

    points = []
    for nu in LANDSCAPE_NUS:
        bound = next(row for row in boundary if row["nu_raw"] == nu)
        vmax = float(bound["V_A_max_feasible"])
        for fraction in LANDSCAPE_FRACTIONS:
            va = V_MIN + fraction * (vmax - V_MIN)
            points.append((nu, va))
    evaluator = ExactMBEvaluator(
        config, channel, args.output_dir, source_cache_dir=SHARED_CACHE
    )
    valid_points = []
    invalid = []
    for nu, va in points:
        try:
            build_mb_ensemble(config, nu, va)
            valid_points.append((nu, va))
        except Exception as error:
            invalid.append({"nu_raw": nu, "VA": va, "error": f"{type(error).__name__}: {error}"})
    evaluator.prepare_sources(valid_points, args.source_workers)
    rows = []
    for nu, va in valid_points:
        print(f"evaluate nu_raw={nu:.6g} VA={va:.6g}", flush=True)
        rows.append(evaluate(config, channel, evaluator, nu, va))
    write_csv(args.output_dir / "joint_landscape.csv", rows)
    report = {
        "status": "JOINT_EXACT_LANDSCAPE_COMPLETE",
        "authorization_scope": "EXACT_MB_OPTIMIZATION_AND_ASYMPTOTIC_CERTIFICATION",
        "publication_lifecycle": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "channel_fixture": channel,
        "boundary_rows": len(boundary),
        "landscape_rows": len(rows),
        "invalid_points": invalid,
        "best_grid_row": max(rows, key=lambda row: row["SKR"]) if rows else None,
        "optimizer": "NOT RUN; landscape/boundary diagnostics first",
        "interpolation": "NO",
        "security_equations_changed": "NO",
    }
    (args.output_dir / "run_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
