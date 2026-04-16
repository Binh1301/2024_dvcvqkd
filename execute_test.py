#!/usr/bin/env python
"""
Execute compile check and SKR computations
"""
import sys
import py_compile
import os
import traceback

# Change to the correct directory
os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

print("=" * 120)
print("STEP 1: Compile Check")
print("=" * 120)

try:
    py_compile.compile('cvqkd_simulation.py', doraise=True)
    print("✓ Compilation successful: cvqkd_simulation.py")
except py_compile.PyCompileError as e:
    print(f"✗ Compilation failed:")
    print(e)
    sys.exit(1)

print("\n" + "=" * 120)
print("STEP 2: Computing SKR Values")
print("=" * 120 + "\n")

sys.path.insert(0, r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')

try:
    from cvqkd_simulation import (
        total_transmittance, 
        skr_gm, 
        skr_psk, 
        skr_qam,
        EPS_CH,
        VA_GM,
        VA_PSK,
        VA_QAM
    )
    import numpy as np
    
    # Parameters
    theta_deg = 90
    Dr = 1.0
    V = 200
    Cn2 = 1e-16
    beta = 0.9
    eps = EPS_CH
    
    altitudes = [160e3, 300e3, 450e3, 600e3]
    
    print("=" * 120)
    print(f"{'Altitude(km)':<12} {'T':<10} {'SKR_GM':<12} {'SKR_8PSK':<12} {'SKR_4PSK':<12} {'SKR_64QAM_b':<12} {'SKR_64QAM_dg':<14} {'SKR_256QAM_b':<14} {'SKR_256QAM_dg':<14}")
    print("=" * 120)
    
    for h in altitudes:
        T, L_tot, ff_ok = total_transmittance(theta_deg, h, Dr, V, Cn2)
        
        # Compute SKR values
        # Note: The provided script used uppercase function names that don't exist.
        # Using the actual function names: skr_gm, skr_psk, skr_qam
        skr_gm_val = skr_gm(VA_GM, T, eps, beta)
        skr_8psk_val = skr_psk(VA_PSK, T, eps, 8, beta)
        skr_4psk_val = skr_psk(VA_PSK, T, eps, 4, beta)
        skr_64qam_b_val = skr_qam(VA_QAM, T, eps, 64, beta, prob_model='binomial')
        skr_64qam_dg_val = skr_qam(VA_QAM, T, eps, 64, beta, prob_model='disc_gaussian')
        skr_256qam_b_val = skr_qam(VA_QAM, T, eps, 256, beta, prob_model='binomial')
        skr_256qam_dg_val = skr_qam(VA_QAM, T, eps, 256, beta, prob_model='disc_gaussian')
        
        alt_km = h / 1000
        print(f"{alt_km:<12.0f} {T:<10.4f} {skr_gm_val:<12.6f} {skr_8psk_val:<12.6f} {skr_4psk_val:<12.6f} {skr_64qam_b_val:<12.6f} {skr_64qam_dg_val:<14.6f} {skr_256qam_b_val:<14.6f} {skr_256qam_dg_val:<14.6f}")
    
    print("=" * 120)
    print("\n✓ All computations completed successfully!")
    
except Exception as e:
    print(f"\n✗ Error during execution:")
    print(traceback.format_exc())
    sys.exit(1)
