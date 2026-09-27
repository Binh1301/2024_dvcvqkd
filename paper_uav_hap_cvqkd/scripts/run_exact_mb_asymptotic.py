"""Authorized exact-MB boundary/asymptotic landscape, no Adam."""

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
from scripts.run_exact_mb_test2a import deterministic_value
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.secret_key_rate import fading_secret_key_rate


OUTPUT = ROOT / "results" / "exact_mb_asymptotic"
AUTHORIZED_SCOPE = "EXACT_MB_OPTIMIZATION_AND_ASYMPTOTIC_CERTIFICATION"
POINTS = (0.20, 0.22, 0.25, 0.30, 0.35, 0.40, 0.50)


def _shell_masses(ensemble) -> tuple[float, float, float]:
    probabilities = ensemble.probabilities[0]
    energy = ensemble.raw_constellation.abs().square().real
    levels = torch.sort(torch.unique(energy)).values
    lowest = levels[0]
    second = levels[1]
    low_mass = float(probabilities[torch.isclose(energy, lowest, atol=1e-14, rtol=0.0)].sum())
    second_mass = float(probabilities[torch.isclose(energy, second, atol=1e-14, rtol=0.0)].sum())
    return low_mass, second_mass, 1.0 - low_mass - second_mass


def evaluate_point(config, channel, evaluator: ExactMBEvaluator, nu_raw: float) -> dict:
    ensemble = build_mb_ensemble(config, nu_raw, VA)
    source = evaluator.source_moments(ensemble, nu_raw, VA)
    gh = deterministic_value(nu_raw, channel, 8, "product")
    t = torch.tensor([channel["T_eff"]], dtype=torch.float64)
    epsilon_total = channel["epsilon_base"] + channel["c_phi"] * VA
    epsilon = torch.tensor([epsilon_total], dtype=torch.float64)
    numerical = evaluator.numerical
    holevo = _holevo_from_source_moments(
        ensemble,
        t,
        epsilon,
        coherent_correlation=torch.tensor([source["C"]], dtype=torch.float64),
        w_raw=torch.tensor([source["w"]], dtype=torch.float64),
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        diagnostics={
            "backend": "authorized_exact_mb_asymptotic",
            "ensemble_hash": ensemble_hash(ensemble),
            "source_cache_key": source["cache_key"],
        },
    )
    beta = float(config["cvqkd"]["beta_reconciliation"])
    chi = float(holevo.chi_be[0])
    beta_i = beta * gh
    skr = beta_i - chi
    low_mass, second_mass, remaining = _shell_masses(ensemble)
    raw_constellation = ensemble.raw_constellation
    mean_energy = float(torch.sum(ensemble.probabilities[0] * raw_constellation.abs().square()))
    scale = math.sqrt(VA / (2.0 * mean_energy))
    alpha_energy = ensemble.amplitudes[0].abs().square()
    return {
        "nu_raw": nu_raw,
        "nu_repo": nu_mb_repo(nu_raw),
        "ensemble_hash": ensemble_hash(ensemble),
        "fresh_or_cache": source["cache_origin"],
        "cache_hit": source["cache_hit"],
        "I_AB_GH": gh,
        "C": float(source["C"]),
        "sqrt2_minus_C": math.sqrt(2.0) - float(source["C"]),
        "w": float(source["w"]),
        "Z_star": float(holevo.z[0]),
        "chi_BE": chi,
        "beta_I_AB": beta_i,
        "SKR": skr,
        "H_X": float(-(ensemble.probabilities[0] * torch.log2(ensemble.probabilities[0])).sum()),
        "N_eff": float(torch.exp(-(ensemble.probabilities[0] * torch.log(ensemble.probabilities[0])).sum())),
        "min_p": float(ensemble.probabilities.min()),
        "max_p": float(ensemble.probabilities.max()),
        "lowest_shell_probability": low_mass,
        "second_shell_probability": second_mass,
        "remaining_probability": remaining,
        "mean_raw_constellation_energy": mean_energy,
        "normalization_scale": scale,
        "VA_actual": float(ensemble.computed_va()[0]),
        "fourth_moment": float(torch.sum(ensemble.probabilities[0] * alpha_energy.square())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-workers", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.source_workers < 1:
        parser.error("source-workers must be positive")
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    evaluator = ExactMBEvaluator(config, channel, args.output_dir)
    authorization = {
        "scope": AUTHORIZED_SCOPE,
        "publication_scale_authorized": False,
        "physical_security_model_changes_authorized": False,
        "adam_authorized": False,
        "interpolation_authorized": False,
        "source": "author_attachment_5fd02748-2aa7-4dc0-a470-a23cd9b15ca2",
        "global_lifecycle_preserved": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "author_authorization.json").write_text(
        json.dumps(authorization, indent=2) + "\n", encoding="utf-8"
    )
    points = list(POINTS)
    valid_points = []
    invalid_points = []
    for nu in points:
        try:
            build_mb_ensemble(config, nu, VA)
            valid_points.append(nu)
        except Exception as error:
            invalid_points.append({
                "nu_raw": nu,
                "status": "FAILED_PHYSICAL_DOMAIN",
                "error": f"{type(error).__name__}: {error}",
            })
    evaluator.prepare_sources([(nu, VA) for nu in valid_points], args.source_workers)
    rows = []
    for nu in valid_points:
        print(f"evaluate nu_raw={nu:.12g}", flush=True)
        rows.append(evaluate_point(config, channel, evaluator, nu))
        print(f"ready nu_raw={nu:.12g} SKR={rows[-1]['SKR']:.12g}", flush=True)
    rows.sort(key=lambda row: row["nu_raw"])
    report = {
        "status": "AUTHORIZED_EXACT_MB_LANDSCAPE_COMPLETE",
        "authorization": authorization,
        "channel_fixture": channel,
        "points": points,
        "rows": rows,
        "invalid_points": invalid_points,
        "skR_increasing_to_old_boundary": rows[0]["SKR"] < rows[-1]["SKR"],
        "turnover_found": any(rows[i + 1]["SKR"] < rows[i]["SKR"] for i in range(len(rows) - 1)),
        "finite_interior_bracket": False,
        "full_bounded_search": "NOT RUN; no valid interior bracket before the hard peak-photon boundary",
        "production_positive_pmf_invariant_weakened": False,
    }
    (args.output_dir / "extended_landscape.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "extended_landscape.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted({key for row in rows for key in row}), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
