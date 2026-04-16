#!/usr/bin/env python
"""Check current SKR values across different modulation schemes."""

import sys
import py_compile

# Step 1: Compile check
try:
    py_compile.compile(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd\cvqkd_simulation.py', doraise=True)
    print("✓ Compilation successful")
except Exception as e:
    print(f"✗ Compilation failed: {e}")
    sys.exit(1)

print()

# Step 2: Import and calculate SKR values
sys.path.insert(0, r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

from cvqkd_simulation import (
    total_transmittance, skr_gm, skr_psk, skr_qam,
    EPS_CH, VA_GM, VA_PSK, VA_QAM
)
import numpy as np

# Parameters
theta_deg = 90
Dr = 1.0
V_km = 200
Cn2 = 1e-16
beta = 0.9
eps = EPS_CH

altitudes = [160e3, 300e3, 450e3, 600e3]

print(f"{'Altitude(km)':<12} {'T':<10} {'SKR_GM':<12} {'SKR_8PSK':<12} {'SKR_4PSK':<12} {'SKR_64QAM_b':<12} {'SKR_64QAM_dg':<14} {'SKR_256QAM_b':<14} {'SKR_256QAM_dg':<14}")
print("-" * 110)

for h in altitudes:
    T, L_tot, ff_ok = total_transmittance(theta_deg, h, Dr, V_km, Cn2)
    
    skr_gm_val = skr_gm(VA_GM, T, eps, beta)
    skr_8psk_val = skr_psk(VA_PSK, T, eps, 8, beta)
    skr_4psk_val = skr_psk(VA_PSK, T, eps, 4, beta)
    skr_64qam_b = skr_qam(VA_QAM, T, eps, 64, beta, prob_model='binomial')
    skr_64qam_dg = skr_qam(VA_QAM, T, eps, 64, beta, prob_model='disc_gaussian')
    skr_256qam_b = skr_qam(VA_QAM, T, eps, 256, beta, prob_model='binomial')
    skr_256qam_dg = skr_qam(VA_QAM, T, eps, 256, beta, prob_model='disc_gaussian')
    
    alt_km = h / 1000
    print(f"{alt_km:<12.0f} {T:<10.4f} {skr_gm_val:<12.6f} {skr_8psk_val:<12.6f} {skr_4psk_val:<12.6f} {skr_64qam_b:<12.6f} {skr_64qam_dg:<14.6f} {skr_256qam_b:<14.6f} {skr_256qam_dg:<14.6f}")
