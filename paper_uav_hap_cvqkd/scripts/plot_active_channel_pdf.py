"""Plot the manuscript active HAP--UAV channel PDF and its AoA mixture.

This is a channel-only diagnostic.  It evaluates the raw manuscript law
``X = eta_atm * H_sc * H_p`` and the mixed raw law
``T_raw = 0`` with probability ``p_out`` or ``X`` with probability ``p_in``.
It does not clip, condition, renormalize over ``[0, 1]``, train, or evaluate
CV-QKD security.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterSciNotation
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.plot_eq62_raw_transmittance_pdf import (
    CONFIG_DEFAULT,
    _derive,
    _integrate_log_density,
    make_active_pdf,
)


OUTPUT_DEFAULT = ROOT / "diagnostics"
DEFAULT_SAMPLE_COUNT = 1_000_000
DEFAULT_SEED = 202612


def _finite(name: str, values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if np.any(~np.isfinite(values)):
        raise FloatingPointError(f"{name} contains NaN or infinity.")
    return values


def _pdf_values(log_pdf_from_log_t, t: np.ndarray) -> np.ndarray:
    log_values = _finite("log f_X", log_pdf_from_log_t(np.log(t)))
    values = _finite("f_X", np.exp(log_values))
    representable_floor = math.log(np.finfo(np.float64).tiny)
    if np.any((values == 0.0) & (log_values > representable_floor)):
        raise FloatingPointError("f_X underflowed above the representable floor.")
    if np.any(values < 0.0):
        raise FloatingPointError("f_X contains a negative density.")
    return values


def _sample_active(params: dict[str, float], sample_count: int, seed: int) -> np.ndarray:
    if sample_count < 2:
        raise ValueError("sample_count must be at least two.")
    rng = np.random.default_rng(seed)
    v_sc = params["v_sc"]
    h_sc = np.exp(rng.normal(-0.5 * v_sc, math.sqrt(v_sc), sample_count))
    x_jitter = rng.normal(params["rho_x"], params["sigma_jt"], sample_count)
    y_jitter = rng.normal(params["rho_y"], params["sigma_jt"], sample_count)
    h_p = params["A0"] * np.exp(
        -2.0 * (x_jitter**2 + y_jitter**2) / params["omega_L_eq"] ** 2
    )
    samples = params["eta_atm"] * h_sc * h_p
    samples = _finite("Monte Carlo active X", samples)
    if np.any(samples <= 0.0):
        raise FloatingPointError("Monte Carlo active X must be strictly positive.")
    return samples


def _mode_grid(params: dict[str, float], samples: np.ndarray) -> np.ndarray:
    scale = params["A0_eta_atm"]
    q001, q999 = np.quantile(samples, (1.0e-3, 0.999))
    lower = max(np.finfo(np.float64).tiny, min(q001 * 0.1, scale * 1.0e-6))
    upper = max(q999 * 2.0, scale * 2.0)
    return np.geomspace(lower, upper, 30_000)


def _print_table(params: dict[str, float]) -> None:
    rows = (
        ("L", params["L"], "m"),
        ("eta_atm", params["eta_atm"], "dimensionless"),
        ("omega_0", params["omega_0"], "m"),
        ("D_r", params["D_r"], "m"),
        ("sigma_R0^2", params["sigma_R0_squared"], "dimensionless"),
        ("AA", params["AA"], "dimensionless"),
        ("sigma_R,D^2", params["sigma_R_squared"], "dimensionless"),
        ("sigma_X^2", params["sigma_X_squared"], "dimensionless"),
        ("omega_L", params["omega_L"], "m"),
        ("G_d", params["G_d"], "dimensionless"),
        ("omega_L,e", params["omega_L_e"], "m"),
        ("A0", params["A0"], "dimensionless"),
        ("omega_L,eq", params["omega_L_eq"], "m"),
        ("L * theta_jt", params["L_sigma_hap"], "m"),
        ("sigma_jt", params["sigma_jt"], "m"),
        ("chi", params["chi"], "dimensionless"),
        ("C1", params["C1"], "dimensionless"),
        ("C2", params["C2"], "dimensionless"),
        ("mu", params["mu"], "dimensionless"),
        ("A0 eta_atm", params["A0_eta_atm"], "dimensionless"),
        ("sigma_o", params["sigma_o"], "rad"),
        ("theta_FOV", params["theta_FOV"], "rad"),
        ("p_out", params["p_out"], "dimensionless"),
        ("p_in", params["p_in"], "dimensionless"),
    )
    print("\nDerived active-channel parameters")
    for name, value, unit in rows:
        print(f"{name:18s} = {value:.16g}  [{unit}]")


def _sanity_checks(params: dict[str, float]) -> None:
    checks = {
        "L > 0": params["L"] > 0.0,
        "0 < eta_atm <= 1": 0.0 < params["eta_atm"] <= 1.0,
        "omega_0 > 0": params["omega_0"] > 0.0,
        "D_r > 0": params["D_r"] > 0.0,
        "sigma_R0^2 >= 0": params["sigma_R0_squared"] >= 0.0,
        "0 < AA <= 1": 0.0 < params["AA"] <= 1.0,
        "sigma_X^2 >= 0": params["sigma_X_squared"] >= 0.0,
        "0 < A0 <= 1": 0.0 < params["A0"] <= 1.0,
        "omega_L_eq > 0": params["omega_L_eq"] > 0.0,
        "sigma_jt > 0": params["sigma_jt"] > 0.0,
        "chi > 0": params["chi"] > 0.0,
        "C2 > 0": params["C2"] > 0.0,
        "0 <= p_out <= 1": 0.0 <= params["p_out"] <= 1.0,
        "0 <= p_in <= 1": 0.0 <= params["p_in"] <= 1.0,
        "p_in + p_out = 1": abs(params["p_in"] + params["p_out"] - 1.0) < 1.0e-12,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError(f"Sanity checks failed: {failed}")


def _save_active_figure(
    output_dir: Path,
    t_grid: np.ndarray,
    active_values: np.ndarray,
    scale: float,
    active_mode: float,
    histogram_samples: np.ndarray,
) -> tuple[Path, Path]:
    edges = np.linspace(t_grid[0], t_grid[-1], 140)
    histogram, _ = np.histogram(histogram_samples, bins=edges, density=True)
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.stairs(histogram, edges, color="0.55", alpha=0.7, label="Monte Carlo density")
    ax.plot(t_grid, active_values, color="tab:blue", linewidth=2.0, label=r"Analytical $f_X(t)$")
    ax.axvline(scale, color="tab:green", linestyle="--", linewidth=1.3,
               label=r"$A_0\eta_{\rm atm}$ reference scale")
    ax.scatter([active_mode], [np.interp(active_mode, t_grid, active_values)],
               color="tab:red", zorder=4, label=f"Analytical mode = {active_mode:.4g}")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(LogFormatterSciNotation())
    ax.set_xlabel(r"Active transmittance $X$")
    ax.set_ylabel(r"Probability density $f_X(t)$")
    ax.set_title("HAP--UAV active optical-channel PDF")
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=8)
    fig.tight_layout()
    png_path = output_dir / "active_X_pdf.png"
    pdf_path = output_dir / "active_X_pdf.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path


def _save_mc_figure(
    output_dir: Path,
    t_grid: np.ndarray,
    active_values: np.ndarray,
    scale: float,
    active_mode: float,
    samples: np.ndarray,
) -> tuple[Path, Path, float]:
    edges = np.linspace(t_grid[0], t_grid[-1], 220)
    histogram, _ = np.histogram(samples, bins=edges, density=True)
    peak_index = int(np.argmax(histogram))
    mc_mode = math.sqrt(edges[peak_index] * edges[peak_index + 1])
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.stairs(histogram, edges, color="0.45", alpha=0.8, label="Monte Carlo density")
    ax.plot(t_grid, active_values, color="tab:blue", linewidth=2.0, label=r"Analytical $f_X(t)$")
    ax.axvline(scale, color="tab:green", linestyle="--", linewidth=1.3,
               label=r"$A_0\eta_{\rm atm}$ reference scale")
    ax.axvline(active_mode, color="tab:red", linestyle=":", linewidth=1.3,
               label=f"Analytical mode = {active_mode:.4g}")
    ax.axvline(mc_mode, color="tab:orange", linestyle="-.", linewidth=1.3,
               label=f"MC histogram mode = {mc_mode:.4g}")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(LogFormatterSciNotation())
    ax.set_xlabel(r"Active transmittance $X$")
    ax.set_ylabel(r"Probability density")
    ax.set_title("HAP--UAV active PDF: analytical/Monte Carlo comparison")
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=8)
    fig.tight_layout()
    png_path = output_dir / "active_X_pdf_mc_compare.png"
    pdf_path = output_dir / "active_X_pdf_mc_compare.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path, mc_mode


def _save_raw_figure(
    output_dir: Path,
    t_grid: np.ndarray,
    active_values: np.ndarray,
    params: dict[str, float],
    active_mode: float,
) -> tuple[Path, Path]:
    raw_values = params["p_in"] * active_values
    fig, ax = plt.subplots(figsize=(7.8, 4.9))
    ax.plot(t_grid, active_values, color="tab:blue", linewidth=2.0, label=r"$f_X(t)$")
    ax.plot(t_grid, raw_values, color="tab:orange", linestyle="--", linewidth=2.0,
            label=r"$p_{in}f_X(t)$")
    ax.axvline(params["A0_eta_atm"], color="tab:green", linestyle=":", linewidth=1.3,
               label=r"$A_0\eta_{\rm atm}$ reference scale")
    ax.set_xlim(0.0, float(t_grid[-1]))
    ax.set_xlabel(r"Raw transmittance $T_{raw}$")
    ax.set_ylabel("Continuous probability density")
    ax.set_title("HAP--UAV raw channel PDF with AoA outage")
    ax.grid(alpha=0.25)

    ax_mass = ax.twinx()
    ax_mass.vlines(0.0, 0.0, params["p_out"], color="tab:red", linewidth=3.0)
    ax_mass.scatter([0.0], [params["p_out"]], color="tab:red", zorder=4,
                    label=rf"$P(T_{{raw}}=0)=p_{{out}}={params['p_out']:.4g}$")
    ax_mass.set_ylim(0.0, 1.0)
    ax_mass.set_ylabel("Discrete outage probability mass")
    handles, labels = ax.get_legend_handles_labels()
    mass_handles, mass_labels = ax_mass.get_legend_handles_labels()
    ax.legend(handles + mass_handles, labels + mass_labels, fontsize=8, loc="upper right")
    ax.text(
        0.02,
        0.98,
        f"active mode = {active_mode:.6g}\n"
        f"positive mass = p_in = {params['p_in']:.6f}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox={"boxstyle": "round", "alpha": 0.12},
    )
    fig.tight_layout()
    png_path = output_dir / "raw_T_pdf_eq62.png"
    pdf_path = output_dir / "raw_T_pdf_eq62.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--sample-count", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--tau-zen", type=float, default=None)
    args = parser.parse_args()

    config = load_yaml(args.config.resolve())
    radius_of_curvature = float(config["optics"]["radius_of_curvature_m"])
    if not math.isinf(radius_of_curvature):
        raise ValueError("The final baseline requires F0=infinity.")
    params, backends = _derive(config, args.tau_zen)
    _sanity_checks(params)
    _print_table(params)
    print("F0                 = infinity  [m]")
    print("\nRepository helper reuse")
    for name, reused in backends.items():
        print(f"{name:22s}: {'reused' if reused else 'local fallback'}")

    log_pdf_from_log_t, _, _ = make_active_pdf(params)
    active_integral = _integrate_log_density(log_pdf_from_log_t, -80.0, 20.0)
    raw_positive_integral = params["p_in"] * active_integral
    normalization_error = abs(active_integral - 1.0)
    raw_mass_error = abs(raw_positive_integral - params["p_in"])
    if normalization_error > 1.0e-5 or raw_mass_error > 1.0e-5:
        raise AssertionError(
            f"PDF normalization failed: active={active_integral}, "
            f"positive_raw={raw_positive_integral}, p_in={params['p_in']}"
        )

    samples = _sample_active(params, args.sample_count, args.seed)
    mode_grid = _mode_grid(params, samples)
    mode_values = _pdf_values(log_pdf_from_log_t, mode_grid)
    mode_index = int(np.argmax(mode_values))
    active_mode = float(mode_grid[mode_index])
    raw_mode_index = int(np.argmax(params["p_in"] * mode_values))
    if mode_index != raw_mode_index:
        raise AssertionError("AoA scaling changed the active/raw positive mode location.")

    q01, q10, q50, q90, q99, q999 = np.quantile(
        samples, [0.01, 0.10, 0.50, 0.90, 0.99, 0.999]
    )
    plot_low = max(min(q01 * 0.5, active_mode * 0.5), np.finfo(np.float64).tiny)
    plot_high = max(q999 * 1.05, params["A0_eta_atm"] * 1.1, active_mode * 2.0)
    t_grid = np.geomspace(plot_low, plot_high, 2400)
    active_values = _pdf_values(log_pdf_from_log_t, t_grid)
    args.output_dir.resolve().mkdir(parents=True, exist_ok=True)

    active_paths = _save_active_figure(
        args.output_dir.resolve(), t_grid, active_values,
        params["A0_eta_atm"], active_mode, samples,
    )
    mc_paths = _save_mc_figure(
        args.output_dir.resolve(), t_grid, active_values,
        params["A0_eta_atm"], active_mode, samples,
    )
    raw_paths = _save_raw_figure(
        args.output_dir.resolve(), t_grid, active_values, params, active_mode
    )

    print("\nPDF validation")
    print(f"active integral       = {active_integral:.12f}")
    print(f"active normalization  = {normalization_error:.3e}")
    print(f"positive raw integral = {raw_positive_integral:.12f}")
    print(f"positive mass error   = {raw_mass_error:.3e}")
    print(f"analytical mode       = {active_mode:.12g}")
    print(f"MC histogram mode     = {mc_paths[2]:.12g}")
    print(f"mean X                = {np.mean(samples):.12g}")
    print(f"median X              = {q50:.12g}")
    print(f"q01                   = {q01:.12g}")
    print(f"q10                   = {q10:.12g}")
    print(f"q50                   = {q50:.12g}")
    print(f"q90                   = {q90:.12g}")
    print(f"q99                   = {q99:.12g}")
    print(f"p_out                 = {params['p_out']:.12g}")
    print(f"p_in                  = {params['p_in']:.12g}")
    print("active/raw-positive mode match = True")
    for path in (*active_paths, *mc_paths[:2], *raw_paths):
        print(f"saved                 = {path}")
    print("T <= 1 conditioning    = NOT RUN")
    print("CV-QKD/SKR/security    = NOT RUN")


if __name__ == "__main__":
    main()
