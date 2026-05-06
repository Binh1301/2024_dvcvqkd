from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

import matplotlib

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from scipy.special import i0, i1

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.linestyle": ":",
        "grid.color": "#aaaaaa",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "lines.linewidth": 2.0,
        "lines.markersize": 5,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)

COLORS = {
    "black": "#000000",
    "yellow": "#E6A817",
    "blue": "#2166AC",
    "red": "#D6604D",
    "green": "#1A9641",
    "purple": "#762A83",
}

LINESTYLES = {
    "solid": "-",
    "dashed": "--",
    "dashdot": "-.",
    "dotted": ":",
}


XI_KM_INV = 0.09232
W0_M = 0.0626
WAVELENGTH_M = 1550e-9

SIGMA_X_M = 0.0521
SIGMA_Y_M = 0.0502
SIGMA_Z_M = 0.0703
SIGMA_TH_RAD = 2.60e-3
SIGMA_PH_RAD = 2.04e-3
SIGMA_PS_RAD = 4.06e-3

CN2 = 1e-15
EPS_CH = 0.01
V_EL = 0.01

N_SAMPLES = 30_000

DEFAULT_ETA_DET = 0.97
DEFAULT_L_LINK_KM = 20.0
DEFAULT_L_APERTURE_M = 0.20
DEFAULT_VA = 2.0
DEFAULT_BETA = 0.95

ETA_DET_RANGE = np.arange(0.60, 1.00 + 1e-12, 0.05)
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


def _kruse_q_parameter(visibility_km: float) -> float:
    v = float(visibility_km)
    if v > 50.0:
        return 1.6
    if 6.0 < v <= 50.0:
        return 1.3
    return 0.585 * np.cbrt(max(v, EPS))


def _kruse_xi_per_km(visibility_km: float, wavelength_m: float) -> float:
    v = max(float(visibility_km), EPS)
    lambda_nm = max(float(wavelength_m), EPS) * 1e9
    q_v = _kruse_q_parameter(v)
    return float((3.912 / v) * (lambda_nm / 550.0) ** (-q_v))


def _g_lambda(x: Union[np.ndarray, float]) -> np.ndarray:
    values = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(
            values <= 1.0 + 1e-10,
            0.0,
            ((values + 1.0) / 2.0) * np.log2((values + 1.0) / 2.0)
            - ((values - 1.0) / 2.0) * np.log2((values - 1.0) / 2.0),
        )


def _compute_one(
    l_link_km: float,
    l_aperture_m: float,
    v_a: float,
    eta_det: float,
    beta: float,
    *,
    xi_km_inv: Optional[float],
    visibility_km: float,
    w0_m: float,
    wavelength_m: float,
    cn2: float,
    sigma_x_m: float,
    sigma_y_m: float,
    sigma_z_m: float,
    sigma_th_rad: float,
    sigma_ph_rad: float,
    sigma_ps_rad: float,
    eps_ch: float,
    v_el: float,
    n_samples: int,
    seed: int,
    sigma_r_override_m: Optional[float] = None,
) -> Dict[str, float]:
    rng = np.random.default_rng(int(seed))
    l_link_m = float(l_link_km) * 1000.0
    a = max(float(l_aperture_m), EPS)
    w0 = max(float(w0_m), EPS)
    wavelength = max(float(wavelength_m), EPS)

    # Step 1
    xi_use = float(xi_km_inv) if xi_km_inv is not None else _kruse_xi_per_km(visibility_km, wavelength)
    eta_atm = float(np.exp(-xi_use * float(l_link_km)))

    # Step 2-4
    z_r = np.pi * w0**2 / wavelength
    w_l = w0 * np.sqrt(1.0 + (l_link_m / max(z_r, EPS)) ** 2)
    arg = 2.0 * a**2 / max(w_l**2, EPS)
    t0 = float(np.sqrt(np.clip(1.0 - np.exp(-arg), 0.0, 1.0)))

    # Step 5-9
    sigma2_pos = float(sigma_x_m) ** 2 + float(sigma_y_m) ** 2 + float(sigma_z_m) ** 2
    sigma2_orient = float(sigma_th_rad) ** 2 + float(sigma_ph_rad) ** 2 + float(sigma_ps_rad) ** 2
    sigma2_uav = sigma2_pos + a**2 * sigma2_orient
    sigma2_turb = 1.919 * float(cn2) * l_link_m**3 * (2.0 * w0) ** (-1.0 / 3.0)
    sigma2_r = float(sigma2_turb + sigma2_uav)
    if sigma_r_override_m is not None:
        sigma2_r = float(max(float(sigma_r_override_m), 0.0) ** 2)

    # Step 10-12
    x = (2.0 * a / max(w_l, EPS)) ** 2
    ex = float(np.exp(-x))
    ex_i0 = ex * float(i0(x))
    ex_i1 = ex * float(i1(x))
    term = max(1.0 - ex_i0, EPS)
    ratio = max(2.0 * t0**2 / term, 1.0 + EPS)
    ln_ratio = max(float(np.log(ratio)), EPS)
    numerator = 2.0 * x * ex_i1
    denominator = max(term * ln_ratio, EPS)
    gamma = max(float(numerator / denominator), EPS)
    r_scale = float(a / (ln_ratio ** (1.0 / gamma)))

    # Step 13
    sigma_s = float(np.sqrt(max(sigma2_r / 2.0, 0.0)))
    if sigma_s > EPS:
        r_samples = rng.rayleigh(scale=sigma_s, size=int(max(n_samples, 1)))
    else:
        r_samples = np.zeros(int(max(n_samples, 1)), dtype=float)
    t_samples = t0 * np.sqrt(np.exp(-np.power(np.maximum(r_samples, 0.0) / max(r_scale, EPS), gamma)))
    mean_t2 = float(np.mean(t_samples**2))

    # Step 14-18
    t_eff = float(eta_atm * mean_t2)
    chi_hom = float((1.0 - eta_det) / max(eta_det, EPS) + float(v_el) / max(eta_det, EPS))
    chi_line = float(1.0 / max(t_eff, EPS) - 1.0 + float(eps_ch))
    chi_tot = float(chi_line + chi_hom / max(t_eff, EPS))
    V = float(v_a) + 1.0
    i_ab = float(0.5 * np.log2((V + chi_tot) / max(1.0 + chi_tot, EPS)))

    # Step 19-20
    A = V**2 * (1.0 - 2.0 * t_eff) + 2.0 * t_eff + t_eff**2 * (V + chi_line) ** 2
    B = t_eff**2 * (V * chi_line + 1.0) ** 2
    disc = max(A**2 - 4.0 * B, 0.0)
    lambda1 = float(np.sqrt(max(0.5 * (A + np.sqrt(disc)), EPS)))
    lambda2 = float(np.sqrt(max(0.5 * (A - np.sqrt(disc)), EPS)))
    lambda3 = float(
        np.sqrt(
            max(
                ((V + chi_hom) * (V * chi_line + 1.0))
                / max((V + chi_line) * (1.0 + chi_hom), EPS),
                EPS,
            )
        )
    )

    # Step 22-23
    chi_be = float(_g_lambda(lambda1) + _g_lambda(lambda2) - _g_lambda(lambda3))
    skr_raw = float(beta * i_ab - chi_be)
    skr = max(skr_raw, 0.0)

    return {
        "L_link_m": float(l_link_m),
        "xi_km_inv": xi_use,
        "eta_atm": eta_atm,
        "z_R": float(z_r),
        "W_L": float(w_l),
        "T_0": t0,
        "sigma2_pos": float(sigma2_pos),
        "sigma2_orient": float(sigma2_orient),
        "sigma2_UAV": float(sigma2_uav),
        "sigma2_turb": float(sigma2_turb),
        "sigma2_r": float(sigma2_r),
        "sigma_r": float(np.sqrt(max(sigma2_r, 0.0))),
        "x": float(x),
        "Gamma": float(gamma),
        "R": float(r_scale),
        "mean_T2": float(mean_t2),
        "T_eff": float(t_eff),
        "chi_hom": float(chi_hom),
        "chi_line": float(chi_line),
        "chi_tot": float(chi_tot),
        "I_AB": float(i_ab),
        "lambda1": float(lambda1),
        "lambda2": float(lambda2),
        "lambda3": float(lambda3),
        "chi_BE": float(chi_be),
        "SKR_raw": float(skr_raw),
        "SKR": float(skr),
    }


def compute_skr_gaussian(
    l_link_km: Union[np.ndarray, float],
    l_aperture_m: Union[np.ndarray, float],
    v_a: Union[np.ndarray, float],
    eta_det: Union[np.ndarray, float],
    beta: Union[np.ndarray, float],
    *,
    xi_km_inv: Optional[float] = XI_KM_INV,
    visibility_km: float = 10.0,
    w0_m: float = W0_M,
    wavelength_m: float = WAVELENGTH_M,
    cn2: float = CN2,
    sigma_x_m: float = SIGMA_X_M,
    sigma_y_m: float = SIGMA_Y_M,
    sigma_z_m: float = SIGMA_Z_M,
    sigma_th_rad: float = SIGMA_TH_RAD,
    sigma_ph_rad: float = SIGMA_PH_RAD,
    sigma_ps_rad: float = SIGMA_PS_RAD,
    eps_ch: float = EPS_CH,
    v_el: float = V_EL,
    n_samples: int = N_SAMPLES,
    seed: int = 42,
    sigma_r_override_m: Optional[float] = None,
) -> Dict[str, np.ndarray]:
    arrays = np.broadcast_arrays(
        np.asarray(l_link_km, dtype=float),
        np.asarray(l_aperture_m, dtype=float),
        np.asarray(v_a, dtype=float),
        np.asarray(eta_det, dtype=float),
        np.asarray(beta, dtype=float),
    )
    shape = arrays[0].shape
    total = int(np.prod(shape, dtype=int))

    keys = [
        "L_link_m",
        "xi_km_inv",
        "eta_atm",
        "z_R",
        "W_L",
        "T_0",
        "sigma2_pos",
        "sigma2_orient",
        "sigma2_UAV",
        "sigma2_turb",
        "sigma2_r",
        "sigma_r",
        "x",
        "Gamma",
        "R",
        "mean_T2",
        "T_eff",
        "chi_hom",
        "chi_line",
        "chi_tot",
        "I_AB",
        "lambda1",
        "lambda2",
        "lambda3",
        "chi_BE",
        "SKR_raw",
        "SKR",
    ]
    out_flat = {k: np.empty(total, dtype=float) for k in keys}

    flat = [arr.reshape(-1) for arr in arrays]
    for idx in range(total):
        one = _compute_one(
            l_link_km=float(flat[0][idx]),
            l_aperture_m=float(flat[1][idx]),
            v_a=float(flat[2][idx]),
            eta_det=float(flat[3][idx]),
            beta=float(flat[4][idx]),
            xi_km_inv=xi_km_inv,
            visibility_km=visibility_km,
            w0_m=w0_m,
            wavelength_m=wavelength_m,
            cn2=cn2,
            sigma_x_m=sigma_x_m,
            sigma_y_m=sigma_y_m,
            sigma_z_m=sigma_z_m,
            sigma_th_rad=sigma_th_rad,
            sigma_ph_rad=sigma_ph_rad,
            sigma_ps_rad=sigma_ps_rad,
            eps_ch=eps_ch,
            v_el=v_el,
            n_samples=n_samples,
            seed=int(seed) + idx,
            sigma_r_override_m=sigma_r_override_m,
        )
        for k in keys:
            out_flat[k][idx] = one[k]

    return {k: out_flat[k].reshape(shape) for k in keys}


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
    fig.suptitle("CV-QKD Gaussian SKR Sweeps for UAV-HAP Link", fontsize=15, fontweight="bold")

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
        title="SKR vs UAV-HAP Link Distance",
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


def compute_skr(params: Mapping[str, float]) -> Dict[str, float]:
    """
    Scalar SKR pipeline interface from a parameter dictionary.
    Required core fields can be overridden in `params`.
    """
    base = {
        "L_link_m": 20e3,
        "a_m": 0.20,
        "VA": 2.0,
        "eta_det": 0.97,
        "beta": 0.95,
        "xi_km_inv": XI_KM_INV,
        "visibility_km": 10.0,
        "W0_m": W0_M,
        "lambda_m": WAVELENGTH_M,
        "Cn2": CN2,
        "sigma_x_m": SIGMA_X_M,
        "sigma_y_m": SIGMA_Y_M,
        "sigma_z_m": SIGMA_Z_M,
        "sigma_th_rad": SIGMA_TH_RAD,
        "sigma_ph_rad": SIGMA_PH_RAD,
        "sigma_ps_rad": SIGMA_PS_RAD,
        "epsilon_ch": EPS_CH,
        "v_el": V_EL,
        "N_samples": N_SAMPLES,
        "seed": 42,
        "sigma_r_override_m": None,
    }
    base.update(dict(params))

    out = compute_skr_gaussian(
        l_link_km=float(base["L_link_m"]) / 1e3,
        l_aperture_m=float(base["a_m"]),
        v_a=float(base["VA"]),
        eta_det=float(base["eta_det"]),
        beta=float(base["beta"]),
        xi_km_inv=base["xi_km_inv"],
        visibility_km=float(base["visibility_km"]),
        w0_m=float(base["W0_m"]),
        wavelength_m=float(base["lambda_m"]),
        cn2=float(base["Cn2"]),
        sigma_x_m=float(base["sigma_x_m"]),
        sigma_y_m=float(base["sigma_y_m"]),
        sigma_z_m=float(base["sigma_z_m"]),
        sigma_th_rad=float(base["sigma_th_rad"]),
        sigma_ph_rad=float(base["sigma_ph_rad"]),
        sigma_ps_rad=float(base["sigma_ps_rad"]),
        eps_ch=float(base["epsilon_ch"]),
        v_el=float(base["v_el"]),
        n_samples=int(base["N_samples"]),
        seed=int(base["seed"]),
        sigma_r_override_m=base["sigma_r_override_m"],
    )
    return {k: float(np.asarray(v).reshape(-1)[0]) for k, v in out.items()}


def debug_reference_case(seed: int = 42, n_samples: int = 30_000) -> Dict[str, float]:
    vals = compute_skr(
        {
            "L_link_m": 20e3,
            "Cn2": 1e-15,
            "VA": 2.0,
            "beta": 0.95,
            "eta_det": 0.97,
            "N_samples": int(n_samples),
            "seed": int(seed),
            "epsilon_ch": 0.01,
            "v_el": 0.01,
            "xi_km_inv": 0.09232,
            "W0_m": 0.0626,
            "a_m": 0.20,
            "lambda_m": 1550e-9,
            "sigma_x_m": 0.0521,
            "sigma_y_m": 0.0502,
            "sigma_z_m": 0.0703,
            "sigma_th_rad": 2.60e-3,
            "sigma_ph_rad": 2.04e-3,
            "sigma_ps_rad": 4.06e-3,
        }
    )
    print(f"eta_atm   = {vals['eta_atm']:.5f}   | chuẩn = 0.15780")
    print(f"z_R       = {vals['z_R']:.2f} m    | chuẩn = 7942.68 m")
    print(f"W_L       = {vals['W_L']:.5f} m    | chuẩn = 0.16960 m")
    print(f"T0        = {vals['T_0']:.5f}       | chuẩn = 0.96852")
    print(f"sigma2_turb = {vals['sigma2_turb']:.6f} m² | chuẩn = 0.030688")
    print(f"sigma2_UAV  = {vals['sigma2_UAV']:.6f} m² | chuẩn = 0.010178")
    print(f"sigma2_r    = {vals['sigma2_r']:.6f} m²   | chuẩn = 0.040866")
    print(f"Gamma     = {vals['Gamma']:.4f}    | chuẩn = 2.5779")
    print(f"R         = {vals['R']:.5f} m      | chuẩn = ~0.17 m")
    print(f"mean_T2   = {vals['mean_T2']:.5f}  | chuẩn = 0.51995")
    print(f"T_eff     = {vals['T_eff']:.5f}    | chuẩn = 0.08205")
    print(f"chi_hom   = {vals['chi_hom']:.6f}  | chuẩn = 0.041237")
    print(f"chi_line  = {vals['chi_line']:.4f} | chuẩn = 11.1976")
    print(f"chi_tot   = {vals['chi_tot']:.4f}  | chuẩn = 11.7002")
    print(f"IAB       = {vals['I_AB']:.5f}      | chuẩn = 0.10519")
    print(f"lambda3   = {vals['lambda3']:.4f}  | chuẩn = 2.668")
    print(f"chi_BE    = {vals['chi_BE']:.4f}   | chuẩn = 0.094")
    print(f"SKR       = {vals['SKR_raw']:.5f}      | chuẩn = 0.00593")
    return vals


def _plot_style() -> None:
    pass


def _apply_publication_ticks(ax: plt.Axes) -> None:
    if ax.get_xscale() == "linear":
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    if ax.get_yscale() == "linear":
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())


def _safe_contour_level(z_values: np.ndarray, desired: float = 1e-6) -> Optional[float]:
    z = np.asarray(z_values, dtype=float)
    z_min = float(np.nanmin(z))
    z_max = float(np.nanmax(z))
    if z_min <= desired <= z_max:
        return desired
    if z_min <= 0.0 <= z_max:
        return 0.0
    return None


def _finalize_and_save(fig: plt.Figure, path: Path, show: bool) -> None:
    fig.tight_layout()
    fig.savefig(path)
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_1_skr_vs_distance(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: str = "plot1_SKR_vs_L.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    l_values = np.linspace(10e3, 25e3, 60)
    skr_raw = np.zeros_like(l_values)

    for i, l_m in enumerate(l_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        skr_raw[i] = out["SKR_raw"]
    skr_values = np.maximum(skr_raw, 1e-8)

    non_pos = np.where(skr_raw <= 0.0)[0]
    l_max_km = float(l_values[non_pos[0]] / 1e3) if non_pos.size > 0 else float(l_values[-1] / 1e3)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.semilogy(l_values / 1e3, skr_values, color=COLORS["black"], lw=2, label="SKR (asymptotic)")
    ax.axhline(1e-8, color="gray", lw=0.8, ls=":")
    ax.axvline(
        l_max_km,
        color=COLORS["red"],
        lw=1.2,
        ls=LINESTYLES["dashed"],
        label=rf"$L_{{max}}$ ≈ {l_max_km:.1f} km",
    )
    ax.set_xlabel("Satellite Altitude / Link Distance [km]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title("Secret Key Rate vs Link Distance")
    ax.set_xlim([10, 25])
    ax.set_ylim([1e-6, 1])
    info = (
        f"$C_n^2 = {float(params.get('Cn2', CN2)):.1e}$ m$^{{-2/3}}$\n"
        f"$V_A = {float(params.get('VA', 2.0)):.0f}$ SNU\n"
        f"$\\beta = {float(params.get('beta', 0.95)):.2f}$"
    )
    ax.text(
        0.97,
        0.97,
        info,
        transform=ax.transAxes,
        fontsize=9,
        va="top",
        ha="right",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "gray", "alpha": 0.8},
    )
    _apply_publication_ticks(ax)
    ax.legend(loc="upper right", framealpha=0.9)

    _finalize_and_save(fig, Path(save_path), show)
    return {"L_values_m": l_values, "SKR_values": skr_raw, "L_max_km": l_max_km, "save_path": str(Path(save_path))}


def plot_2_skr_vs_va(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: str = "plot2_SKR_vs_VA.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    params["L_link_m"] = float(params.get("L_link_m", 20e3))
    va_values = np.linspace(0.5, 15.0, 100)
    skr_values = np.zeros_like(va_values)

    for i, va in enumerate(va_values):
        p = dict(params)
        p["VA"] = float(va)
        p["seed"] = int(params.get("seed", 42)) + i
        skr_values[i] = compute_skr(p)["SKR_raw"]

    idx = int(np.argmax(skr_values))
    va_opt = float(va_values[idx])

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(va_values, skr_values, color=COLORS["yellow"], lw=2, label="SKR (Gaussian)")
    ax.axvline(
        va_opt,
        color=COLORS["red"],
        lw=1.2,
        ls=LINESTYLES["dashed"],
        label=rf"$V_A^{{opt}}$ = {va_opt:.2f} SNU",
    )
    ax.set_xlabel(r"Modulation Variance $V_A$ [SNU]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title(r"SKR vs Modulation Variance at $L = 20$ km")
    ax.set_xlim([0, 15])
    _apply_publication_ticks(ax)
    ax.legend(framealpha=0.9)

    _finalize_and_save(fig, Path(save_path), show)
    return {"VA_values": va_values, "SKR_values": skr_values, "VA_opt": va_opt, "save_path": str(Path(save_path))}


def plot_3_skr_vs_cn2(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: str = "plot3_SKR_vs_Cn2.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    cn2_values = np.logspace(-17, -14, 60)
    skr_values_l20 = np.zeros_like(cn2_values)
    skr_values_l15 = np.zeros_like(cn2_values)

    for i, cn2 in enumerate(cn2_values):
        p20 = dict(params)
        p20["L_link_m"] = 20e3
        p20["Cn2"] = float(cn2)
        p20["seed"] = int(params.get("seed", 42)) + i
        skr_values_l20[i] = compute_skr(p20)["SKR_raw"]

        p15 = dict(params)
        p15["L_link_m"] = 15e3
        p15["Cn2"] = float(cn2)
        p15["seed"] = int(params.get("seed", 42)) + 1000 + i
        skr_values_l15[i] = compute_skr(p15)["SKR_raw"]

    neg_idx = np.where(skr_values_l20 <= 0.0)[0]
    cn2_max = float(cn2_values[neg_idx[0]]) if neg_idx.size > 0 else None

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.semilogx(cn2_values, skr_values_l20, color=COLORS["yellow"], lw=2, label=r"$L = 20$ km")
    ax.semilogx(
        cn2_values,
        skr_values_l15,
        color=COLORS["blue"],
        lw=2,
        ls=LINESTYLES["dashed"],
        label=r"$L = 15$ km",
    )
    ax.axhline(0, color="gray", lw=0.8, ls=LINESTYLES["dashed"])
    if cn2_max is not None:
        ax.axvspan(cn2_max, cn2_values[-1], alpha=0.12, color=COLORS["red"], label="SKR < 0")

    ax.set_xlabel(r"Turbulence Strength $C_n^2$ [m$^{-2/3}$]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title(r"SKR vs Atmospheric Turbulence at $L = 20$ km")
    _apply_publication_ticks(ax)
    ax.legend(framealpha=0.9)

    _finalize_and_save(fig, Path(save_path), show)
    return {
        "Cn2_values": cn2_values,
        "SKR_values_L20": skr_values_l20,
        "SKR_values_L15": skr_values_l15,
        "Cn2_max": cn2_max,
        "save_path": str(Path(save_path)),
    }


def plot_4_loss_decomposition(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: str = "plot4_loss.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    l_values = np.linspace(5e3, 30e3, 80)
    eta_atm_list = np.zeros_like(l_values)
    mean_t2_list = np.zeros_like(l_values)
    t_eff_list = np.zeros_like(l_values)
    for i, l_m in enumerate(l_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        eta_atm_list[i] = out["eta_atm"]
        mean_t2_list[i] = out["mean_T2"]
        t_eff_list[i] = out["T_eff"]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(
        l_values / 1e3,
        10 * np.log10(np.maximum(eta_atm_list, 1e-20)),
        color=COLORS["black"],
        lw=2,
        ls=LINESTYLES["solid"],
        label=r"$\eta_{atm}$ (Beer–Lambert)",
    )
    ax.plot(
        l_values / 1e3,
        10 * np.log10(np.maximum(mean_t2_list, 1e-20)),
        color=COLORS["blue"],
        lw=2,
        ls=LINESTYLES["dashed"],
        label=r"$\langle T^2 \rangle$ (pointing + turbulence)",
    )
    ax.plot(
        l_values / 1e3,
        10 * np.log10(np.maximum(t_eff_list, 1e-20)),
        color=COLORS["red"],
        lw=2.5,
        ls=LINESTYLES["solid"],
        label=r"$T_{eff} = \eta_{atm} \cdot \langle T^2 \rangle$",
    )
    ax.set_xlabel("Link Distance [km]")
    ax.set_ylabel("Attenuation [dB]")
    ax.set_title("Channel Loss Breakdown")
    _apply_publication_ticks(ax)
    ax.legend(framealpha=0.9, loc="lower left")

    _finalize_and_save(fig, Path(save_path), show)
    return {
        "L_values_m": l_values,
        "eta_atm_list": eta_atm_list,
        "mean_T2_list": mean_t2_list,
        "T_eff_list": t_eff_list,
        "save_path": str(Path(save_path)),
    }


def plot_5_skr_vs_sigma_r(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: str = "plot5_SKR_vs_sigma.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    sigma_r_values = np.linspace(0.01, 0.30, 80)
    l_list = [15e3, 20e3]
    curves: Dict[str, np.ndarray] = {}

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for idx_l, l_m in enumerate(l_list):
        skr_list = np.zeros_like(sigma_r_values)
        for i, sigma_r in enumerate(sigma_r_values):
            p = dict(params)
            p["L_link_m"] = float(l_m)
            p["sigma_r_override_m"] = float(sigma_r)
            p["seed"] = int(params.get("seed", 42)) + idx_l * 1000 + i
            skr_list[i] = compute_skr(p)["SKR_raw"]
        curves[f"L_{int(l_m/1e3)}km"] = skr_list
        ax.plot(
            sigma_r_values * 100.0,
            skr_list,
            lw=2,
            color=COLORS["blue"] if idx_l == 0 else COLORS["yellow"],
            ls=LINESTYLES["solid"] if idx_l == 0 else LINESTYLES["dashed"],
            label=rf"$L = {l_m/1e3:.0f}$ km",
        )

    ax.axhline(0, color="gray", lw=0.8, ls=LINESTYLES["dashed"])
    ax.set_xlabel(r"Pointing Error Std. Dev. $\sigma_r$ [cm]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title("Effect of Pointing Error on SKR")
    _apply_publication_ticks(ax)
    ax.legend(framealpha=0.9)

    _finalize_and_save(fig, Path(save_path), show)
    return {"sigma_r_values_m": sigma_r_values, "curves": curves, "save_path": str(Path(save_path))}


def plot_6_skr_heatmap(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: str = "plot6_heatmap.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    l_arr = np.linspace(10e3, 30e3, 30)
    cn2_arr = np.logspace(-17, -14, 30)
    skr_matrix = np.zeros((len(cn2_arr), len(l_arr)), dtype=float)

    for i, cn2 in enumerate(cn2_arr):
        for j, l_m in enumerate(l_arr):
            p = dict(params)
            p["Cn2"] = float(cn2)
            p["L_link_m"] = float(l_m)
            p["seed"] = int(params.get("seed", 42)) + i * len(l_arr) + j
            skr_matrix[i, j] = compute_skr(p)["SKR_raw"]

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.pcolormesh(
        l_arr / 1e3,
        np.log10(cn2_arr),
        skr_matrix,
        cmap="viridis",
        shading="auto",
        vmin=0,
        vmax=max(float(np.nanmax(skr_matrix)), 1e-8),
    )
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("SKR [bits/pulse]", fontsize=11)

    level = _safe_contour_level(skr_matrix, desired=1e-6)
    if level is not None:
        cs = ax.contour(
            l_arr / 1e3,
            np.log10(cn2_arr),
            skr_matrix,
            levels=[level],
            colors=[COLORS["red"]],
            linewidths=2,
        )
        ax.clabel(cs, fmt="SKR = 0", fontsize=9)

    ax.plot(
        20,
        np.log10(1e-15),
        "*",
        color=COLORS["red"],
        markersize=12,
        label="Operating point\n($L=20$ km, $C_n^2=10^{-15}$)",
    )
    ax.set_xlabel("Link Distance [km]")
    ax.set_ylabel(r"$\log_{10}(C_n^2)$ [m$^{-2/3}$]")
    ax.set_title("SKR Feasibility Map")
    _apply_publication_ticks(ax)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

    _finalize_and_save(fig, Path(save_path), show)
    return {"L_arr_m": l_arr, "Cn2_arr": cn2_arr, "SKR_matrix": skr_matrix, "save_path": str(Path(save_path))}


def plot_all_skr_figures(
    base_params: Optional[Mapping[str, float]] = None,
    output_dir: Union[str, Path] = ".",
    show: bool = True,
) -> Dict[str, Any]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    params = dict(base_params or {})
    results = {
        "plot_1": plot_1_skr_vs_distance(params, save_path=str(out_dir / "plot1_SKR_vs_L.png"), show=show),
        "plot_2": plot_2_skr_vs_va(params, save_path=str(out_dir / "plot2_SKR_vs_VA.png"), show=show),
        "plot_3": plot_3_skr_vs_cn2(params, save_path=str(out_dir / "plot3_SKR_vs_Cn2.png"), show=show),
        "plot_4": plot_4_loss_decomposition(params, save_path=str(out_dir / "plot4_loss.png"), show=show),
        "plot_5": plot_5_skr_vs_sigma_r(params, save_path=str(out_dir / "plot5_SKR_vs_sigma.png"), show=show),
        "plot_6": plot_6_skr_heatmap(params, save_path=str(out_dir / "plot6_heatmap.png"), show=show),
    }
    return results


def plot_all_skr_figures_combined(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: Union[str, Path] = "CV_QKD_all_plots.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.patch.set_facecolor("white")
    fig.suptitle("CV-QKD UAV–HAP — Performance Analysis", fontsize=14, fontweight="normal", y=1.01)

    # Plot 1
    l_values = np.linspace(10e3, 25e3, 60)
    skr_raw = np.zeros_like(l_values)
    for i, l_m in enumerate(l_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        skr_raw[i] = out["SKR_raw"]
    skr_values = np.maximum(skr_raw, 1e-8)
    non_pos = np.where(skr_raw <= 0.0)[0]
    l_max_km = float(l_values[non_pos[0]] / 1e3) if non_pos.size > 0 else float(l_values[-1] / 1e3)
    ax = axes[0, 0]
    ax.semilogy(l_values / 1e3, skr_values, color=COLORS["black"], lw=2)
    ax.axhline(1e-8, color="gray", lw=0.8, ls=LINESTYLES["dotted"])
    ax.axvline(l_max_km, color=COLORS["red"], lw=1.2, ls=LINESTYLES["dashed"])
    ax.set_xlabel("Satellite Altitude / Link Distance [km]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title("Secret Key Rate vs Link Distance")
    ax.set_xlim([10, 25])
    ax.set_ylim([1e-6, 1])
    _apply_publication_ticks(ax)

    # Plot 2
    va_values = np.linspace(0.5, 15.0, 100)
    va_skr = np.zeros_like(va_values)
    for i, va in enumerate(va_values):
        p = dict(params)
        p["L_link_m"] = float(params.get("L_link_m", 20e3))
        p["VA"] = float(va)
        p["seed"] = int(params.get("seed", 42)) + 1000 + i
        va_skr[i] = max(compute_skr(p)["SKR_raw"], 0.0)
    va_opt = float(va_values[int(np.argmax(va_skr))])
    ax = axes[0, 1]
    ax.plot(va_values, va_skr, color=COLORS["yellow"], lw=2)
    ax.axvline(va_opt, color=COLORS["red"], lw=1.2, ls=LINESTYLES["dashed"])
    ax.set_xlabel(r"Modulation Variance $V_A$ [SNU]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title(r"SKR vs Modulation Variance at $L = 20$ km")
    ax.set_xlim([0, 15])
    _apply_publication_ticks(ax)

    # Plot 3
    cn2_values = np.logspace(-17, -14, 60)
    cn2_skr_l20 = np.zeros_like(cn2_values)
    cn2_skr_l15 = np.zeros_like(cn2_values)
    for i, cn2 in enumerate(cn2_values):
        p20 = dict(params)
        p20["L_link_m"] = 20e3
        p20["Cn2"] = float(cn2)
        p20["seed"] = int(params.get("seed", 42)) + 2000 + i
        cn2_skr_l20[i] = compute_skr(p20)["SKR_raw"]
        p15 = dict(params)
        p15["L_link_m"] = 15e3
        p15["Cn2"] = float(cn2)
        p15["seed"] = int(params.get("seed", 42)) + 3000 + i
        cn2_skr_l15[i] = compute_skr(p15)["SKR_raw"]
    neg = np.where(cn2_skr_l20 <= 0.0)[0]
    cn2_max = float(cn2_values[neg[0]]) if neg.size > 0 else None
    ax = axes[0, 2]
    ax.semilogx(cn2_values, cn2_skr_l20, color=COLORS["yellow"], lw=2, label=r"$L = 20$ km")
    ax.semilogx(cn2_values, cn2_skr_l15, color=COLORS["blue"], lw=2, ls=LINESTYLES["dashed"], label=r"$L = 15$ km")
    ax.axhline(0, color="gray", lw=0.8, ls=LINESTYLES["dashed"])
    if cn2_max is not None:
        ax.axvspan(cn2_max, cn2_values[-1], alpha=0.12, color=COLORS["red"])
    ax.set_xlabel(r"Turbulence Strength $C_n^2$ [m$^{-2/3}$]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title(r"SKR vs Atmospheric Turbulence at $L = 20$ km")
    _apply_publication_ticks(ax)
    ax.legend(framealpha=0.9)

    # Plot 4
    l2_values = np.linspace(5e3, 30e3, 80)
    eta_atm = np.zeros_like(l2_values)
    mean_t2 = np.zeros_like(l2_values)
    t_eff = np.zeros_like(l2_values)
    for i, l_m in enumerate(l2_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + 3000 + i
        out = compute_skr(p)
        eta_atm[i] = out["eta_atm"]
        mean_t2[i] = out["mean_T2"]
        t_eff[i] = out["T_eff"]
    ax = axes[1, 0]
    ax.plot(l2_values / 1e3, 10 * np.log10(np.maximum(eta_atm, 1e-20)), color=COLORS["black"], lw=2, ls=LINESTYLES["solid"])
    ax.plot(l2_values / 1e3, 10 * np.log10(np.maximum(mean_t2, 1e-20)), color=COLORS["blue"], lw=2, ls=LINESTYLES["dashed"])
    ax.plot(l2_values / 1e3, 10 * np.log10(np.maximum(t_eff, 1e-20)), color=COLORS["red"], lw=2.5, ls=LINESTYLES["solid"])
    ax.set_xlabel("Link Distance [km]")
    ax.set_ylabel("Attenuation [dB]")
    ax.set_title("Channel Loss Breakdown")
    _apply_publication_ticks(ax)

    # Plot 5
    sigma_r_values = np.linspace(0.01, 0.30, 80)
    ax = axes[1, 1]
    for idx_l, l_m in enumerate([15e3, 20e3]):
        y = np.zeros_like(sigma_r_values)
        for i, sigma_r in enumerate(sigma_r_values):
            p = dict(params)
            p["L_link_m"] = float(l_m)
            p["sigma_r_override_m"] = float(sigma_r)
            p["seed"] = int(params.get("seed", 42)) + 4000 + idx_l * 1000 + i
            y[i] = compute_skr(p)["SKR_raw"]
        ax.plot(
            sigma_r_values * 100.0,
            y,
            color=COLORS["blue"] if idx_l == 0 else COLORS["yellow"],
            lw=2,
            ls=LINESTYLES["solid"] if idx_l == 0 else LINESTYLES["dashed"],
            label=rf"$L = {l_m/1e3:.0f}$ km",
        )
    ax.axhline(0, color="gray", lw=0.8, ls=LINESTYLES["dashed"])
    ax.set_xlabel(r"Pointing Error Std. Dev. $\sigma_r$ [cm]")
    ax.set_ylabel("SKR [bits/pulse]")
    ax.set_title("Effect of Pointing Error on SKR")
    _apply_publication_ticks(ax)
    ax.legend(fontsize=9, framealpha=0.9)

    # Plot 6
    l_arr = np.linspace(10e3, 30e3, 30)
    cn2_arr = np.logspace(-17, -14, 30)
    skr_matrix = np.zeros((len(cn2_arr), len(l_arr)), dtype=float)
    for i, cn2 in enumerate(cn2_arr):
        for j, l_m in enumerate(l_arr):
            p = dict(params)
            p["Cn2"] = float(cn2)
            p["L_link_m"] = float(l_m)
            p["seed"] = int(params.get("seed", 42)) + 6000 + i * len(l_arr) + j
            skr_matrix[i, j] = compute_skr(p)["SKR_raw"]
    ax = axes[1, 2]
    im = ax.pcolormesh(
        l_arr / 1e3,
        np.log10(cn2_arr),
        skr_matrix,
        cmap="viridis",
        shading="auto",
        vmin=0,
        vmax=max(float(np.nanmax(skr_matrix)), 1e-8),
    )
    level = _safe_contour_level(skr_matrix, desired=1e-6)
    if level is not None:
        cs = ax.contour(l_arr / 1e3, np.log10(cn2_arr), skr_matrix, levels=[level], colors=[COLORS["red"]], linewidths=2)
        ax.clabel(cs, fmt="SKR = 0", fontsize=9)
    ax.plot(20, np.log10(1e-15), "*", color=COLORS["red"], markersize=12)
    ax.set_xlabel("Link Distance [km]")
    ax.set_ylabel(r"$\log_{10}(C_n^2)$ [m$^{-2/3}$]")
    ax.set_title("SKR Feasibility Map")
    _apply_publication_ticks(ax)
    fig.colorbar(im, ax=ax, label="SKR [bits/pulse]")

    fig.tight_layout(pad=2.0)
    fig.savefig(Path(save_path), dpi=200, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return {"save_path": str(Path(save_path))}
