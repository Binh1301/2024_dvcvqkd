"""
Deep diagnostics: Investigate why Z_raw > Zmax persists even at ideal channel params.
Purpose: Audit Z* convention, mapping, and identify root cause of clipping.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1.config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_BETA,
        QAM_NCUT_BINOMIAL,
    )
    from uav_hap_1.protocol.qam_protocol import (
        build_state_binomial,
        compute_metrics,
    )
    from uav_hap_1.zstar import base as zbase
else:
    from .config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_BETA,
        QAM_NCUT_BINOMIAL,
    )
    from .protocol.qam_protocol import (
        build_state_binomial,
        compute_metrics,
    )
    from .zstar import base as zbase


def audit_zstar_convention():
    """
    Audit Z* calculation and convention.
    
    Current implementation:
        Z* = 2*sqrt(T)*TrC - sqrt(2*T*eps*w)
    
    This is used in covariance matrix Gamma_AB:
        Gamma_AB = [[aI, Z*sigma_z], [Z*sigma_z, bI]]
    where a = VA+1, b = 1+T*VA+T*eps
    
    Zmax = sqrt(ab) is the maximum value Z* can take for matrix to be physical.
    
    Hypothesis: The convention might be off by a factor (sqrt(2), 2, etc.)
    """
    print("=" * 80)
    print("AUDIT: Z* CONVENTION AND COVARIANCE MAPPING")
    print("=" * 80)

    # Build binomial state at reasonable params
    state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    print(f"\nBinomial state (Ncut={QAM_NCUT_BINOMIAL}):")
    print(f"  VA = {state.va:.10f}")
    print(f"  TrC = {state.tr_c:.10f}")
    print(f"  w = {state.w:.10f}")

    # Test with ideal-ish channel
    T = 0.95
    eps = 0.0
    eta = 0.99
    v_el = 0.0
    
    print(f"\nChannel params (near-ideal):")
    print(f"  T = {T}, eps = {eps}, eta = {eta}, v_el = {v_el}")

    # Compute Z* using current formula
    z_raw = zbase.compute_zstar(state.tr_c, state.w, T, eps)
    
    # Compute covariance eigenvalues
    a = state.va + 1.0
    b = 1.0 + T * state.va + T * eps
    z_max = np.sqrt(a * b)
    
    print(f"\nCovariance matrix parameters:")
    print(f"  a = VA + 1 = {a:.10f}")
    print(f"  b = 1 + T*VA + T*eps = {b:.10f}")
    print(f"  Zmax = sqrt(ab) = {z_max:.10f}")
    
    print(f"\nZ* calculation:")
    term_signal = 2 * np.sqrt(T) * state.tr_c
    term_noise = np.sqrt(2 * T * eps * state.w)
    z_raw_verify = term_signal - term_noise
    
    print(f"  term_signal = 2*sqrt(T)*TrC = {term_signal:.10f}")
    print(f"  term_noise = sqrt(2*T*eps*w) = {term_noise:.10f}")
    print(f"  Z*_raw = signal - noise = {z_raw:.10f}")
    print(f"  Verify: {z_raw_verify:.10f} (match: {np.isclose(z_raw, z_raw_verify)})")
    
    print(f"\nPhysicality check:")
    print(f"  Z*_raw / Zmax = {z_raw / z_max:.6f} (should be <= 1.0)")
    print(f"  Status: {'physical' if z_raw <= z_max else 'CLIPPED'}")
    
    # Try alternative conventions (debug only)
    print(f"\n" + "=" * 80)
    print("TESTING ALTERNATIVE CONVENTIONS (diagnostic only)")
    print("=" * 80)
    
    alt_conventions = [
        ("Current: 2*sqrt(T)*TrC - sqrt(2*T*eps*w)", 2, 1.0, 2.0),
        ("Alt 1: sqrt(T)*TrC - sqrt(2*T*eps*w) [half signal]", 1, 1.0, 2.0),
        ("Alt 2: 2*sqrt(T)*TrC - sqrt(T*eps*w) [half noise sqrt]", 2, 1.0, 1.0),
        ("Alt 3: 2*sqrt(T)*TrC - T*eps*w [no sqrt on noise]", 2, 1.0, 0.5),
        ("Alt 4: sqrt(T)*TrC - sqrt(T*eps*w)/sqrt(2) [symmetric factors]", 1, 1.0, 0.5),
    ]
    
    for label, sig_scale, sig_sqrt_scale, noise_scale in alt_conventions:
        # Compute with alternative convention
        alt_signal = sig_scale * (np.sqrt(T) ** sig_sqrt_scale) * state.tr_c
        alt_noise = noise_scale * np.sqrt(T * eps * state.w)
        alt_z = alt_signal - alt_noise
        ratio = alt_z / z_max if z_max > 0 else np.inf
        status = "✓ physical" if alt_z <= z_max else "✗ clipped"
        print(f"\n{label}")
        print(f"  Z* = {alt_z:.10f}, ratio = {ratio:.6f} {status}")
    
    # Check if problem is simply scale of Z
    print(f"\n" + "=" * 80)
    print("SCALE ANALYSIS: What happens if we scale Z_raw down?")
    print("=" * 80)
    
    scale_factors = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    for scale in scale_factors:
        z_scaled = z_raw * scale
        ratio = z_scaled / z_max
        status = "physical" if z_scaled <= z_max else "clipped"
        print(f"  Z* * {scale:.1f} = {z_scaled:.10f}, ratio = {ratio:.6f} [{status}]")
    
    # Investigate term magnitudes across parameter space
    print(f"\n" + "=" * 80)
    print("TERM MAGNITUDE ANALYSIS: Signal vs Noise balance")
    print("=" * 80)
    
    # Simulate how Z_raw changes with T and eps
    for T_test in [0.1, 0.3, 0.5, 0.7, 0.9, 0.95]:
        for eps_test in [0.0, 0.001, 0.005, 0.01]:
            sig = 2 * np.sqrt(T_test) * state.tr_c
            noi = np.sqrt(2 * T_test * eps_test * state.w)
            z = sig - noi
            a_test = state.va + 1.0
            b_test = 1.0 + T_test * state.va + T_test * eps_test
            z_max_test = np.sqrt(a_test * b_test)
            ratio = z / z_max_test
            clipped = "Y" if z > z_max_test else "N"
            print(f"  T={T_test:.2f}, eps={eps_test:.4f}: Z*={z:.6f}, Zmax={z_max_test:.6f}, "
                  f"ratio={ratio:.4f}, clipped={clipped}")


if __name__ == "__main__":
    audit_zstar_convention()
