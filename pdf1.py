"""10,000-sample HAP--UAV FSO channel diagnostic from the attached PDF.

This is a raw, channel-only Monte Carlo experiment.  It does not run the
repository's CV-QKD/security pipeline and does not clip the raw transmittance.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.special import erf, i0e, i1e


N_MC = 10_000
SEED = 42
OUTPUT_DIR = Path(__file__).resolve().parent / "results" / "hap_uav_fso_monte_carlo"
PDF_PATH = Path(r"C:\Users\admin\Downloads\2026__Binh_s_work__Copy___Copy_ (3).pdf")

# Table I, SI units.
LAMBDA_M = 1.55e-6
H_HAP_M = 2.0e4
H_UAV_M = 1.0e3
ZETA_RAD = 0.0
V_WIND_M_PER_S = 21.0
CN2_GROUND_M_MINUS_TWO_THIRDS = 5.0e-14
D_R_M = 0.08
THETA_DIV_RAD = 223.0e-6
OMEGA_0_TABLE_M = 4.425e-3
F_0_M = math.inf
ETA_ATM = 0.9316271221
SIGMA_H_M = 1.0
THETA_JT_RAD = 15.61e-6
RHO_X_M = 0.0
RHO_Y_M = 0.0


def cn2_hufnagel_valley(height_m: float) -> float:
    """Hufnagel--Valley refractive-index profile, PDF Eq. (2)."""

    return (
        0.00594
        * (V_WIND_M_PER_S / 27.0) ** 2
        * (1.0e-5 * height_m) ** 10
        * math.exp(-height_m / 1000.0)
        + 2.7e-16 * math.exp(-height_m / 1500.0)
        + CN2_GROUND_M_MINUS_TWO_THIRDS * math.exp(-height_m / 100.0)
    )


def derive_channel_parameters() -> dict[str, float]:
    """Evaluate the deterministic quantities used by the Monte Carlo run."""

    sec_zeta = 1.0 / math.cos(ZETA_RAD)
    # PDF Eq. (3).
    k_wave = 2.0 * math.pi / LAMBDA_M
    # PDF Eq. (4).
    path_height_m = H_HAP_M - H_UAV_M
    link_length_m = path_height_m * sec_zeta

    # PDF Eq. (5).
    rytov_integral, rytov_error = quad(
        lambda h: cn2_hufnagel_valley(h) * (h - H_UAV_M) ** (5.0 / 6.0),
        H_UAV_M,
        H_HAP_M,
        epsabs=1.0e-24,
        epsrel=2.0e-13,
        limit=300,
    )
    sigma_R0_squared = (
        2.25
        * k_wave ** (7.0 / 6.0)
        * sec_zeta ** (11.0 / 6.0)
        * rytov_integral
    )

    # PDF Eq. (7).
    aperture_numerator, aperture_numerator_error = quad(
        lambda h: cn2_hufnagel_valley(h) * h**2,
        H_UAV_M,
        H_HAP_M,
        epsabs=1.0e-18,
        epsrel=2.0e-13,
        limit=300,
    )
    aperture_denominator, aperture_denominator_error = quad(
        lambda h: cn2_hufnagel_valley(h) * h ** (5.0 / 6.0),
        H_UAV_M,
        H_HAP_M,
        epsabs=1.0e-24,
        epsrel=2.0e-13,
        limit=300,
    )
    phi_m = (aperture_numerator / aperture_denominator) ** (6.0 / 7.0)
    # PDF Eq. (6).
    aperture_factor = (
        1.0
        + 1.11 * (D_R_M**2 / (LAMBDA_M * phi_m) * sec_zeta) ** (7.0 / 6.0)
    ) ** -1.0
    # PDF Eqs. (8)--(10): v_sc = sigma_R,D^2.
    sigma_RD_squared = aperture_factor * sigma_R0_squared
    v_sc = sigma_RD_squared

    # PDF Eq. (29).  Table I's omega_0 is rounded; use the equation-derived
    # value and retain the table value as an explicit consistency check.
    omega_0_m = 2.0 * LAMBDA_M / (math.pi * THETA_DIV_RAD)
    # PDF Eqs. (27)--(28), with F_0 = infinity from Table I.
    curvature_term = 1.0 if math.isinf(F_0_M) else 1.0 - link_length_m / F_0_M
    omega_L_m = omega_0_m * math.sqrt(
        curvature_term**2 + (2.0 * link_length_m / (k_wave * omega_0_m**2)) ** 2
    )

    # PDF Eq. (32).  Its Lambda uses the free-space beam radius from Eq. (27).
    lambda_beam = 2.0 * link_length_m / (k_wave * omega_L_m**2)
    beam_spreading_integral, beam_spreading_error = quad(
        lambda h: cn2_hufnagel_valley(h)
        * ((h - H_UAV_M) / path_height_m) ** (5.0 / 3.0),
        H_UAV_M,
        H_HAP_M,
        epsabs=1.0e-24,
        epsrel=2.0e-13,
        limit=300,
    )
    G_d = (
        4.35
        * lambda_beam ** (5.0 / 6.0)
        * k_wave ** (7.0 / 6.0)
        * path_height_m ** (5.0 / 6.0)
        * sec_zeta ** (11.0 / 6.0)
        * beam_spreading_integral
    )
    # PDF Eqs. (30)--(31).  The attached PDF prints the same expression twice.
    omega_L_e_m = omega_L_m * math.sqrt(1.0 + G_d)
    # PDF Eq. (33).
    nu = math.sqrt(math.pi) * D_R_M / (2.0 * math.sqrt(2.0) * omega_L_m)
    # PDF Eq. (34).
    A_0 = float(erf(nu) ** 2)
    # PDF Eq. (35).
    omega_L_eq_squared_m2 = (
        omega_L_e_m**2
        * math.sqrt(math.pi)
        * float(erf(nu))
        / (2.0 * nu * math.exp(-nu**2))
    )
    omega_L_eq_m = math.sqrt(omega_L_eq_squared_m2)

    # PDF Eqs. (17), (18), and (22).
    sigma_H_theta_m = link_length_m * THETA_JT_RAD
    sigma_jt_m = math.sqrt(SIGMA_H_M**2 + sigma_H_theta_m**2)
    rho_m = math.hypot(RHO_X_M, RHO_Y_M)

    return {
        "lambda_m": LAMBDA_M,
        "h_hap_m": H_HAP_M,
        "h_uav_m": H_UAV_M,
        "zenith_angle_rad": ZETA_RAD,
        "link_length_m": link_length_m,
        "path_height_m": path_height_m,
        "wind_speed_m_per_s": V_WIND_M_PER_S,
        "cn2_ground_m_minus_two_thirds": CN2_GROUND_M_MINUS_TWO_THIRDS,
        "receiver_diameter_m": D_R_M,
        "theta_div_rad": THETA_DIV_RAD,
        "omega_0_table_m": OMEGA_0_TABLE_M,
        "omega_0_from_eq29_m": omega_0_m,
        "f_0_m": None if math.isinf(F_0_M) else F_0_M,
        "f_0_is_infinite": math.isinf(F_0_M),
        "eta_atm": ETA_ATM,
        "sigma_h_m": SIGMA_H_M,
        "theta_jt_rad": THETA_JT_RAD,
        "rho_x_m": RHO_X_M,
        "rho_y_m": RHO_Y_M,
        "rho_m": rho_m,
        "wave_number_per_m": k_wave,
        "rytov_integral": rytov_integral,
        "rytov_quad_error": rytov_error,
        "sigma_R0_squared": sigma_R0_squared,
        "aperture_numerator": aperture_numerator,
        "aperture_numerator_quad_error": aperture_numerator_error,
        "aperture_denominator": aperture_denominator,
        "aperture_denominator_quad_error": aperture_denominator_error,
        "Phi_m": phi_m,
        "AA": aperture_factor,
        "sigma_RD_squared": sigma_RD_squared,
        "v_sc": v_sc,
        "omega_L_m": omega_L_m,
        "Lambda": lambda_beam,
        "beam_spreading_integral": beam_spreading_integral,
        "beam_spreading_quad_error": beam_spreading_error,
        "G_d": G_d,
        "omega_L_e_m": omega_L_e_m,
        "nu": nu,
        "A0": A_0,
        "omega_L_eq_squared_m2": omega_L_eq_squared_m2,
        "omega_L_eq_m": omega_L_eq_m,
        "sigma_H_theta_m": sigma_H_theta_m,
        "sigma_jt_m": sigma_jt_m,
    }


def lognormal_pdf(values: np.ndarray, v_sc: float) -> np.ndarray:
    """Analytical PDF from PDF Eq. (12), for h > 0."""

    values = np.asarray(values, dtype=np.float64)
    result = np.zeros_like(values)
    positive = values > 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        log_values = np.log(values[positive])
        result[positive] = np.exp(
            -log_values
            - 0.5 * math.log(2.0 * math.pi * v_sc)
            - (log_values + v_sc / 2.0) ** 2 / (2.0 * v_sc)
        )
    return result


def rician_pdf(values: np.ndarray, sigma_m: float, rho_m: float) -> np.ndarray:
    """Analytical Rician PDF from PDF Eq. (26), for r >= 0."""

    values = np.asarray(values, dtype=np.float64)
    sigma_squared = sigma_m**2
    bessel_argument = rho_m * values / sigma_squared
    # i0(z) = exp(|z|) i0e(z), which keeps the general Rician form stable.
    with np.errstate(over="ignore", invalid="ignore"):
        return (
            values
            / sigma_squared
            * np.exp(
                -(values**2 + rho_m**2) / (2.0 * sigma_squared)
                + np.abs(bessel_argument)
            )
            * i0e(bessel_argument)
        )


def rician_mean(sigma_m: float, rho_m: float) -> float:
    """Theoretical Rician mean; it reduces to Rayleigh at rho=0."""

    # Requested Section 6 Rayleigh mean is the rho=0 case of this expression.
    b_squared = (rho_m / sigma_m) ** 2
    x = b_squared / 4.0
    # Stable form of sigma*sqrt(pi/2)*exp(-x)*[(1+b^2/2)I0(x)+(b^2/2)I1(x)].
    return float(
        sigma_m
        * math.sqrt(math.pi / 2.0)
        * ((1.0 + b_squared / 2.0) * i0e(x) + (b_squared / 2.0) * i1e(x))
    )


def stats(values: np.ndarray) -> dict[str, float | dict[str, float]]:
    """Return the requested descriptive statistics."""

    percentiles = np.percentile(values, [1, 5, 50, 95, 99])
    return {
        "mean": float(np.mean(values)),
        "variance": float(np.var(values)),
        "standard_deviation": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "percentiles": {
            "1%": float(percentiles[0]),
            "5%": float(percentiles[1]),
            "50%": float(percentiles[2]),
            "95%": float(percentiles[3]),
            "99%": float(percentiles[4]),
        },
    }


def save_histogram(
    values: np.ndarray,
    path: Path,
    *,
    xlabel: str,
    title: str,
    pdf_x: np.ndarray | None = None,
    pdf_y: np.ndarray | None = None,
    pdf_label: str | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.hist(values, bins=60, density=True, alpha=0.72, label="Monte Carlo")
    if pdf_x is not None and pdf_y is not None:
        ax.plot(pdf_x, pdf_y, color="black", linewidth=2.0, label=pdf_label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_simulation() -> dict[str, object]:
    """Run the fixed-seed raw-channel experiment and persist its outputs."""

    params = derive_channel_parameters()
    v_sc = params["v_sc"]
    sigma_jt_m = params["sigma_jt_m"]
    rho_m = params["rho_m"]

    print("H_sc: Log-normal random variable.")
    print("r_mis: Rician random variable.")
    print("H_p: deterministic nonlinear transformation of r_mis.")
    print("X_active = eta_atm * H_sc * H_p.")
    if rho_m == 0.0:
        print("rho=0: the Rician displacement reduces to the Rayleigh special case.")

    rng = np.random.default_rng(SEED)
    # PDF Eq. (11): ln(H_sc) ~ N(-v_sc/2, v_sc).
    H_sc = np.exp(rng.normal(-v_sc / 2.0, math.sqrt(v_sc), N_MC))
    # PDF Eqs. (23)--(26): independent Cartesian normals give general Rician r_mis.
    x = rng.normal(RHO_X_M, sigma_jt_m, N_MC)
    y = rng.normal(RHO_Y_M, sigma_jt_m, N_MC)
    r_mis = np.hypot(x, y)
    # PDF Eq. (36): transform radial displacement into pointing coefficient.
    H_p = params["A0"] * np.exp(-2.0 * r_mis**2 / params["omega_L_eq_squared_m2"])
    # PDF Eqs. (1) and (48), with B_AoA=1 as requested for this first test.
    B_AoA = np.ones(N_MC, dtype=np.float64)
    X_active = params["eta_atm"] * H_sc * H_p * B_AoA

    for name, values in {
        "H_sc": H_sc,
        "r_mis": r_mis,
        "H_p": H_p,
        "X_active": X_active,
    }.items():
        if values.shape != (N_MC,) or not np.all(np.isfinite(values)):
            raise AssertionError(f"{name} has invalid shape or non-finite values")
    if not np.all(H_sc > 0.0):
        raise AssertionError("H_sc must be strictly positive")
    if not np.all((H_p > 0.0) & (H_p <= params["A0"] + 1.0e-15)):
        raise AssertionError("H_p left the mathematical interval (0, A0]")
    if not math.isclose(float(np.mean(H_sc)), 1.0, rel_tol=0.02):
        raise AssertionError("The sampled H_sc mean is not approximately one")

    theoretical_r_mis_mean = rician_mean(sigma_jt_m, rho_m)
    simulated_r_mis_mean = float(np.mean(r_mis))
    relative_r_mis_mean_error = abs(simulated_r_mis_mean - theoretical_r_mis_mean) / theoretical_r_mis_mean

    summary = {
        "status": "EXPLORATORY_PDF_TABLE_I_RAW_CHANNEL_DIAGNOSTIC",
        "source_pdf": str(PDF_PATH),
        "source_pdf_sha256": sha256(PDF_PATH),
        "seed": SEED,
        "N_MC": N_MC,
        "draw_order": ["H_sc", "X", "Y"],
        "aoa": {"included": False, "B_AoA": 1.0},
        "parameters": params,
        "statistics": {
            "H_sc": stats(H_sc),
            "r_mis": stats(r_mis),
            "H_p": stats(H_p),
            "X_active": stats(X_active),
        },
        "validation": {
            "mean_H_sc_target": 1.0,
            "theoretical_rician_mean_r_mis": theoretical_r_mis_mean,
            "simulated_mean_r_mis": simulated_r_mis_mean,
            "relative_r_mis_mean_error": relative_r_mis_mean_error,
            "H_p_support_verified": True,
            "n_X_active_gt_1": int(np.count_nonzero(X_active > 1.0)),
            "P_X_active_gt_1": float(np.mean(X_active > 1.0)),
        },
        "arrays_file": "samples.npz",
        "script": str(Path(__file__).resolve()),
        "figures": [
            "H_sc_histogram.png",
            "r_mis_histogram.png",
            "H_p_histogram.png",
            "X_active_histogram.png",
        ],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUTPUT_DIR / "samples.npz",
        H_sc=H_sc,
        r_mis=r_mis,
        H_p=H_p,
        X_active=X_active,
    )
    (OUTPUT_DIR / "simulation_results.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    hsc_x = np.geomspace(max(np.min(H_sc) * 0.8, 1.0e-6), np.max(H_sc) * 1.2, 800)
    save_histogram(
        H_sc,
        OUTPUT_DIR / "H_sc_histogram.png",
        xlabel=r"Scintillation gain $H_{\rm sc}$ (dimensionless)",
        title=r"$H_{\rm sc}$: Monte Carlo and log-normal PDF",
        pdf_x=hsc_x,
        pdf_y=lognormal_pdf(hsc_x, v_sc),
        pdf_label="Analytical log-normal PDF (Eq. 12)",
    )
    r_x = np.linspace(0.0, np.max(r_mis) * 1.1, 800)
    save_histogram(
        r_mis,
        OUTPUT_DIR / "r_mis_histogram.png",
        xlabel=r"Radial displacement $r_{\rm mis}$ (m)",
        title=r"$r_{\rm mis}$: Monte Carlo and Rician PDF",
        pdf_x=r_x,
        pdf_y=rician_pdf(r_x, sigma_jt_m, rho_m),
        pdf_label="Analytical Rician PDF (Eq. 26)",
    )
    save_histogram(
        H_p,
        OUTPUT_DIR / "H_p_histogram.png",
        xlabel=r"Pointing coefficient $H_p$ (dimensionless)",
        title=r"$H_p$ from the displacement transformation (Eq. 36)",
    )
    save_histogram(
        X_active,
        OUTPUT_DIR / "X_active_histogram.png",
        xlabel=r"Raw active gain $X=\eta_{\rm atm}H_{\rm sc}H_p$ (dimensionless)",
        title=r"$X_{\rm active}$ without AoA and without clipping",
    )

    validation_rows = {
        "N_MC": N_MC,
        "L": params["link_length_m"],
        "sigma_H_theta": params["sigma_H_theta_m"],
        "sigma_jt": params["sigma_jt_m"],
        "v_sc": params["v_sc"],
        "mean(H_sc)": float(np.mean(H_sc)),
        "mean(r_mis)": simulated_r_mis_mean,
        "A0": params["A0"],
        "omega_L": params["omega_L_m"],
        "omega_L_e": params["omega_L_e_m"],
        "omega_L_eq": params["omega_L_eq_m"],
        "mean(H_p)": float(np.mean(H_p)),
        "mean(X_active)": float(np.mean(X_active)),
        "min(X_active)": float(np.min(X_active)),
        "max(X_active)": float(np.max(X_active)),
        "count(X_active > 1)": int(np.count_nonzero(X_active > 1.0)),
        "P(X_active > 1)": float(np.mean(X_active > 1.0)),
    }
    print("\nDerived deterministic quantities")
    print("--------------------------------")
    for key in (
        "sigma_R0_squared",
        "AA",
        "sigma_RD_squared",
        "G_d",
        "nu",
        "omega_0_from_eq29_m",
    ):
        print(f"{key:24s} {params[key]:.16g}")
    print("\nValidation table")
    print("----------------")
    for key, value in validation_rows.items():
        print(f"{key:20s} {value:.16g}" if isinstance(value, float) else f"{key:20s} {value}")
    print(f"\nTheoretical E[r_mis]  {theoretical_r_mis_mean:.16g}")
    print(f"Relative mean error   {relative_r_mis_mean_error:.6%}")
    print("\nDescriptive statistics")
    print("---------------------")
    for name in ("H_sc", "r_mis", "H_p", "X_active"):
        print(f"\n{name}")
        record = summary["statistics"][name]
        print(json.dumps(record, indent=2))
    print(f"\nSaved outputs to {OUTPUT_DIR.resolve()}")
    return summary


if __name__ == "__main__":
    run_simulation()
