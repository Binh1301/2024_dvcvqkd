"""Compare the same raw active HAP--UAV PDF in three independent ways.

The active variable is the unconditioned raw product
``X = eta_atm * H_sc * H_p``.  This diagnostic deliberately does not apply
AoA, an outage atom, clipping, conditioning on ``X <= 1``, or any CV-QKD
quantity.  The three density evaluations are:

1. the existing stable manuscript Eq. (51) implementation;
2. a separate numerical product integral over the transformed ``H_p`` PDF;
3. a Monte Carlo composition using one shared ``H_sc``/``H_p`` sample set.

It is a channel-only diagnostic, not a publication-scale or security run.
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
from scipy.special import i0e


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
_LOG_TINY = math.log(np.finfo(np.float64).tiny)


def _finite(name: str, values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if np.any(~np.isfinite(values)):
        raise FloatingPointError(f"{name} contains NaN or infinity.")
    return values


def _log_i0(values: float | np.ndarray) -> float | np.ndarray:
    """Stable log(I0(values)) using the exponentially scaled Bessel function."""

    array = np.asarray(values, dtype=np.float64)
    absolute = np.abs(array)
    scaled = np.asarray(i0e(absolute), dtype=np.float64)
    result = np.empty_like(absolute)
    regular = scaled > 0.0
    result[regular] = np.log(scaled[regular]) + absolute[regular]
    large = ~regular
    if np.any(large):
        # I0(z) ~ exp(z) / sqrt(2*pi*z); this branch is only for an
        # unrepresentably small scaled value.
        result[large] = absolute[large] - 0.5 * (
            math.log(2.0 * math.pi) + np.log(absolute[large])
        )
    if array.ndim == 0:
        return float(result)
    return result


def _log_hsc_from_log_h(log_h: float | np.ndarray, params: dict[str, float]):
    """Log PDF of the requested lognormal H_sc law."""

    variance = params["v_sc"]
    values = np.asarray(log_h, dtype=np.float64)
    result = (
        -values
        - 0.5 * math.log(2.0 * math.pi * variance)
        - (values + 0.5 * variance) ** 2 / (2.0 * variance)
    )
    if values.ndim == 0:
        return float(result)
    return result


def _hsc_pdf(h: np.ndarray, params: dict[str, float]) -> np.ndarray:
    values = np.asarray(h, dtype=np.float64)
    result = np.zeros_like(values)
    valid = values > 0.0
    if np.any(valid):
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            result[valid] = np.exp(_log_hsc_from_log_h(np.log(values[valid]), params))
    return result


def _log_hp_from_log_u(log_u: float | np.ndarray, params: dict[str, float]):
    """Log PDF of the transformed Rician pointing transmittance H_p."""

    values = np.asarray(log_u, dtype=np.float64)
    log_a0 = math.log(params["A0"])
    q = params["chi_squared"]
    sigma_jt_squared = params["sigma_jt"] ** 2
    log_ratio = np.minimum(values - log_a0, 0.0)
    radius = np.sqrt(np.maximum(-0.5 * params["omega_L_eq"] ** 2 * log_ratio, 0.0))
    bessel_argument = params["rho"] * radius / sigma_jt_squared
    result = (
        math.log(q)
        - q * log_a0
        - params["rho"] ** 2 / (2.0 * sigma_jt_squared)
        + (q - 1.0) * values
        + _log_i0(bessel_argument)
    )
    result = np.where(np.isfinite(values), result, -np.inf)
    if values.ndim == 0:
        return float(result)
    return result


def _hp_pdf(u: np.ndarray, params: dict[str, float]) -> np.ndarray:
    values = np.asarray(u, dtype=np.float64)
    result = np.zeros_like(values)
    valid = (values > 0.0) & (values <= params["A0"])
    if np.any(valid):
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            result[valid] = np.exp(_log_hp_from_log_u(np.log(values[valid]), params))
    return result


def _log_product_integrand_s(s: float, log_t: float, params: dict[str, float]) -> float:
    """Log integrand after u=A0*exp(-s), for the independent product integral."""

    log_u = math.log(params["A0"]) - s
    log_h = log_t - math.log(params["eta_atm"]) - log_u
    log_value = (
        -math.log(params["eta_atm"])
        + _log_hsc_from_log_h(log_h, params)
        + _log_hp_from_log_u(log_u, params)
    )
    return float(log_value)


def _product_pdf_numerical(t: float, params: dict[str, float]) -> float:
    """Evaluate the product integral without calling the Eq. (51) PDF.

    Starting from
    ``f_X(t)=integral_0^A0 f_Hsc(t/(eta*u))*f_Hp(u)/(eta*u) du``,
    the substitution ``u=A0*exp(-s)`` gives an integral over s in [0,infty)
    with a bounded log-domain integrand.
    """

    if not math.isfinite(t) or t <= 0.0:
        raise ValueError("The product PDF requires finite t > 0.")
    log_t = math.log(t)

    def integrand(s: float) -> float:
        log_value = _log_product_integrand_s(s, log_t, params)
        if not math.isfinite(log_value) or log_value < _LOG_TINY:
            return 0.0
        return math.exp(log_value)

    value, error = quad(
        integrand,
        0.0,
        np.inf,
        epsabs=1.0e-11,
        epsrel=2.0e-8,
        limit=200,
    )
    if not math.isfinite(value) or value < 0.0:
        raise FloatingPointError(f"Independent product integral failed at t={t}: {value}")
    if error > 1.0e-6 * max(1.0, value):
        print(f"NOTE: inner quadrature estimate at t={t:.6g} is {error:.3e}")
    return float(value)


def _product_pdf_grid(t_grid: np.ndarray, params: dict[str, float]) -> np.ndarray:
    values = np.asarray(
        [_product_pdf_numerical(float(t), params) for t in t_grid],
        dtype=np.float64,
    )
    return _finite("independent product PDF", values)


def _integrate_log_function(log_pdf_from_log_t, lower: float, upper: float) -> float:
    """Numerically integrate f(t) dt by fixed-panel Gauss--Legendre in log t."""

    nodes, weights = np.polynomial.legendre.leggauss(8)
    previous = None
    for panel_count in (16, 32):
        edges = np.linspace(lower, upper, panel_count + 1)
        total = 0.0
        for left, right in zip(edges[:-1], edges[1:]):
            center = (left + right) / 2.0
            half = (right - left) / 2.0
            log_t = center + half * nodes
            log_pdf = np.asarray(log_pdf_from_log_t(log_t), dtype=np.float64)
            log_integrand = log_pdf + log_t
            total += half * float(np.dot(weights, np.exp(log_integrand)))
        if previous is not None and abs(total - previous) <= 2.0e-5 * max(1.0, abs(total)):
            return total
        previous = total
    return float(previous)


def _hp_moment(params: dict[str, float], power: int) -> float:
    """Numerically integrate E[H_p**power] in the same transformed coordinate."""

    log_a0 = math.log(params["A0"])

    def integrand(s: float) -> float:
        log_u = log_a0 - s
        log_value = power * log_u + _log_hp_from_log_u(log_u, params) + log_u
        if not math.isfinite(log_value) or log_value < _LOG_TINY:
            return 0.0
        return math.exp(log_value)

    value, error = quad(integrand, 0.0, np.inf, epsabs=1.0e-12, epsrel=2.0e-9, limit=200)
    if error > 1.0e-7 * max(1.0, value):
        raise RuntimeError(f"H_p moment quadrature did not converge: error={error}")
    return float(value)


def _print_derived(params: dict[str, float]) -> None:
    rows = (
        ("L", params["L"], "m"),
        ("D_r", params["D_r"], "m"),
        ("omega_0", params["omega_0"], "m"),
        ("eta_atm", params["eta_atm"], "dimensionless"),
        ("sigma_R0^2", params["sigma_R0_squared"], "dimensionless"),
        ("AA", params["AA"], "dimensionless"),
        ("sigma_R,D^2", params["sigma_R_squared"], "dimensionless"),
        ("sigma_X^2", params["sigma_X_squared"], "dimensionless"),
        ("omega_L", params["omega_L"], "m"),
        ("G_d", params["G_d"], "dimensionless"),
        ("omega_L,e", params["omega_L_e"], "m"),
        ("A0", params["A0"], "dimensionless"),
        ("omega_L,eq", params["omega_L_eq"], "m"),
        ("sigma_jt", params["sigma_jt"], "m"),
        ("chi", params["chi"], "dimensionless"),
    )
    print("\nCommon derived channel parameters (one set for all methods)")
    for name, value, unit in rows:
        print(f"{name:16s} = {value:.16g} [{unit}]")


def _save_component_plots(
    output_dir: Path,
    h_sc: np.ndarray,
    h_p: np.ndarray,
    params: dict[str, float],
    hsc_normalization: float,
    hp_normalization: float,
) -> None:
    hsc_edges = np.geomspace(max(np.min(h_sc) * 0.95, 1.0e-12), np.max(h_sc) * 1.05, 100)
    hsc_grid = np.geomspace(hsc_edges[0], hsc_edges[-1], 1200)
    hsc_hist, _ = np.histogram(h_sc, bins=hsc_edges, density=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.stairs(hsc_hist, hsc_edges, color="tab:blue", linewidth=1.0, alpha=0.72, label=r"MC $H_{\rm sc}$")
    ax.plot(hsc_grid, _hsc_pdf(hsc_grid, params), color="black", linewidth=1.8, label=r"Analytical $f_{H_{\rm sc}}$")
    ax.set_xscale("log")
    ax.set_xlabel(r"Scintillation factor $H_{\rm sc}$")
    ax.set_ylabel("Probability density")
    ax.set_title("HAP--UAV scintillation component")
    ax.grid(alpha=0.25)
    ax.legend()
    ax.text(
        0.03,
        0.97,
        f"analytical integral = {hsc_normalization:.8f}\nMC mean = {np.mean(h_sc):.8f}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox={"boxstyle": "round", "alpha": 0.12},
    )
    fig.tight_layout()
    fig.savefig(output_dir / "hsc_component_pdf.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "hsc_component_pdf.pdf", bbox_inches="tight")
    plt.close(fig)

    hp_edges = np.linspace(0.0, params["A0"], 101)
    hp_grid = np.linspace(params["A0"] * 1.0e-10, params["A0"], 1400)
    hp_hist, _ = np.histogram(h_p, bins=hp_edges, density=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.stairs(hp_hist, hp_edges, color="tab:blue", linewidth=1.0, alpha=0.72, label="MC $H_p$")
    ax.plot(hp_grid, _hp_pdf(hp_grid, params), color="black", linewidth=1.8, label="Analytical $f_{H_p}$")
    ax.set_xlabel(r"Pointing transmittance $H_p$")
    ax.set_ylabel("Probability density")
    ax.set_title("HAP--UAV pointing-transmittance component")
    ax.grid(alpha=0.25)
    ax.legend()
    ax.text(
        0.03,
        0.97,
        f"analytical integral = {hp_normalization:.8f}\nMC mean = {np.mean(h_p):.8g}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox={"boxstyle": "round", "alpha": 0.12},
    )
    fig.tight_layout()
    fig.savefig(output_dir / "hp_component_pdf.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "hp_component_pdf.pdf", bbox_inches="tight")
    plt.close(fig)


def _save_three_method_plot(
    output_dir: Path,
    x_mc: np.ndarray,
    x_grid: np.ndarray,
    closed_pdf: np.ndarray,
    integral_pdf: np.ndarray,
    params: dict[str, float],
    seed: int,
) -> tuple[float, float]:
    tail_low, tail_high = np.quantile(x_mc, [1.0e-4, 0.9999])
    edges = np.geomspace(max(float(tail_low) * 0.5, np.finfo(np.float64).tiny), float(tail_high) * 2.0, 100)
    histogram, _ = np.histogram(x_mc, bins=edges, density=True)
    centers = np.sqrt(edges[:-1] * edges[1:])
    histogram_integral = float(np.sum(histogram * np.diff(edges)))

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    ax.stairs(histogram, edges, color="tab:blue", linewidth=1.0, alpha=0.72, label="MC $X$")
    ax.plot(x_grid, closed_pdf, color="black", linewidth=1.9, label="Eq. (51) closed form")
    ax.plot(x_grid, integral_pdf, color="black", linewidth=1.4, linestyle="--", label="Independent product integral")
    ax.set_xscale("log")
    ax.set_xlabel(r"Active raw transmittance $X=\eta_{\rm atm}H_{\rm sc}H_p$")
    ax.set_ylabel("Probability density")
    ax.set_title("HAP--UAV active transmittance: three-method comparison")
    ax.grid(alpha=0.25)
    ax.legend()
    ax.text(
        0.03,
        0.97,
        f"MC integral = {histogram_integral:.8f}\nN = {x_mc.size:,}; seed = {seed}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox={"boxstyle": "round", "alpha": 0.12},
    )
    fig.tight_layout()
    fig.savefig(output_dir / "active_pdf_three_methods.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "active_pdf_three_methods.pdf", bbox_inches="tight")
    plt.close(fig)

    histogram_at_centers = histogram
    closed_at_centers = np.interp(np.log(centers), np.log(x_grid), closed_pdf)
    histogram_l1 = float(np.sum(np.abs(histogram_at_centers - closed_at_centers) * np.diff(edges)))
    return histogram_integral, histogram_l1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--sample-count", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--grid-size", type=int, default=220)
    args = parser.parse_args()

    config = load_yaml(args.config)
    params, _ = _derive(config)
    _print_derived(params)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.grid_size < 80:
        raise ValueError("grid-size must be at least 80.")

    sample_count = int(config["diagnostics"]["sample_count"] if args.sample_count is None else args.sample_count)
    seed = int(config["diagnostics"]["seed"] if args.seed is None else args.seed)
    if sample_count <= 1:
        raise ValueError("sample-count must be at least two.")

    # One RNG and one shared sample set feed all three figures and all checks.
    rng = np.random.default_rng(seed)
    h_sc = np.exp(rng.normal(-0.5 * params["v_sc"], math.sqrt(params["v_sc"]), sample_count))
    x_jitter = rng.normal(params["rho_x"], params["sigma_jt"], sample_count)
    y_jitter = rng.normal(params["rho_y"], params["sigma_jt"], sample_count)
    r_mis = np.hypot(x_jitter, y_jitter)
    h_p = params["A0"] * np.exp(-2.0 * r_mis**2 / params["omega_L_eq"] ** 2)
    x_mc = params["eta_atm"] * h_sc * h_p
    _finite("H_sc samples", h_sc)
    _finite("H_p samples", h_p)
    _finite("X samples", x_mc)
    if np.any((h_sc <= 0.0) | (h_p <= 0.0) | (x_mc <= 0.0)):
        raise FloatingPointError("The sampled active factors must be strictly positive.")

    hsc_normalization, hsc_quad_error = quad(
        lambda log_h: math.exp(_log_hsc_from_log_h(float(log_h), params) + float(log_h)),
        -80.0,
        20.0,
        epsabs=1.0e-12,
        epsrel=1.0e-10,
        limit=200,
    )
    if hsc_quad_error > 1.0e-8:
        raise RuntimeError(f"H_sc normalization quadrature did not converge: error={hsc_quad_error}")
    hp_normalization = _hp_moment(params, 0)
    closed_log_pdf, _, closed_pdf_function = make_active_pdf(params)
    closed_normalization = _integrate_log_density(closed_log_pdf, -80.0, 20.0)

    q01, q99 = np.quantile(x_mc, [1.0e-4, 0.9999])
    x_low = max(float(q01) * 0.5, np.finfo(np.float64).tiny)
    x_high = max(float(q99) * 2.0, params["A0_eta_atm"] * 2.0)
    x_grid = np.geomspace(x_low, x_high, args.grid_size)
    closed_pdf = np.asarray(closed_pdf_function(x_grid), dtype=np.float64)
    integral_pdf = _product_pdf_grid(x_grid, params)
    if np.any(~np.isfinite(closed_pdf)) or np.any(closed_pdf < 0.0):
        raise FloatingPointError("Eq. (51) curve is not finite and nonnegative.")

    def independent_log_pdf(log_t: np.ndarray) -> np.ndarray:
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

    independent_normalization = _integrate_log_function(
        independent_log_pdf,
        -35.0,
        5.0,
    )

    hsc_mean_mc = float(np.mean(h_sc))
    hp_mean_mc = float(np.mean(h_p))
    hsc_mean = 1.0
    hp_mean = _hp_moment(params, 1)
    expected_x_mean = params["eta_atm"] * hsc_mean * hp_mean
    mc_x_mean = float(np.mean(x_mc))
    closed_mode = float(x_grid[int(np.argmax(closed_pdf))])
    integral_mode = float(x_grid[int(np.argmax(integral_pdf))])
    histogram_edges = np.geomspace(x_low, x_high, 100)
    histogram_values, _ = np.histogram(x_mc, bins=histogram_edges, density=True)
    histogram_mode = float(np.sqrt(histogram_edges[:-1] * histogram_edges[1:])[int(np.argmax(histogram_values))])
    abs_difference = np.abs(closed_pdf - integral_pdf)
    max_abs_difference = float(np.max(abs_difference))
    max_relative_difference = float(np.max(abs_difference / np.maximum(closed_pdf, 1.0e-300)))
    histogram_integral, histogram_l1 = _save_three_method_plot(
        args.output_dir,
        x_mc,
        x_grid,
        closed_pdf,
        integral_pdf,
        params,
        seed,
    )
    _save_component_plots(
        args.output_dir,
        h_sc,
        h_p,
        params,
        hsc_normalization,
        hp_normalization,
    )

    q_values = np.quantile(x_mc, [0.01, 0.10, 0.50, 0.90, 0.99])
    mean_relative_error = abs(mc_x_mean - expected_x_mean) / expected_x_mean
    method_3_agrees = bool(mean_relative_error < 5.0e-3 and histogram_l1 < 0.12)

    print("\nNormalization checks")
    print(f"sample count / seed             = {sample_count} / {seed}")
    print(f"integral f_Hsc                 = {hsc_normalization:.12f}")
    print(f"integral f_Hp                  = {hp_normalization:.12f}")
    print(f"integral f_X Eq. (51)          = {closed_normalization:.12f}")
    print(f"integral f_X product integral  = {independent_normalization:.12f}")
    print(f"integral MC histogram          = {histogram_integral:.12f}")
    print("\nMoments and locations")
    print(f"E[H_sc] analytical / MC        = {hsc_mean:.12g} / {hsc_mean_mc:.12g}")
    print(f"E[H_p] analytical / MC          = {hp_mean:.12g} / {hp_mean_mc:.12g}")
    print(f"eta*E[H_sc]*E[H_p]              = {expected_x_mean:.12g}")
    print(f"E[X_MC]                         = {mc_x_mean:.12g}")
    print(f"relative mean error              = {mean_relative_error:.3e}")
    print(f"mode Eq. (51)                   = {closed_mode:.12g}")
    print(f"mode product integral            = {integral_mode:.12g}")
    print(f"mode MC histogram               = {histogram_mode:.12g}")
    print(
        "MC q01, q10, q50, q90, q99     = "
        f"{q_values[0]:.12g}, {q_values[1]:.12g}, {q_values[2]:.12g}, "
        f"{q_values[3]:.12g}, {q_values[4]:.12g}"
    )
    print("\nMethod comparison")
    print(f"max abs difference Eq.51/integral = {max_abs_difference:.3e}")
    print(f"max relative difference            = {max_relative_difference:.3e}")
    print(f"MC-vs-Eq.51 histogram L1           = {histogram_l1:.3e}")
    print(f"Method 3 agrees                    = {method_3_agrees}")
    print("AoA / outage / clipping / X<=1 conditioning = NOT RUN")
    print(f"saved figures under               = {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
