"""Reconcile historical MC MB MI with deterministic MI on identical inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_exact_mb_test2 import (
    CRN_SEEDS,
    MI_SAMPLES_PER_SYMBOL,
    VA,
    build_mb_ensemble,
    channel_fixture,
    ensemble_hash,
)
from scripts.run_exact_mb_test2a import (
    differentiable_mb_ensemble,
    deterministic_value,
    deterministic_value_and_gradient,
)
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.utils.random import torch_generator


OUTPUT = ROOT / "results" / "exact_mb_reconciliation"
POINTS = (0.10, 0.13, 0.14, 0.15, 0.16, 0.17, 0.20)
WIDE_POINTS = (0.00, 0.02, 0.05, 0.08, 0.10, 0.13, 0.15, 0.16, 0.17, 0.20, 0.25)
HIGH_MI_SAMPLES = 65536


def byte_hash(value: torch.Tensor) -> str:
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def load_old_rows() -> dict[float, dict]:
    path = ROOT / "results" / "exact_mb_test2" / "coarse_landscape.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        return {float(row["nu_raw"]): row for row in csv.DictReader(stream)}


def mc_rows(ensemble, t, epsilon, samples: int) -> tuple[list[float], float, float]:
    values = []
    for seed in CRN_SEEDS:
        noise = standard_complex_noise(
            (1, 256, samples),
            generator=torch_generator(seed),
            device=t.device,
        )
        values.append(float(discrete_mutual_information(
            ensemble,
            t,
            epsilon,
            noise_samples_per_symbol=samples,
            standard_noise_samples=noise,
            implementation="product",
            noise_sample_chunk_size=4096 if samples > 4096 else None,
        )[0]))
    mean = float(np.mean(values))
    stderr = float(np.std(values, ddof=1) / math.sqrt(len(values)))
    return values, mean, stderr


def main() -> int:
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    t = torch.tensor([channel["T_eff"]], dtype=torch.float64)
    epsilon_total = channel["epsilon_base"] + channel["c_phi"] * VA
    epsilon = torch.tensor([epsilon_total], dtype=torch.float64)
    old_rows = load_old_rows()
    reconciliation = []
    low_snr = []
    wide_gradient = []
    for nu_raw in POINTS:
        ensemble = build_mb_ensemble(config, nu_raw, VA)
        gh = deterministic_value(nu_raw, channel, 8, "product")
        old_mc_values, mc_2048, stderr_2048 = mc_rows(ensemble, t, epsilon, MI_SAMPLES_PER_SYMBOL)
        mc_values, mc_65536, stderr_65536 = mc_rows(ensemble, t, epsilon, HIGH_MI_SAMPLES)
        old = old_rows[nu_raw]
        chi = float(old["chi_BE"])
        beta = float(config["cvqkd"]["beta_reconciliation"])
        raw_points = torch.as_tensor(ensemble.raw_constellation)
        probabilities = ensemble.probabilities[0]
        mean_energy = float(torch.sum(probabilities * raw_points.abs().square()))
        scale = math.sqrt(VA / (2.0 * mean_energy))
        alpha_energy = ensemble.amplitudes[0].abs().square()
        row = {
            "nu_raw": nu_raw,
            "nu_repo": 42.5 * nu_raw,
            "ensemble_hash": ensemble_hash(ensemble),
            "PMF_hash": byte_hash(ensemble.probabilities),
            "amplitude_hash": byte_hash(ensemble.amplitudes),
            "sum_p": float(ensemble.probabilities.sum()),
            "VA_actual": float(ensemble.computed_va()[0]),
            "T": float(t[0]),
            "epsilon_total": epsilon_total,
            "sigma_c2": float(1.0 + t[0] * epsilon[0] / 2.0),
            "I_AB_old_coarse": float(old["I_AB"]),
            "I_AB_MC_2048_rerun": mc_2048,
            "MC_2048_stderr": stderr_2048,
            "I_AB_GH": gh,
            "I_AB_MC_65536": mc_65536,
            "MC_65536_stderr": stderr_65536,
            "MC_GH_difference": mc_65536 - gh,
            "MC_GH_over_stderr": (mc_65536 - gh) / stderr_65536,
            "old_coarse_minus_GH": float(old["I_AB"]) - gh,
            "old_coarse_z_reconstructed": (float(old["I_AB"]) - gh) / stderr_2048,
            "old_SKR": float(old["SKR"]),
            "C": float(old["C"]),
            "w": float(old["w"]),
            "chi_BE": chi,
            "new_deterministic_SKR": beta * gh - chi,
            "beta_I_GH": beta * gh,
            "mean_energy_before_normalization": mean_energy,
            "normalization_scale": scale,
            "second_moment_after_normalization": float(alpha_energy.mul(probabilities).sum()),
            "fourth_moment": float((probabilities * alpha_energy.square()).sum()),
            "min_p": float(probabilities.min()),
            "max_p": float(probabilities.max()),
            "entropy_bits": float(-(probabilities * torch.log2(probabilities)).sum()),
            "delta_SKR": beta * gh - chi - float(old["SKR"]),
        }
        row["old_MC_variation_resolved"] = abs(row["old_coarse_z_reconstructed"]) > 3.0
        reconciliation.append(row)
        low_snr.append({key: row[key] for key in (
            "nu_raw", "mean_energy_before_normalization", "normalization_scale",
            "second_moment_after_normalization", "fourth_moment", "min_p", "max_p",
            "entropy_bits", "I_AB_GH",
        )})

    for nu_raw in WIDE_POINTS:
        value, gradient = deterministic_value_and_gradient(nu_raw, channel, 8)
        ensemble = differentiable_mb_ensemble(nu_raw)
        wide_gradient.append({
            "nu_raw": nu_raw,
            "I_AB_GH": value,
            "dI_AB_dnu_raw": gradient,
            "entropy_bits": float(-(ensemble.probabilities[0] * torch.log2(ensemble.probabilities[0])).sum()),
            "max_p": float(ensemble.probabilities.max()),
        })

    max_old_z = max(abs(row["old_coarse_z_reconstructed"]) for row in reconciliation)
    max_mc_z = max(abs(row["MC_GH_over_stderr"]) for row in reconciliation)
    report = {
        "status": "RECONCILIATION_PASS" if max_mc_z <= 3.0 else "RECONCILIATION_REVIEW",
        "channel_fixture": channel,
        "crn_seeds": list(CRN_SEEDS),
        "old_coarse_mi_classification": "STOCHASTIC_COARSE_ONLY" if max_old_z <= 3.0 else "COARSE_TREND_REQUIRES_REVIEW",
        "old_coarse_variation_statistically_resolvable": max_old_z > 3.0,
        "max_old_coarse_z_reconstructed": max_old_z,
        "max_high_sample_mc_gh_z": max_mc_z,
        "full_exact_skr_point_evaluation": "READY_BY_EXISTING_EXACT_COMMON_EVALUATOR",
        "holevo_derivative_required_for_bounded_search": "NO",
        "full_skr_search": {
            "status": "NOT RUN",
            "reason": "Optimized-MB search/baseline selection is not authorized by current lifecycle state.",
        },
        "reconciliation_rows": reconciliation,
        "low_snr_rows": low_snr,
        "wide_gradient_rows": wide_gradient,
        "integrity": {
            "common_ensemble_hashes_identical": "YES_BY_EVID_0087_CONTRACT",
            "C_w_interpolation": "NO",
            "physical_security_equations_changed": "NO",
            "historical_invalid_cache_used": "NO",
            "deterministic_MI_used_in_final_SKR": "YES_FOR_CORRECTED_COARSE_ROWS",
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "run_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "low_snr_diagnostics.json").write_text(json.dumps(low_snr, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "wide_gradient.json").write_text(json.dumps(wide_gradient, indent=2) + "\n", encoding="utf-8")
    with (OUTPUT / "same_point_reconciliation.csv").open("w", newline="", encoding="utf-8") as stream:
        rows = reconciliation
        writer = csv.DictWriter(stream, fieldnames=sorted({key for row in rows for key in row}), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
