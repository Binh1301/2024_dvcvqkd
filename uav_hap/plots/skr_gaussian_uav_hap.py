from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

import matplotlib

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import i0, i1


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
                ((V + chi_line) * (1.0 + chi_hom))
                / max((V + chi_hom) * (V * chi_line + 1.0), EPS),
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


def _plot_style() -> None:
    plt.style.use("seaborn-v0_8-darkgrid")


def _finalize_and_save(fig: plt.Figure, path: Path, show: bool) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_1_skr_vs_distance(base_params: Optional[Mapping[str, float]] = None, save_path: str = "plot_1.png", show: bool = True) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    l_values = np.linspace(10e3, 30e3, 80)
    skr_values = np.zeros_like(l_values)
    skr_raw = np.zeros_like(l_values)
    cmap = plt.get_cmap("viridis")

    for i, l_m in enumerate(l_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        skr_values[i] = max(out["SKR"], 0.0)
        skr_raw[i] = out["SKR_raw"]

    positive_idx = np.where(skr_raw > 0.0)[0]
    l_max_km = float(l_values[positive_idx[-1]] / 1e3) if positive_idx.size > 0 else float(l_values[0] / 1e3)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(l_values / 1e3, skr_values, color=cmap(0.75), lw=2.0, label="SKR")
    ax.axhline(0, color="red", linestyle="--", label="SKR = 0")
    ax.axvline(l_max_km, color="red", linestyle="-.", label=f"L_max ≈ {l_max_km:.2f} km")
    ax.set_xlabel("Khoảng cách L_link (km)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("SKR vs khoảng cách UAV-HAP")
    info = (
        f"C²ₙ = {float(params.get('Cn2', CN2)):.1e}\n"
        f"V_A = {float(params.get('VA', 2.0)):.2f}\n"
        f"beta = {float(params.get('beta', 0.95)):.2f}"
    )
    ax.text(0.97, 0.97, info, transform=ax.transAxes, va="top", ha="right", fontsize=9, bbox={"fc": "white", "alpha": 0.85})
    ax.legend()

    _finalize_and_save(fig, Path(save_path), show)
    return {"L_values_m": l_values, "SKR_values": skr_values, "L_max_km": l_max_km, "save_path": str(Path(save_path))}


def plot_2_skr_vs_va(base_params: Optional[Mapping[str, float]] = None, save_path: str = "plot_2.png", show: bool = True) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    params["L_link_m"] = float(params.get("L_link_m", 20e3))
    va_values = np.linspace(0.1, 20.0, 100)
    skr_values = np.zeros_like(va_values)
    cmap = plt.get_cmap("viridis")

    for i, va in enumerate(va_values):
        p = dict(params)
        p["VA"] = float(va)
        p["seed"] = int(params.get("seed", 42)) + i
        skr_values[i] = max(compute_skr(p)["SKR"], 0.0)

    idx = int(np.argmax(skr_values))
    va_opt = float(va_values[idx])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(va_values, skr_values, color=cmap(0.75), lw=2.0, label="SKR")
    ax.axvline(va_opt, color="orange", linestyle="--", label=f"V_A opt = {va_opt:.2f} SNU")
    ax.set_xlabel("Modulation variance V_A (SNU)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("Tối ưu V_A tại L = 20 km")
    ax.legend()

    _finalize_and_save(fig, Path(save_path), show)
    return {"VA_values": va_values, "SKR_values": skr_values, "VA_opt": va_opt, "save_path": str(Path(save_path))}


def plot_3_skr_vs_cn2(base_params: Optional[Mapping[str, float]] = None, save_path: str = "plot_3.png", show: bool = True) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    params["L_link_m"] = float(params.get("L_link_m", 20e3))
    cn2_values = np.logspace(-17, -14, 60)
    skr_values = np.zeros_like(cn2_values)
    skr_raw = np.zeros_like(cn2_values)
    cmap = plt.get_cmap("viridis")

    for i, cn2 in enumerate(cn2_values):
        p = dict(params)
        p["Cn2"] = float(cn2)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        skr_values[i] = max(out["SKR"], 0.0)
        skr_raw[i] = out["SKR_raw"]

    neg_idx = np.where(skr_raw <= 0.0)[0]
    cn2_max = float(cn2_values[neg_idx[0]]) if neg_idx.size > 0 else float(cn2_values[-1])

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.semilogx(cn2_values, skr_values, color=cmap(0.75), lw=2.0, label="SKR")
    ax.axhline(0, color="red", linestyle="--")
    ax.axvspan(cn2_max, 1e-14, alpha=0.15, color="red", label="Vùng SKR < 0")
    ax.set_xlabel("Cường độ nhiễu loạn C²ₙ (m⁻²/³)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("SKR vs turbulence tại L = 20 km")
    ax.legend()

    _finalize_and_save(fig, Path(save_path), show)
    return {"Cn2_values": cn2_values, "SKR_values": skr_values, "Cn2_max": cn2_max, "save_path": str(Path(save_path))}


def plot_4_loss_decomposition(base_params: Optional[Mapping[str, float]] = None, save_path: str = "plot_4.png", show: bool = True) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    l_values = np.linspace(5e3, 30e3, 80)
    eta_atm_list = np.zeros_like(l_values)
    mean_t2_list = np.zeros_like(l_values)
    t_eff_list = np.zeros_like(l_values)
    cmap = plt.get_cmap("viridis")

    for i, l_m in enumerate(l_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        eta_atm_list[i] = out["eta_atm"]
        mean_t2_list[i] = out["mean_T2"]
        t_eff_list[i] = out["T_eff"]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(l_values / 1e3, 10 * np.log10(np.clip(eta_atm_list, EPS, 1.0)), linestyle="--", color=cmap(0.25), label="η_atm (Beer-Lambert)")
    ax.plot(l_values / 1e3, 10 * np.log10(np.clip(mean_t2_list, EPS, 1.0)), linestyle="-.", color=cmap(0.55), label="⟨T²⟩ (pointing+turb)")
    ax.plot(l_values / 1e3, 10 * np.log10(np.clip(t_eff_list, EPS, 1.0)), linestyle="-", linewidth=2.2, color=cmap(0.85), label="T_eff = η_atm × ⟨T²⟩")
    ax.set_xlabel("Khoảng cách L_link (km)")
    ax.set_ylabel("Suy hao (dB)")
    ax.set_title("Phân tích suy hao kênh")
    ax.legend()

    _finalize_and_save(fig, Path(save_path), show)
    return {
        "L_values_m": l_values,
        "eta_atm_list": eta_atm_list,
        "mean_T2_list": mean_t2_list,
        "T_eff_list": t_eff_list,
        "save_path": str(Path(save_path)),
    }


def plot_5_skr_vs_sigma_r(base_params: Optional[Mapping[str, float]] = None, save_path: str = "plot_5.png", show: bool = True) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    sigma_r_values = np.linspace(0.01, 0.35, 80)
    l_list = [15e3, 20e3]
    cmap = plt.get_cmap("viridis")
    curves: Dict[str, np.ndarray] = {}

    fig, ax = plt.subplots(figsize=(7, 5))
    for idx_l, l_m in enumerate(l_list):
        skr_list = np.zeros_like(sigma_r_values)
        for i, sigma_r in enumerate(sigma_r_values):
            p = dict(params)
            p["L_link_m"] = float(l_m)
            p["sigma_r_override_m"] = float(sigma_r)
            p["seed"] = int(params.get("seed", 42)) + idx_l * 1000 + i
            skr_list[i] = max(compute_skr(p)["SKR"], 0.0)
        curves[f"L_{int(l_m/1e3)}km"] = skr_list
        ax.plot(sigma_r_values * 100.0, skr_list, lw=2.0, color=cmap(0.35 + 0.45 * idx_l), label=f"L = {l_m/1e3:.0f} km")

    ax.axhline(0, color="red", linestyle="--")
    ax.set_xlabel("Phương sai lệch tâm σ_r (cm)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("Ảnh hưởng pointing error lên SKR")
    ax.legend()

    _finalize_and_save(fig, Path(save_path), show)
    return {"sigma_r_values_m": sigma_r_values, "curves": curves, "save_path": str(Path(save_path))}


def plot_6_skr_heatmap(base_params: Optional[Mapping[str, float]] = None, save_path: str = "plot_6.png", show: bool = True) -> Dict[str, Any]:
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
            skr_matrix[i, j] = max(compute_skr(p)["SKR"], 0.0)

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.pcolormesh(l_arr / 1e3, np.log10(cn2_arr), skr_matrix, cmap="viridis", shading="auto")
    fig.colorbar(im, ax=ax, label="SKR (bits/pulse)")
    ax.contour(l_arr / 1e3, np.log10(cn2_arr), skr_matrix, levels=[1e-6], colors="red", linewidths=1.5)
    ax.set_xlabel("Khoảng cách L_link (km)")
    ax.set_ylabel("log₁₀(C²ₙ) [m⁻²/³]")
    ax.set_title("Heatmap SKR - Vùng khả thi hệ thống")
    ax.plot(20, np.log10(1e-15), "r*", markersize=12, label="Điểm tài liệu (L=20km, C²ₙ=1e-15)")
    ax.legend(fontsize=9)

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
        "plot_1": plot_1_skr_vs_distance(params, save_path=str(out_dir / "plot_1.png"), show=show),
        "plot_2": plot_2_skr_vs_va(params, save_path=str(out_dir / "plot_2.png"), show=show),
        "plot_3": plot_3_skr_vs_cn2(params, save_path=str(out_dir / "plot_3.png"), show=show),
        "plot_4": plot_4_loss_decomposition(params, save_path=str(out_dir / "plot_4.png"), show=show),
        "plot_5": plot_5_skr_vs_sigma_r(params, save_path=str(out_dir / "plot_5.png"), show=show),
        "plot_6": plot_6_skr_heatmap(params, save_path=str(out_dir / "plot_6.png"), show=show),
    }
    return results


def plot_all_skr_figures_combined(
    base_params: Optional[Mapping[str, float]] = None,
    save_path: Union[str, Path] = "plot_all.png",
    show: bool = True,
) -> Dict[str, Any]:
    _plot_style()
    params = dict(base_params or {})
    cmap = plt.get_cmap("viridis")
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("CV-QKD UAV-HAP - Phân tích hiệu năng", fontsize=14)

    # Plot 1
    l_values = np.linspace(10e3, 30e3, 80)
    skr_values = np.zeros_like(l_values)
    skr_raw = np.zeros_like(l_values)
    for i, l_m in enumerate(l_values):
        p = dict(params)
        p["L_link_m"] = float(l_m)
        p["seed"] = int(params.get("seed", 42)) + i
        out = compute_skr(p)
        skr_values[i] = max(out["SKR"], 0.0)
        skr_raw[i] = out["SKR_raw"]
    pos = np.where(skr_raw > 0.0)[0]
    l_max_km = float(l_values[pos[-1]] / 1e3) if pos.size > 0 else float(l_values[0] / 1e3)
    ax = axes[0, 0]
    ax.plot(l_values / 1e3, skr_values, color=cmap(0.75), lw=2.0)
    ax.axhline(0, color="red", linestyle="--")
    ax.axvline(l_max_km, color="red", linestyle="-.")
    ax.set_xlabel("Khoảng cách L_link (km)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("1) SKR vs khoảng cách")

    # Plot 2
    va_values = np.linspace(0.1, 20.0, 100)
    va_skr = np.zeros_like(va_values)
    for i, va in enumerate(va_values):
        p = dict(params)
        p["L_link_m"] = float(params.get("L_link_m", 20e3))
        p["VA"] = float(va)
        p["seed"] = int(params.get("seed", 42)) + 1000 + i
        va_skr[i] = max(compute_skr(p)["SKR"], 0.0)
    va_opt = float(va_values[int(np.argmax(va_skr))])
    ax = axes[0, 1]
    ax.plot(va_values, va_skr, color=cmap(0.75), lw=2.0)
    ax.axvline(va_opt, color="orange", linestyle="--")
    ax.set_xlabel("Modulation variance V_A (SNU)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("2) SKR vs V_A")

    # Plot 3
    cn2_values = np.logspace(-17, -14, 60)
    cn2_skr = np.zeros_like(cn2_values)
    cn2_raw = np.zeros_like(cn2_values)
    for i, cn2 in enumerate(cn2_values):
        p = dict(params)
        p["L_link_m"] = float(params.get("L_link_m", 20e3))
        p["Cn2"] = float(cn2)
        p["seed"] = int(params.get("seed", 42)) + 2000 + i
        out = compute_skr(p)
        cn2_skr[i] = max(out["SKR"], 0.0)
        cn2_raw[i] = out["SKR_raw"]
    neg = np.where(cn2_raw <= 0.0)[0]
    cn2_max = float(cn2_values[neg[0]]) if neg.size > 0 else float(cn2_values[-1])
    ax = axes[0, 2]
    ax.semilogx(cn2_values, cn2_skr, color=cmap(0.75), lw=2.0)
    ax.axhline(0, color="red", linestyle="--")
    ax.axvspan(cn2_max, 1e-14, alpha=0.15, color="red")
    ax.set_xlabel("Cường độ nhiễu loạn C²ₙ (m⁻²/³)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("3) SKR vs C²ₙ")

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
    ax.plot(l2_values / 1e3, 10 * np.log10(np.clip(eta_atm, EPS, 1.0)), linestyle="--", color=cmap(0.25))
    ax.plot(l2_values / 1e3, 10 * np.log10(np.clip(mean_t2, EPS, 1.0)), linestyle="-.", color=cmap(0.55))
    ax.plot(l2_values / 1e3, 10 * np.log10(np.clip(t_eff, EPS, 1.0)), linestyle="-", lw=2.2, color=cmap(0.85))
    ax.set_xlabel("Khoảng cách L_link (km)")
    ax.set_ylabel("Suy hao (dB)")
    ax.set_title("4) Phân tích suy hao")

    # Plot 5
    sigma_r_values = np.linspace(0.01, 0.35, 80)
    ax = axes[1, 1]
    for idx_l, l_m in enumerate([15e3, 20e3]):
        y = np.zeros_like(sigma_r_values)
        for i, sigma_r in enumerate(sigma_r_values):
            p = dict(params)
            p["L_link_m"] = float(l_m)
            p["sigma_r_override_m"] = float(sigma_r)
            p["seed"] = int(params.get("seed", 42)) + 4000 + idx_l * 1000 + i
            y[i] = max(compute_skr(p)["SKR"], 0.0)
        ax.plot(sigma_r_values * 100.0, y, color=cmap(0.35 + 0.45 * idx_l), lw=2.0, label=f"L={l_m/1e3:.0f} km")
    ax.axhline(0, color="red", linestyle="--")
    ax.set_xlabel("Phương sai lệch tâm σ_r (cm)")
    ax.set_ylabel("SKR (bits/pulse)")
    ax.set_title("5) SKR vs σ_r")
    ax.legend(fontsize=8)

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
            skr_matrix[i, j] = max(compute_skr(p)["SKR"], 0.0)
    ax = axes[1, 2]
    im = ax.pcolormesh(l_arr / 1e3, np.log10(cn2_arr), skr_matrix, cmap="viridis", shading="auto")
    ax.contour(l_arr / 1e3, np.log10(cn2_arr), skr_matrix, levels=[1e-6], colors="red", linewidths=1.5)
    ax.plot(20, np.log10(1e-15), "r*", markersize=10)
    ax.set_xlabel("Khoảng cách L_link (km)")
    ax.set_ylabel("log₁₀(C²ₙ)")
    ax.set_title("6) Heatmap SKR")
    fig.colorbar(im, ax=ax, label="SKR (bits/pulse)")

    _finalize_and_save(fig, Path(save_path), show)
    return {"save_path": str(Path(save_path))}
