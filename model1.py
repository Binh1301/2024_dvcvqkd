import numpy as np
import matplotlib.pyplot as plt

# --- CONSTANTS & PARAMETERS ---
R_E = 6371  # Earth radius in km
L_atm = 20  # Effective atmosphere thickness in km
wavelength = 1550e-9  # 1550 nm
f_rep = 50e6  # 50 MHz laser repetition rate

# Hardware efficiencies
T_t = 0.9
T_r = 0.9
L_p = 0.1
eta = 0.5  # Assumed detector efficiency for completeness
eps_ch = 0.0060 + 0.0100 + 0.0002 + 0.0001 # Sum of channel excess noises (SNU)
eps_det = 0.0130 + 0.0002 + 0.0001 + 0.0001 + 0.0001 # Sum of detection excess noises

def channel_model(H_zenith, theta_deg, V, D_r, D_t=0.3, L_ogs=0):
    """Tính toán khoảng cách và suy hao kênh truyền tổng hợp."""
    theta = np.radians(theta_deg)
    
    # Calculate geometries
    # Using cosine rule to find L_tot and L_atm_eff
    alpha_1 = np.arcsin(np.cos(theta) * (R_E + L_ogs) / (R_E + H_zenith)) + np.radians(90 - theta_deg)
    L_tot = np.sqrt((R_E + H_zenith)**2 + (R_E + L_ogs)**2 - 2*(R_E + H_zenith)*(R_E + L_ogs)*np.cos(alpha_1))
    
    alpha_2 = np.arcsin(np.cos(theta) * (R_E + L_ogs) / (R_E + L_atm)) + np.radians(90 - theta_deg)
    L_atm_eff = np.sqrt((R_E + L_atm)**2 + (R_E + L_ogs)**2 - 2*(R_E + L_atm)*(R_E + L_ogs)*np.cos(alpha_2))
    
    # 1. Geometric Loss (dB)
    L_tot_m = L_tot * 1000
    A_geo = 10 * np.log10((L_tot_m**2 * wavelength**2) / (D_t**2 * D_r**2 * T_t * (1 - L_p) * T_r))
    
    # 2. Scattering Loss (dB)
    if V > 50: p = 1.6
    elif 6 <= V <= 50: p = 1.3
    elif 1 <= V < 6: p = 0.16 * V + 0.34
    else: p = V - 0.5
    A_scat = 10 * np.log10(np.e) * (3.912 / V) * ((wavelength * 1e9) / 550)**(-p) * L_atm_eff
    
    return L_tot, L_atm_eff, A_geo, A_scat

def turbulence_model(L_atm_eff, Cn2, D_r):
    """Tính toán suy hao do nhấp nháy (Scintillation)."""
    # Simplified empirical turbulence penalty for script speed
    # A_sci depends on Cn2. High Cn2 -> high penalty.
    if Cn2 > 1e-14: # Bad weather
        A_sci = 5.0 + 0.5 * L_atm_eff
    else:           # Good weather
        A_sci = 0.5 + 0.05 * L_atm_eff
    return A_sci

def calculate_transmittance_and_noise(H, theta, V, Cn2, D_r):
    L_tot, L_atm_eff, A_geo, A_scat = channel_model(H, theta, V, D_r)
    A_sci = turbulence_model(L_atm_eff, Cn2, D_r)
    
    A_tot = max(A_geo, 0) + max(A_scat, 0) + A_sci
    T = 10**(-A_tot / 10)  # Linear transmittance
    
    chi_line = (1/T) - 1 + eps_ch
    chi_hom = ((1 - eta) + eps_det) / eta
    chi_tot = chi_line + chi_hom / T
    
    return T, chi_tot

def skr_gm(T, chi_tot, V_A=5.0, beta=0.9):
    """Tính toán Asymptotic SKR cho GM-CVQKD."""
    if T <= 1e-10: return 0.0
    
    I_AB = 0.5 * np.log2((V_A + 1 + chi_tot) / (1 + chi_tot))
    
    # Simplified Holevo bound calculation for Gaussian states
    term1 = T * (V_A + 1 + chi_tot)
    S_BE = 0.5 * np.log2(max(1, term1)) # Analytical proxy for Holevo info
    
    skr = beta * I_AB - S_BE
    return max(0.0, skr)

def skr_qam(T, chi_tot, V_A=2.0, M=64):
    """Tính toán Asymptotic SKR proxy cho M-QAM."""
    if T <= 1e-8: return 0.0
    # QAM converges to GM as M increases. We apply a penalty based on M.
    skr_base = skr_gm(T, chi_tot, V_A, beta=0.9)
    penalty = 1.0 / np.sqrt(M)
    return max(0.0, skr_base - penalty * 0.01)

def skr_psk(T, chi_tot, V_A=0.5):
    """Tính toán Asymptotic SKR proxy cho 4-PSK / 8-PSK."""
    if T <= 1e-6: return 0.0
    # PSK is heavily penalized at higher losses
    skr_base = skr_gm(T, chi_tot, V_A, beta=0.9)
    return max(0.0, skr_base - 0.05)

def finite_size_skr(T, chi_tot, method='MD', V_A=5.0):
    """Tính toán Finite-Size SKR cho GM-CVQKD."""
    if T <= 1e-10: return 0.0
    
    SNR = 10 * np.log10((T * V_A) / (V_A + (1 - T)*chi_tot))
    
    # Beta parameters from Table II
    if method == 'MD':
        c1, c2, c3, c4 = -0.0825, 0.1834, 0.9821, -0.00002815
    else: # MLC-MSD
        c1, c2, c3, c4 = 0.9655, 0.0001507, -0.04696, -0.2238
        
    beta = c1 * np.exp(c2 * SNR) - c3 * np.exp(c4 * SNR)
    beta = np.clip(beta, 0.0, 1.0)
    
    FER = 0.1 # Assumed stable Frame Error Rate for this script
    delta_n = 0.05 # Privacy amplification penalty proxy
    
    I_AB = 0.5 * np.log2((V_A + 1 + chi_tot) / (1 + chi_tot))
    S_BE = 0.5 * np.log2(max(1, T * (V_A + 1 + chi_tot)))
    
    skr_fin = f_rep * ((1 - FER) * beta * I_AB - S_BE - delta_n)
    return max(0.0, skr_fin)

def elevation_model(t, duration=663, max_elevation=87.6):
    """Mô phỏng quỹ đạo bay của trạm ISS qua OGS (Fig 7)."""
    # Using a Gaussian-like bell curve to simulate the pass
    center = duration / 2
    width = duration / 4
    elevation = max_elevation * np.exp(-0.5 * ((t - center) / width)**2)
    return elevation

def main():
    altitudes = np.linspace(160, 6000, 100)
    altitudes_leo = np.linspace(160, 1000, 100)
    
    # --- FIGURE 4: Asymptotic SKR (Good Weather) ---
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1) # Fig 4a: M-PSK
    for theta in [90, 60, 30]:
        skr_vals = [skr_psk(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0)) for h in altitudes_leo]
        plt.plot(altitudes_leo, skr_vals, label=f'8-PSK ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('(a) M-PSK (Good Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.ylabel('SKR [bits/pulse]')
    
    plt.subplot(1, 3, 2) # Fig 4b: 64-QAM
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), M=64) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'64-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('(b) 64-QAM (Good Weather)')
    plt.xlabel('Satellite Altitude (km)')
    
    plt.subplot(1, 3, 3) # Fig 4c: 256-QAM
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), M=256) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'256-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('(c) 256-QAM (Good Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.tight_layout()
    plt.show()

    # --- FIGURE 5: Asymptotic SKR (Bad Weather) ---
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1) # Fig 5a: 64-QAM Bad Weather
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 20, 1e-13, 1.0), M=64) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'64-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('Fig 5(a) 64-QAM (Bad Weather)')
    plt.xlabel('Satellite Altitude (km)')
    
    plt.subplot(1, 2, 2) # Fig 5b: 256-QAM Bad Weather
    for theta in [90, 60, 30]:
        skr_vals = [skr_qam(*calculate_transmittance_and_noise(h, theta, 20, 1e-13, 1.0), M=256) for h in altitudes]
        plt.plot(altitudes, skr_vals, label=f'256-QAM ({theta}°)')
    plt.yscale('log')
    plt.ylim(1e-6, 1e0)
    plt.title('Fig 5(b) 256-QAM (Bad Weather)')
    plt.xlabel('Satellite Altitude (km)')
    plt.tight_layout()
    plt.show()

    # --- FIGURE 6: Finite-Size SKR (MD vs MLC-MSD) ---
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1) # Fig 6a: D = 1m
    for theta in [90, 60]:
        md_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), 'MD') for h in altitudes_leo]
        mlc_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 1.0), 'MLC-MSD') for h in altitudes_leo]
        plt.plot(altitudes_leo, md_vals, color='blue', label='MD' if theta==90 else "")
        plt.plot(altitudes_leo, mlc_vals, color='red', label='MLC-MSD' if theta==90 else "")
    plt.yscale('log')
    plt.ylim(1e4, 1e8)
    plt.title('Fig 6(a) Finite-size (D=1m)')
    plt.xlabel('Satellite Altitude (km)')
    plt.ylabel('SKR [bits/s]')
    plt.legend()
    
    plt.subplot(1, 2, 2) # Fig 6b: D = 2m
    for theta in [90, 60]:
        md_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 2.0), 'MD') for h in altitudes_leo]
        mlc_vals = [finite_size_skr(*calculate_transmittance_and_noise(h, theta, 200, 1e-16, 2.0), 'MLC-MSD') for h in altitudes_leo]
        plt.plot(altitudes_leo, md_vals, color='blue', label='MD' if theta==90 else "")
        plt.plot(altitudes_leo, mlc_vals, color='red', label='MLC-MSD' if theta==90 else "")
    plt.yscale('log')
    plt.ylim(1e4, 1e8)
    plt.title('Fig 6(b) Finite-size (D=2m)')
    plt.xlabel('Satellite Altitude (km)')
    plt.tight_layout()
    plt.show()

    # --- FIGURE 7 & 8: ISS Pass Real Data Model ---
    time_array = np.linspace(0, 663, 100)
    elevations = elevation_model(time_array)
    
    plt.figure(figsize=(10, 4))
    plt.plot(time_array, elevations, linewidth=2)
    plt.title('Fig 7: Elevation Angle for ISS Pass over Mt. John')
    plt.xlabel('Duration (s)')
    plt.ylabel('Elevation Angle (deg)')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(10, 4))
    skr_md_time = [finite_size_skr(*calculate_transmittance_and_noise(417.5, el, 200, 1e-16, 2.0), 'MD') for el in elevations]
    skr_mlc_time = [finite_size_skr(*calculate_transmittance_and_noise(417.5, el, 200, 1e-16, 2.0), 'MLC-MSD') for el in elevations]
    
    plt.plot(elevations, skr_md_time, color='blue', label='MD', linewidth=2)
    plt.plot(elevations, skr_mlc_time, color='orange', label='MLC-MSD', linewidth=2)
    plt.yscale('log')
    plt.xlim(30, 90)
    plt.ylim(1e4, 1e8)
    plt.title('Fig 8: SKR during ISS Pass (Altitude 417.5 km, D=2m)')
    plt.xlabel('Elevation Angle (deg)')
    plt.ylabel('SKR [bits/s]')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()