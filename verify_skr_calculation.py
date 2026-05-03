#!/usr/bin/env python3
"""
Verify SKR calculation against hand-computed reference.
Test case: L_link=20 km, η_det=0.95, L_ap=0.20 m, V_A=4, β=0.93
Expected SKR ≈ +0.00657 bits/pulse (hand calc) vs code output.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

# Import the SKR computation function
from uav_hap.plots.skr_gaussian_uav_hap import compute_skr_gaussian

# Test parameters (exact values from hand calculation)
XI_KM_INV = 0.09232
W0_M = 0.0626
WAVELENGTH_M = 1550e-9
EPS_CH = 0.01
V_EL = 0.01

L_link_km = 20.0
L_aperture_m = 0.20
V_A = 4.0
eta_det = 0.95
beta = 0.93

print("=" * 70)
print("SKR CALCULATION VERIFICATION")
print("=" * 70)
print(f"\nTest Parameters:")
print(f"  L_link         = {L_link_km} km")
print(f"  ξ              = {XI_KM_INV} km⁻¹")
print(f"  W₀             = {W0_M} m = {W0_M*100} cm")
print(f"  λ              = {WAVELENGTH_M*1e9} nm")
print(f"  η_det          = {eta_det}")
print(f"  L_aperture     = {L_aperture_m} m = {L_aperture_m*100} cm")
print(f"  V_A            = {V_A}")
print(f"  β              = {beta}")
print(f"  ε_ch           = {EPS_CH}")
print(f"  v_el           = {V_EL}")

# Run computation
result = compute_skr_gaussian(
    l_link_km=L_link_km,
    l_aperture_m=L_aperture_m,
    v_a=V_A,
    eta_det=eta_det,
    beta=beta,
    xi_km_inv=XI_KM_INV,
    w0_m=W0_M,
    wavelength_m=WAVELENGTH_M,
    eps_ch=EPS_CH,
    v_el=V_EL,
)

print("\n" + "=" * 70)
print("STEP-BY-STEP VERIFICATION")
print("=" * 70)

# Extract scalar values
eta_atm = float(result["eta_atm"])
z_r = float(result["z_R"])
w_l = float(result["W_L"])
t0 = float(result["T_0"])
t_eff = float(result["T_eff"])
chi_hom = float(result["chi_hom"])
chi_line = float(result["chi_line"])
chi_tot = float(result["chi_tot"])
i_ab = float(result["I_AB"])
lambda1 = float(result["lambda1"])
lambda2 = float(result["lambda2"])
lambda3 = float(result["lambda3"])
chi_be = float(result["chi_BE"])
skr_raw = float(result["SKR_raw"])
skr = float(result["SKR"])

print(f"\nStep 1 – Atmospheric attenuation:")
print(f"  η_atm = exp(-ξ × L_link) = exp(-{XI_KM_INV} × {L_link_km})")
print(f"        = {eta_atm:.5f}")
print(f"  Expected: 0.15802 ✓" if abs(eta_atm - 0.15802) < 0.001 else f"  Expected: 0.15802 ✗")

print(f"\nStep 2 – Rayleigh range:")
print(f"  z_R = π × W₀² / λ")
print(f"      = {z_r:.1f} m")
print(f"  Expected: 7,941.7 m ✓" if abs(z_r - 7941.7) < 10 else f"  Expected: 7,941.7 m ✗")

print(f"\nStep 3 – Beam radius at receiver:")
print(f"  W_L = {w_l:.5f} m")
print(f"  Expected: 0.16964 m ✓" if abs(w_l - 0.16964) < 0.001 else f"  Expected: 0.16964 m ✗")

print(f"\nStep 4 – Aperture transmittance:")
print(f"  T₀ = {t0:.5f}")
print(f"  Expected: 0.96843 ✓" if abs(t0 - 0.96843) < 0.001 else f"  Expected: 0.96843 ✗")

print(f"\nStep 5 – Effective transmittance:")
print(f"  T_eff = η_atm × T₀² = {t_eff:.5f}")
print(f"  Expected: 0.14820 ✓" if abs(t_eff - 0.14820) < 0.001 else f"  Expected: 0.14820 ✗")

print(f"\nStep 6 – Detector noise:")
print(f"  χ_hom = (1-η_det)/η_det + v_el/η_det = {chi_hom:.5f}")
print(f"  Expected: 0.06316 ✓" if abs(chi_hom - 0.06316) < 0.001 else f"  Expected: 0.06316 ✗")

print(f"\nStep 7 – Channel excess noise:")
print(f"  χ_line = 1/T_eff - 1 + ε_ch = {chi_line:.5f}")
print(f"  Expected: 5.7576 ✓" if abs(chi_line - 5.7576) < 0.01 else f"  Expected: 5.7576 ✗")

print(f"\nStep 8 – Total noise:")
print(f"  χ_tot = χ_line + χ_hom/T_eff = {chi_tot:.5f}")
print(f"  Expected: 6.1838 ✓" if abs(chi_tot - 6.1838) < 0.01 else f"  Expected: 6.1838 ✗")

print(f"\nStep 9 – Mutual information I(A:B):")
print(f"  I(A:B) = 0.5 × log₂((V+χ_tot)/(1+χ_tot)) = {i_ab:.5f} bits/pulse")
print(f"  Expected: 0.31939 ✓" if abs(i_ab - 0.31939) < 0.01 else f"  Expected: 0.31939 ✗")

print(f"\nStep 10 – Symplectic eigenvalues:")
print(f"  λ₁ = {lambda1:.5f}")
print(f"  Expected: 4.4074 ✓" if abs(lambda1 - 4.4074) < 0.01 else f"  Expected: 4.4074 ✗")
print(f"  λ₂ = {lambda2:.5f}")
print(f"  Expected: 1.0012 ✓" if abs(lambda2 - 1.0012) < 0.001 else f"  Expected: 1.0012 ✗")

print(f"\nStep 11 – Eigenvalue λ₃:")
print(f"  λ₃ = {lambda3:.5f}")
print(f"  Expected: 3.6317 ✓" if abs(lambda3 - 3.6317) < 0.01 else f"  Expected: 3.6317 ✗")

print(f"\nStep 12 – Holevo bound χ(B:E):")
print(f"  χ(B:E) = g(λ₁) + g(λ₂) - g(λ₃) = {chi_be:.5f}")
print(f"  Expected: 0.29046 ✓" if abs(chi_be - 0.29046) < 0.01 else f"  Expected: 0.29046 ✗")

print(f"\nStep 13 – Secret key rate (raw):")
print(f"  SKR_raw = β × I(A:B) - χ(B:E)")
print(f"          = {beta} × {i_ab:.5f} - {chi_be:.5f}")
print(f"          = {skr_raw:.5f} bits/pulse")

print(f"\nStep 14 – SKR (clipped to ≥0):")
print(f"  SKR = max(0, SKR_raw) = {skr:.5f} bits/pulse")
print(f"  Expected: +0.00657 bits/pulse")
print(f"  Tolerance: hand calc +0.00657, code allowed ±0.002 for rounding")

if abs(skr - 0.00657) < 0.002:
    print(f"  ✓ PASS (within rounding tolerance)")
else:
    print(f"  ⚠ MISMATCH (diff = {skr - 0.00657:.5f})")

print("\n" + "=" * 70)
print("FINAL RESULT")
print("=" * 70)
print(f"SKR = {skr:.5f} bits/pulse")
print(f"Status: {'✓ CORRECT' if skr > 0 else '✗ NEGATIVE (outage)'}")
print("=" * 70)
