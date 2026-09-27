"""Plot the active HAP--UAV transmittance PDF in four focused figures.

The same unconditioned active variable is used everywhere:
``X = eta_atm * H_sc * H_p``.  This script does not apply AoA, outage,
clipping, physical-domain conditioning, raw ``T_raw``, or CV-QKD code.

The PDF implementations and common sampling law are reused from the existing
three-method diagnostic; only the four-figure presentation is new here.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.compare_active_pdf_three_methods import (
    _finite,
    _log_hsc_from_log_h,
    _hp_moment,
    _integrate_log_function,
    _product_pdf_grid,
    _product_pdf_numerical,
    _print_derived,
)
from scripts.plot_eq62_raw_transmittance_pdf import (
    CONFIG_DEFAULT,
    _derive,
    _integrate_log_density,
    make_active_pdf,
)


OUTPUT_DEFAULT = ROOT / "diagnostics"


def _sample_active(params: dict[str, float], sample_count: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    h_sc = np.exp(rng.normal(-0.5 * params["v_sc"], math.sqrt(params["v_sc"]), sample_count))
    x_jitter = rng.normal(params["rho_x"], params["sigma_jt"], sample_count)
    y_jitter = rng.normal(params["rho_y"], params["sigma_jt"], sample_count)
    h_p = params["A0"] * np.exp(
        -2.0 * (x_jitter**2 + y_jitter**2) / params["omega_L_eq"] ** 2
    )
    x_mc = params["eta_atm"] * h_sc * h_p
    _finite("H_sc samples", h_sc)
    _finite("H_p samples", h_p)
    _finite("X samples", x_mc)
    return h_sc, h_p, x_mc


def _hsc_normalization(params: dict[str, float]) -> float:
    value, error = quad(
        lambda log_h: math.exp(_log_hsc_from_log_h(float(log_h), params) + float(log_h)),
        -80.0,
        20.0,
        epsabs=1.0e-12,
        epsrel=1.0e-10,
        limit=200,
    )
    if error > 1.0e-8:
        raise RuntimeError(f"H_sc normalization quadrature did not converge: error={error}")
    return float(value)


def _independent_log_pdf(log_t: np.ndarray, params: dict[str, float]) -> np.ndarray:
    values = np.asarray(log_t, dtype=np.float64)
    return np.asarray(
        [
            math.log(
                max(
                    _product_pdf_numerical(math.exp(float(value)), params),
                    np.finfo(np.float64).tiny,
                )
            )
            for value in values.reshape(-1)
        ],
        dtype=np.float64,
    ).reshape(values.shape)


def _save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(output_dir / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def _format_axis(ax: plt.Axes, x_right: float) -> None:
    ax.set_xlim(0.0, x_right)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(alpha=0.25)


def _save_four_figures(
    output_dir: Path,
    x_right: float,
    reference_scale: float,
    bins: np.ndarray,
    histogram: np.ndarray,
    t_grid: np.ndarray,
    closed_pdf: np.ndarray,
    integral_pdf: np.ndarray,
    sample_count: int,
) -> tuple[float, float]:
    x_label = r"Active transmittance $X=\eta_{\rm atm}H_{\rm sc}H_p$"
    y_label = "Probability density"
    reference_label = r"reference scale $A_0\eta_{\rm atm}$"

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.plot(t_grid, closed_pdf, color="black", linewidth=1.9, label="Eq. (51) closed form")
    ax.axvline(reference_scale, color="tab:green", linestyle=":", linewidth=1.4, label=reference_label)
    ax.set_title("HAP--UAV active transmittance PDF: closed-form method")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _format_axis(ax, x_right)
    ax.legend()
    _save_figure(fig, output_dir, "figure1_active_pdf_closed_form")

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.plot(t_grid, integral_pdf, color="black", linewidth=1.9, label="Independent product integral")
    ax.axvline(reference_scale, color="tab:green", linestyle=":", linewidth=1.4, label=reference_label)
    ax.set_title("HAP--UAV active transmittance PDF: integral method")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _format_axis(ax, x_right)
    ax.legend()
    _save_figure(fig, output_dir, "figure2_active_pdf_integral")

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.stairs(
        histogram,
        bins,
        color="tab:blue",
        linewidth=1.0,
        alpha=0.78,
        label=f"Monte Carlo histogram (N={sample_count:,})",
    )
    ax.axvline(reference_scale, color="tab:green", linestyle=":", linewidth=1.4, label=reference_label)
    ax.set_title("HAP--UAV active transmittance PDF: Monte Carlo method")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _format_axis(ax, x_right)
    ax.legend()
    _save_figure(fig, output_dir, "figure3_active_pdf_monte_carlo")

    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.stairs(histogram, bins, color="tab:blue", linewidth=1.0, alpha=0.72, label="MC $X$")
    ax.plot(t_grid, closed_pdf, color="black", linewidth=1.9, label="Eq. (51) closed form")
    ax.plot(
        t_grid,
        integral_pdf,
        color="black",
        linewidth=1.4,
        linestyle="--",
        label="Independent product integral",
    )
    ax.axvline(reference_scale, color="tab:green", linestyle=":", linewidth=1.4, label=reference_label)
    ax.set_title("HAP--UAV active transmittance: three-method comparison")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _format_axis(ax, x_right)
    ax.legend()
    _save_figure(fig, output_dir, "figure4_active_pdf_combined")

    centers = 0.5 * (bins[:-1] + bins[1:])
    closed_at_centers = np.interp(centers, t_grid, closed_pdf)
    histogram_l1 = float(np.sum(np.abs(histogram - closed_at_centers) * np.diff(bins)))
    histogram_integral = float(np.sum(histogram * np.diff(bins)))
    return histogram_integral, histogram_l1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--sample-count", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--tau-zen", type=float, default=None)
    parser.add_argument("--grid-size", type=int, default=600)
    args = parser.parse_args()

    config = load_yaml(args.config)
    params, _ = _derive(config, args.tau_zen)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _print_derived(params)
    if args.grid_size < 200:
        raise ValueError("grid-size must be at least 200.")

    sample_count = int(config["diagnostics"]["sample_count"] if args.sample_count is None else args.sample_count)
    seed = int(config["diagnostics"]["seed"] if args.seed is None else args.seed)
    if sample_count <= 1:
        raise ValueError("sample-count must be at least two.")

    h_sc, h_p, x_mc = _sample_active(params, sample_count, seed)
    reference_scale = params["A0_eta_atm"]
    x_right = max(
        float(np.quantile(x_mc, 0.999)) * 1.05,
        float(np.max(x_mc)) * 1.02,
        reference_scale * 1.2,
    )
    bins = np.linspace(0.0, x_right, 81)
    histogram, _ = np.histogram(x_mc, bins=bins, density=True)
    # The axis still starts at zero; this positive numerical start avoids the
    # unresolvable extreme lower-tail endpoint of the adaptive inner integral.
    t_grid = np.linspace(max(x_right * 1.0e-4, np.finfo(np.float64).tiny), x_right, args.grid_size)

    closed_log_pdf, _, closed_pdf_function = make_active_pdf(params)
    closed_pdf = np.asarray(closed_pdf_function(t_grid), dtype=np.float64)
    integral_pdf = _product_pdf_grid(t_grid, params)
    if np.any(~np.isfinite(closed_pdf)) or np.any(~np.isfinite(integral_pdf)):
        raise FloatingPointError("Analytical PDF values contain NaN or infinity.")

    hsc_normalization = _hsc_normalization(params)
    hp_normalization = _hp_moment(params, 0)
    closed_normalization = _integrate_log_density(closed_log_pdf, -80.0, 20.0)
    integral_normalization = _integrate_log_function(
        lambda log_t: _independent_log_pdf(log_t, params),
        -35.0,
        5.0,
    )
    histogram_integral, histogram_l1 = _save_four_figures(
        args.output_dir,
        x_right,
        reference_scale,
        bins,
        histogram,
        t_grid,
        closed_pdf,
        integral_pdf,
        sample_count,
    )

    hsc_mean_mc = float(np.mean(h_sc))
    hp_mean_mc = float(np.mean(h_p))
    x_mean_mc = float(np.mean(x_mc))
    x_median_mc = float(np.median(x_mc))
    quantiles = np.quantile(x_mc, [0.01, 0.10, 0.50, 0.90, 0.99])
    closed_mode = float(t_grid[int(np.argmax(closed_pdf))])
    integral_mode = float(t_grid[int(np.argmax(integral_pdf))])
    histogram_mode = float((bins[:-1] + bins[1:])[int(np.argmax(histogram))] / 2.0)
    meaningful = np.maximum(closed_pdf, integral_pdf) >= 1.0e-4 * max(
        float(np.max(closed_pdf)), float(np.max(integral_pdf))
    )
    max_relative_difference = float(
        np.max(
            np.abs(closed_pdf[meaningful] - integral_pdf[meaningful])
            / np.maximum(np.maximum(closed_pdf[meaningful], integral_pdf[meaningful]), 1.0e-300)
        )
    )
    hp_mean = _hp_moment(params, 1)
    expected_x_mean = params["eta_atm"] * hp_mean
    mean_relative_error = abs(x_mean_mc - expected_x_mean) / expected_x_mean
    method3_agrees = bool(mean_relative_error < 5.0e-3 and histogram_l1 < 0.12)
    if abs(hsc_normalization - 1.0) > 2.0e-8:
        raise AssertionError(f"f_Hsc normalization failed: {hsc_normalization}")
    if abs(hp_normalization - 1.0) > 2.0e-8:
        raise AssertionError(f"f_Hp normalization failed: {hp_normalization}")
    if abs(closed_normalization - 1.0) > 2.0e-8:
        raise AssertionError(f"closed-form f_X normalization failed: {closed_normalization}")
    if abs(integral_normalization - 1.0) > 5.0e-5:
        raise AssertionError(f"integral f_X normalization failed: {integral_normalization}")
    if not method3_agrees:
        raise AssertionError("Monte Carlo PDF does not agree with the analytical methods.")

    print("\nNormalization / consistency checks")
    print(f"sample count / seed             = {sample_count} / {seed}")
    print(f"integral f_Hsc                  = {hsc_normalization:.12f}")
    print(f"integral f_Hp                   = {hp_normalization:.12f}")
    print(f"integral f_X_closed             = {closed_normalization:.12f}")
    print(f"integral f_X_integral            = {integral_normalization:.12f}")
    print(f"integral MC histogram           = {histogram_integral:.12f}")
    print(f"common linear x-range           = [0, {x_right:.12g}]")
    print("\nMonte Carlo summary")
    print(f"mean(H_sc)                      = {hsc_mean_mc:.12g}")
    print(f"mean(H_p)                       = {hp_mean_mc:.12g}")
    print(f"mean(X_MC)                      = {x_mean_mc:.12g}")
    print(f"expected eta*E[H_sc]*E[H_p]    = {expected_x_mean:.12g}")
    print(f"mean relative error             = {mean_relative_error:.3e}")
    print(f"median(X_MC)                   = {x_median_mc:.12g}")
    print(
        "q01, q10, q50, q90, q99        = "
        f"{quantiles[0]:.12g}, {quantiles[1]:.12g}, {quantiles[2]:.12g}, "
        f"{quantiles[3]:.12g}, {quantiles[4]:.12g}"
    )
    print(f"mode f_X_closed                = {closed_mode:.12g}")
    print(f"mode f_X_integral              = {integral_mode:.12g}")
    print(f"histogram peak estimate         = {histogram_mode:.12g}")
    print("\nMethod comparison")
    print(f"max relative difference (meaningful region) = {max_relative_difference:.3e}")
    print(f"MC-vs-closed histogram L1                   = {histogram_l1:.3e}")
    print(f"Method 3 agrees with Methods 1/2             = {method3_agrees}")
    print("AoA / outage / clipping / X<=1 conditioning / raw T_raw = NOT RUN")
    print("\nSaved figures")
    for stem in (
        "figure1_active_pdf_closed_form",
        "figure2_active_pdf_integral",
        "figure3_active_pdf_monte_carlo",
        "figure4_active_pdf_combined",
    ):
        print(f"{(args.output_dir / (stem + '.png')).resolve()}")
        print(f"{(args.output_dir / (stem + '.pdf')).resolve()}")


if __name__ == "__main__":
    main()
