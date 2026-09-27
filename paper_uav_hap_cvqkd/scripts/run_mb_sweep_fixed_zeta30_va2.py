"""Diagnostic MB sweep at fixed zeta=30 deg, V_A=2, and AO=0.95."""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
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
from src.cvqkd.gram_moments import c4_gram_source_moments
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import reference_ensemble
from src.modulation.qam256 import square_qam256
from src.utils.random import torch_generator


VA = 2.0
ZETA_DEG = 30.0
ETA_AO = 0.95
CN2_PHASE = 1.0e-16  # Existing AO=0.95 diagnostic fixture, not production phase approval.
NU_VALUES = tuple(round(0.05 + 0.01 * index, 2) for index in range(16))
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
CSV_FIELDS = (
    "nu_mb", "V_A", "zenith_deg", "alpha_scale", "entropy_bits", "I_AB",
    "I_AB_stderr", "chi_BE", "SKR", "T_eff", "epsilon_eff", "Z_star",
    "w", "fock_dim", "pmf_normalization", "VA_actual", "source_rank",
    "status", "error",
)


def _tensor_sha256(value: torch.Tensor) -> str:
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def _raw_mb_ensemble(config: dict, nu_mb: float):
    # canonical_square_qam256 uses |x|^2/42.5; convert the requested raw-grid
    # parameter to the existing reference_ensemble convention exactly.
    code_nu = float(nu_mb) * 42.5
    ensemble = reference_ensemble(
        "mb",
        batch_size=1,
        modulation_variance=VA,
        nu_mb=code_nu,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    raw_points = square_qam256(alpha0=math.sqrt(30.0))
    raw_energy = raw_points.abs().square().to(dtype=torch.float64)
    pmf = torch.exp(-float(nu_mb) * raw_energy)
    pmf = pmf / pmf.sum()
    if not bool(torch.allclose(ensemble.probabilities[0], pmf, atol=1e-14, rtol=1e-14)):
        raise AssertionError("Reference MB PMF does not match the requested raw-grid formula.")
    e_nu = float(torch.sum(pmf * raw_energy))
    alpha_scale = math.sqrt(VA / (2.0 * e_nu))
    expected_amplitudes = alpha_scale * raw_points
    if not bool(torch.allclose(ensemble.amplitudes[0], expected_amplitudes, atol=2e-12, rtol=2e-12)):
        raise AssertionError("Physical amplitudes do not match per-nu raw-grid scaling.")
    pmf_sum = float(ensemble.probabilities.sum())
    va_actual = float(ensemble.computed_va()[0])
    if abs(pmf_sum - 1.0) > 1e-12 or abs(va_actual - VA) > 1e-10:
        raise AssertionError(f"MB normalization/VA failed at nu={nu_mb}: {pmf_sum}, {va_actual}")
    entropy_bits = float(-(pmf * torch.log2(pmf)).sum())
    return ensemble, {
        "alpha_scale": alpha_scale,
        "entropy_bits": entropy_bits,
        "pmf_normalization": pmf_sum,
        "VA_actual": va_actual,
        "pmf_sha256": _tensor_sha256(ensemble.probabilities),
        "amplitude_sha256": _tensor_sha256(ensemble.amplitudes),
    }


def _source_moments(ensemble, nu_mb: float, cache_dir: Path, numerical: dict[str, float]):
    cache_path = cache_dir / f"source_nu_{nu_mb:.2f}.json"
    hashes = {
        "pmf_sha256": _tensor_sha256(ensemble.probabilities),
        "amplitude_sha256": _tensor_sha256(ensemble.amplitudes),
    }
    if cache_path.is_file():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if payload.get("input_hashes") == hashes and payload.get("rank") == 256:
            return payload
    moments = c4_gram_source_moments(
        ensemble,
        density_eigenvalue_tolerance=numerical["density_eigenvalue_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
    )
    diagnostic = moments.diagnostics[0]
    rank = int(diagnostic.get("numerical_retained_rank", 256))
    if rank != 256:
        raise FloatingPointError(f"Source rank is {rank}, not full support.")
    payload = {
        "nu_mb": nu_mb,
        "rank": rank,
        "C": float(moments.coherent_correlation[0]),
        "w": float(moments.w[0]),
        "route": diagnostic.get("route"),
        "input_hashes": hashes,
        "minimum_eigenvalue": diagnostic.get("minimum_eigenvalue"),
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _evaluate(ensemble, source, t_eff: float, epsilon_eff: float, numerical: dict[str, float], config: dict):
    t = torch.tensor([t_eff], dtype=torch.float64)
    epsilon = torch.tensor([epsilon_eff], dtype=torch.float64)
    c = torch.tensor([source["C"]], dtype=torch.float64)
    w = torch.tensor([source["w"]], dtype=torch.float64)
    mi_values = []
    for seed in MI_SEEDS:
        noise = standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=t.device,
        )
        mi_values.append(float(discrete_mutual_information(
            ensemble, t, epsilon,
            noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
            standard_noise_samples=noise,
        )[0]))
    mi = float(np.mean(mi_values))
    mi_stderr = float(np.std(mi_values, ddof=1) / math.sqrt(len(mi_values)))
    holevo = _holevo_from_source_moments(
        ensemble, t, epsilon,
        coherent_correlation=c, w_raw=w, tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False,
        diagnostics={"backend": "mb_sweep_fixed_zeta30_va2", "source_route": source["route"]},
    )
    chi = float(holevo.chi_be[0])
    key_rate = fading_secret_key_rate(
        torch.tensor([mi], dtype=torch.float64),
        torch.tensor([chi], dtype=torch.float64),
        float(config["cvqkd"]["beta_reconciliation"]),
    )
    minimum_lambda = min(
        float(holevo.covariance.lambda1[0]),
        float(holevo.covariance.lambda2[0]),
        float(holevo.covariance.lambda3[0]),
    )
    if minimum_lambda < 1.0 - 1.0e-10:
        raise FloatingPointError(f"Nonphysical covariance: lambda_min={minimum_lambda}")
    return {
        "I_AB": mi,
        "I_AB_stderr": mi_stderr,
        "chi_BE": chi,
        "SKR": float(key_rate.fading_average_raw),
        "T_eff": t_eff,
        "epsilon_eff": epsilon_eff,
        "Z_star": float(holevo.z[0]),
        "w": float(source["w"]),
        "fock_dim": "c4_gram",
        "source_rank": int(source["rank"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--tau-zen", type=float, default=0.92)
    parser.add_argument("--eta-ao", type=float, default=ETA_AO)
    parser.add_argument("--cn2-phase", type=float, default=CN2_PHASE)
    parser.add_argument("--source-workers", type=int, default=4)
    parser.add_argument("--output-csv", type=Path, default=ROOT / "results" / "mb_sweep_fixed_zeta30_VA2.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "mb_sweep_fixed_zeta30_VA2_sources")
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    if args.source_workers < 1:
        raise ValueError("source-workers must be positive.")
    if not math.isclose(args.eta_ao, ETA_AO, rel_tol=0.0, abs_tol=0.0):
        raise ValueError("This runner is fixed to the existing eta_AO=0.95 diagnostic scenario.")
    physical = derive_physical_inputs(float(args.tau_zen))
    analysis = analyze_product(physical["v_sc"], physical)
    moments = analysis["moments"]
    t_eff = float(moments["mean_sqrt_eta"]) ** 2
    tau_raw = phase_distortion_variance(args.cn2_phase, physical["wavelength_m"], physical["link_length_m"])
    c_phi = phase_noise_coefficient((1.0 - args.eta_ao) * tau_raw)
    epsilon_base = float(physical["epsilon_ch_snu"])
    epsilon_eff = epsilon_base + c_phi * VA
    numerical = holevo_numerical_kwargs(config)
    prepared = {}
    def prepare(nu):
        ensemble, checks = _raw_mb_ensemble(config, nu)
        source = _source_moments(ensemble, nu, args.output_dir, numerical)
        return ensemble, checks, source

    with ThreadPoolExecutor(max_workers=args.source_workers) as pool:
        futures = {pool.submit(prepare, nu): nu for nu in NU_VALUES}
        for future in as_completed(futures):
            nu = futures[future]
            try:
                prepared[nu] = future.result()
                print(f"source ready nu_MB={nu:.2f}", flush=True)
            except Exception as error:
                prepared[nu] = error
                print(f"source failed nu_MB={nu:.2f}: {type(error).__name__}: {error}", flush=True)

    rows = []
    for nu_mb in NU_VALUES:
        row = {"nu_mb": nu_mb, "V_A": VA, "zenith_deg": ZETA_DEG, "status": "FAILED", "error": None}
        try:
            if isinstance(prepared[nu_mb], Exception):
                raise prepared[nu_mb]
            ensemble, checks, source = prepared[nu_mb]
            row.update(checks)
            row.update(_evaluate(ensemble, source, t_eff, epsilon_eff, numerical, config))
            row["status"] = "PASS"
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"nu_MB={nu_mb:.2f} status={row['status']} SKR={row.get('SKR')} error={row.get('error')}", flush=True)

    passed = [row for row in rows if row["status"] == "PASS"]
    if len(passed) != len(NU_VALUES):
        raise RuntimeError(f"Sweep incomplete: {len(passed)}/{len(NU_VALUES)} points passed.")
    if not all(passed[i]["entropy_bits"] >= passed[i + 1]["entropy_bits"] for i in range(len(passed) - 1)):
        raise AssertionError("MB entropy did not decrease with raw nu_MB.")
    best = max(passed, key=lambda row: float(row["SKR"]))
    figure_dir = ROOT / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = figure_dir / "skr_vs_mb_fixed_zeta30_VA2.pdf"
    png_path = figure_dir / "skr_vs_mb_fixed_zeta30_VA2.png"
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot([r["nu_mb"] for r in passed], [r["SKR"] for r in passed], marker="o", linewidth=1.5)
    ax.scatter([best["nu_mb"]], [best["SKR"]], color="tab:red", zorder=3, label=f"max nu={best['nu_mb']:.2f}")
    ax.set_xlabel("Maxwell–Boltzmann shaping parameter, nu_MB")
    ax.set_ylabel("Secret-key rate, K (bits/symbol)")
    ax.set_title("SKR versus Maxwell–Boltzmann Shaping Parameter\nzeta = 30 deg, V_A = 2 SNU")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print(json.dumps({"csv": str(args.output_csv.resolve()), "pdf": str(pdf_path.resolve()), "png": str(png_path.resolve()), "best_nu_mb": best["nu_mb"], "maximum_skr": best["SKR"], "t_eff": t_eff, "epsilon_eff": epsilon_eff}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
