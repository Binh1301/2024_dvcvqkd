"""
Compare SKR performance across Binomial, Uniform, MB, and Gaussian reference.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.channel.channel_model import channel
    from uav_hap_1_sample.config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from uav_hap_1_sample.protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from uav_hap_1_sample.zstar.base import (
        compute_eigenvalues,
        compute_chi_BE,
        compute_chi_tot,
        compute_IAB,
        compute_SKR,
    )
else:
    from ..channel.channel_model import channel
    from ..config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from ..protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from ..zstar.base import (
        compute_eigenvalues,
        compute_chi_BE,
        compute_chi_tot,
        compute_IAB,
        compute_SKR,
    )


BASELINE = {
    "eta": float(QAM_ETA),
    "eps": float(QAM_EPS),
    "beta": float(QAM_BETA),
    "v_el": float(QAM_V_EL),
}
VA_GAUSS = 2.0
T_REF = 0.2
H_HAP_DEFAULT = 20_000.0

N_SAMPLES = 20_000
SKR_TOL = 1e-8


@dataclass(frozen=True)
class DistSpec:
    name: str
    color: str
    state: object


def _ensure_output_dir() -> str:
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _skr_from_state(state, t_eff: float, eps: float, beta: float, eta: float, v_el: float):
    metrics = compute_metrics(state, float(t_eff), float(eps), float(beta), float(eta), float(v_el))
    return float(metrics.skr_raw), float(metrics.chi_be), float(metrics.i_ab)


def skr_gaussian(va: float, t_eff: float, eps: float, beta: float, eta: float, v_el: float):
    z_gau = math.sqrt(float(t_eff) * (float(va) ** 2 + 2.0 * float(va)))
    l1, l2, l3, _, _, _ = compute_eigenvalues(float(va), float(z_gau), float(t_eff), float(eps))
    chi_be = compute_chi_BE(l1, l2, l3)
    chi_tot, _, _ = compute_chi_tot(float(t_eff), float(eps), float(eta), float(v_el))
    i_ab = compute_IAB(float(va), float(t_eff), chi_tot)
    skr = compute_SKR(float(beta), i_ab, chi_be)
    return float(skr), float(chi_be), float(i_ab)


def _bisect_root(func, lo: float, hi: float, tol: float = SKR_TOL, max_iter: int = 120) -> float:
    f_lo = func(lo)
    f_hi = func(hi)
    if f_lo == 0:
        return float(lo)
    if f_hi == 0:
        return float(hi)
    if f_lo * f_hi > 0:
        return float("nan")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = func(mid)
        if abs(f_mid) < tol:
            return float(mid)
        if f_lo * f_mid <= 0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return float(0.5 * (lo + hi))


def _bisect_eps_max(func, lo: float = 1e-4, hi: float = 0.05) -> float:
    def f(eps: float) -> float:
        return func(eps)

    f_lo = f(lo)
    f_hi = f(hi)
    if f_lo * f_hi > 0:
        return float("nan")
    for _ in range(120):
        mid = 10 ** (0.5 * (math.log10(lo) + math.log10(hi)))
        f_mid = f(mid)
        if abs(f_mid) < SKR_TOL:
            return float(mid)
        if f_lo * f_mid <= 0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return float(10 ** (0.5 * (math.log10(lo) + math.log10(hi))))


def _find_root_in_series(x: np.ndarray, y: np.ndarray) -> float:
    for i in range(len(x) - 1):
        y0, y1 = y[i], y[i + 1]
        if y0 == 0:
            return float(x[i])
        if y0 * y1 < 0:
            x0, x1 = x[i], x[i + 1]
            return float(x0 + (0 - y0) * (x1 - x0) / (y1 - y0))
    return float("nan")


def _format_float(value: float, fmt: str = "{:.4f}") -> str:
    if value != value or np.isinf(value):
        return "n/a"
    return fmt.format(value)


def _configure_style():
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def _build_specs() -> list[DistSpec]:
    return [
        DistSpec(
            name="Binomial",
            color="tab:blue",
            state=build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL),
        ),
        DistSpec(
            name="Uniform",
            color="tab:orange",
            state=build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM),
        ),
        DistSpec(
            name="MB",
            color="tab:green",
            state=build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE),
        ),
    ]


def _plot_skr_vs_t(specs: list[DistSpec]) -> dict[str, float]:
    _configure_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    t_vals = np.linspace(0.05, 0.5, 60)
    t_min_map = {}

    for spec in specs:
        skr_vals = np.array(
            [_skr_from_state(spec.state, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0] for t in t_vals],
            dtype=float,
        )
        t_min = _bisect_root(
            lambda t: _skr_from_state(spec.state, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0],
            0.01,
            0.5,
        )
        t_min_map[spec.name] = t_min
        label = f"{spec.name} (T_min={_format_float(t_min, '{:.3f}')})"
        ax.plot(t_vals, skr_vals, color=spec.color, label=label)
        if t_min == t_min:
            ax.scatter([t_min], [0], color=spec.color, zorder=4)
            ax.annotate(f"{t_min:.3f}", (t_min, 0), textcoords="offset points", xytext=(6, 6), fontsize=9)

    gauss_skr = np.array(
        [skr_gaussian(VA_GAUSS, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0] for t in t_vals],
        dtype=float,
    )
    t_min_g = _bisect_root(
        lambda t: skr_gaussian(VA_GAUSS, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0],
        0.01,
        0.5,
    )
    t_min_map["Gaussian"] = t_min_g
    ax.plot(t_vals, gauss_skr, color="black", linestyle="--", label=f"Gaussian (T_min={_format_float(t_min_g, '{:.3f}')})")
    if t_min_g == t_min_g:
        ax.scatter([t_min_g], [0], color="black", zorder=4)

    ax.set_xlabel("T_eff")
    ax.set_ylabel("SKR_raw")
    ax.set_title("SKR vs T_eff")
    ax.grid(alpha=0.3)
    ax.axhspan(ax.get_ylim()[0], 0.0, color="0.9", zorder=0)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(_ensure_output_dir(), "compare_skr_vs_T.png"), dpi=200)
    return t_min_map


def _plot_skr_vs_eps(specs: list[DistSpec]) -> dict[str, float]:
    _configure_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    eps_vals = np.logspace(np.log10(1e-4), np.log10(0.05), 40)
    eps_max_map = {}

    for spec in specs:
        skr_vals = np.array(
            [_skr_from_state(spec.state, T_REF, e, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0] for e in eps_vals],
            dtype=float,
        )
        eps_max = _bisect_eps_max(
            lambda e: _skr_from_state(spec.state, T_REF, e, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0],
            lo=1e-4,
            hi=0.05,
        )
        eps_max_map[spec.name] = eps_max
        label = f"{spec.name} (eps_max={_format_float(eps_max, '{:.3g}')})"
        ax.plot(eps_vals, skr_vals, color=spec.color, label=label)
        if eps_max == eps_max:
            ax.scatter([eps_max], [0], color=spec.color, zorder=4)

    gauss_skr = np.array(
        [skr_gaussian(VA_GAUSS, T_REF, e, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0] for e in eps_vals],
        dtype=float,
    )
    eps_max_g = _bisect_eps_max(
        lambda e: skr_gaussian(VA_GAUSS, T_REF, e, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0],
        lo=1e-4,
        hi=0.05,
    )
    eps_max_map["Gaussian"] = eps_max_g
    ax.plot(
        eps_vals,
        gauss_skr,
        color="black",
        linestyle="--",
        label=f"Gaussian (eps_max={_format_float(eps_max_g, '{:.3g}')})",
    )
    if eps_max_g == eps_max_g:
        ax.scatter([eps_max_g], [0], color="black", zorder=4)

    ax.set_xscale("log")
    ax.set_xlabel("eps")
    ax.set_ylabel("SKR_raw")
    ax.set_title("SKR vs eps (T_eff=0.2)")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(_ensure_output_dir(), "compare_skr_vs_eps.png"), dpi=200)
    return eps_max_map


def _plot_skr_vs_l(specs: list[DistSpec]) -> dict[str, float]:
    _configure_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    geometry = GeometryParams(H_HAP_m=H_HAP_DEFAULT, H_UAV_m=0.0)
    channel_params = ChannelParams()
    L_km = np.linspace(5.0, 25.0, 40)
    rng = np.random.default_rng(123)
    t_eff_L = np.array(
        [
            channel(
                geometry=geometry,
                channel_params=channel_params,
                N=N_SAMPLES,
                rng=rng,
                L_override_m=float(l) * 1000.0,
            )["T_eff"]
            for l in L_km
        ],
        dtype=float,
    )

    l_max_map = {}
    for spec in specs:
        skr_vals = np.array(
            [_skr_from_state(spec.state, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0] for t in t_eff_L],
            dtype=float,
        )
        l_max = _find_root_in_series(L_km, skr_vals)
        l_max_map[spec.name] = l_max
        ax.plot(L_km, skr_vals, color=spec.color, label=f"{spec.name} (L_max={_format_float(l_max, '{:.2f}')})")
        if l_max == l_max:
            ax.scatter([l_max], [0], color=spec.color, zorder=4)

    gauss_skr = np.array(
        [skr_gaussian(VA_GAUSS, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0] for t in t_eff_L],
        dtype=float,
    )
    l_max_g = _find_root_in_series(L_km, gauss_skr)
    l_max_map["Gaussian"] = l_max_g
    ax.plot(
        L_km,
        gauss_skr,
        color="black",
        linestyle="--",
        label=f"Gaussian (L_max={_format_float(l_max_g, '{:.2f}')})",
    )
    if l_max_g == l_max_g:
        ax.scatter([l_max_g], [0], color="black", zorder=4)

    ax.set_xlabel("L (km)")
    ax.set_ylabel("SKR_raw")
    ax.set_title("SKR vs L (H_HAP=20km)")
    ax.grid(alpha=0.3)
    ax.axhspan(ax.get_ylim()[0], 0.0, color="0.9", zorder=0)
    ax.legend(loc="best", fontsize=9)

    order = np.argsort(L_km)
    l_sorted = L_km[order]
    t_sorted = t_eff_L[order]

    def l_to_t(x):
        return np.interp(x, l_sorted, t_sorted)

    def t_to_l(x):
        return np.interp(x, t_sorted[::-1], l_sorted[::-1])

    sec = ax.secondary_xaxis("top", functions=(l_to_t, t_to_l))
    sec.set_xlabel("T_eff")

    fig.tight_layout()
    fig.savefig(os.path.join(_ensure_output_dir(), "compare_skr_vs_L.png"), dpi=200)
    return l_max_map


def _plot_bar_summary(specs: list[DistSpec]) -> None:
    _configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    labels = [spec.name for spec in specs] + ["Gaussian"]
    skr_vals = []
    chi_vals = []
    for spec in specs:
        skr, chi, _ = _skr_from_state(spec.state, T_REF, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
        skr_vals.append(skr)
        chi_vals.append(chi)
    skr_g, chi_g, _ = skr_gaussian(VA_GAUSS, T_REF, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
    skr_vals.append(skr_g)
    chi_vals.append(chi_g)

    ax = axes[0]
    ax.bar(labels, skr_vals, color=["tab:blue", "tab:orange", "tab:green", "black"])
    ax.set_title("SKR @ T_eff=0.2")
    ax.set_ylabel("SKR_raw")
    ax.grid(alpha=0.3, axis="y")
    for i, v in enumerate(skr_vals):
        ax.text(i, v, f"{v:.3e}", ha="center", va="bottom", fontsize=9, rotation=90)

    ax = axes[1]
    ax.bar(labels, chi_vals, color=["tab:blue", "tab:orange", "tab:green", "black"])
    ax.set_title("chi_BE @ T_eff=0.2")
    ax.set_ylabel("chi_BE")
    ax.grid(alpha=0.3, axis="y")
    for i, v in enumerate(chi_vals):
        ax.text(i, v, f"{v:.3e}", ha="center", va="bottom", fontsize=9, rotation=90)

    fig.tight_layout()
    fig.savefig(os.path.join(_ensure_output_dir(), "compare_bar_summary.png"), dpi=200)


def _plot_chi_iab_vs_t(specs: list[DistSpec]) -> None:
    _configure_style()
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    t_vals = np.linspace(0.05, 0.5, 60)

    for spec in specs:
        chi = []
        iab = []
        for t in t_vals:
            _, chi_be, i_ab = _skr_from_state(spec.state, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
            chi.append(chi_be)
            iab.append(i_ab)
        axes[0].plot(t_vals, chi, color=spec.color, label=spec.name)
        axes[1].plot(t_vals, iab, color=spec.color, label=spec.name)

    chi_g = []
    iab_g = []
    for t in t_vals:
        _, chi_be, i_ab = skr_gaussian(VA_GAUSS, t, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
        chi_g.append(chi_be)
        iab_g.append(i_ab)
    axes[0].plot(t_vals, chi_g, color="black", linestyle="--", label="Gaussian")
    axes[1].plot(t_vals, iab_g, color="black", linestyle="--", label="Gaussian")

    axes[0].set_ylabel("chi_BE")
    axes[0].set_title("chi_BE vs T_eff")
    axes[0].grid(alpha=0.3)
    axes[0].legend(loc="best", fontsize=9)

    axes[1].set_xlabel("T_eff")
    axes[1].set_ylabel("MI (bits/symbol)")
    axes[1].set_title("Discrete-input and Gaussian-reference MI vs T_eff")
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc="best", fontsize=9)

    fig.tight_layout()
    fig.savefig(os.path.join(_ensure_output_dir(), "compare_chi_iab_vs_T.png"), dpi=200)


def _plot_alpha0_opt() -> dict[str, float]:
    _configure_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    alpha_vals = np.linspace(1.0, 4.0, 20)
    results = {}

    def eval_bin(a):
        ncut = max(45, int(3.0 * a**2) + 10)
        state = build_state_binomial(a, ncut)
        return _skr_from_state(state, T_REF, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0]

    def eval_uni(a):
        ncut = max(150, int(3.0 * a**2) + 10)
        state = build_state_uniform(a, ncut)
        return _skr_from_state(state, T_REF, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0]

    def eval_mb(a):
        ncut = max(150, int(3.0 * a**2) + 10)
        state = build_state_mb(a, ncut, QAM_NU_TILDE)
        return _skr_from_state(state, T_REF, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])[0]

    curves = {
        "Binomial": (eval_bin, "tab:blue"),
        "Uniform": (eval_uni, "tab:orange"),
        "MB": (eval_mb, "tab:green"),
    }

    for name, (fn, color) in curves.items():
        skr_vals = np.array([fn(a) for a in alpha_vals], dtype=float)
        ax.plot(alpha_vals, skr_vals, color=color, label=name)
        idx = int(np.nanargmax(skr_vals))
        alpha_opt = float(alpha_vals[idx])
        results[name] = alpha_opt
        ax.scatter([alpha_opt], [skr_vals[idx]], color=color, zorder=4)
        ax.annotate(f"{alpha_opt:.2f}", (alpha_opt, skr_vals[idx]), textcoords="offset points", xytext=(6, 6), fontsize=9)

    ax.set_xlabel("alpha0")
    ax.set_ylabel("SKR_raw")
    ax.set_title("Optimal alpha0 @ T_eff=0.2")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(_ensure_output_dir(), "compare_alpha0_opt.png"), dpi=200)
    return results


def _print_summary(t_min_map, eps_max_map, l_max_map, alpha_opt_map) -> None:
    headers = ["Distribution", "T_min", "eps_max", "L_max(km)", "alpha0_opt"]
    rows = []
    names = ["Binomial", "Uniform", "MB", "Gaussian"]
    for name in names:
        rows.append(
            [
                name,
                _format_float(t_min_map.get(name, float("nan")), "{:.4f}"),
                _format_float(eps_max_map.get(name, float("nan")), "{:.4g}"),
                _format_float(l_max_map.get(name, float("nan")), "{:.3f}"),
                _format_float(alpha_opt_map.get(name, float("nan")), "{:.3f}"),
            ]
        )
    widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print("\nSummary (SKR=0 boundaries and optimal alpha0):")
    print("  ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers)))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(f"{row[i]:<{widths[i]}}" for i in range(len(row))))


def main() -> None:
    specs = _build_specs()

    t_min_map = _plot_skr_vs_t(specs)
    eps_max_map = _plot_skr_vs_eps(specs)
    l_max_map = _plot_skr_vs_l(specs)
    _plot_bar_summary(specs)
    _plot_chi_iab_vs_t(specs)
    alpha_opt_map = _plot_alpha0_opt()

    _print_summary(t_min_map, eps_max_map, l_max_map, alpha_opt_map)
    plt.show()


if __name__ == "__main__":
    main()
