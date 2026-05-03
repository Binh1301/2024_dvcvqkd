from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np


XI_KM_INV = 0.09232
W0_M = 0.0626
WAVELENGTH_M = 1550e-9
EPS_CH = 0.01
V_EL = 0.01

DEFAULT_ETA_DET = 0.85
DEFAULT_L_LINK_KM = 10.0
DEFAULT_L_APERTURE_M = 0.125
DEFAULT_VA = 4.0
DEFAULT_BETA = 0.93

ETA_DET_RANGE = np.arange(0.60, 0.95 + 1e-12, 0.05)
L_LINK_RANGE_KM = np.arange(10.0, 20.0 + 1e-12, 1.0)
L_APERTURE_RANGE_M = np.arange(0.075, 0.30 + 1e-12, 0.025)
VA_RANGE = np.arange(2.0, 10.0 + 1e-12, 1.0)
BETA_RANGE = np.arange(0.80, 1.00 + 1e-12, 0.05)

EPS = 1e-12


@dataclass(frozen=True)
class SKRDefaults:
    eta_det: float = DEFAULT_ETA_DET
    l_link_km: float = DEFAULT_L_LINK_KM
    l_aperture_m: float = DEFAULT_L_APERTURE_M
    v_a: float = DEFAULT_VA
    beta: float = DEFAULT_BETA


def _g(x: Union[np.ndarray, float]) -> np.ndarray:
    values = np.asarray(x, dtype=float)
    values = np.maximum(values, 1.0 + EPS)
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((values + 1.0) / 2.0) * np.log2((values + 1.0) / 2.0) - ((values - 1.0) / 2.0) * np.log2((values - 1.0) / 2.0)


def compute_skr_gaussian(
    l_link_km: Union[np.ndarray, float],
    l_aperture_m: Union[np.ndarray, float],
    v_a: Union[np.ndarray, float],
    eta_det: Union[np.ndarray, float],
    beta: Union[np.ndarray, float],
    *,
    xi_km_inv: float = XI_KM_INV,
    w0_m: float = W0_M,
    wavelength_m: float = WAVELENGTH_M,
    eps_ch: float = EPS_CH,
    v_el: float = V_EL,
) -> Dict[str, np.ndarray]:
    l_link_km_arr = np.asarray(l_link_km, dtype=float)
    l_link_m = l_link_km_arr * 1000.0
    l_aperture_arr = np.asarray(l_aperture_m, dtype=float)
    v_a_arr = np.asarray(v_a, dtype=float)
    eta_det_arr = np.asarray(eta_det, dtype=float)
    beta_arr = np.asarray(beta, dtype=float)

    eta_atm = np.exp(-float(xi_km_inv) * l_link_km_arr)
    z_r = np.pi * float(w0_m) ** 2 / float(wavelength_m)
    w_l = float(w0_m) * np.sqrt(1.0 + (l_link_m / z_r) ** 2)
    arg = 2.0 * l_aperture_arr**2 / np.maximum(w_l**2, EPS)
    t0 = np.sqrt(np.maximum(1.0 - np.exp(-arg), 0.0))
    t_eff = np.maximum(eta_atm * t0**2, EPS)

    chi_hom = (1.0 - eta_det_arr) / np.maximum(eta_det_arr, EPS) + v_el / np.maximum(eta_det_arr, EPS)
    chi_line = 1.0 / t_eff - 1.0 + eps_ch
    chi_tot = chi_line + chi_hom / t_eff

    v = v_a_arr + 1.0
    i_ab = 0.5 * np.log2((v + chi_tot) / np.maximum(1.0 + chi_tot, EPS))

    a_term = v**2 * (1.0 - 2.0 * t_eff) + 2.0 * t_eff + t_eff**2 * (v + chi_line) ** 2
    b_term = t_eff**2 * (v * chi_line + 1.0) ** 2
    disc = np.maximum(a_term**2 - 4.0 * b_term, 0.0)
    lambda1 = np.sqrt(np.maximum((a_term + np.sqrt(disc)) / 2.0, 1.0 + EPS))
    lambda2 = np.sqrt(np.maximum((a_term - np.sqrt(disc)) / 2.0, 1.0 + EPS))
    lambda3_num = (v + chi_hom) * (v * chi_line + 1.0)
    lambda3_den = np.maximum((v + chi_line) * (1.0 + chi_hom), EPS)
    lambda3 = np.sqrt(np.maximum(lambda3_num / lambda3_den, 1.0 + EPS))

    chi_be = _g(lambda1) + _g(lambda2) - _g(lambda3)
    skr_raw = beta_arr * i_ab - chi_be
    skr = np.maximum(skr_raw, 0.0)

    return {
        "eta_atm": eta_atm,
        "z_R": np.asarray(z_r, dtype=float),
        "W_L": w_l,
        "T_0": t0,
        "T_eff": t_eff,
        "chi_hom": chi_hom,
        "chi_line": chi_line,
        "chi_tot": chi_tot,
        "I_AB": i_ab,
        "lambda1": lambda1,
        "lambda2": lambda2,
        "lambda3": lambda3,
        "chi_BE": chi_be,
        "SKR_raw": skr_raw,
        "SKR": skr,
    }


def _annotate_default(ax: plt.Axes, x_value: float, y_value: float) -> None:
    ax.scatter([x_value], [y_value], marker="*", s=160, color="red", edgecolor="white", linewidth=0.6, zorder=5)


def _plot_curve(
    ax: plt.Axes,
    x_values: np.ndarray,
    y_values: np.ndarray,
    default_x: float,
    default_y: float,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    legend_label: str,
) -> None:
    ax.plot(x_values, y_values, color="#1f77b4", linewidth=2.2, label=legend_label)
    ax.axhline(0.0, color="red", linestyle="--", linewidth=1.4, label="SKR = 0")
    _annotate_default(ax, default_x, default_y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.32)
    ax.legend(loc="best", frameon=True)


def plot_skr_sweeps(
    output_path: Optional[Union[str, Path]] = None,
    defaults: SKRDefaults = SKRDefaults(),
    *,
    dpi: int = 300,
) -> tuple[plt.Figure, Dict[str, Any]]:
    fig, axes = plt.subplots(5, 1, figsize=(9.0, 18.0), sharex=False, constrained_layout=True)
    fig.suptitle("CV-QKD Gaussian SKR Sweeps for UAV–HAP Link", fontsize=15, fontweight="bold")

    default_skr = float(
        compute_skr_gaussian(
            defaults.l_link_km,
            defaults.l_aperture_m,
            defaults.v_a,
            defaults.eta_det,
            defaults.beta,
        )["SKR"]
    )

    eta_curve = compute_skr_gaussian(
        l_link_km=defaults.l_link_km,
        l_aperture_m=defaults.l_aperture_m,
        v_a=defaults.v_a,
        eta_det=ETA_DET_RANGE,
        beta=defaults.beta,
    )
    _plot_curve(
        axes[0],
        ETA_DET_RANGE,
        eta_curve["SKR"],
        defaults.eta_det,
        default_skr,
        xlabel=r"Detector efficiency $\eta_{det}$",
        ylabel="SKR (bits/pulse)",
        title="SKR vs Detector Efficiency",
        legend_label="SKR",
    )

    link_curve = compute_skr_gaussian(
        l_link_km=L_LINK_RANGE_KM,
        l_aperture_m=defaults.l_aperture_m,
        v_a=defaults.v_a,
        eta_det=defaults.eta_det,
        beta=defaults.beta,
    )
    _plot_curve(
        axes[1],
        L_LINK_RANGE_KM,
        link_curve["SKR"],
        defaults.l_link_km,
        default_skr,
        xlabel="Link distance $L_{link}$ (km)",
        ylabel="SKR (bits/pulse)",
        title="SKR vs UAV–HAP Link Distance",
        legend_label="SKR",
    )

    aperture_curve = compute_skr_gaussian(
        l_link_km=defaults.l_link_km,
        l_aperture_m=L_APERTURE_RANGE_M,
        v_a=defaults.v_a,
        eta_det=defaults.eta_det,
        beta=defaults.beta,
    )
    _plot_curve(
        axes[2],
        L_APERTURE_RANGE_M * 100.0,
        aperture_curve["SKR"],
        defaults.l_aperture_m * 100.0,
        default_skr,
        xlabel="Aperture radius $L_{aperture}$ (cm)",
        ylabel="SKR (bits/pulse)",
        title="SKR vs Receiver Aperture Radius",
        legend_label="SKR",
    )

    va_curve = compute_skr_gaussian(
        l_link_km=defaults.l_link_km,
        l_aperture_m=defaults.l_aperture_m,
        v_a=VA_RANGE,
        eta_det=defaults.eta_det,
        beta=defaults.beta,
    )
    _plot_curve(
        axes[3],
        VA_RANGE,
        va_curve["SKR"],
        defaults.v_a,
        default_skr,
        xlabel="Modulation variance $V_A$ (SNU)",
        ylabel="SKR (bits/pulse)",
        title="SKR vs Modulation Variance",
        legend_label="SKR",
    )

    beta_curve = compute_skr_gaussian(
        l_link_km=defaults.l_link_km,
        l_aperture_m=defaults.l_aperture_m,
        v_a=defaults.v_a,
        eta_det=defaults.eta_det,
        beta=BETA_RANGE,
    )
    _plot_curve(
        axes[4],
        BETA_RANGE,
        beta_curve["SKR"],
        defaults.beta,
        default_skr,
        xlabel=r"Reconciliation efficiency $\beta$",
        ylabel="SKR (bits/pulse)",
        title="SKR vs Reconciliation Efficiency",
        legend_label="SKR",
    )

    for ax in axes:
        ax.set_ylim(bottom=0.0)

    if output_path is None:
        output_path = Path(__file__).resolve().parents[1] / "outputs" / "skr_gaussian_uav_hap_sweeps.png"
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    return fig, {
        "output_path": str(output_path),
        "defaults": defaults,
        "curves": {
            "eta_det": eta_curve,
            "L_link_km": link_curve,
            "L_aperture_m": aperture_curve,
            "V_A": va_curve,
            "beta": beta_curve,
        },
    }


def example_usage(show: bool = True) -> str:
    fig, result = plot_skr_sweeps()
    if show:
        plt.show()
    plt.close(fig)
    return result["output_path"]
