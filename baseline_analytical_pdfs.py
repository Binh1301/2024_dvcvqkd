"""Baseline analytical H_p and X PDFs from PDF Eqs. (37) and (50).

No Monte Carlo sampling or parameter sweep is performed here.
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
from scipy.special import i0

from pdf1 import derive_channel_parameters


SOURCE_PDF = Path(r"C:\Users\admin\Downloads\2026__Binh_s_work__Copy___Copy_ (4).pdf")
OUTPUT_DIR = Path(__file__).resolve().parent / "results" / "hap_uav_fso_monte_carlo"
BASELINE = derive_channel_parameters()

ETA_ATM = float(BASELINE["eta_atm"])
A0 = float(BASELINE["A0"])
OMEGA_L_EQ_M = float(BASELINE["omega_L_eq_m"])
SIGMA_JT_M = float(BASELINE["sigma_jt_m"])
RHO_M = 0.0
V_SC = float(BASELINE["v_sc"])
CHI = OMEGA_L_EQ_M / (2.0 * SIGMA_JT_M)  # PDF Eq. (38).
CHI_SQUARED = CHI**2


def hp_pdf_eq37(hp: float) -> float:
    """Pointing-coefficient PDF from PDF Eq. (37)."""

    if not 0.0 < hp <= A0:
        return 0.0
    sigma_squared = SIGMA_JT_M**2
    # PDF Eq. (36) inverted inside Eq. (37).
    radial_squared = -0.5 * OMEGA_L_EQ_M**2 * math.log(hp / A0)
    bessel_argument = RHO_M * math.sqrt(radial_squared) / sigma_squared
    # PDF Eq. (37), including its A0**chi^2 normalization factor.
    return (
        CHI_SQUARED
        / A0**CHI_SQUARED
        * math.exp(-RHO_M**2 / (2.0 * sigma_squared))
        * hp ** (CHI_SQUARED - 1.0)
        * float(i0(bessel_argument))
    )


def x_pdf_eq50(t: float) -> float:
    """Active-channel PDF from PDF Eq. (50), using scipy.integrate.quad."""

    if not t > 0.0:
        return 0.0
    sigma_squared = SIGMA_JT_M**2

    def integrand(hp: float) -> float:
        if hp <= 0.0:
            return 0.0
        # PDF Eq. (37)'s Bessel argument inside Eq. (50).
        radial_squared = -0.5 * OMEGA_L_EQ_M**2 * math.log(hp / A0)
        bessel_argument = RHO_M * math.sqrt(radial_squared) / sigma_squared
        # The integrand is the exact Eq. (50) integrand.
        return (
            hp ** (CHI_SQUARED - 1.0)
            * math.exp(
                -(
                    math.log(t / (ETA_ATM * hp)) + V_SC / 2.0
                )
                ** 2
                / (2.0 * V_SC)
            )
            * float(i0(bessel_argument))
        )

    # For rho=0, this is the peak of the Eq. (50) integrand in hp.  Supplying
    # it to quad prevents a narrow low-t log-normal peak from being skipped.
    hp_peak = t * math.exp(V_SC * (CHI_SQUARED - 0.5)) / ETA_ATM
    points = [hp_peak] if 0.0 < hp_peak < A0 else None
    integral, _ = quad(
        integrand,
        0.0,
        A0,
        points=points,
        epsabs=1.0e-14,
        epsrel=1.0e-10,
        limit=300,
    )
    # PDF Eq. (50) prefactor.
    prefactor = (
        CHI_SQUARED
        * math.exp(-RHO_M**2 / (2.0 * sigma_squared))
        / (A0**CHI_SQUARED * t * math.sqrt(2.0 * math.pi * V_SC))
    )
    return float(prefactor * integral)


def numerical_mass_hp() -> float:
    return float(quad(hp_pdf_eq37, 0.0, A0, epsabs=1.0e-10, epsrel=1.0e-10)[0])


def numerical_mass_x() -> float:
    """Check Eq. (50) over a log-t domain covering the full mass."""

    def integrand(log_t: float) -> float:
        t = math.exp(log_t)
        return x_pdf_eq50(t) * t

    return float(
        quad(
            integrand,
            -40.0,
            0.0,
            epsabs=2.0e-8,
            epsrel=2.0e-7,
            limit=200,
        )[0]
    )


def save_plot(x: np.ndarray, y: np.ndarray, path: Path, xlabel: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    ax.plot(x, y, linewidth=2.0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_combined_x_plot(t: np.ndarray, pdf: np.ndarray) -> None:
    """Overlay the saved MC histogram and analytical Eq. (50) PDF."""

    samples_path = OUTPUT_DIR / "samples.npz"
    if not samples_path.is_file():
        raise FileNotFoundError(f"Missing saved Monte Carlo samples: {samples_path}")
    with np.load(samples_path) as samples:
        x_active = np.asarray(samples["X_active"], dtype=np.float64)

    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    ax.hist(
        x_active,
        bins=60,
        density=True,
        alpha=0.65,
        label="Monte Carlo histogram (N=10,000)",
    )
    ax.plot(t, pdf, color="black", linewidth=2.0, label="Analytical PDF (Eq. 50)")
    ax.set_xlim(0.0, float(t[-1]))
    ax.set_xlabel(r"Active channel $X=\eta_{\rm atm}H_{\rm sc}H_p$ (dimensionless)")
    ax.set_ylabel("Probability density")
    ax.set_title(r"$X_{\rm active}$: Monte Carlo histogram and analytical PDF")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "x_active_combined.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def source_pdf_sha256() -> str | None:
    if not SOURCE_PDF.is_file():
        return None
    return hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest()


def run() -> dict[str, object]:
    """Evaluate and plot only the two baseline analytical PDFs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # PDF Eq. (39): 0 < hp <= A0; zero is excluded from the grid.
    hp_grid = np.linspace(A0 * 1.0e-12, A0, 500)
    # Requested baseline active-channel plotting grid.
    t_grid = np.linspace(1.0e-8, 0.0015, 500)
    hp_values = np.asarray([hp_pdf_eq37(float(hp)) for hp in hp_grid])
    x_values = np.asarray([x_pdf_eq50(float(t)) for t in t_grid])

    if not np.all(np.isfinite(hp_values)) or not np.all(np.isfinite(x_values)):
        raise AssertionError("Analytical PDF evaluation produced non-finite values.")
    if not np.all(hp_values >= 0.0) or not np.all(x_values >= 0.0):
        raise AssertionError("Analytical PDF evaluation produced negative values.")

    save_plot(
        hp_grid,
        hp_values,
        OUTPUT_DIR / "hp_pdf_baseline.png",
        xlabel=r"Pointing coefficient $h_p$ (dimensionless)",
        title=r"Baseline analytical $f_{H_p}(h_p)$ from Eq. (37)",
    )
    save_plot(
        t_grid,
        x_values,
        OUTPUT_DIR / "x_pdf_baseline.png",
        xlabel=r"Active channel $t=X$ (dimensionless)",
        title=r"Baseline analytical $f_X(t)$ from Eq. (50)",
    )
    save_combined_x_plot(t_grid, x_values)

    result = {
        "status": "BASELINE_ANALYTICAL_PDF_DIAGNOSTIC_ONLY",
        "source_pdf": str(SOURCE_PDF),
        "source_pdf_sha256": source_pdf_sha256(),
        "monte_carlo_used": False,
        "parameter_sweep": False,
        "equations": {"H_p": "Eq. (37)", "X": "Eq. (50)"},
        "baseline": {
            "eta_atm": ETA_ATM,
            "v_sc": V_SC,
            "sigma_jt_m": SIGMA_JT_M,
            "rho_m": RHO_M,
            "A0": A0,
            "omega_L_eq_m": OMEGA_L_EQ_M,
            "chi": CHI,
            "chi_squared": CHI_SQUARED,
        },
        "grids": {
            "H_p": {"count": 500, "lower": float(hp_grid[0]), "upper": float(hp_grid[-1])},
            "X": {"count": 500, "lower": float(t_grid[0]), "upper": float(t_grid[-1])},
        },
        "normalization": {
            "H_p_integral": numerical_mass_hp(),
            "X_integral_log_t_minus_40_to_0": numerical_mass_x(),
        },
        "figures": [
            "hp_pdf_baseline.png",
            "x_pdf_baseline.png",
            "x_active_combined.png",
        ],
        "combined_plot_uses_saved_samples": True,
    }
    (OUTPUT_DIR / "baseline_analytical_pdf_results.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    print(f"Saved plots to {OUTPUT_DIR.resolve()}")
    return result


if __name__ == "__main__":
    run()
