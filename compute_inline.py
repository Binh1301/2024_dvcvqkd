"""Inline computation of SKR metrics using direct imports."""
try:
    import sys
    import os
    os.chdir(r'E:\py learn\adversarial_attack_DRL\2024_dvcvqkd')
    sys.path.insert(0, '.')
    
    import numpy as np
    from scipy.special import erfinv
    
    # Import all required functions and constants
    from cvqkd_simulation import (
        link_geometry, total_transmittance, skr_gm, skr_psk,
        VA_GM, VA_PSK, EPS_CH, LAMBDA, DT
    )
    
    # Parameters as specified
    theta_deg = 90.0
    H_zen = 380_000  # 380 km in meters
    Dr = 1.0  # 1 meter
    V_km = 200  # 200 km in km
    Cn2 = 1e-16
    beta = 0.9
    
    # Get transmittance and link geometry
    T, L_tot, far_field_ok = total_transmittance(theta_deg, H_zen, Dr, V_km, Cn2)
    L_km = L_tot / 1000.0
    
    # Calculate far-field parameter
    L_tot_geo, L_atm = link_geometry(theta_deg, H_zen)
    k = 2 * np.pi / LAMBDA
    d_farfield = np.sqrt(k * Dr**2 / (4 * L_atm))
    
    # Calculate SKR values
    skr_4psk = skr_psk(VA_PSK, T, EPS_CH, 4, beta)
    skr_8psk = skr_psk(VA_PSK, T, EPS_CH, 8, beta)
    skr_gm_val = skr_gm(VA_GM, T, EPS_CH, beta)
    
    # Print results in exact scientific format
    print(f"T = {T:.10e}")
    print(f"L_km = {L_km:.10e}")
    print(f"far_field = {d_farfield:.10e}")
    print(f"SKR_4PSK (asymptotic bits/pulse) = {skr_4psk:.10e}")
    print(f"SKR_8PSK (asymptotic bits/pulse) = {skr_8psk:.10e}")
    print(f"SKR_GM (asymptotic bits/pulse) = {skr_gm_val:.10e}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", file=__import__('sys').stderr)
    import traceback
    traceback.print_exc()
