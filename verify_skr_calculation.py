#!/usr/bin/env python3
"""
Verification for UAV-HAP Gaussian CV-QKD SKR at L=20 km, Cn2=1e-15.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from uav_hap.plots.skr_gaussian_uav_hap import compute_skr_gaussian


def _ok(value: float, target: float, tol: float) -> str:
    return "PASS" if abs(value - target) <= tol else "FAIL"


if __name__ == "__main__":
    out = compute_skr_gaussian(
        l_link_km=20.0,
        l_aperture_m=0.20,
        v_a=2.0,
        eta_det=0.97,
        beta=0.95,
        xi_km_inv=0.09232,
        w0_m=0.0626,
        wavelength_m=1550e-9,
        cn2=1e-15,
        sigma_x_m=0.0521,
        sigma_y_m=0.0502,
        sigma_z_m=0.0703,
        sigma_th_rad=2.60e-3,
        sigma_ph_rad=2.04e-3,
        sigma_ps_rad=4.06e-3,
        eps_ch=0.01,
        v_el=0.01,
        n_samples=30_000,
        seed=42,
    )

    vals = {k: float(v) for k, v in out.items()}

    refs = {
        "eta_atm": (0.15780, 2e-4),
        "z_R": (7942.68, 0.8),
        "W_L": (0.16960, 3e-4),
        "T_0": (0.96852, 3e-4),
        "sigma2_r": (0.040866, 5e-4),
        "Gamma": (2.5779, 6e-3),
        "mean_T2": (0.51995, 0.015),
        "T_eff": (0.08205, 0.003),
        "chi_hom": (0.041237, 5e-5),
        "chi_line": (11.1976, 0.25),
        "chi_tot": (11.7002, 0.35),
        "I_AB": (0.10519, 0.01),
        "lambda3": (2.668, 0.05),
        "chi_BE": (0.094, 0.03),
        "SKR": (0.0059, 0.01),
    }

    print("=" * 72)
    print("UAV-HAP CV-QKD SKR VERIFICATION")
    print("=" * 72)
    for name, (target, tol) in refs.items():
        value = vals[name]
        print(f"{name:>10s} = {value:>10.6f} | ref {target:>10.6f} | {_ok(value, target, tol)}")
    print("=" * 72)
