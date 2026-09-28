"""LEGACY_INVALID_COMMON_ENSEMBLE: cached MB C,w diagnostic only.

The supplied moments use raw-grid ``nu``, while this historical runner passed
that value directly to the canonical repository PMF.  Its SKR output therefore
mixes MI and source moments from different ensembles and must not be reused for
common-ensemble or publication comparisons.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import analyze_product, derive_physical_inputs
from src.channel.phase_noise import phase_distortion_variance, phase_noise_coefficient
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import reference_ensemble
from src.modulation.qam256 import square_qam256
from src.utils.random import torch_generator


VA = 2.0
ZETA_DEG = 30.0
ETA_AO = 0.95
CN2_PHASE = 9.4e-18  # User-selected AO=0.95 diagnostic fixture.
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
CW_ROWS = (
    (0.020000, 1.4098394087966897, 9.43278191001156e-3),
    (0.050000, 1.4135635227562485, 1.3718689713290113e-3),
    (0.075000, 1.4141065289183806, 2.2817290836018868e-4),
    (0.087500, 1.4141718359824701, 9.035310968641115e-5),
    (0.090625, 1.4141806789017032, 7.153811083233796e-5),
    (0.093750, 1.4141876699275133, 5.660577791009835e-5),
    (0.100000, 1.4141975446461089, 3.53821884252737e-5),
    (0.125000, 1.4142112629148078, 5.310560072298239e-6),
    (0.150000, 1.4142132377824911, 7.818684597230906e-7),
    (0.200000, 1.4142135560377151, 1.6265500905208522e-8),
)
CSV_FIELDS = (
    "nu_mb", "V_A", "zenith_deg", "alpha_scale", "entropy_bits", "I_AB",
    "I_AB_stderr", "chi_BE", "SKR", "T_eff", "epsilon_eff", "Z_star",
    "w", "fock_dim", "pmf_normalization", "VA_actual", "source_rank",
    "status", "error",
)


def _ensemble(config: dict, nu_mb: float):
    ensemble = reference_ensemble(
        "mb", batch_size=1, modulation_variance=VA, nu_mb=nu_mb,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    raw = square_qam256(alpha0=math.sqrt(30.0))
    energy = float(torch.sum(ensemble.probabilities[0] * raw.abs().square()))
    alpha_scale = math.sqrt(VA / (2.0 * energy))
    pmf_sum = float(ensemble.probabilities.sum())
    va_actual = float(ensemble.computed_va()[0])
    if abs(pmf_sum - 1.0) > 1e-12 or abs(va_actual - VA) > 1e-10:
        raise AssertionError(f"MB normalization/VA failed at nu={nu_mb}: {pmf_sum}, {va_actual}")
    entropy_bits = float(-(ensemble.probabilities[0] * torch.log2(ensemble.probabilities[0])).sum())
    return ensemble, alpha_scale, entropy_bits, pmf_sum, va_actual


def _evaluate(ensemble, c_value, w_value, t_eff, epsilon_eff, numerical, config):
    t = torch.tensor([t_eff], dtype=torch.float64)
    epsilon = torch.tensor([epsilon_eff], dtype=torch.float64)
    mi_values = []
    for seed in MI_SEEDS:
        mi_values.append(float(discrete_mutual_information(
            ensemble, t, epsilon,
            noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
            standard_noise_samples=standard_complex_noise(
                (1, 256, MI_SAMPLES_PER_SYMBOL),
                generator=torch_generator(seed), device=t.device,
            ),
        )[0]))
    mi = float(np.mean(mi_values))
    mi_stderr = float(np.std(mi_values, ddof=1) / math.sqrt(len(mi_values)))
    holevo = _holevo_from_source_moments(
        ensemble, t, epsilon,
        coherent_correlation=torch.tensor([c_value], dtype=torch.float64),
        w_raw=torch.tensor([w_value], dtype=torch.float64),
        tau=None, tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False,
        diagnostics={
            "backend": "supplied_cached_mb_cw",
            "source_table": "mb_nu_threshold_va2_refined",
        },
    )
    chi = float(holevo.chi_be[0])
    rate = fading_secret_key_rate(
        torch.tensor([mi], dtype=torch.float64),
        torch.tensor([chi], dtype=torch.float64),
        float(config["cvqkd"]["beta_reconciliation"]),
    )
    minimum_lambda = min(
        float(holevo.covariance.lambda1[0]),
        float(holevo.covariance.lambda2[0]),
        float(holevo.covariance.lambda3[0]),
    )
    if minimum_lambda < 1.0 - 1e-10:
        raise FloatingPointError(f"Nonphysical covariance: lambda_min={minimum_lambda}")
    return {
        "I_AB": mi, "I_AB_stderr": mi_stderr, "chi_BE": chi,
        "SKR": float(rate.fading_average_raw), "T_eff": t_eff,
        "epsilon_eff": epsilon_eff, "Z_star": float(holevo.z[0]),
        "w": w_value, "fock_dim": "c4_gram", "source_rank": 256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--tau-zen", type=float, default=0.92)
    parser.add_argument("--eta-ao", type=float, default=ETA_AO)
    parser.add_argument("--output-csv", type=Path, default=ROOT / "results" / "mb_sweep_fixed_zeta30_VA2.csv")
    args = parser.parse_args()
    if args.eta_ao != ETA_AO:
        raise ValueError("This cached diagnostic is fixed to eta_AO=0.95.")
    config = load_yaml(args.config.resolve())
    physical = derive_physical_inputs(args.tau_zen)
    moments = analyze_product(physical["v_sc"], physical)["moments"]
    t_eff = float(moments["mean_sqrt_eta"]) ** 2
    tau_raw = phase_distortion_variance(CN2_PHASE, physical["wavelength_m"], physical["link_length_m"])
    c_phi = phase_noise_coefficient((1.0 - ETA_AO) * tau_raw)
    epsilon_eff = float(physical["epsilon_ch_snu"]) + c_phi * VA
    numerical = holevo_numerical_kwargs(config)
    rows = []
    for nu_mb, c_value, w_value in CW_ROWS:
        row = {"nu_mb": nu_mb, "V_A": VA, "zenith_deg": ZETA_DEG, "status": "FAILED", "error": None}
        try:
            ensemble, alpha_scale, entropy_bits, pmf_sum, va_actual = _ensemble(config, nu_mb)
            row.update(alpha_scale=alpha_scale, entropy_bits=entropy_bits,
                       pmf_normalization=pmf_sum, VA_actual=va_actual)
            row.update(_evaluate(ensemble, c_value, w_value, t_eff, epsilon_eff, numerical, config))
            row["status"] = "PASS"
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"nu_MB={nu_mb:.6f} status={row['status']} SKR={row.get('SKR')} error={row.get('error')}", flush=True)
    passed = [row for row in rows if row["status"] == "PASS"]
    if len(passed) != len(CW_ROWS):
        raise RuntimeError(f"Cached C,w sweep incomplete: {len(passed)}/{len(CW_ROWS)} points passed.")
    best = max(passed, key=lambda row: row["SKR"])
    figure_dir = ROOT / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = figure_dir / "skr_vs_mb_fixed_zeta30_VA2.pdf"
    png_path = figure_dir / "skr_vs_mb_fixed_zeta30_VA2.png"
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot([r["nu_mb"] for r in passed], [r["SKR"] for r in passed], marker="o", linewidth=1.5)
    ax.scatter([best["nu_mb"]], [best["SKR"]], color="tab:red", zorder=3, label=f"max nu={best['nu_mb']:.6f}")
    ax.set_xlabel("Maxwell–Boltzmann shaping parameter, nu_MB")
    ax.set_ylabel("Secret-key rate, K (bits/symbol)")
    ax.set_title("SKR versus Maxwell–Boltzmann Shaping Parameter\nzeta = 30 deg, V_A = 2 SNU")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print(json.dumps({
        "csv": str(args.output_csv.resolve()), "pdf": str(pdf_path.resolve()),
        "png": str(png_path.resolve()), "best_nu_mb": best["nu_mb"],
        "maximum_skr": best["SKR"], "T_eff": t_eff, "epsilon_eff": epsilon_eff,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
